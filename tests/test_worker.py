import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('core',Path(__file__).parents[1]/'worker-agent/core.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
sys.path.insert(0,str(Path(__file__).parents[1]/'worker-agent'))
import yam_trial
from yam_trial import AttributedSessionAPI,LiveCameraRecorder
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
  job={'id':'00000000-0000-0000-0000-000000000001','campaign':'00000000-0000-0000-0000-000000000002','kind':'hardware','method':'EmbodiedEvo','execution_mode':'physical YAM','runner_name':'Ada Operator','email':'ada@example.com','config':{'task':'stack_blocks','model':'gpt-6-astra','effort':'xhigh','pins':core.PINS,'budget':1,'scenes':1,'seed':0,'seconds':60},'hardware':{'method':'EmbodiedEvo','robot':'yam-1','task':'stack the blue cube','seconds':600,'budget':100,'runner_name':'Ada Operator','email':'ada@example.com'},'artifact':'00000000-0000-0000-0000-000000000003'}
  self.assertIs(core.validate_job(job),job)
  for field in ('runner_name','email'):
   invalid=json.loads(json.dumps(job));invalid['hardware'].pop(field)
   with self.assertRaises(ValueError):core.validate_job(invalid)
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
if __name__=='__main__':unittest.main()
