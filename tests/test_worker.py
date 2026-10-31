import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import threading
import tempfile
import unittest
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'worker-agent'))
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'upstream/EmbodiedEvo'))
spec=importlib.util.spec_from_file_location('core',Path(__file__).parents[1]/'worker-agent/core.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
import yam_trial
import evidence
from yam_trial import (
 AttributedSessionAPI,LiveCameraRecorder,SessionSocketBridge,
 adapt_agent_command_for_session_bridge,enable_docker_session_bridge_client,
 zero_execution_failure,
)
class WorkerTests(unittest.TestCase):
 def test_observations_never_cross_practice_and_test_phases(self):
  with tempfile.TemporaryDirectory() as d:
   run=Path(d)
   practice=run/'playground/workspace/observations/000000/current_cam_head.png'
   practice.parent.mkdir(parents=True);practice.write_bytes(b'practice frame')
   self.assertEqual(core.latest_observation(run,'practice'),practice)
   self.assertIsNone(core.latest_observation(run,'sim_test'))
   test=run/'test/scene_0000/workspace/observations/000000/current_cam_head.png'
   test.parent.mkdir(parents=True);test.write_bytes(b'test frame')
   os.utime(practice,ns=(test.stat().st_mtime_ns+1000000,)*2)
   self.assertEqual(core.latest_observation(run,'sim_test'),test)
   self.assertEqual(core.latest_observation(run,'practice'),practice)
 def test_observations_follow_newest_test_scene_without_raw_frames(self):
  with tempfile.TemporaryDirectory() as d:
   run=Path(d);frames=[]
   for index in range(2):
    frame=run/f'test/scene_{index:04d}/workspace/observations/000000/current_cam_head.png'
    frame.parent.mkdir(parents=True);frame.write_bytes(b'public frame')
    os.utime(frame,ns=(1000000000*(index+1),)*2);frames.append(frame)
   (frames[1].parent/'raw_cam_head.png').write_bytes(b'private raw frame')
   self.assertEqual(core.latest_observation(run,'sim_test'),frames[1])
 def test_test_reuses_timestamped_practice_run_without_replacing_it(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);run=core.native_run_path(p,'practice')
   self.assertRegex(run.name,r'^\d{12}_practice$')
   self.assertEqual(core.native_run_path(p,'sim_test'),run)
   with self.assertRaises(FileExistsError):core.native_run_path(p,'practice')
 def test_test_cannot_select_another_native_directory(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'native-run.json').write_text(json.dumps({'directory':'../other'}))
   with self.assertRaises(ValueError):core.native_run_path(p,'sim_test')
 def test_frozen_manifest_must_match_native_protocol(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'frozen_harness/skills').mkdir(parents=True);(p/'frozen_harness/lessons').mkdir();raw=b'authored fixture';(p/'frozen_harness/skills/f.py').write_bytes(raw)
   protocol={'phase':'frozen','playground_valid':True,'harness':{'skills/f.py':hashlib.sha256(raw).hexdigest()}};(p/'protocol.json').write_text(json.dumps(protocol))
   self.assertEqual(core.frozen_files(p)[0]['path'],'skills/f.py');(p/'frozen_harness/skills/f.py').write_text('changed')
   with self.assertRaises(ValueError):core.frozen_files(p)
 def test_binary_frozen_knowledge_preserves_native_bytes_and_hashes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'frozen_harness/skills/__pycache__').mkdir(parents=True);(p/'frozen_harness/lessons').mkdir()
   raw=b'\xa7\x0d\x0d\x0a\x00compiled cache';name='skills/__pycache__/helper.pyc'
   (p/'frozen_harness'/name).write_bytes(raw)
   (p/'protocol.json').write_text(json.dumps({'phase':'frozen','playground_valid':True,'harness':{name:hashlib.sha256(raw).hexdigest()}}))
   file=core.frozen_files(p)[0];self.assertEqual(file['encoding'],'base64');self.assertEqual(base64.b64decode(file['content']),raw)
   self.assertEqual(file['sha256'],hashlib.sha256(raw).hexdigest())
 def test_invalid_protocol_never_becomes_frozen_package(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'protocol.json').write_text(json.dumps({'phase':'playground','playground_valid':False}))
   with self.assertRaises(ValueError):core.frozen_files(p)
 def test_native_scene_failures_stay_in_denominator(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.json').write_text(json.dumps({'scene_indices':[0,2],'results':[{'valid':True,'task_completed':False},{'valid':False,'failure':'interrupted_scene'}]}));r=core.outcomes(p)
   self.assertEqual([x['scene'] for x in r],[1,3]);self.assertFalse(r[0]['success']);self.assertFalse(r[1]['valid']);self.assertIsNone(r[1]['success'])
 def test_every_execution_requires_method_mode_and_confirmed_runner(self):
  base={'id':'00000000-0000-0000-0000-000000000001','campaign':'00000000-0000-0000-0000-000000000002','kind':'practice','method':'EmbodiedEvo','execution_mode':'Practice','runner_name':'Ada Operator','email':'ada@example.com','config':{'task':'stack_blocks','model':'gpt-6-astra','effort':'xhigh','pins':core.PINS,'budget':1,'scenes':1,'seed':0,'seconds':60}}
  self.assertIs(core.validate_job(base),base)
  for field in ('method','execution_mode','runner_name','email'):
   invalid=dict(base);invalid.pop(field)
   with self.assertRaises(ValueError):core.validate_job(invalid)
 def test_physical_jobs_require_runner_identity(self):
  job={'id':'00000000-0000-0000-0000-000000000001','campaign':'00000000-0000-0000-0000-000000000002','kind':'hardware','method':'EmbodiedEvo','execution_mode':'physical YAM','runner_name':'Ada Operator','email':'ada@example.com','config':{'task':'stack_blocks','model':'gpt-6-astra','effort':'xhigh','pins':core.PINS,'budget':100,'scenes':1,'seed':0,'seconds':600,'direct_yam':True,'skill_id':'stack_blocks','skill_library_revision':core.SKILL_LIBRARY_REVISION},'hardware':{'method':'EmbodiedEvo','robot':'yam-1','task':'stack the blue cube','seconds':600,'budget':100,'runner_name':'Ada Operator','email':'ada@example.com','source':'upstream_skill_library','skill_id':'stack_blocks','skill_library_revision':core.SKILL_LIBRARY_REVISION}}
  self.assertIs(core.validate_job(job),job)
  for field in ('runner_name','email'):
   invalid=json.loads(json.dumps(job));invalid['hardware'].pop(field)
   with self.assertRaises(ValueError):core.validate_job(invalid)
  for field,value in [('source','simulator_frozen_package'),('skill_id','cover_blocks'),('skill_library_revision','0'*40)]:
   invalid=json.loads(json.dumps(job));invalid['hardware'][field]=value
   with self.assertRaises(ValueError):core.validate_job(invalid)
 def test_upstream_skill_manifest_is_bounded_and_hash_uses_git_blob_format(self):
  from skill_library import SKILLS,git_blob_sha1,skill_manifest
  import hashlib
  self.assertGreaterEqual(len(SKILLS),40)
  self.assertEqual(git_blob_sha1(b'example'),hashlib.sha1(b'blob 7\0example').hexdigest())
  self.assertEqual(skill_manifest('stack_blocks')['revision'],core.SKILL_LIBRARY_REVISION)
  with self.assertRaises(ValueError):skill_manifest('../../outside')
 def test_attributed_session_api_forwards_confirmed_human_fields(self):
  class Stub:
   supports_trajectories=True
   def create_session(self,prompt,run_duration_s=300,**kwargs):return {'prompt':prompt,'run_duration_s':run_duration_s,**kwargs}
  api=AttributedSessionAPI(Stub(),'Ada Operator','ada@example.com')
  result=api.create_session('stack the blue cube',run_duration_s=600)
  self.assertEqual(result,{'prompt':'stack the blue cube','run_duration_s':600,'runner_name':'Ada Operator','email':'ada@example.com'})
  self.assertTrue(api.supports_trajectories)
 def test_live_recorder_captures_only_read_only_yam_camera_frames(self):
  class Response:
   status=200
   headers={'Content-Type':'image/jpeg'}
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def read(self,limit):return b'\xff\xd8fixture-jpeg\xff\xd9'
  urls=[]
  def open_camera(url,timeout):urls.append(url);return Response()
  with tempfile.TemporaryDirectory() as d:
   recorder=LiveCameraRecorder('https://yam.example','yam-1',Path(d)/'frames',fps=10)
   with patch.object(yam_trial,'urlopen',side_effect=open_camera):
    recorder.start();self.assertTrue(recorder.wait_until_ready(2));self.assertTrue(recorder.all_cameras_fresh())
    self.assertEqual(set(recorder.frame_counts),{'top','left','right'})
    self.assertTrue(all((Path(d)/'frames'/role/'000001.jpg').is_file() for role in recorder.CAMERAS))
    self.assertEqual(set(url.rsplit('/',1)[-1] for url in urls[:3]),{'top.jpg','left.jpg','right.jpg'})
    recorder.stop_event.set();recorder.thread.join(2)
 def test_physical_yam_session_environment_drops_simulator_egl(self):
  from orchestrator import host_policy
  with patch.object(host_policy,'require_allowed') as allowed, patch.dict(os.environ,{
   'MUJOCO_GL':'egl','PYOPENGL_PLATFORM':'egl','MUJOCO_EGL_DEVICE_ID':'0',
   'VK_ICD_FILENAMES':'/simulator/vulkan.json','CUDA_VISIBLE_DEVICES':'0,1',
   'OMP_NUM_THREADS':'16','OPENBLAS_NUM_THREADS':'16'},clear=False):
   env=yam_trial.physical_yam_session_env(None,'robodojo')
  allowed.assert_called_once_with('local')
  for name in ('MUJOCO_GL','PYOPENGL_PLATFORM','MUJOCO_EGL_DEVICE_ID','VK_ICD_FILENAMES'):
   self.assertNotIn(name,env)
  self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'')
  self.assertEqual(env['OMP_NUM_THREADS'],'1')
  self.assertEqual(env['OPENBLAS_NUM_THREADS'],'1')
 def test_yam_runtime_bootstrap_imports_with_native_mujoco_settings(self):
  from orchestrator import host_policy
  with patch.object(host_policy,'require_allowed'), patch.dict(os.environ,{
   'MUJOCO_GL':'egl','PYOPENGL_PLATFORM':'egl','MUJOCO_EGL_DEVICE_ID':'0',
   'VK_ICD_FILENAMES':'/simulator/vulkan.json'},clear=False):
   env=yam_trial.physical_yam_session_env(None,'robodojo')
  env.update(EMBODIEDEVO_YAM_PYTHON=sys.executable,
   EMBODIEDEVO_REPO=str(ROOT/'upstream/EmbodiedEvo'))
  result=subprocess.run([str(ROOT/'worker-agent/yam-runtime/bin/python'),
   '-m','orchestrator.session','--help'],env=env,text=True,capture_output=True,timeout=20)
  self.assertEqual(result.returncode,0,result.stderr)
  self.assertIn('Host-owned persistent simulator',result.stdout)
 def test_session_bridge_client_adapter_is_scoped_to_copied_upstream_cli(self):
  upstream=ROOT/'upstream/EmbodiedEvo/tasks/RoboDojo/Workspace/scripts/env.py'
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'env.py';path.write_text(upstream.read_text())
   self.assertTrue(enable_docker_session_bridge_client(path))
   self.assertFalse(enable_docker_session_bridge_client(path))
   compile(path.read_text(),str(path),'exec')
   patched=path.read_text()
   self.assertIn('host.docker.internal',patched)
   self.assertIn('EMBODIEDEVO_SESSION_BRIDGE_TOKEN',patched)
   self.assertIn('socket.AF_UNIX',patched)
 def test_session_socket_bridge_authenticates_and_forwards_one_json_request(self):
  with tempfile.TemporaryDirectory() as directory:
   socket_path=str(Path(directory)/'session.sock')
   native=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
   native.bind(socket_path);native.listen(1)
   bridge=SessionSocketBridge(socket_path)
   observed={}
   request=(json.dumps({'op':'status'})+chr(10)).encode()
   response=(json.dumps({'ok':True,'execution':0})+chr(10)).encode()
   def session_server():
    client,_=native.accept()
    with client:
     observed['request']=client.makefile('rb').readline(1024)
     client.sendall(response)
   thread=threading.Thread(target=session_server,daemon=True);thread.start()
   try:
    with socket.create_connection(('127.0.0.1',bridge.port),timeout=3) as client:
     stream=client.makefile('rwb')
     stream.write(('AUTH '+bridge.token+chr(10)).encode());stream.flush()
     self.assertEqual(stream.readline(128),b'OK'+bytes((10,)))
     stream.write(request);stream.flush()
     self.assertEqual(json.loads(stream.readline(1024)),{'ok':True,'execution':0})
    thread.join(3)
    self.assertEqual(observed['request'],request)
    self.assertEqual(bridge.snapshot()['requests_forwarded'],1)
    self.assertEqual(bridge.snapshot()['responses_received'],1)
   finally:
    bridge.close();native.close()
 def test_session_socket_bridge_rejects_untrusted_clients(self):
  with tempfile.TemporaryDirectory() as directory:
   bridge=SessionSocketBridge(str(Path(directory)/'missing.sock'))
   try:
    with socket.create_connection(('127.0.0.1',bridge.port),timeout=3) as client:
     client.sendall(b'AUTH wrong'+bytes((10,)))
     self.assertEqual(client.makefile('rb').readline(128),b'DENIED'+bytes((10,)))
    self.assertEqual(bridge.snapshot()['rejected'],1)
    self.assertEqual(bridge.snapshot()['requests_forwarded'],0)
   finally:bridge.close()
 def test_session_bridge_rewrites_only_the_session_mount_and_address(self):
  class Bridge:
   address='tcp://host.docker.internal:42123'
   token='one-run-token'
  argv=['docker','run','--mount','type=bind,src=/tmp/session,dst=/run/embodiedevo,readonly',
        '--mount','type=bind,src=/tmp/home,dst=/home/agent',
        '--env','EMBODIEDEVO_SOCKET=/run/embodiedevo/session.sock','embodiedevo-agent:latest']
  adapted=adapt_agent_command_for_session_bridge(argv,Bridge())
  self.assertNotIn('/run/embodiedevo',str(adapted))
  self.assertIn('type=bind,src=/tmp/home,dst=/home/agent',adapted)
  self.assertIn('EMBODIEDEVO_SOCKET=tcp://host.docker.internal:42123',adapted)
  self.assertIn('EMBODIEDEVO_SESSION_BRIDGE_TOKEN=one-run-token',adapted)
  with self.assertRaisesRegex(RuntimeError,'Pinned upstream Docker command changed'):
   adapt_agent_command_for_session_bridge(['docker','run','image'],Bridge())
 def test_zero_program_session_is_infrastructure_failure_but_task_failure_is_valid(self):
  self.assertEqual(zero_execution_failure({'valid':True,'executions_used':0},{'requests_forwarded':0}),
                   'agent_transport_unavailable')
  self.assertEqual(zero_execution_failure({'valid':True,'executions_used':0},{'requests_forwarded':2}),
                   'agent_no_program_submitted')
  self.assertIsNone(zero_execution_failure({'valid':True,'executions_used':1},{'requests_forwarded':1}))
 def test_physical_evidence_uses_timestamp_prefixed_session_run(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);native=root/'202610312121_session';native.mkdir()
   self.assertEqual(evidence.physical_session_directory(root),native)
   (root/'202610312122_session').mkdir()
   with self.assertRaisesRegex(ValueError,'exactly one'):
    evidence.physical_session_directory(root)
 def test_physical_evidence_keeps_legacy_session_path(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);legacy=root/'session';legacy.mkdir()
   self.assertEqual(evidence.physical_session_directory(root),legacy)
if __name__=='__main__':unittest.main()
