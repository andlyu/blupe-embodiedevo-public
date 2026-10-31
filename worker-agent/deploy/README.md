# Direct physical YAM worker deployment

The public Site hosts the UI and queue. A separate worker runs the pinned EmbodiedEvo code session and connects to BluPe Remote YAM. The physical path uses published RoboDojo skill files as read-only references in a fresh session. It does not run Isaac Sim or replay simulated poses or actions.

## Worker host

Use a Linux x86_64 host with Docker Engine, or macOS with Docker Desktop, and outbound HTTPS access to the model service, Site, and YAM session API. It needs CPU and memory for a small Codex container and MuJoCo kinematics checks, but no NVIDIA GPU, driver, Isaac Sim, RoboDojo binary assets, or GPU lease. AWS is one possible host; a suitable existing machine also works.

1. Clone the public repository with its two pinned upstream submodules. Preserve the commit pins in `worker-agent/core.py` and `upstream_skill_manifest.json`.
2. Run `bash worker-agent/deploy/bootstrap-yam.sh`. It validates source pins, installs the Python 3.12 CPU environment, direct YAM dependencies, and upstream agent image. It never starts a model session, contacts the station, or moves a robot.
3. Complete the operator's own model login with `bash worker-agent/deploy/login.sh`. No API key is needed for subscription use. The login remains on this worker.
4. Run `.venv-worker/bin/python worker-agent/run.py --check --yam-only` to check the host, pinned imports, Docker image, and login. Add `--runtime-only` to skip the login check. The live YAM contract, calibration, feedback, and camera freshness checks happen again before each accepted physical session.
5. Configure `SITE_ORIGIN`, a private random `WORKER_TOKEN` (at least 32 characters), the Site `SITE_ACCESS_TOKEN` if required by ingress, stable `WORKER_ID`, private persistent `RUN_STORE`, `EMBODIEDEVO_CODEX_HOME`, and `EMBODIEDEVO_ENABLE_YAM=1` in `/etc/blupe-embodiedevo/worker.env` on Linux or a private local env file on macOS. Set the matching worker token in the Site runtime. Never put credentials in Git, the public UI, or shell history.
6. On Linux, install the stopped service with `bash worker-agent/deploy/install-service.sh`. On macOS, start the foreground worker with `bash worker-agent/deploy/run-local-yam.sh /path/to/worker.env` and keep its terminal open while using the Site. Before either launch, load the environment file and run `.venv-worker/bin/python worker-agent/run.py --check-site` to verify Site identity and source pins without a heartbeat or job claim. Start only after the operator confirms the station is clear and the public Run button is configured for that worker.

The physical session is bounded by the selected skill/task, a 60–600 second lease, and 1–100 code executions. It uses fresh live top and wrist cameras, measured YAM poses, and BluPe's paired-arm validation, Stop, and lease checks. The task can fail. The worker records the selected skill revision, exact file hashes, submitted programs, and protected live footage. An operator reviews the evidence to determine the outcome.

The separate `bootstrap.sh`, `smoke.sh`, and `finalize-runtime.sh` scripts prepare RoboDojo simulation workers. They are not prerequisites for direct physical YAM runs.
