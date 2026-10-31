#!/usr/bin/env bash
# Installs a stopped service. Start only after native smoke and operator login.
set -euo pipefail
service_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
service_user="$(id -un)"
[[ "$service_root" != *' '* ]] || { echo 'Use a checkout path without spaces.' >&2; exit 1; }
sudo install -d -m 700 -o "$service_user" -g "$(id -gn)" /etc/blupe-embodiedevo
if [[ ! -e /etc/blupe-embodiedevo/worker.env ]]; then
  sudo install -m 600 -o "$service_user" -g "$(id -gn)" /dev/null /etc/blupe-embodiedevo/worker.env
fi
sudo tee /etc/systemd/system/blupe-embodiedevo-worker.service >/dev/null <<EOF
[Unit]
Description=BluPe EmbodiedEvo YAM worker
After=network-online.target docker.service
Wants=network-online.target
Requires=docker.service
[Service]
Type=simple
User=$service_user
SupplementaryGroups=docker
WorkingDirectory=$service_root
EnvironmentFile=/etc/blupe-embodiedevo/worker.env
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=$service_root/.venv-worker/bin/python $service_root/worker-agent/run.py
Restart=on-failure
RestartSec=15
KillSignal=SIGINT
KillMode=control-group
TimeoutStopSec=60
UMask=0077
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
echo 'Service definition installed without starting/enabling it. Configure the private environment and inspect its status before startup.'
