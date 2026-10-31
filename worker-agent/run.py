#!/usr/bin/env python3
"""Authenticated polling worker. Running this command can start queued model/GPU jobs."""
import argparse
import base64
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.parse import urlsplit

from core import PINS, validate_job, verify_pins, frozen_files, outcomes, native_run_path, latest_observation
from doctor import inspect_runtime

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*_):
        return None

class Client:
    def __init__(self,origin,token,worker,access=''):
        u=urlsplit(origin)
        if u.username or u.password or u.path not in ('','/') or u.query or u.fragment or not u.hostname or not (u.scheme=='https' or u.scheme=='http' and u.hostname in {'localhost','127.0.0.1'}):
            raise ValueError('Use the website HTTPS origin or a loopback preview')
        if len(token)<32:
            raise ValueError('WORKER_TOKEN must contain at least 32 characters')
        self.origin,self.token,self.worker,self.access=origin.rstrip('/'),token,worker,access
        self.open=build_opener(ProxyHandler({}),NoRedirect()).open
    def post(self,path,data):
        headers={'Content-Type':'application/json','Authorization':'Bearer '+self.token}
        if self.access:
            headers['OAI-Sites-Authorization']=self.access if self.access.startswith('Bearer ') else 'Bearer '+self.access
        request=Request(self.origin+'/api/worker/'+path,data=json.dumps(dict(data,worker=self.worker),allow_nan=False).encode(),headers=headers)
        with self.open(request,timeout=30) as response:
            return json.load(response)
    def heartbeat(self):
        return self.post('heartbeat',{'version':PINS['embodiedevo'],'yam':os.environ.get('EMBODIEDEVO_ENABLE_YAM')=='1'})

def serve_job(client,job,root,store):
    validate_job(job)
    verify_pins(root)
    directory=store/job['campaign'];directory.mkdir(parents=True,exist_ok=True)
    original=native_run_path(directory,job['kind'])
    run=original/'physical'/job['id'] if job['kind']=='hardware' else original
    jobfile=directory/(job['id']+'.json');jobfile.write_text(json.dumps(job))
    logpath=directory/(job['id']+'.log')
    cancelled=False;last_frame=None
    with logpath.open('wb') as log:
        python=str(root/'upstream/EmbodiedEvo/.venv-robodojo/bin/python') if job['kind']=='hardware' else sys.executable
        child=subprocess.Popen([python,str(root/'worker-agent/execute.py'),str(jobfile),str(run)],
                               cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        started=time.monotonic()
        try:
            while child.poll() is None:
                client.heartbeat()
                status=client.post('status',{'job':job['id']})
                if status.get('state')=='cancel_requested' or time.monotonic()-started>(job['hardware']['seconds']+240 if job['kind']=='hardware' else job['config']['seconds']*(job['config']['scenes']+1)+300):
                    cancelled=True;os.killpg(child.pid,signal.SIGINT)
                    try:child.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid,signal.SIGKILL);child.wait()
                    break
                if job['kind']=='hardware':
                    progress=run/'hardware-progress.json'
                    if progress.exists():client.post('progress',{'job':job['id'],'progress':json.loads(progress.read_text())})
                # Only public native camera images exported for the agent are uploaded.
                frame=latest_observation(run,job['kind'])
                if frame is not None:
                    key=(str(frame),frame.stat().st_mtime_ns)
                    if key!=last_frame:
                        raw=frame.read_bytes()
                        if len(raw)<=2*1024*1024:
                            client.post('observation',{'job':job['id'],'png':base64.b64encode(raw).decode()})
                        last_frame=key
                time.sleep(2)
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGINT)
                try:child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise
    report={'job':job['id'],'state':'cancelled' if cancelled else 'completed' if child.returncode==0 else 'failed',
            'summary':'Native process cancelled; attempt retained.' if cancelled else 'Pinned upstream process exited '+str(child.returncode)+'.',
            'outcomes':outcomes(run)}
    if job['kind']=='hardware':
        result_path=run/'physical-result.json'
        result=json.loads(result_path.read_text()) if result_path.exists() else {}
        progress_path=run/'hardware-progress.json'
        if progress_path.exists():report['progress']=json.loads(progress_path.read_text())
        summary='Physical transfer attempt retained. Task outcome requires evidence review.' if result.get('valid') else str(result.get('reason') or 'Physical process ended before valid completion.')
        if isinstance(result.get('recording'),dict):
            frames=result['recording'].get('frames',{})
            report['recording']={'source':'live_yam_cameras','continuous':True,
                                 'fps':result['recording'].get('fps'),
                                 'frames':frames}
            summary+=f" Live YAM camera footage recorded at {result['recording'].get('fps')} fps ({sum(frames.values())} frames across three views)."
        if result.get('recording_error'):
            report['recording']={'source':'live_yam_cameras','continuous':False,
                                 'error':str(result['recording_error'])[:300]}
            summary+=' Live YAM camera recording incomplete: '+str(result['recording_error'])[:300]
        report.update(outcomes=[{'scene':1,'valid':result.get('valid',False),'success':None,'reason':result.get('reason') or ''}],summary=summary)
    try:
        from evidence import publish_evidence
        publish_evidence(client,job,run)
    except Exception as exc:
        report['summary']+=' Evidence upload incomplete: '+str(exc)[:300]
    if report['state']=='completed' and job['kind']=='practice':
        try:report.update(protocolValid=True,files=frozen_files(run))
        except Exception as exc:report.update(state='failed',summary=str(exc),protocolValid=False,failureCode='knowledge_export_failed')
    # Native Test has per-scene validity/completion; process exit is not a success metric.
    # A lost report response is reconciled via status, not by starting another job.
    try:client.post('report',report)
    except Exception:
        state=client.post('status',{'job':job['id']}).get('state')
        if state in {'running','cancel_requested'}:
            if state=='cancel_requested':report['state']='cancelled'
            client.post('report',report)
        elif state not in {'completed','failed','cancelled'}:
            raise

def main():
    os.umask(0o077)  # Native run/config evidence stays private to the operator.
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish-evidence',metavar='CAMPAIGN',help='Publish retained native evidence without running models or hardware')
    parser.add_argument('--check',action='store_true',help='Inspect real prerequisites without starting physics/models/jobs')
    parser.add_argument('--runtime-only',action='store_true',help='With --check, inspect installed runtime before operator login')
    parser.add_argument('--check-site',action='store_true',help='Authenticate to the site without heartbeat, job claim or execution')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];verify_pins(root)
    if args.check:
        result=inspect_runtime(root,model=not args.runtime_only)
        print(json.dumps(result,indent=2));return 0 if result['ready'] else 1
    if args.runtime_only:
        parser.error('--runtime-only requires --check')
    client=Client(os.environ['SITE_ORIGIN'],os.environ['WORKER_TOKEN'],os.environ.get('WORKER_ID','sim-worker-1'),os.environ.get('SITE_ACCESS_TOKEN',''))
    if args.publish_evidence:
        import re
        from evidence import publish_evidence
        if not re.fullmatch(r'[a-f0-9-]{36}',args.publish_evidence):raise ValueError('Invalid campaign')
        store=Path(os.environ['RUN_STORE']).resolve();directory=store/args.publish_evidence
        for path in sorted(directory.glob('*.json')):
            job=json.loads(path.read_text())
            if job.get('id')!=path.stem or job.get('kind') not in {'practice','sim_test','hardware'}:continue
            validate_job(job);run=native_run_path(directory,'sim_test')
            if job['kind']=='hardware':run=run/'physical'/job['id']
            publish_evidence(client,job,run)
        print(json.dumps({'published':True,'startsExecution':False}));return 0
    if args.check_site:
        result=client.post('probe',{})
        if result.get('pins')!=PINS:raise ValueError('Website source pins differ')
        print(json.dumps(result));return 0
    readiness=inspect_runtime(root)
    if not readiness['ready']:
        print(json.dumps(readiness,indent=2),file=sys.stderr)
        return 1
    store=Path(os.environ.get('RUN_STORE',str(root/'worker-agent/.runs'))).resolve();store.mkdir(parents=True,exist_ok=True)
    while True:
        client.heartbeat();job=client.post('claim',{}).get('job')
        if job:serve_job(client,job,root,store)
        else:time.sleep(3)

if __name__=='__main__':raise SystemExit(main())
