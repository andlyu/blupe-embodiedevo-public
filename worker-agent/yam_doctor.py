"""Read-only station/model qualification; never creates a robot session."""
import json
from pathlib import Path
import sys
import time
from urllib.request import urlopen
import numpy as np
root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root/'upstream/EmbodiedEvo'),str(root/'upstream/blupe-remote-yam/codex-runner/src')]
from yam_environment import validate_action,YamTask
from remote_yam.mujoco_ik import BimanualRelativeIK,ROBOT_SHA256,SCENE_SHA256
from remote_yam.aspire_adapter import arm_pose
from remote_yam.cameras import CameraFrameSource
from yam_trial import ORIGIN,ROBOT

def check():
 with urlopen(ORIGIN+f'/v1/robots/{ROBOT}/calibration',timeout=10) as r:c=json.load(r)
 with urlopen(ORIGIN+f'/v1/robots/{ROBOT}/observation',timeout=10) as r:f=json.load(r)
 with urlopen(ORIGIN+'/v1/contracts',timeout=10) as r:contract=json.load(r)
 assert c['kinematics']['robot_model_sha256']==ROBOT_SHA256 and c['kinematics']['scene_sha256']==SCENE_SHA256
 assert contract['joint_trajectory_request']['properties']['cadence_hz']['const']==10
 ik=BimanualRelativeIK(base_spacing_m=c['base_geometry']['spacing_m']);q=np.clip(np.deg2rad(f['left_joints_deg']+f['right_joints_deg']),ik.low,ik.high);errors=[]
 for d in (np.zeros(12),np.linspace(-.02,.02,12),np.linspace(.02,-.02,12)):
  sample=np.clip(q+d,ik.low,ik.high);ik._forward(sample);obs={s+'_joints_deg':np.rad2deg(sample[i*6:(i+1)*6]).tolist() for i,s in enumerate(('left','right'))}
  for s,(p,r) in zip(('left','right'),ik._poses()):
   t=arm_pose(c,obs,s);errors.append(float(max(np.max(abs(p-t[:3,3])),np.max(abs(r-t[:3,:3])))))
 assert max(errors)<2e-6
 frames=CameraFrameSource(ORIGIN).capture_for_policy(f)
 assert len(frames)==3 and all(x.source_captured_at and 0<=time.time()-x.source_captured_at<5 for x in frames)
 action={s+'_'+k:([0]*6 if k=='arm_joint_state' else [.5]) for s in ('left','right') for k in ('arm_joint_state','ee_joint_state')}
 assert validate_action(action)[0]=='joint'
 for change in ({'left_ee_joint_state':[2]},{'left_arm_joint_state':[float('nan')]*6},{'right_arm_joint_state':[True]*6}):
  try:validate_action({**action,**change})
  except ValueError:pass
  else:raise AssertionError('Invalid command admitted')
 assert callable(YamTask._build_observation)
 return {'ready':True,'source':'read_only_live_station_and_pinned_model','geometry_max_error':max(errors),'virtual_fk_samples':3,'camera_roles':[x.name for x in frames],'robot':ROBOT,'calibration_id':c['calibration_id'],'station_mode':f['mode'],'physical_session_created':False,'physical_motion_started':False}
if __name__=='__main__':print(json.dumps(check(),indent=2))
