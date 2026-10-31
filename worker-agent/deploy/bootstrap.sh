#!/usr/bin/env bash
# Run only on the dedicated, approved Linux NVIDIA compute host.
set -euo pipefail
umask 077
if [[ "${1:-}" != --accept-isaac-eula ]]; then
  echo 'Review NVIDIA Isaac Sim terms, then invoke with --accept-isaac-eula.' >&2
  echo 'https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html' >&2
  exit 2
fi
[[ "$(uname -sm)" == 'Linux x86_64' ]] || { echo 'Requires Linux x86_64.' >&2; exit 1; }
deploy_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
deploy_upstream="$deploy_root/upstream/EmbodiedEvo"
deploy_native="$deploy_upstream/vendor/robodojo"
deploy_lock="$deploy_root/worker-agent/runtime-lock.json"
deploy_runtime="$deploy_root/worker-agent/.runtime"
mkdir -p "$deploy_runtime"
deploy_started="$(date -u +%FT%TZ)"
exec > >(tee -a "$deploy_runtime/bootstrap.log") 2>&1
lock_value() { python3 -c 'import json,sys; v=json.load(open(sys.argv[1]));
for k in sys.argv[2].split("."): v=v[k]
print(v)' "$deploy_lock" "$1"; }
python3 - "$deploy_root" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/'worker-agent'))
from core import verify_pins
from doctor import inspect_gpu
import json
verify_pins(Path(sys.argv[1]))
print(inspect_gpu(json.loads((Path(sys.argv[1])/'worker-agent/runtime-lock.json').read_text())))
PY
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
# Native packages and assets are large; fail before changing a small host.
deploy_free_kb="$(df -Pk "$deploy_root" | awk 'END {print $4}')"
if [[ ! -f "$deploy_native/.embodiedevo-provisioned.json" && "$deploy_free_kb" -lt 314572800 ]]; then
  echo 'Provisioning needs at least 300 GiB free. Use a separate adequately sized compute host.' >&2; exit 1
fi
sudo apt-get update
sudo apt-get install -y git git-lfs curl rsync cmake build-essential ffmpeg libxt6 libegl1 libgl1 libglu1-mesa libvulkan1 libglib2.0-0
if ! command -v docker >/dev/null; then
  sudo apt-get install -y docker.io
  sudo systemctl enable --now docker
fi
if ! docker info >/dev/null 2>&1; then
  if [[ "${BLUPE_DOCKER_GROUP_RETRY:-0}" == 1 ]]; then
    echo 'Docker is still unavailable after obtaining the docker group; inspect the daemon.' >&2; exit 1
  fi
  sudo usermod -aG docker "$(id -un)"
  # A fresh process obtains the updated supplementary group; no daemon bypass.
  exec sudo -u "$(id -un)" -H env BLUPE_DOCKER_GROUP_RETRY=1 bash "$0" --accept-isaac-eula
fi
if [[ ! -x /usr/local/cuda-12.8/bin/nvcc ]]; then
  sudo apt-get install -y cuda-toolkit-12-8
fi
export CUDA_HOME=/usr/local/cuda-12.8
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"
if [[ ! -x "$deploy_runtime/miniforge/bin/conda" ]]; then
  curl --fail --location "$(lock_value miniforge.url)" --output "$deploy_runtime/miniforge.sh"
  echo "$(lock_value miniforge.sha256)  $deploy_runtime/miniforge.sh" | sha256sum --check
  bash "$deploy_runtime/miniforge.sh" -b -p "$deploy_runtime/miniforge"
fi
eval "$("$deploy_runtime/miniforge/bin/conda" shell.bash hook)"
if [[ ! -x "$deploy_root/.venv-worker/bin/python" ]]; then
  conda create --prefix "$deploy_root/.venv-worker" --override-channels -c conda-forge python=3.12 -y
fi
"$deploy_root/.venv-worker/bin/python" -m pip install -r "$deploy_upstream/requirements-host.txt" -e "$deploy_upstream"
mkdir -p "$deploy_upstream/vendor"
if [[ ! -d "$deploy_native/.git" ]]; then
  git clone --no-checkout https://github.com/RoboDojo-Benchmark/RoboDojo.git "$deploy_native"
  git -C "$deploy_native" checkout --detach "$(lock_value robodojo)"
fi
[[ "$(git -C "$deploy_native" rev-parse HEAD)" == "$(lock_value robodojo)" ]]
git -C "$deploy_native" submodule update --init --recursive
python3 - "$deploy_native" "$deploy_lock" <<'PY'
import json,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]);lock=json.load(open(sys.argv[2]))
for path,expected in lock['submodules'].items():
 actual=subprocess.check_output(['git','-C',str(root/path),'rev-parse','HEAD'],text=True).strip()
 assert actual==expected,(path,actual)
PY
if [[ ! -x "$deploy_upstream/.venv-robodojo/bin/python" ]]; then
  conda create --prefix "$deploy_upstream/.venv-robodojo" --override-channels -c conda-forge python=3.11 -y
fi
conda activate "$deploy_upstream/.venv-robodojo"
export OMNI_KIT_ACCEPT_EULA=YES ACCEPT_EULA=Y
# Source the pinned installer only to load its functions. Calling its full install
# would advance submodules with --remote and accept Anaconda terms automatically.
source "$deploy_native/scripts/install.sh" --help >/dev/null
setup_base_deps
setup_isaacsim
setup_isaaclab
setup_curobo
python -m pip install --no-deps --no-build-isolation -e "$deploy_upstream"
conda deactivate
bash "$deploy_root/worker-agent/deploy/finalize-runtime.sh" "$deploy_started"
