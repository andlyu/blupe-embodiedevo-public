"""Pinned upstream EmbodiedEvo skill files for direct YAM sessions."""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

MANIFEST_PATH = Path(__file__).resolve().parents[1] / 'upstream_skill_manifest.json'
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
SKILL_LIBRARY_REVISION = MANIFEST['revision']
SKILL_LIBRARY_REPOSITORY = MANIFEST['repository']
SKILL_LIBRARY_URL = MANIFEST['repository_url']
SKILL_LIBRARY_PATH = MANIFEST['library_path']
SKILLS = MANIFEST['skills']
MAX_FILE_BYTES = 64 * 1024
MAX_TOTAL_BYTES = 64 * 1024
MAX_FILES = 20
RAW_ORIGIN = 'https://raw.githubusercontent.com'


def skill_manifest(skill_id):
    """Return immutable, task-matched metadata from the checked-in manifest."""
    if not isinstance(skill_id, str) or skill_id not in SKILLS:
        raise ValueError('Choose an upstream skill available in the pinned library')
    skill = SKILLS[skill_id]
    files = skill.get('files')
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise ValueError('The pinned upstream skill manifest is invalid')
    destinations = set()
    total = 0
    checked = []
    prefix = f"{SKILL_LIBRARY_PATH}/{skill_id}/"
    for item in files:
        source = item.get('source', '')
        destination = item.get('destination', '')
        size = item.get('bytes')
        digest = item.get('git_blob_sha1', '')
        relative = PurePosixPath(destination) if isinstance(destination, str) else PurePosixPath('.')
        if (not isinstance(source, str) or not source.startswith(prefix)
                or '..' in PurePosixPath(source).parts
                or relative.is_absolute() or not relative.parts
                or any(part in {'', '.', '..'} for part in relative.parts)
                or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', '/'.join(relative.parts))
                or relative.suffix not in {'.md', '.py'}
                or destination in destinations or type(size) is not int
                or not 0 < size <= MAX_FILE_BYTES
                or not re.fullmatch(r'[a-f0-9]{40}', digest)):
            raise ValueError('The pinned upstream skill manifest contains an unsafe file entry')
        if source != prefix + destination:
            raise ValueError('The upstream source path does not match its selected skill')
        destinations.add(destination)
        total += size
        checked.append({'source': source, 'destination': destination,
                        'git_blob_sha1': digest, 'bytes': size})
    if total > MAX_TOTAL_BYTES:
        raise ValueError('The selected upstream skill exceeds the download size limit')
    return {'skill_id': skill_id, 'name': skill['name'], 'task': skill['task'],
            'repository': SKILL_LIBRARY_REPOSITORY,
            'repository_url': SKILL_LIBRARY_URL,
            'library_path': SKILL_LIBRARY_PATH,
            'revision': SKILL_LIBRARY_REVISION,
            'revision_url': f"{SKILL_LIBRARY_URL}/tree/{SKILL_LIBRARY_REVISION}/{SKILL_LIBRARY_PATH}/{skill_id}",
            'files': checked}


def git_blob_sha1(content):
    return hashlib.sha1(b'blob ' + str(len(content)).encode('ascii') + b'\0' + content).hexdigest()


def download_skill_set(skill_id, task, skills_directory):
    """Fetch one selected skill set and verify every Git object before use."""
    source = skill_manifest(skill_id)
    if task != source['task']:
        raise ValueError('The upstream skill set must match its selected RoboDojo task')
    skills_dir = Path(skills_directory)
    if skills_dir.is_symlink():
        raise ValueError('The frozen skills directory cannot be a symbolic link')
    skills_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for item in source['files']:
        relative = PurePosixPath(item['destination'])
        destination = skills_dir.joinpath(*relative.parts)
        parent = skills_dir
        for part in relative.parts[:-1]:
            parent = parent / part
            if parent.is_symlink():
                raise ValueError('An upstream skill destination cannot traverse a symbolic link')
            parent.mkdir(exist_ok=True)
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"Upstream skill file conflicts with an existing file: {item['destination']}")
        path = quote(item['source'], safe='/')
        url = f"{RAW_ORIGIN}/{SKILL_LIBRARY_REPOSITORY}/{SKILL_LIBRARY_REVISION}/{path}"
        try:
            request = Request(url, headers={'User-Agent': 'BluPe-EmbodiedEvo-worker'})
            with urlopen(request, timeout=12) as response:
                content = response.read(MAX_FILE_BYTES + 1)
        except (OSError, URLError) as exc:
            raise RuntimeError(f"Could not download pinned upstream file {item['source']}: {exc}") from exc
        if len(content) != item['bytes'] or len(content) > MAX_FILE_BYTES:
            raise ValueError(f"Upstream file size changed at {item['source']}")
        if git_blob_sha1(content) != item['git_blob_sha1']:
            raise ValueError(f"Git blob SHA-1 mismatch for upstream file {item['source']}")
        destination.write_bytes(content)
        written.append(item)
    return {**source, 'files': written, 'status': 'verified'}
