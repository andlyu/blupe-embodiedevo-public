"""Pure job/provenance helpers. No simulator, model, or robot is started here."""
import hashlib
import base64
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from skill_library import SKILL_LIBRARY_REVISION, SKILLS as UPSTREAM_SKILLS

PINS = {'embodiedevo': '470278c478bdb5e4b6f17dde1ea0393761f230f0',
        'blupe': 'e8158b7cfcbb90b2824dfc73e632b537bdfd942c'}
TASKS = {'stack_blocks', 'cover_blocks', 'stack_bowls'}

def latest_observation(run, kind):
    """Select a public head-camera frame from this job's native phase only."""
    if kind == 'practice':
        sessions = [run / 'playground']
    elif kind == 'sim_test':
        sessions = (run / 'test').glob('scene_*')
    elif kind == 'hardware':
        sessions = [run / 'session']
    else:
        raise ValueError('Unsupported observation phase')
    frames = (frame for session in sessions for frame in
              session.glob('workspace/observations/*/current_cam_head.png'))
    return max(frames, key=lambda path: path.stat().st_mtime_ns, default=None)

def native_run_path(directory, kind):
    """Persist the original timestamped run identity across Practice and Test."""
    pointer = directory / 'native-run.json'
    if kind == 'practice':
        name = datetime.now(timezone.utc).strftime('%Y%m%d%H%M') + '_practice'
        with pointer.open('x') as target:
            json.dump({'directory': name}, target)
    name = json.loads(pointer.read_text())['directory']
    if not re.fullmatch(r'[0-9]{12}_practice', name):
        raise ValueError('Invalid original native run identity')
    return directory / name

def verify_pins(root):
    for name, path in [('embodiedevo', 'EmbodiedEvo'), ('blupe', 'blupe-remote-yam')]:
        directory = root / 'upstream' / path
        revision = subprocess.check_output(['git', '-C', str(directory), 'rev-parse', 'HEAD'], text=True).strip()
        if revision != PINS[name]:
            raise ValueError(f'{name} source revision differs from the website pin')
        subprocess.run(['git', '-C', str(directory), 'diff', '--quiet', 'HEAD', '--'], check=True)

def validate_job(job):
    if job.get('kind') not in {'practice', 'sim_test', 'hardware'}:
        raise ValueError('Unsupported execution kind')
    if job.get('method')!='EmbodiedEvo' or job.get('execution_mode') not in {'Practice','simulation Test','physical YAM'}:
        raise ValueError('Actual method and execution mode are required')
    runner_name=job.get('runner_name')
    email=job.get('email')
    if not isinstance(runner_name,str) or not 2<=len(runner_name.strip())<=120 or any(ord(c)<32 or ord(c)==127 for c in runner_name):
        raise ValueError('A confirmed human runner name is required')
    if not isinstance(email,str) or len(email)>254 or not re.fullmatch(r'\S+@\S+\.\S+',email.strip()):
        raise ValueError('A confirmed runner email is required')
    for key in ['id', 'campaign']:
        if not re.fullmatch(r'[a-f0-9-]{36}', str(job.get(key, ''))):
            raise ValueError('Invalid job identity')
    c = job['config']
    direct_yam = job['kind'] == 'hardware' and c.get('direct_yam') is True
    if (c.get('task') not in (UPSTREAM_SKILLS if direct_yam else TASKS)
            or c.get('model') != 'gpt-6-astra' or c.get('effort') != 'xhigh'):
        raise ValueError('Unsupported task or agent configuration')
    if c.get('pins') != PINS:
        raise ValueError('Campaign source pins differ')
    if direct_yam:
        if (c.get('skill_id') != c.get('task')
                or c.get('skill_library_revision') != SKILL_LIBRARY_REVISION):
            raise ValueError('The direct YAM skill source or its pinned revision is unsupported')
    elif c.get('direct_yam') is True or c.get('skill_id') is not None or c.get('skill_library_revision') is not None:
        raise ValueError('Direct upstream skills are supported only by the direct YAM job path')
    for key, minimum, maximum in [('budget',1,100),('scenes',1,25),('seed',0,2147483647),('seconds',60,1800)]:
        if type(c.get(key)) is not int or not minimum <= c[key] <= maximum:
            raise ValueError('Invalid campaign '+key)
    if job['kind']=='hardware':
        h=job.get('hardware',{})
        if h.get('method')!='EmbodiedEvo' or h.get('robot')!='yam-1' or not isinstance(h.get('task'),str) or not 5<=len(h['task'])<=2000:
            raise ValueError('EmbodiedEvo physical task and supported YAM station are required')
        for key,minimum,maximum in [('seconds',60,600),('budget',1,100)]:
            if type(h.get(key)) is not int or not minimum<=h[key]<=maximum:
                raise ValueError('Invalid physical '+key)
        if h.get('method')!='EmbodiedEvo' or h.get('runner_name')!=runner_name or h.get('email')!=email:
            raise ValueError('The physical task attribution differs from the confirmed runner or method')
        if direct_yam:
            if (h.get('source') != 'upstream_skill_library'
                    or h.get('skill_id') != c.get('skill_id')
                    or h.get('skill_library_revision') != SKILL_LIBRARY_REVISION
                    or job.get('artifact') not in (None, '')):
                raise ValueError('Direct YAM jobs must use the selected pinned upstream skill set without a simulator artifact')
        elif not re.fullmatch(r'[a-f0-9-]{36}',str(job.get('artifact',''))):
            raise ValueError('Physical transfer requires the original frozen artifact')
    return job

def frozen_files(run):
    protocol = json.loads((run / 'protocol.json').read_text())
    if protocol.get('phase') != 'frozen' or protocol.get('playground_valid') is not True:
        raise ValueError('Native Playground did not reach a valid frozen state')
    base = run / 'frozen_harness'
    if {p.name for p in base.iterdir()} != {'skills','lessons'}:
        raise ValueError('Frozen source must contain only skills and lessons')
    files = []
    for path in sorted(base.rglob('*')):
        if path.is_symlink():
            raise ValueError('Frozen knowledge cannot contain symlinks')
        if path.is_file():
            raw = path.read_bytes()
            try:
                content = raw.decode('utf-8')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                content = base64.b64encode(raw).decode('ascii')
                encoding = 'base64'
            files.append({'path':path.relative_to(base).as_posix(), 'content':content,
                          'encoding':encoding, 'sha256':hashlib.sha256(raw).hexdigest()})
    actual = {f['path']:f['sha256'] for f in files}
    if protocol.get('harness') != actual:
        raise ValueError('Native frozen hashes differ from package contents')
    return files

def outcomes(run):
    path = run / 'test.json'
    if not path.exists():
        return []
    report = json.loads(path.read_text())
    return [{'scene':i+1,'success':r.get('task_completed') if type(r.get('task_completed')) is bool else None,
             'valid':r.get('valid') if type(r.get('valid')) is bool else None,
             'reason':str(r.get('failure') or r.get('reason') or '')[:300]}
            for i,r in zip(report.get('scene_indices', []),report.get('results', []))]
