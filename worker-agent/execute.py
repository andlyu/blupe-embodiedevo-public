"""Trusted child entrypoint around the pinned upstream orchestrator."""
import json
import os
from pathlib import Path
import signal
import sys
from dataclasses import replace

from core import validate_job

def main():
    root=Path(__file__).resolve().parents[1]
    job=validate_job(json.loads(Path(sys.argv[1]).read_text()))
    run=Path(sys.argv[2]).resolve()
    upstream=root/'upstream/EmbodiedEvo'
    os.environ['EMBODIEDEVO_REPO']=str(upstream)
    sys.path.insert(0,str(upstream))
    from orchestrator.config import load_task, config_dict, config_from_dict
    from orchestrator import session_runner
    def cancelled(*_):
        raise KeyboardInterrupt('Worker cancellation requested')
    signal.signal(signal.SIGTERM,cancelled)
    signal.signal(signal.SIGINT,cancelled)
    if job['kind']=='hardware':
        from yam_trial import run as run_physical
        from core import native_run_path
        if job.get('hardware',{}).get('source')=='upstream_skill_library':
            return run_physical(job,None,run,root)
        original=native_run_path(Path(sys.argv[1]).parent,'sim_test')
        return run_physical(job,original,run,root)
    saved=run.parent/'resolved-config.json'
    c=job['config']
    if job['kind']=='practice':
        cfg=load_task(upstream/'tasks/RoboDojo',env_task=c['task'])
        cfg=replace(cfg,agent=replace(cfg.agent,model=c['model'],reasoning_effort=c['effort'],timeout_sec=c['seconds']),
                    playground=replace(cfg.playground,seed=c['seed'],budget=c['budget']),
                    test=replace(cfg.test,scenes=c['scenes'],budget=c['budget'],generation_timeout_sec=c['seconds']))
        saved.write_text(json.dumps(config_dict(cfg)))
        return session_runner.explore(cfg,run,gpu=os.environ.get('EMBODIEDEVO_GPU','0'),timeout_sec=c['seconds'])
    if not saved.exists():
        raise ValueError('The original practice worker volume is required for pinned Test provenance')
    cfg=config_from_dict(json.loads(saved.read_text()))
    # Native Test validates the frozen hashes and creates fresh scene/agent workspaces.
    return session_runner.test(cfg,run,gpu=os.environ.get('EMBODIEDEVO_GPU','0'))

if __name__=='__main__':
    raise SystemExit(main())
