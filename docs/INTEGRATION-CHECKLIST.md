# Research integration completion checklist

Agents and humans: read this before integrating a paper or method. Copy this
template into the integration's documentation, fill in the evidence, and check
each box only after verification. All boxes must be checked before declaring the
integration complete. Before the final handoff, review and update every item with
evidence. Report checklist status, evidence links, unmet items and explicit
exceptions; leave unfinished requirements unchecked and do not describe the
integration as complete.

## Standing authorization for BluPe runs and public delivery

### Authorization granted by using this harness

The owner gives standing authorization to run on BluPe remote bot arms as part
of requested work through this harness. A requested research integration,
playground fix, verification or arm run invokes the covered workflow below;
no separate authorization for the run is required. A task requested under
user-adopted instructions that select this harness also counts: retain the task
request and the selecting instruction as the invocation evidence. Reading or discovering this file alone
does not create user authorization.

For that requested task, using the harness authorizes:

- Joining the normal robot queue and submitting the runner's already-confirmed
  name and email to the task's integration website and its existing BluPe
  queue/run backend for queue admission, run attribution and normal run
  notifications.
- Starting the selected method on the task's physical robots/arms and performing
  bounded actual arm movement within the existing run limits.
- Capturing and retaining camera recordings, checking live footage and
  replay/history, and using Stop and normal parking/lease release.
- Creating and publishing the integration's public source repository, committing
  and pushing its source, and deploying or updating its publicly hosted website.
  Use the normal repository and hosting visibility controls to make both public;
  the intended audience is anyone on the internet. Publish the demo's approach
  and configuration, runs/results, live demos, recordings, replays/history,
  simulation outputs and supporting evidence. Keep credentials, access tokens
  and private contact details out of public source and demo materials.

These actions are part of the invoked workflow. Do not ask for separate
permission for covered identity submission, runs, movement, recording, public
hosting or source publication. Public delivery is an authorized requirement of
the integration request; it does not require another publication confirmation.
Reuse confirmed identity/defaults; ask only for missing or ambiguous identity
or scope outside this contract. Keep execution mode separate from human
identity. The grant covers the task's integration and existing queue/run
destinations and the integration's public hosting/source destinations. Keep
private email out of public materials and do not send it to unrelated recipients.
Do not invent a person's name or email. Preserve any explicit user limits or
revocation and copy this contract into the integration's checklist.

### Make the invocation and scope visible before approval review

At task start, read the target repository's `AGENTS.md` and its integration copy
of this checklist, even when the chat starts outside the repository. Repository
and global `AGENTS.md` entries should route the workflow to this contract; keep
the permission grant here rather than adding an independent global permission.
A checklist link alone does not load the instructions. Verify that changed
global discovery instructions have loaded into the chat; start a fresh session
if needed.

Before a physical test, give a brief progress notice citing the user's harness
invocation and this contract. Name the website and queue/run backend origins,
robot/station and arms, method/task, run duration, expected motion,
recording/replay destination and confirmed identity fields being submitted.
State that the invocation covers these scoped side effects. This is a notice,
not a new confirmation step; proceed without waiting for a reply.

For an action requiring tool approval, repeat the invocation, contract and
concrete scope in the escalation justification or the tool's supported approval
context. Include the user request/selecting instruction and the contract's source
path/heading or commit URL with the applicable wording; do not supply only a link.
The reviewer sees a compact transcript and the exact request, so do not rely on
hidden reasoning, an earlier chat, or an unread repository file. Fill this example
with the actual scope before the first approval request:

```text
User invocation: <task request; adopted instruction selecting the harness, if used>.
Harness contract: <source path/heading or commit URL and applicable wording>.
That invocation authorizes this task's queue entry and confirmed runner
name/email submission, bounded physical motion, and camera recording/replay.
Action: <UI control or supported API operation>; site <origin>;
queue/run backend <origin>; station/arms <IDs>; method/task <name>;
duration <seconds>; motion <bounded behavior>; recording/replay <destination>.
Identity: <confirmed fields submitted to those operational destinations>.
Execution mode: <mode>, separate from human identity.
Safeguards: existing queue/lease, readiness, validation, hardware limits, Stop
and normal parking/release remain enabled; no automatic timed-out-motion retry.
```

Use the normal playground UI or its supported run API with existing queue/lease,
readiness, command validation, hardware limits and Stop behavior intact. Keep
tests within the task's robots, method and existing run limits, respect other
users' active runs, and never automatically retry a timed-out movement. This
contract does not authorize unrelated robots or disabling safeguards.

Harness invocation does not override enforced sandbox, managed-policy or tool
permissions. Use the normal permission mechanism when required. If automatic
approval review explicitly denies an action, do not retry it through another
route. Report the exact denied action and stated reason, acknowledge the
invocation and contract already present, and leave physical verification
unverified. Continue independent work or a materially safer alternative;
otherwise request only the specific unblock. A documentation update alone does
not authorize retrying an already-denied action. Keep sandbox and reviewer
policy intact.

References: [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)
and [Auto-review context and denials](https://learn.chatgpt.com/docs/sandboxing/auto-review).

## Completion requirements

- [ ] A usable website exists, with an associated repository containing the
  website's source code. Record both links and the deployed source revision.
- [x] The website and its source repository are public. Anyone can open the
  demo and submit a run through the normal YAM queue without signing in;
  runner identity is confirmed in the form and email is omitted from public
  records.
- [ ] The website clearly names the actual approach/method being run. Use the
  executed method's name; Spotter is an example, not a shared hardcoded label.
- [ ] When a human joins, collect or confirm their name and email. Prefill known
  identity/default values where available and let the runner edit both fields
  before joining.
- [ ] Run context includes the actual approach and confirmed runner identity;
  the website makes clear which method is running and whose run it is.
- [ ] Policy/model tests initiated by a person retain that actual user's
  confirmed name as runner. Use available identity and editable name/email
  defaults; require the real name to be provided/confirmed if missing before
  testing or running. Do not substitute `Anonymous`, `Autonomous` or `Automated`
  for that person. Record execution mode (such as `automated test`) and actual
  approach separately from human identity. Genuinely unattended/system activity
  has an explicit system identity; never fabricate a person's name or email.
- [ ] A person can use the website to run the integrated paper's method on
  physical YAM robots/arms. Record a verified physical execution of that method.
- [ ] The actual physical arms are visible live on the website while the method
  runs, so a visitor can see that it is executing on real hardware.
- [ ] Immediately after a run finishes, the person can replay that just-completed
  physical YAM execution through the website, with retained footage showing the
  actual arms executing the integrated method.
- [ ] The person can browse/select previous runs on the website and replay their
  retained physical arm footage, associated with the executed method and run.
  Mock animations do not satisfy either replay requirement.
- [ ] If the integrated method executes anything in simulation, those executions
  are reviewable within the integration website and tied to the corresponding
  run. A reviewer can inspect what ran and its results using suitable
  replay/visualization and relevant outputs, as appropriate to the simulation.
  Clearly label simulation content to distinguish it from physical-arm footage.
  If nothing executes in simulation, record an explicit not-applicable
  explanation instead of claiming simulation review.
- [ ] The website is intuitive: a new visitor, without coaching, can find how to
  run the method and have the physical YAM arms actually executing it within
  **15 seconds of entering the website**, verified as described below.
- [ ] **Mandatory for every run:** after the person clicks Run, the physical YAM
  arms start actual method-driven motion within **15 seconds**, unless that run
  requires launching a GPU as documented below. Verify and record every run;
  a sampled demonstration is insufficient.
- [ ] Every meaningful wait after a website action is immediately explained in
  a persistent inline status/progress area at that action (below Run in the run
  panel for launches). Show the current stage, a plain-language reason and real
  stage completion, with honest failure/stall status and available recovery.
  Verify the detailed wait-stage behavior below.
- [ ] Before marking the integration complete or reporting it done, open the
  deployed website and perform a final end-to-end physical YAM run through its
  normal user interface. Verify every completion requirement against that
  deployment and record evidence; unmet or unverified requirements block
  completion.

## Verify the 15-second path

Time a visitor's full path. Start at initial navigation to the website (`t0`);
stop at the first observed physical arm motion executing the integrated method
(`t1`). Require `t1 - t0 <= 15 seconds`. Include page loading, finding the controls,
login/setup, queue/readiness waits and inference in the elapsed time; do not
restart the clock at Run. Queued, submitted, accepted or a UI "running" status
alone does not pass, nor does backend latency alone.

Include join-time name/email entry or confirmation in this same measurement.

Record the visitor's starting state and test conditions. Keep a timed screen
recording showing site entry, the visitor's actions and the live arms beginning
the method, linked to the matching physical run. If the elapsed time exceeds
15 seconds or physical motion is unverified, leave the box unchecked.

## Verify every Run click

This is an additional per-run measure; keep the site-entry test above. For every
run, start at the Run click (`t_run`) and stop at the first observed actual
method-driven physical arm motion (`t_motion`). Require
`t_motion - t_run <= 15 seconds`, subject to the GPU-launch exception below.
An acknowledgement, accepted request, queued status, submitted action or inference
starting is insufficient.

Record every run below (add rows), including visual evidence of the click and
motion. Mark the outcome as pass, missed target, unverified or exception.
Exceptions are not fulfilled <=15-second runs.

**GPU-launch exception:** a run that requires launching/provisioning a GPU (for
example on RunPod) may exceed this Run-click target. Record why the GPU had to be
launched and its startup evidence for that run. Keep the full elapsed time from
Run click to observed physical motion; do not reset the clock when the GPU becomes
ready. If GPU startup causes the target to be missed, label the outcome as an
exception. If the GPU is already available, the normal 15-second requirement
applies. This exception does not change the site-entry measure above.

Other exceptions require a specific justification grounded in the integrated
paper/research, explaining why it applies to that run, plus a supporting source
citation/link and relevant section/page. Outside the explicit GPU-launch case,
slow loading, queueing, setup or infrastructure delay is a missed target, not in
itself a paper/research-grounded exemption.

| Run reference | Run click (`t_run`) | First observed method-driven arm motion (`t_motion`) / visual evidence | Elapsed seconds | Outcome |
| --- | --- | --- | --- | --- |
| | | | | |

- Exception record (repeat for each affected run):
- Exception category (GPU launch or paper/research-grounded):
- Affected run reference:
- Specific reason and why it applies to this run:
- GPU-launch evidence (if applicable: provider, instance/job reference,
  launch/ready timestamps and startup log/link):
- Supporting paper/research source (for other exceptions: citation/link and
  relevant section/page):

## Visible progress while waiting

Use a compact persistent inline status area directly below Run in the existing
run panel; keep other meaningful waits beside their initiating control. Show the
current stage and why it is taking time immediately, keep it readable throughout
the wait, and visibly mark completed stages as actual lifecycle state advances.
A transient toast alone or a generic spinner is insufficient.

When a model requires a new GPU, show only the stages that actually exist:
`Starting GPU` / "We're launching a GPU on RunPod for this model" -> `GPU ready`
-> `Loading model` -> `Running`. GPU startup must be explicit immediately after
Run; visibly confirm actual GPU readiness before subsequent loading/running and
retain completed-stage confirmation. Use the applicable provider/model wording.
On failure or a stalled stage, state the known condition honestly and show an
available recovery action, such as retry or cancel where supported. Do not invent
percentages, ETA or completion, or expose irrelevant infrastructure internals.
This transparency requirement adds no timing exemption or clock reset.

## Final verification before completion

Open the deployed website and its associated source repository. Use the normal
visitor flow to join, run the integrated method on physical YAMs and watch the
actual arms live. Check both 15-second measures, approach/runner identities,
replay of the just-completed run and selection/replay of previous runs. Review
every checklist item against current evidence, including public visibility and
actual user attribution in policy/model tests, with execution mode separate.
Verify wait status appears immediately, keeps a readable reason, and visibly
confirms real stage completion (GPU ready before subsequent loading/running).
Check failure/stall status and available recovery evidence too. Record the
tested deployment, run and evidence below.
Leave unmet or unverified items unchecked and report gaps and explicit exceptions
before any completion claim.

## Integration and evidence

- Paper / method (link and version):
- Final verification (reviewer/date, tested website URL and deployed revision,
  physical run reference):
- Final checklist review (evidence for every item, replay links/timings, unmet
  items and explicit exceptions):
- Actual approach name / website label evidence:
- Human join evidence (name/email collection or confirmation, prefilled defaults
  and edits to both fields):
- Run context evidence (run ID, approach and runner identity; website attribution):
- User-initiated test evidence (run ID, confirmed human runner, actual approach,
  separate execution mode; editable defaults and missing-name confirmation):
- Unattended/system activity evidence (explicit system identity, execution mode
  and actual approach; no fabricated person):
- Wait-status evidence (action/run reference, immediate inline visibility,
  ongoing stage/reason and real completion transitions):
- GPU-startup UI evidence (startup shown after Run, actual readiness confirmed
  before loading/running, completed stages and matching lifecycle evidence):
- Failure/stall status and available recovery evidence:
- Website URL:
- Website source repository URL / deployed revision:
- Public-visibility exceptions (write "none", or the affected website/repository,
  explicit exception, reason and approval reference):
- Physical-test authorization/scope (source path/heading or commit URL, website
  and queue/run backend origins, station/arms, confirmed runner identity fields,
  method/task, duration, expected motion and recording/replay destination):
- Approval-context evidence (surfaced notice and escalation wording, applicable
  user invocation/selecting instruction and harness contract version/scope,
  review decision/rationale if required; redact private email from public evidence):
- Physical execution (date, method/configuration, YAM station/arm IDs, run ID):
- Live physical arm footage (website location and evidence link):
- Just-completed replay URL / immediate availability evidence (same physical run):
- Previous-run browser URL / selected prior run and replay evidence:
- Simulation review (corresponding run reference, website review link, what ran
  and its results, suitable replay/visualization/outputs, clear simulation label;
  or explicit not-applicable explanation if nothing executes in simulation):
- 15-second test (tester/date, browser/session/network and robot readiness):
- Visitor's starting state and entry-to-motion steps:
- `t0` / `t1` / total elapsed seconds:
- Timed screen recording / matching physical run evidence:
- Remaining gaps:

## Direct skill-to-YAM integration evidence — October 31, 2026

Invocation evidence: the user requested setup, then specified that simulation-learned EmbodiedEvo skills should be reused directly on physical YAM without a simulation campaign. The target is the independent public BluPe × EmbodiedEvo Site and its public source repository. The shared harness authorization-by-use clause applies to this requested integration and public delivery.

Scope surfaced before validation: Site `https://blupe-embodiedevo.andlyu.chatgpt.site`; direct queue `/api/direct-yam`; YAM Session API `https://yam-session-api.n5hthc3gj4cqy.us-east-1.cs.amazonlightsail.com`; station `yam-1`, both arms; one selected upstream EmbodiedEvo skill/task; up to 600 seconds and 100 code executions; bounded motion through the existing BluPe controller and validation; public run history with top and both wrist camera footage. The worker setup checks submit no runner identity and do not connect to or move the station.

Implementation: the public selector uses the 42 published skill sets pinned to EmbodiedEvo commit `689a09b419d2555bf94f7345f58c62969a43739e`. The worker fetches only allowlisted files and verifies sizes and Git object hashes, mounts them read-only in a fresh session, and routes commands through the BluPe YAM controller. It must adapt to real measured observations; simulated poses and replay are not used. New simulator-campaign and simulation-job API submissions are disabled. A direct worker preflight and CPU-only install path have been added; the direct worker no longer requires Isaac Sim, a GPU, RoboDojo assets or the simulator Python environment.

Local verification completed: domain/access tests (10 passed); YAM readiness tests (6 passed); worker tests (13 passed); runtime preflight tests (5 passed); TypeScript check passed; production Site build passed; shell syntax checks passed. Targeted ESLint on `lib/api.ts` reports 36 `no-explicit-any` errors and one pre-existing `prefer-const` error in that existing API module, plus one image warning in the camera UI; this is not reported as a passing lint check. The first worker image build found an upstream build-script incompatibility with macOS Bash 3.2 empty arrays; the direct bootstrap now builds the same pinned Dockerfile without modifying upstream source and its CPU-only preflight passed.

Public GitHub source update: `https://github.com/andlyu/blupe-embodiedevo-public`, commit `682420d5a4d8f9a700a40496eb9fe18e3b886039`. The internal integration checklist and run notes remain excluded from that public snapshot. Production Site version 24 was deployed with public page viewing. Runtime worker/site secrets are configured; the local CPU worker is heartbeating. At the time of this status entry, physical access had not been checked.

No physical job has been queued or submitted in this update. The Mac's direct dependencies and pinned agent image are installed; `run.py --check --yam-only` passed, and the worker heartbeat is current. The worker setup does not require AWS or a GPU. At the time of this status entry, station readiness had not been checked. No physical motion, live recording, replay, task outcome, or 15-second entry-to-motion measure had been verified. The previous old-path attempt with two code executions and zero packets/waypoints is not evidence for the new direct path.

| Requirement area | Status |
| --- | --- |
| Direct public skill selector and pinned provenance | Deployed in the public Site; source update is public. |
| No simulation campaign required | Direct path is deployed; simulator APIs reject new submissions. |
| Exact skill files verified and read-only to a fresh session | Implemented; direct physical execution is not yet qualified. |
| CPU-only direct worker preflight and install | Docker image built; YAM-only preflight passed. |
| Connected worker and station readiness | Worker connected; production station readiness still needs live verification. |
| Physical motion, live recording and replay | Not run. |
| Public Site deployment of this revision | Version 24 predates the public-control update below. |
| 15-second entry-to-motion test | Not measured. |

Remaining evidence at the time: use the normal UI to review station readiness and submit one bounded direct skill run with a confirmed task, object arrangement and runner attribution. Inspect actual motion, footage, replay, attribution and task outcome. Leave all physical completion items unchecked until those checks pass.

## Public demo access update — October 31, 2026

The user clarified that the demo must be usable by any visitor with no site sign-in. The shared harness specifies public-by-default access for the website, controls, run records, live demo and evidence. The run remains bounded to one task on station `yam-1`, both arms, at most 600 seconds and 100 executions, with normal BluPe admission, validation, Stop and lease release. A visitor must confirm their own real name and email for YAM attribution; email is redacted from public records. This is the direct YAM workflow, with no simulation campaign.

Implemented in source: anonymous bootstrap and public controls/history/cameras/evidence, public shared run namespace, one queued or active physical run globally, email redaction, and no sign-in UI. Worker token protection, station readiness gates, command validation, execution limits and runner identity confirmation remain. The unused `SITE_OPERATOR_USER_IDS` secret was removed; only `WORKER_TOKEN` remains in the Site runtime environment.

Fresh verification: `node --test tests/domain.test.mjs tests/public-demo.test.mjs` (9 passed); `node --experimental-strip-types --test tests/yam.test.mjs` (6 passed); `python3 -m unittest tests.test_runtime tests.test_worker` (18 passed); `npx tsc --noEmit` passed; `npm run build` passed. `BLUPE_TEST_ORIGIN=http://127.0.0.1:8799 python3 tests/api_integration.py` passed 8 checks against a local preview. An unsigned local browser preview displayed the public run form and public evidence sections with no sign-in link. No physical job was submitted, and no robot motion occurred during validation.

The public controls are deployed as Site v27 and the no-sign-in page is verified. Public source is available at `https://github.com/andlyu/blupe-embodiedevo-public`. Physical motion, a task result, and replay of method-driven motion remain unverified.

| Requirement area | Current status |
| --- | --- |
| Public no-sign-in site controls and run history | Deployed at Site v27 and available to any visitor. |
| Direct physical skill run; no simulation campaign | Implemented and submitted through the public UI; physical execution remains unverified. |
| Pinned skill files verified and mounted read-only | Verified for both recorded Stack Blocks attempts; neither submitted a task program. |
| Worker heartbeat and station connection | Connected; station was not homed or settled until a run lease. |
| Physical method motion, task outcome and replay | Not yet verified. |
| Public Site deployment of public-control revision | Deployed. |
| 15-second entry-to-motion test | Not passed; both attempts showed no method-driven motion. |

Upstream skill library: https://github.com/Einsia/EmbodiedEvo/tree/689a09b419d2555bf94f7345f58c62969a43739e/Workspace/skills

## Direct YAM startup diagnosis — October 31, 2026

The confirmed Stack Blocks run `da1ac9c0-843d-4d5e-97f1-3fe0e6b2a20f` fetched and hash-verified all seven files from the pinned upstream skill revision, entered the normal `yam-1` queue, and received settled hardware feedback. It failed before the EmbodiedEvo agent started: `session/timing.json` records `agent_started_at=null`, and `hardware-progress.json` records zero submitted commands and packets. No Stack Blocks task motion was sent. The error was infrastructure startup, not a failed policy attempt.

Root cause was reproduced on the worker: the shared simulator launcher supplied `MUJOCO_GL=egl` and `PYOPENGL_PLATFORM=egl` to the direct YAM runtime. The worker's macOS MuJoCo rejects `MUJOCO_GL=egl` during module import with `RuntimeError: invalid value for environment variable MUJOCO_GL: egl`. The real-hardware adapter does not render through MuJoCo; it uses measured camera frames and MuJoCo for local kinematics/collision checks.

The direct YAM session now keeps the upstream local-execution host-policy check and single-thread limits while removing simulator-only EGL/Vulkan variables and hiding CUDA devices in the child. Its explicit native `--run-dir` has the upstream-required `YYYYMMDDHHMM` prefix; the evidence publisher recognizes that timestamped path and retains legacy path compatibility. This fix was published before the second normal-UI attempt, allowing the agent to start; that attempt then revealed the Docker Desktop socket issue below.

| Requirement area | Current status |
| --- | --- |
| Root cause of first direct physical run | Confirmed worker/runtime incompatibility; no method command packets. |
| Direct YAM environment fix and regression coverage | Published in public source commit `4074b95ab8c41c2fc04f4a3ec6ddd8f38a618fe8`; 27 Python and 15 JavaScript tests passed at that revision. |
| Fresh physical Stack Blocks run through public UI | Run `588e0ab1-97f9-4abd-9c58-bf59d724d952` reached the agent but failed at session transport. |
| Actual method motion, camera replay, outcome, and 15-second timing | Unverified; first attempt did not execute the method. |

## Direct YAM session bridge diagnosis — October 31, 2026

Second public-UI attempt: run 588e0ab1-97f9-4abd-9c58-bf59d724d952 was
queued at 2026-10-31T21:26:41.827Z for the pinned Stack Blocks skill on
yam-1. All seven upstream skill files were hash-verified and mounted
read-only; the live camera recording retained 69 frames across three views.
The agent started, but its session RPC requests all failed with Connection
refused. The run submitted zero code programs, controller packets, or native
steps. No method-driven arm motion occurred. The site initially labeled this
as a valid completed attempt; this was an infrastructure failure, not a
failed Stack Blocks attempt. The Run-click-to-motion requirement was missed.

Root cause was reproduced locally: Docker Desktop on the Mac cannot connect
from the isolated agent container to the host's Unix session socket through a
bind mount. A minimal container made the same Connection refused call.
The container can reach a host service through host.docker.internal even
when it binds only to 127.0.0.1.

The adapter change keeps the upstream Unix session server and JSON request
protocol intact. For a physical run, the worker now bridges the copied
upstream CLI through a short-lived loopback TCP listener with a fresh
per-session token. The physical Docker command no longer mounts the socket.
Transport counters are retained in the run record. A valid upstream session
with zero submitted programs is classified as agent_transport_unavailable
or agent_no_program_submitted; a submitted program remains a valid attempt
even when the task itself fails.

Verification completed locally: 32 Python tests in .venv-worker, 15
JavaScript tests, TypeScript check, production build, and git diff --check
passed. An isolated Docker end-to-end check ran the copied upstream CLI against
a fake local session server and verified one authenticated status request and
reply; it did not contact YAM or move a robot.

The run was reviewed as a failure in the public attempt history with the
zero-program transport diagnosis. The public source bridge fix is published at
https://github.com/andlyu/blupe-embodiedevo-public/commit/3ca258b8889226672e585604a8e807210792ba2e.

| Requirement area | Current status |
| --- | --- |
| Docker Desktop socket failure and reproduction | Confirmed with the production run record and a minimal local Docker reproduction. |
| Authenticated TCP session bridge and truthful zero-program classification | Published in commit `3ca258b8889226672e585604a8e807210792ba2e`; 32 Python and 15 JavaScript tests, typecheck, build, diff check and isolated Docker request/reply passed. |
| Actual Stack Blocks program submission and method-driven arm motion | Not yet verified; run 588e0ab1-97f9-4abd-9c58-bf59d724d952 sent no task command. |
| Live footage and replay of method-driven motion | Not yet verified; existing frames show observation and queue/homing only. |
| 15-second entry-to-motion and per-run timing | Not passed; the two recorded attempts did not show method-driven motion. |
| Final end-to-end public website run | Pending a new normal-UI run with the updated worker source. |
