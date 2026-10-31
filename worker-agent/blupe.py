"""Use the actual pinned BluPe SDK for a future qualified hardware adapter.

This module does not submit motion, create sessions or implement pretend YAM
primitives. Hardware jobs are rejected by the website and simulation worker.
"""
from pathlib import Path
import sys

def session_api_class():
    source=Path(__file__).resolve().parents[1]/'upstream/blupe-remote-yam/codex-runner/src'
    sys.path.insert(0,str(source))
    from remote_yam.session import HttpSessionAPI
    return HttpSessionAPI

ADAPTER_STATUS={'implemented':False,'validated':False,'source':'upstream/blupe-remote-yam',
                'missing':['primitive mapping','robot geometry and frame calibration','observation mapping',
                           'completion and recovery feedback','physical trial evidence']}
