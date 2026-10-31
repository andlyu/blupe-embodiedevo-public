"""Trusted native session entrypoint. Physical replay is intentionally unsupported."""
import os
from pathlib import Path
import runpy
import sys

root=Path(__file__).resolve().parents[1]
if len(sys.argv)<3 or sys.argv[1:3]!=['-m','orchestrator.session']:
    raise ValueError('Physical entrypoint supports only a live session, never replay')
sys.path.insert(0,str(root/'upstream/EmbodiedEvo'))
sys.path.insert(0,str(root/'upstream/blupe-remote-yam/codex-runner/src'))
import simulators.backend
from yam_environment import YamTask
simulators.backend.build=lambda cfg,seed=None:YamTask(
    socket_path=os.environ['EMBODIEDEVO_YAM_BRIDGE'],
    origin=os.environ['EMBODIEDEVO_YAM_ORIGIN'],
    robot=os.environ['EMBODIEDEVO_YAM_ROBOT'],
    instruction=os.environ['EMBODIEDEVO_YAM_TASK'])
sys.argv=['orchestrator.session',*sys.argv[3:]]
runpy.run_module('orchestrator.session',run_name='__main__')
