# BluPe × EmbodiedEvo

An independent public website for hosting the EmbodiedEvo workflow on BluPe Remote YAM. It is separate from the existing BluPe app.

- Website: https://blupe-embodiedevo.andlyu.chatgpt.site/
- Public source snapshot: https://github.com/andlyu/blupe-embodiedevo-public
- Upstream method: [Einsia/EmbodiedEvo](https://github.com/Einsia/EmbodiedEvo)

The website exposes a view-only demo to visitors. Campaign data, model runs, live YAM cameras, physical runs and recordings remain protected behind an exact operator allowlist. A compute worker is not started by opening the website. The current integration has not yet verified a successful method-driven physical YAM task; simulator results and physical outcomes must be reported separately.

## What the code contains

- A campaign UI and durable D1 records for Practice, frozen knowledge and fresh simulation Tests.
- A worker that calls the pinned upstream EmbodiedEvo orchestration and stores native observations, outcomes and replay artifacts.
- A physical YAM adapter built on the pinned BluPe controller, with fresh measured feedback, bounded paired-arm commands, Stop handling and camera recording.
- Operator-only API checks and worker-token authentication. Public visitors cannot create campaigns, inspect private run records, read live cameras or start compute and robot jobs.

Git submodules pin the upstream BluPe Remote YAM and EmbodiedEvo repositories. Learned campaign packages, private run receipts, recordings, operator identities, production Site IDs and deployment secrets are not part of this public source snapshot.

## Run locally

Requirements: Node.js >=22.13 and Python 3. Clone with submodules:

```sh
git clone --recurse-submodules https://github.com/andlyu/blupe-embodiedevo-public.git
cd blupe-embodiedevo-public
npm install
npm run dev
```

The portable preview sign-in route is `/signin-with-chatgpt?return_to=/`. It is for local development and is excluded from production authentication.

To host your own Site, copy `.openai/hosting.example.json` to `.openai/hosting.json` and fill in your own Sites project ID and bindings. Configure `SITE_OPERATOR_USER_IDS` and `WORKER_TOKEN` as runtime secrets in Sites; never put production credentials in Git or the browser bundle. Follow [worker-agent/README.md](worker-agent/README.md) for worker setup. The worker does not start automatically, and physical execution requires a connected YAM-qualified worker and normal station readiness.

## Checks

```sh
node --test tests/domain.test.mjs tests/access-control.test.mjs
node --experimental-strip-types --test tests/yam.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
npx tsc --noEmit
npm run build
```

Local fixtures do not run models, simulation or robots. A successful build or API fixture does not establish physical task success, live motion or replay.

## Source and licensing

This repository is a public source snapshot; it omits production hosting metadata and private operational records. Upstream submodules retain their own licenses and release boundaries. No new license file is included in this snapshot.
