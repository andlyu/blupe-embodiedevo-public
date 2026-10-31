# Real EmbodiedEvo compute worker

This is a thin execution wrapper around the pinned official EmbodiedEvo orchestration. It does not replace the simulator, imitate agent learning, or run physical YAM commands.

## Operator setup

1. Clone `https://github.com/andlyu/blupe-embodiedevo-public` with `--recurse-submodules`. Preserve both pinned submodule revisions. The site, worker and saved campaigns check these pins.
2. Use the executable [dedicated deployment guide](deploy/README.md) and scripts for a fresh Linux NVIDIA host. They install separate host/native environments, pinned RoboDojo source and assets, CUDA 12.8 and the upstream agent image. The operator completes their own model-account login on that host. Do not copy this Mac's credentials into the host, repository or browser. Existing compatible native installations can instead follow the official `upstream/EmbodiedEvo/README.md` instructions.
3. `python worker-agent/run.py --check` inspects source pins, host/GPU, native dependencies and provenance, Docker image and stored login, without starting physics or calling a model. `--check --runtime-only` omits login during installation. Real native qualification is the separate `deploy/smoke.sh` command. Startup checks prerequisites before its first heartbeat/claim. Model availability is established only by a real bounded job.
4. Configure a random secret of at least 32 characters as `WORKER_TOKEN` in the website's server environment and the worker process environment. Keep the value out of shell history and Git. No credential form exists in the website.
5. For an owner-private Sites deployment, also set `SITE_ACCESS_TOKEN` to its dispatch-provided private access token on the compute host. It is sent only in the `OAI-Sites-Authorization` header. Application `WORKER_TOKEN` alone does not bypass the site's ingress authentication. Obtain/provision this token through the owner's native Sites management; never embed it in a URL or browser bundle. Self-hosted deployments can supply their own ingress and omit this header.
6. Set `SITE_ORIGIN` to the deployed website's HTTPS origin, `WORKER_ID` to a stable identifier such as `sim-worker-1`, `RUN_STORE` to a persistent private volume, and `EMBODIEDEVO_GPU` to the selected GPU index (default `0`). Run `python worker-agent/run.py` in that configured environment. **Starting the worker permits queued simulation/model jobs to execute.** Website setup does not start it automatically.

`python worker-agent/run.py --check-site` authenticates to the website and checks source pins without claiming a job or advertising an online worker. The private service token may be raw or already prefixed with `Bearer`; the client sends exactly one prefix. This credential is separate from the application worker token.

## Execution and evidence

The worker claims one queued job atomically, runs a trusted child entrypoint, and sends heartbeats, public native camera observations and terminal reports. Practice calls `session_runner.explore` with the selected task, seed, slot budget and bounded session duration. Each native run has a UTC `YYYYMMDDHHMM_practice` name; its original identity is saved for Test and cannot be replaced by another practice attempt. Upstream creates the persistent simulator/agent session and freezes knowledge after valid completion.

The worker checks `protocol.json`, `playground_valid`, exact skills/lessons directory scope and native file hashes before exporting knowledge. Text files use UTF-8 and binary files use canonical base64 in the downloadable v2 package. Digests and byte counts always describe the original decoded bytes. The website verifies every file digest and stores the unchanged package in R2, with an immutable manifest in D1. Empty protocol-valid packages are allowed and are not described as learned controllers.

Simulation Test calls `session_runner.test` against the original native run and its saved resolved config; upstream verifies frozen hashes and creates each independent scene/agent. The same worker ID and persistent volume are required. A lost worker is not replaced by silently copying or rebuilding its provenance. Native run directories, original code, observations, videos and full logs stay on that volume. The website retains returned scene outcomes, failures, package manifests and the latest public native camera frame; it does not currently publish full native videos or a live code editor.

Stop cancels queued work immediately or marks running work for cancellation. The worker checks it every two seconds, interrupts the native process group and waits for cleanup; a missing worker leaves Stop unconfirmed. Starts are never retried automatically. Lost report responses are reconciled with the same job identity. An uncertain or failed scene is retained; no retry-until-success loop exists.

Only predefined simulation task/model/config fields are accepted. There is no uploaded-code, arbitrary command, arbitrary task path, arbitrary callback URL or hardware job execution surface. Raw native process logs remain on the worker volume; they are not uploaded to the website.

## Physical transfer to YAM

yam_trial.py wraps the real pinned remote_yam.session.HttpSessionAPI and RunnerController; it keeps the normal queue, admission, Home, lease, measured feedback, command validation, Stop and release safeguards. It mounts the original frozen skills read-only, submits the confirmed runner identity to the YAM Session API, and records task and method provenance. A live recorder captures the top and both wrist cameras at 2 fps from queueing through session cleanup, then publishes per-run MP4 footage to protected operator history on the Site. The recorder stops the run if camera freshness is lost. Hardware execution is enabled only on a YAM-qualified worker. The independent website owns the adapter; the existing BluPe application is untouched. End-to-end physical motion and replay have not yet been verified for this updated recorder.
### Physical transfer to YAM

After a valid successful simulation Test, select that campaign and open Real YAM.
The original frozen skills and lessons are mounted read-only in a fresh native
code session. The separate `blupe-physical-transfer-v1` protocol records the
original artifact and hashes; physical results are never presented as paper scores.

Install `mujoco==3.12.0` and `websocket-client==1.9.0` in the native RoboDojo
interpreter. Run its Python on `worker-agent/yam_doctor.py` for read-only geometry,
contract, camera timestamp and action validation. Only after it passes, set
`EMBODIEDEVO_ENABLE_YAM=1` in the worker environment and restart the worker.
This capability flag permits physical job claims. The shared pinned BluPe
RunnerController owns admission, Home, lease, paired 10 Hz packets, measured
completion, cancellation and release. No robot credentials enter the coding agent.

The adapter compares its local MuJoCo FK against the selected station's published
POE calibration at three virtual poses before permitting end-effector control.
Every observation requires measured grippers and fresh post-settle camera source
timestamps. Robot geometry, frames and current state come from YAM, rather than
assuming the simulation's ARX geometry. Physical scene reset and physical action
replay are forbidden. Frozen hashes are checked again after the session.

A physical task outcome remains unknown until an explicit operator review. All
failed and interrupted attempts remain visible. New physical sessions retain
continuous 2 fps top and wrist camera video, subject to a successful capture and
publication. Historical attempts may contain only sampled camera observations.
Use `run.py --publish-evidence CAMPAIGN_UUID` to upload existing native videos and
submitted code without executing the model, simulator or hardware.
