# BluPe × EmbodiedEvo

An independent public website for using EmbodiedEvo’s published simulation-learned skills directly on BluPe Remote YAM. It is separate from the existing BluPe app.

- Website: https://blupe-embodiedevo.andlyu.chatgpt.site/
- Public source: https://github.com/andlyu/blupe-embodiedevo-public
- Upstream method and skill library: [Einsia/EmbodiedEvo](https://github.com/Einsia/EmbodiedEvo)

## Direct YAM workflow

The site lists the task skill sets published under `Workspace/skills/`. The selected files are downloaded from a pinned upstream commit and verified against their Git blob hashes. A fresh EmbodiedEvo coding session receives those files as read-only context, alongside the BluPe YAM primitives and measured physical observations. It must adapt the learned approach to the real task; it does not replay simulated coordinates or execute a RoboDojo helper unchanged.

Users choose a skill set, describe the matching objects arranged on YAM, confirm their run attribution, and submit a bounded physical session through the normal BluPe queue. The integration keeps station readiness, worker qualification, lease limits, command validation, Stop, normal release, protected run history and physical evidence. Limits are at most 600 seconds and 100 code executions. Task success remains unknown until an operator reviews the physical evidence.

No simulator campaign is required by this workflow. The code does not claim that the sim-to-real gap is small or that an upstream skill will succeed on YAM. Physical outcomes must establish that.

## Implementation

- A public task selector backed by `upstream_skill_manifest.json`, with exact upstream source revision, per-file sizes and Git object hashes.
- A direct YAM job API that creates a physical job without a frozen simulator artifact or simulated Test qualification.
- A worker adapter that fetches and verifies the selected files, mounts them read-only as fresh-session knowledge, and routes actions through the existing validated BluPe YAM controller.
- Operator-only controls for live YAM cameras, run attribution, queueing, Stop, protected run history, evidence and review.
- Pinned BluPe Remote YAM and EmbodiedEvo source submodules. Private run records, credentials, operator identities, production Site IDs and deployment secrets are excluded from this public source.

The site is publicly viewable. Running on YAM, live cameras and private run records require an approved operator account. A worker is not started by opening the website. A connected YAM-qualified worker and a ready station are prerequisites for a physical run.

## Run locally

Requirements: Node.js >=22.13 and Python 3. Clone with submodules:

```sh
git clone --recurse-submodules https://github.com/andlyu/blupe-embodiedevo-public.git
cd blupe-embodiedevo-public
npm install
npm run dev
```

To host your own Site, copy `.openai/hosting.example.json` to `.openai/hosting.json` and fill in your own Sites project ID and bindings. Configure `SITE_OPERATOR_USER_IDS` and `WORKER_TOKEN` as runtime secrets; never put production credentials in Git or the browser bundle. Follow [worker-agent/README.md](worker-agent/README.md) for a YAM-capable worker setup.

## Checks

```sh
node --test tests/domain.test.mjs tests/access-control.test.mjs
node --experimental-strip-types --test tests/yam.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
npx tsc --noEmit
npm run build
```

Local checks do not submit a YAM run. They do not establish physical arm motion or task success.

## Source and licensing

This repository is a public source snapshot. Upstream submodules retain their own licenses and release boundaries. No new license file is included in this snapshot.
