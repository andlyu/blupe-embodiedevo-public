"""Resume only pinned public RoboDojo assets with the current Hub retry client."""
import importlib.metadata
import json
import os
from pathlib import Path

# Read before importing Hub. The simulator's older Hub/Xet stack exhausted the
# per-IP API bucket. HTTP resolver downloads and SDK-managed reset waits are
# documented alternatives, with two workers to avoid another request burst.
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT', '60')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
from huggingface_hub import snapshot_download

root = Path(__file__).resolve().parents[2]
lock = json.loads((root / 'worker-agent/runtime-lock.json').read_text())['assets']
target = root / 'upstream/EmbodiedEvo/vendor/robodojo'
print(json.dumps({'event': 'assets_download_started', 'revision': lock['revision'],
                  'client': importlib.metadata.version('huggingface-hub'),
                  'max_workers': 2, 'anonymous_public_assets': True}), flush=True)
snapshot_download(repo_id=lock['repository'], repo_type='dataset',
                  revision=lock['revision'], allow_patterns=[lock['pattern']],
                  local_dir=str(target), max_workers=2, token=False)
for directory in ['Robots', 'Object', 'Material', 'Eval_Layout']:
    if not (target / 'Assets' / directory).is_dir():
        raise RuntimeError('Missing pinned Assets/' + directory)
print(json.dumps({'event': 'assets_download_completed', 'revision': lock['revision']}), flush=True)
