#!/usr/bin/env bash
# Real physics + isolated fixed Docker client. No model calls or scored Test plan.
set -euo pipefail
umask 077
export CUDA_HOME=/usr/local/cuda-12.8
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"
smoke_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
smoke_upstream="$smoke_root/upstream/EmbodiedEvo"
smoke_store="${RUN_STORE:-$smoke_root/worker-agent/.runs}/diagnostics"
smoke_stamp="$(date -u +%Y%m%d%H%M)"
mkdir -p "$smoke_store"
smoke_native="$smoke_store/${smoke_stamp}_native_smoke"
smoke_session="$smoke_store/${smoke_stamp}_docker_smoke"
cd "$smoke_upstream"
".venv-robodojo/bin/python" -m scripts.smoke_robodojo --env-task stack_blocks \
  --gpu "${EMBODIEDEVO_GPU:-0}" --run-dir "$smoke_native"
"$smoke_root/.venv-worker/bin/python" "$smoke_root/worker-agent/deploy/smoke-session.py" --task RoboDojo --env-task stack_blocks \
  --gpu "${EMBODIEDEVO_GPU:-0}" --run-dir "$smoke_session"
python3 - "$smoke_native" "$smoke_session" <<'PY'
import json,sys
from pathlib import Path
for path in map(Path,sys.argv[1:]):
 result=json.loads((path/'smoke.json').read_text())
 assert result.get('passed') is True,result
 print(json.dumps({'path':str(path),'result':result}))
PY
