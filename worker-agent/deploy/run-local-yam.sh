#!/usr/bin/env bash
# Run the direct YAM worker in the foreground using a private local env file.
set -euo pipefail
umask 077
local_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
local_env="${1:-$HOME/.config/blupe-embodiedevo/worker.env}"
[[ -f "$local_env" ]] || { echo "Missing private worker environment: $local_env" >&2; exit 1; }
[[ -x "$local_root/.venv-worker/bin/python" ]] || {
  echo 'Run deploy/bootstrap-yam.sh before starting the local worker.' >&2
  exit 1
}
set -a
# The operator-owned file is intentionally sourced only from a local path.
source "$local_env"
set +a
exec "$local_root/.venv-worker/bin/python" "$local_root/worker-agent/run.py"
