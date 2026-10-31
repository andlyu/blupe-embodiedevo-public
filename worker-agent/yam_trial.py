"""One isolated physical transfer trial using the real pinned code-session host."""
from dataclasses import replace
import json
import os
from pathlib import Path
from queue import Queue,Empty
import shutil
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

from core import frozen_files,native_run_path
from physical_budget import native_seconds

ORIGIN='https://yam-session-api.n5hthc3gj4cqy.us-east-1.cs.amazonlightsail.com'
ROBOT='yam-1'

class AttributedSessionAPI:
    """Add the confirmed human runner to the normal YAM session creation call."""
    def __init__(self,api,runner_name,email):
        self.api=api
        self.runner_name=runner_name
        self.email=email
    def __getattr__(self,name):
        return getattr(self.api,name)
    def create_session(self,prompt,*args,**kwargs):
        kwargs.update(runner_name=self.runner_name,email=self.email)
        return self.api.create_session(prompt,*args,**kwargs)

class LiveCameraRecorder:
    """Capture real YAM views throughout queueing, homing and method execution."""
    CAMERAS={'top':'cam_head','left':'cam_left_wrist','right':'cam_right_wrist'}
    def __init__(self,origin,robot,directory,fps=2):
        self.origin=origin.rstrip('/');self.robot=robot;self.directory=Path(directory);self.fps=fps
        self.stop_event=threading.Event();self.ready=threading.Event();self.thread=None
        self.frame_counts={role:0 for role in self.CAMERAS};self.last_frame_at={}
        self.errors={role:'No live frame received yet' for role in self.CAMERAS}
    def start(self):
        self.directory.mkdir(parents=True,exist_ok=False)
        self.thread=threading.Thread(target=self._capture,name='yam-live-camera-recording',daemon=True)
        self.thread.start()
    def _capture(self):
        period=1/self.fps
        while not self.stop_event.is_set():
            cycle=time.monotonic()
            for role in self.CAMERAS:
                if self.stop_event.is_set():break
                try:
                    url=f'{self.origin}/v1/robots/{self.robot}/cameras/{role}.jpg'
                    with urlopen(url,timeout=4) as response:
                        if response.status!=200 or not response.headers.get('Content-Type','').startswith('image/jpeg'):
                            raise RuntimeError('camera endpoint did not return JPEG')
                        raw=response.read(3*1024*1024+1)
                    if len(raw)>3*1024*1024 or not raw.startswith(b'\xff\xd8') or not raw.endswith(b'\xff\xd9'):
                        raise RuntimeError('camera frame was not a bounded JPEG')
                    index=self.frame_counts[role]+1
                    folder=self.directory/role;folder.mkdir(parents=True,exist_ok=True)
                    (folder/f'{index:06d}.jpg').write_bytes(raw)
                    self.frame_counts[role]=index;self.last_frame_at[role]=time.time()
                    self.errors.pop(role,None)
                except Exception as exc:
                    self.errors[role]=type(exc).__name__+': '+str(exc)[:200]
            if all(self.frame_counts.values()):self.ready.set()
            self.stop_event.wait(max(0,period-(time.monotonic()-cycle)))
    def wait_until_ready(self,timeout=8):return self.ready.wait(timeout)
    def all_cameras_fresh(self,max_age=5):
        now=time.time()
        return all(now-self.last_frame_at.get(role,0)<=max_age for role in self.CAMERAS)
    def finalize(self,episode):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=8)
        if self.thread and self.thread.is_alive():raise TimeoutError('YAM camera recorder did not stop cleanly')
        if not self.ready.is_set() or any(count<2 for count in self.frame_counts.values()):
            raise RuntimeError('Continuous YAM camera footage is incomplete: '+json.dumps(self.errors,sort_keys=True))
        native=Path(__file__).resolve().parents[1]/'upstream/EmbodiedEvo/.venv-robodojo/bin/python'
        ffmpeg=subprocess.check_output([str(native),'-c','import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],text=True,timeout=10).strip()
        final=Path(episode)/'final';final.mkdir(parents=True,exist_ok=True)
        for role,name in self.CAMERAS.items():
            pattern=str(self.directory/role/'%06d.jpg');output=final/f'trace_{name}.mp4'
            subprocess.run([ffmpeg,'-y','-v','error','-framerate',str(self.fps),'-i',pattern,'-an','-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2','-c:v','libx264','-preset','ultrafast','-crf','28','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True,timeout=120)
            if not output.is_file() or output.stat().st_size<=0 or output.stat().st_size>64*1024*1024:
                raise RuntimeError('Encoded physical camera footage is missing or exceeds the evidence limit')
        shutil.rmtree(self.directory)
        return {'fps':self.fps,'frames':dict(self.frame_counts)}

def no_physical_replay(*args,**kwargs):
    return {'status':'recorded_live','complete':True,'ok':True,'physical_replay':False,
            'reason':'Physical command history is recorded live; actions are never replayed.'}

def run(job,original,trial,root):
    from orchestrator import session_runner
    from orchestrator.config import config_from_dict,config_dict
    from orchestrator.files import hashes,write_json
    sys.path.insert(0,str(root/'upstream/blupe-remote-yam/codex-runner/src'))
    from remote_yam.session import HttpSessionAPI
    from remote_yam.controller import RunnerController
    from remote_yam.aspire_api_policy import AspireApiPolicy
    original=Path(original);trial=Path(trial)
    if trial.exists():raise ValueError('A physical attempt cannot be replayed or replaced')
    trial.mkdir(parents=True)
    frozen_files(original)
    source=json.loads((original/'protocol.json').read_text())['harness']
    h=job['hardware']
    if h['robot']!=ROBOT:raise ValueError('Unsupported physical station')
    with urlopen(ORIGIN+'/v1/contracts',timeout=10) as response:contract=json.load(response)
    if contract.get('joint_trajectory_request',{}).get('properties',{}).get('cadence_hz',{}).get('const')!=10:
        raise ValueError('Deployment does not confirm the required packet contract')
    with urlopen(ORIGIN+f'/v1/robots/{ROBOT}/calibration',timeout=10) as response:calibration=json.load(response)
    if calibration.get('robot_id')!=ROBOT:raise ValueError('Station calibration identity differs')
    cfg=config_from_dict(json.loads((original.parent/'resolved-config.json').read_text()))
    cfg=replace(cfg,name='embodiedevo/blupe-physical-transfer',
        simulator=replace(cfg.simulator,interpreter=str(root/'worker-agent/yam-runtime')),
        agent=replace(cfg.agent,timeout_sec=h['seconds']),
        test=replace(cfg.test,scenes=1,budget=h['budget'],generation_timeout_sec=h['seconds'],
                     submission_timeout_sec=min(120,h['seconds']),feedback_fps=10))
    session_runner.prepare_inputs(cfg,trial)
    inputs=trial/'inputs'
    (inputs/'primitives/primitives.md').write_text((root/'worker-agent/yam/primitives.md').read_text())
    with (inputs/'test.md').open('a') as stream:
        stream.write('\n\n# Physical transfer\nRead primitives/primitives.md. This is real YAM hardware, not ARX simulation. Use measured YAM frames and preserve frozen knowledge. Success is reviewed from physical evidence, not your claim. Never request reset or replay an action.\n')
    shutil.copytree(original/'frozen_harness',trial/'frozen_harness')
    write_json(trial/'protocol.json',{'protocol':'blupe-physical-transfer-v1','phase':'physical_test',
        'parent_run':original.name,'parent_job':job['id'],'source_artifact':job['artifact'],
        'harness':source,'inputs':hashes(inputs),'robot':ROBOT,'task':h['task'],
        'physical_replay':False,'success_evaluator':'operator_review'})
    write_json(trial/'calibration.json',calibration)
    leased=Queue(maxsize=1);finished=threading.Event();outcome={}
    def program(socket_path):
        leased.put(socket_path)
        while not finished.wait(.1):
            if policy.cancelled():return {'status':'cancelled'}
        return dict(outcome)
    class EvoPolicy(AspireApiPolicy):
        provider_name='embodiedevo'
        model='EmbodiedEvo frozen skills · Astra'
        def public_config(self):
            return {'provider':self.provider_name,'model':self.model,
                    'physical_motion_enabled':True,'implementation':'frozen_code_session_physical_transfer',
                    'source_artifact':job['artifact'],'phase':'complete' if self._finished else 'physical_trial'}
    policy=EvoPolicy(run_harness=program,calibration=calibration,robot_id=ROBOT,
                    task=h['task'],recording_path=trial,allow_hardware=True)
    api=AttributedSessionAPI(HttpSessionAPI(ORIGIN,robot_id=ROBOT,supports_trajectories=True),h['runner_name'],h['email'])
    controller=RunnerController(api,robot_id=ROBOT,hardware_control_enabled=True,
                                recording_root=trial/'controller',share_conversation=False)
    recorder=LiveCameraRecorder(ORIGIN,ROBOT,trial/'live-camera-frames',fps=2)
    previous=session_runner.run_replay
    stage=trial/'session'
    initial=time.time();native=None
    def progress():
        status=controller.status()
        value={k:status.get(k) for k in ('status','session_id','queue_position',
            'commands_submitted','packets_submitted','error','safety_error',
            'execution_blocked_reason','feedback_warning')}
        value['progress_at']=time.time()
        for file in ('session-result.json','runtime.json'):
            try:
                d=json.loads((stage/file).read_text())
                for k in ('executions_used','native_steps_used'):
                    if type(d.get(k)) is int:value[k]=d[k]
                if file=='runtime.json':value['agent_state']=d.get('status')
            except (OSError,ValueError):pass
        temporary=trial/('hardware-progress.'+str(threading.get_ident())+'.tmp')
        write_json(temporary,value);temporary.replace(trial/'hardware-progress.json')
    def track():
        while not finished.wait(1):
            try:
                if not recorder.all_cameras_fresh(max_age=5):
                    controller.stop(reason='camera_recording_stale')
                    outcome.update(recording_error='A live YAM camera became stale; controller Stop was requested.')
                    return
                progress()
            except Exception:pass  # Reporting cannot change a physical outcome.
    try:
        recorder.start()
        if not recorder.wait_until_ready():raise RuntimeError('Live YAM camera recording did not initialize; no robot session was created')
        controller.join_and_run(policy,h['task'],run_duration_s=h['seconds'])
        while True:
            status=controller.status()
            progress()
            try:socket_path=leased.get(timeout=.25);break
            except Empty:
                if status['status'] in {'stopped','timed_out','disconnected','safety_aborted','error'}:
                    raise RuntimeError(status.get('error') or 'Physical session ended before initialized lease feedback')
                if time.time()-initial>180:raise TimeoutError('Physical queue admission timed out; attempt retained')
        available=native_seconds(controller.status(),h['seconds'],time.time())
        cfg=replace(cfg,agent=replace(cfg.agent,timeout_sec=available),
                    test=replace(cfg.test,generation_timeout_sec=available,submission_timeout_sec=min(120,available)))
        write_json(trial/'physical-budget.json',{'requested_seconds':h['seconds'],
                    'native_seconds':available,'cleanup_reserve_seconds':20,
                    'lease_started_at':controller.status().get('run_started_at')})
        threading.Thread(target=track,name='physical-progress',daemon=True).start()
        os.environ.update(EMBODIEDEVO_YAM_BRIDGE=str(socket_path),EMBODIEDEVO_YAM_ORIGIN=ORIGIN,
            EMBODIEDEVO_YAM_ROBOT=ROBOT,EMBODIEDEVO_YAM_TASK=h['task'],
            EMBODIEDEVO_YAM_PYTHON=sys.executable)
        os.environ.pop('EMBODIEDEVO_ROBODOJO_RUNTIME_PROFILE',None)
        session_runner.run_replay=no_physical_replay
        native=session_runner.run_episode(cfg,stage,trial,phase='test',seed=0,
                    seconds=available,harness=trial/'frozen_harness',gpu=None)
        if hashes(trial/'frozen_harness')!=source or hashes(original/'frozen_harness')!=source:
            raise ValueError('Frozen knowledge changed during physical transfer')
        status=controller.status()
        valid=native.get('valid') is True and not policy._failure and not status.get('error') and not status.get('safety_error')
        outcome.update(status='complete' if valid else 'failed',valid=valid,success=None,
                       executions=native.get('executions_used'),native_steps=native.get('native_steps_used'),
                       reason=native.get('failure') or policy._failure or status.get('error'),
                       evaluator='operator_review',physical_replay=False)
        return 0 if valid else 1
    except BaseException as exc:
        outcome.update(status='failed',valid=False,success=None,reason=type(exc).__name__+': '+str(exc),
                       evaluator='operator_review',physical_replay=False)
        raise
    finally:
        session_runner.run_replay=previous
        finished.set()
        try:controller.stop(reason='policy_complete' if outcome.get('valid') else 'runner_disconnected')
        finally:
            try:outcome['recording']=recorder.finalize(stage)
            except Exception as exc:outcome['recording_error']=type(exc).__name__+': '+str(exc)
            try:progress()
            except Exception:pass
            write_json(trial/'physical-result.json',{**outcome,'source_artifact':job['artifact'],
                       'knowledge_hashes':source,'robot':ROBOT,'task':h['task'],'finished_at':time.time()})
            write_json(trial/'hardware-trace.json',controller.sanitized_episode_trace())
