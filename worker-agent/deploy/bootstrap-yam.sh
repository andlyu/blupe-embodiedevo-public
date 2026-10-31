#!/usr/bin/env bash
# Prepare a CPU-only direct YAM worker; this does not install or launch Isaac Sim.
set -euo pipefail
umask 077
deploy_os="$(uname -s)"
deploy_arch="$(uname -m)"
[[ ("$deploy_os" == Linux && "$deploy_arch" == x86_64) || ("$deploy_os" == Darwin && ("$deploy_arch" == arm64 || "$deploy_arch" == x86_64)) ]] || {
  echo 'The YAM worker requires Linux x86_64 or macOS with Docker.' >&2
  exit 1
}
deploy_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
deploy_upstream="$deploy_root/upstream/EmbodiedEvo"
deploy_runtime="$deploy_root/worker-agent/.runtime"
deploy_miniforge="$deploy_runtime/miniforge"
mkdir -p "$deploy_runtime"

python3 - "$deploy_root" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / 'worker-agent'))
from core import verify_pins
verify_pins(Path(sys.argv[1]))
print('Pinned EmbodiedEvo and BluPe source trees match the website pins.')
PY

command -v docker >/dev/null || { echo 'Install Docker Engine before running this bootstrap.' >&2; exit 1; }
docker version --format '{{.Server.Version}}' >/dev/null || {
  echo 'Start Docker Engine and grant this user daemon access before running this bootstrap.' >&2
  exit 1
}
if [[ "$deploy_os" == Darwin ]]; then
  deploy_python="$(command -v python3.12 || true)"
  [[ -n "$deploy_python" ]] || { echo 'Install Python 3.12 before bootstrapping this macOS worker.' >&2; exit 1; }
  if [[ ! -x "$deploy_root/.venv-worker/bin/python" ]]; then
    "$deploy_python" -m venv "$deploy_root/.venv-worker"
  fi
else
  if [[ ! -x "$deploy_miniforge/bin/conda" ]]; then
  curl --fail --location "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["miniforge"]["url"])' "$deploy_root/worker-agent/runtime-lock.json")" \
    --output "$deploy_runtime/miniforge.sh"
  echo "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["miniforge"]["sha256"])' "$deploy_root/worker-agent/runtime-lock.json")  $deploy_runtime/miniforge.sh" | sha256sum --check
  bash "$deploy_runtime/miniforge.sh" -b -p "$deploy_miniforge"
  fi
  eval "$("$deploy_miniforge/bin/conda" shell.bash hook)"
  if [[ ! -x "$deploy_root/.venv-worker/bin/python" ]]; then
    conda create --prefix "$deploy_root/.venv-worker" --override-channels -c conda-forge python=3.12 -y
  fi
fi
"$deploy_root/.venv-worker/bin/python" -m pip install \
  -r "$deploy_upstream/requirements-host.txt" \
  -r "$deploy_root/worker-agent/requirements-yam.txt" \
  -e "$deploy_upstream"
if [[ "$deploy_os" == Darwin ]]; then
  # The upstream helper uses an empty Bash array under `set -u`, which Bash 3.2
  # on macOS treats as unset. Build the same pinned Dockerfile and run the same
  # no-network image checks without editing the upstream source.
  docker build --tag embodiedevo-agent:latest "$deploy_upstream/docker/agent"
  docker run --rm --network none embodiedevo-agent:latest codex --version
  docker run --rm --network none embodiedevo-agent:latest python -c \
    'import numpy, PIL, imageio; print("Agent Python/image dependencies OK; no model request sent.")'
  docker image inspect embodiedevo-agent:latest --format 'Agent image ready: {{.Id}}'
else
  bash "$deploy_upstream/scripts/build_agent_image.sh"
fi
"$deploy_root/.venv-worker/bin/python" "$deploy_root/worker-agent/run.py" --check --yam-only --runtime-only
echo 'CPU-only YAM runtime prepared. Next: operator login, private worker/site configuration, and station qualification.'
