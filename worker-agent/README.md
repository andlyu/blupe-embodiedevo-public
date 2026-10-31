# EmbodiedEvo direct YAM worker

This worker runs a fresh EmbodiedEvo coding session on BluPe Remote YAM using a selected skill set from the public `Workspace/skills/` library. The skill is reference knowledge: the worker never replays simulator actions or assumes RoboDojo coordinates are valid on physical arms.

## Operator setup

1. Clone `https://github.com/andlyu/blupe-embodiedevo-public` with `--recurse-submodules` and preserve the two pinned upstream source revisions.
2. Follow [`deploy/README.md`](deploy/README.md) and run `bash worker-agent/deploy/bootstrap-yam.sh` on a Linux x86_64 or macOS host with Docker. This installs the CPU-only physical adapter runtime and upstream agent image. It does not install Isaac Sim, RoboDojo assets, an NVIDIA driver, or GPU runtime.
3. Run `bash worker-agent/deploy/login.sh` and complete your own model-account login on that host. Credentials stay on the worker and are never copied into the repository or website.
4. Run `.venv-worker/bin/python worker-agent/run.py --check --yam-only` to inspect pins, dependencies, Docker image, and login without contacting YAM, claiming work, or moving a robot. Add `--runtime-only` to skip the login check. `--check-site` authenticates to the website without a heartbeat, job claim, or execution.
5. Configure a private random secret of at least 32 characters as `WORKER_TOKEN` in both the Site server environment and worker environment. Set the dispatch-provided `SITE_ACCESS_TOKEN` on the worker if the hosting ingress requires it. Keep credentials out of Git and shell history.
6. Set `SITE_ORIGIN`, a stable `WORKER_ID`, private persistent `RUN_STORE`, `EMBODIEDEVO_CODEX_HOME`, and `EMBODIEDEVO_ENABLE_YAM=1` in the worker environment. On Linux, start the installed service after the station is clear and the Site is configured for public demo runs. On macOS, use `bash worker-agent/deploy/run-local-yam.sh /path/to/worker.env` and keep that terminal open while running.

Worker startup validates pinned sources and the direct YAM runtime before its first heartbeat or claim. Direct execution needs CPU compute, Docker, and network access to the Site, model service, and YAM session API; it does not need an NVIDIA GPU or a simulation campaign. Opening the Site alone does not start compute. The physical queue checks station freshness, calibration, feedback, and safety before admission.

## Direct skill staging and execution

`upstream_skill_manifest.json` pins all 42 published task skill sets to one EmbodiedEvo commit. It records each permitted source path, destination, byte size, and Git blob SHA-1. `skill_library.py` downloads only listed files, rejects unsafe paths and symlinks, bounds file count and size, and verifies every Git object before use. Failed verification prevents the physical session from starting.

The verified files are supplied as read-only knowledge to a fresh native session with an empty lessons directory and the physical YAM primitive guide. The physical task description is separately supplied by the operator. The session uses live cameras, measured base-frame end-effector poses, actual calibration, and the four supported YAM primitives. Simulated coordinates, unmeasured assumptions, physical reset, and action replay are forbidden. The task can fail; process exit and agent claims do not establish success.

The normal BluPe `RunnerController` remains responsible for admission, homing, lease timing, paired 10 Hz trajectories, feedback, command validation, Stop, and release. A run is bounded to 60–600 seconds and 1–100 code executions. Physical starts are never retried automatically.

## Evidence and review

The worker retains the selected skill revision and verified file hashes, task/configuration, job log, and controller trace in its private run store. A live recorder captures top and both wrist cameras at 2 fps from queueing through cleanup, encodes them as MP4, and publishes them to the public Site history. The worker requests Stop if camera freshness is lost. Run attribution is submitted through the runner-confirmed YAM session API flow. Runner email is sent to YAM but redacted from public results; run history, names, outcomes and recordings are public.

Task success remains unknown until an operator reviews the physical scene. Failed, invalid, and interrupted attempts remain recorded. Local checks do not establish a successful physical task.

`python worker-agent/run.py --publish-evidence CAMPAIGN_UUID` uploads retained evidence only; it does not execute a model or move a robot.
