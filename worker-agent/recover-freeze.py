#!/usr/bin/env python3
"""Re-export one original valid freeze. Starts no simulator or model."""
import json
import os
from pathlib import Path
import sys

from core import frozen_files, native_run_path, validate_job, verify_pins
from run import Client

def main():
    if len(sys.argv) != 2:
        raise ValueError('Supply the original Practice job JSON path')
    path = Path(sys.argv[1]).resolve()
    job = validate_job(json.loads(path.read_text()))
    if job['kind'] != 'practice' or path.stem != job['id'] or path.parent.name != job['campaign']:
        raise ValueError('Recovery requires the original Practice identity')
    verify_pins(Path(__file__).resolve().parents[1])
    run = native_run_path(path.parent, 'sim_test')  # Read the original pointer; never create a run.
    files = frozen_files(run)
    client = Client(os.environ['SITE_ORIGIN'], os.environ['WORKER_TOKEN'],
                    os.environ['WORKER_ID'], os.environ.get('SITE_ACCESS_TOKEN', ''))
    native_result = json.loads((run / 'playground/result.json').read_text())
    completed = native_result.get('task_completed') is True
    result = client.post('recover-freeze', {
        'job': job['id'], 'state': 'completed', 'protocolValid': True, 'files': files,
        'summary': f'Recovered byte-preserving export of the original valid native freeze; no Practice rerun. Practice task completed: {completed}.'})
    print(json.dumps({'job':job['id'], 'files':len(files), 'result':result,
                      'startsExecution':False}))

if __name__ == '__main__':
    main()
