#!/usr/bin/env bash
# The operator completes this host's own browser/device login.
set -euo pipefail
umask 077
login_home="${EMBODIEDEVO_CODEX_HOME:-$HOME/.local/share/blupe-embodiedevo/codex}"
mkdir -p "$login_home"
if [[ ! -e "$login_home/config.toml" ]]; then
  cat > "$login_home/config.toml" <<'EOF'
model = "gpt-6-astra"
model_reasoning_effort = "xhigh"
cli_auth_credentials_store = "file"
EOF
fi
docker run --rm -it --user "$(id -u):$(id -g)" \
  -e HOME=/home/agent -e CODEX_HOME=/auth -v "$login_home:/auth" \
  embodiedevo-agent:latest codex login --device-auth
echo "Login saved on this compute host. Set EMBODIEDEVO_CODEX_HOME=$login_home in the worker environment."
