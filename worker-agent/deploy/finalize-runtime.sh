#!/usr/bin/env bash
# Resume a prepared native environment after a public asset download failure.
set -euo pipefail
umask 077
finish_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
finish_upstream="$finish_root/upstream/EmbodiedEvo"
finish_native="$finish_upstream/vendor/robodojo"
finish_runtime="$finish_root/worker-agent/.runtime"
mkdir -p "$finish_runtime"
finish_started="${1:-$(date -u +%FT%TZ)}"
"$finish_root/.venv-worker/bin/python" -m pip install -r "$finish_root/worker-agent/requirements-deploy.txt"
"$finish_root/.venv-worker/bin/python" "$finish_root/worker-agent/deploy/download-assets.py"
(cd "$finish_native" && "$finish_upstream/.venv-robodojo/bin/python" utils/update_embodiment_config_path.py)
"$finish_root/.venv-worker/bin/python" - "$finish_native" "$finish_root/worker-agent/runtime-lock.json" "$finish_started" <<'PY'
import json,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]);lock=json.load(open(sys.argv[2]))
subprocess.run(['git','-C',str(root),'diff','--quiet','HEAD','--'],check=True)
manifest={'commit':lock['robodojo'],'assets_revision':lock['assets']['revision'],
          'submodules':lock['submodules'],'installation':'direct independent native checkout',
          'started':sys.argv[3],'historical_runtime_compatibility':'unverified; requires native smoke'}
(root/'.embodiedevo-provisioned.json').write_text(json.dumps(manifest,indent=2)+'\n')
PY
(cd "$finish_upstream" && bash scripts/build_agent_image.sh)
"$finish_root/.venv-worker/bin/python" -m pip freeze > "$finish_runtime/host-packages.txt"
"$finish_upstream/.venv-robodojo/bin/python" -m pip freeze > "$finish_runtime/simulator-packages.txt"
"$finish_root/.venv-worker/bin/python" "$finish_root/worker-agent/run.py" --check --runtime-only
echo 'Runtime installed. Next: deploy/smoke.sh and operator login; then worker service startup.'
