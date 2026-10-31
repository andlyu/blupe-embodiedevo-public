"""Physical YAM implementation of the pinned four-primitive code environment.

No credentials enter agent code. The shared BluPe controller owns the lease,
packet dispatch, safety checks and measured completion through a Unix bridge.
"""
from copy import deepcopy
import io
import math
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

from simulators.execution import CodeTask
from simulators.robodojo_api import RoboDojoLowLevelApi
from remote_yam.aspire_api_policy import BridgeClient
from remote_yam.aspire_adapter import arm_pose
from remote_yam.cameras import CameraFrameSource
from remote_yam.mujoco_ik import BimanualRelativeIK, ROBOT_SHA256, SCENE_SHA256

CAMERAS={'top':'cam_head','left':'cam_left_wrist','right':'cam_right_wrist'}

def vector(value,n,name):
    raw=np.asarray(value)
    if raw.shape!=(n,) or raw.dtype.kind not in 'fiu' or not np.isfinite(raw).all():
        raise ValueError(f'{name} requires {n} finite numbers')
    return raw.astype(float)

def validate_action(action):
    if not isinstance(action,dict):raise ValueError('Action must be a complete paired dictionary')
    joint={f'{s}_{k}' for s in ('left','right') for k in ('arm_joint_state','ee_joint_state')}
    ee={f'{s}_{k}' for s in ('left','right') for k in ('ee_pose','ee_joint_state')}
    if set(action)==joint:mode='joint'
    elif set(action)==ee:mode='ee'
    else:raise ValueError('Supply both arms and grippers in exactly one joint or EE mode')
    result={}
    for s in ('left','right'):
        g=vector(action[s+'_ee_joint_state'],1,s+' gripper')
        if not 0<=g[0]<=1:raise ValueError('Grippers must be in [0,1]')
        result[s+'_ee_joint_state']=g
        name=s+('_arm_joint_state' if mode=='joint' else '_ee_pose')
        v=vector(action[name],6 if mode=='joint' else 7,name)
        if mode=='ee' and not np.isclose(np.linalg.norm(v[3:]),1,atol=1e-4):
            raise ValueError('EE orientation requires a unit wxyz quaternion')
        result[name]=v
    return mode,result

def measured_state(report,feedback):
    if feedback.get('source')!='hardware':raise ValueError('Physical feedback source must be hardware')
    state={}
    for side in ('left','right'):
        q=vector(feedback[side+'_joints_deg'],6,side+' measured joints')
        g=feedback.get(side+'_gripper')
        if type(g) not in (int,float) or not math.isfinite(g) or not 0<=g<=1:
            raise ValueError('Initialized measured gripper feedback is required')
        pose=arm_pose(report,feedback,side)
        xyzw=Rotation.from_matrix(pose[:3,:3]).as_quat()
        state[side+'_arm_joint_state']=np.deg2rad(q)
        state[side+'_ee_joint_state']=np.array([g])
        state[side+'_ee_pose']=np.r_[pose[:3,3],xyzw[3],xyzw[:3]]
    return state

class YamTask(CodeTask):
    def __init__(self,*,socket_path,origin,robot,instruction,bridge=None,cameras=None,ik=None):
        super().__init__()
        self.robot=robot;self._task_prompt=instruction
        self.bridge=bridge or BridgeClient(socket_path,timeout_s=120)
        configuration=self.bridge.call('configuration')
        if configuration.get('physical_motion_enabled') is not True or configuration.get('robot_id')!=robot:
            raise ValueError('A matching owner-controlled physical bridge is required')
        self.report=self.bridge.call('calibration')
        kin=self.report.get('kinematics',{})
        if kin.get('robot_model_sha256')!=ROBOT_SHA256 or kin.get('scene_sha256')!=SCENE_SHA256:
            raise ValueError('Published geometry differs from the pinned local YAM model')
        self.ik=ik or BimanualRelativeIK(base_spacing_m=self.report['base_geometry']['spacing_m'])
        self.cameras=cameras or CameraFrameSource(origin,camera_names=tuple(CAMERAS))
        self.native_step_limit=self.max_steps=3000
        self._initialized=False
        self.initialize(RoboDojoLowLevelApi(self))

    def _feedback(self):
        f=self.bridge.call('observation')
        if f.get('robot_id')!=self.robot or f.get('source')!='hardware':raise ValueError('Robot/source changed')
        measured_state(self.report,f)
        return f

    def _geometry_check(self,f):
        q=self.ik._safe_baseline(f['left_joints_deg'],f['right_joints_deg'])
        # Compare FK at measured and nearby encoder poses without moving a robot.
        for offsets in (np.zeros(12),np.linspace(-.02,.02,12),np.linspace(.02,-.02,12)):
            sample=np.clip(q+offsets,self.ik.low,self.ik.high)
            self.ik._forward(sample)
            obs={s+'_joints_deg':np.rad2deg(sample[i*6:(i+1)*6]).tolist() for i,s in enumerate(('left','right'))}
            for s,(p,r) in zip(('left','right'),self.ik._poses()):
                t=arm_pose(self.report,obs,s)
                if not np.allclose(p,t[:3,3],atol=2e-6) or not np.allclose(r,t[:3,:3],atol=2e-6):
                    raise ValueError('Local FK does not match the selected published station frame')

    def _build_observation(self,f):
        cutoff=f.get('settled_after',f.get('observed_at'))
        if type(cutoff) not in (int,float) or not math.isfinite(cutoff):
            raise ValueError('Measured observation requires a source timestamp')
        deadline=time.monotonic()+10
        while True:
            frames=self.cameras.capture_for_policy(f,cancelled=lambda:self._cancelled())
            stamps=[x.source_captured_at for x in frames]
            if len(frames)==3 and set(x.name for x in frames)==set(CAMERAS) and all(
                type(t) in (int,float) and math.isfinite(t) and t>cutoff and 0<=time.time()-t<=5 for t in stamps):break
            if time.monotonic()>=deadline:raise ValueError('Fresh post-settle camera set unavailable')
            self._cancelled();time.sleep(.1)
        vision={CAMERAS[x.name]:{'color':np.asarray(Image.open(io.BytesIO(x.jpeg)).convert('RGB')),
                'metadata':x.summary()} for x in frames}
        return {'instruction':self._task_prompt,'vision':vision,'state':measured_state(self.report,f),
                'additional_info':{'frequency':10,'source':'hardware','robot_id':self.robot,
                'world_frame':'blupe_base_midpoint','quaternion_order':'wxyz',
                'observed_at':f.get('observed_at'),'calibration_id':self.report.get('calibration_id'),
                'calibration_quality':self.report.get('quality'),'success_evaluator':'operator_review',
                'packet_cadence_hz':10,'physical_replay':False}}

    def _cancelled(self):
        self.bridge.call('configuration')  # Owner checks live cancellation/lease.
        return False

    def reset(self,*,seed=None,options=None):
        if self._initialized:raise PermissionError('Physical scene reset requires a separate operator setup')
        f=self._feedback();self._geometry_check(f);self._initialized=True
        return self.start_episode(seed,self._build_observation(f))

    def reset_from_program(self):
        raise PermissionError('Physical Test reset is forbidden')

    def _step(self,code):
        self.observe(self._build_observation(self._feedback()))
        return super()._step(code)

    def control_step(self,action):
        if self.done:raise ValueError('Physical waypoint budget exhausted; finish the session')
        mode,a=validate_action(action);f=self._feedback()
        q=self.ik._safe_baseline(f['left_joints_deg'],f['right_joints_deg'])
        if mode=='joint':
            goal=np.r_[a['left_arm_joint_state'],a['right_arm_joint_state']]
        else:
            targets=tuple((a[s+'_ee_pose'][:3],Rotation.from_quat(a[s+'_ee_pose'][[4,5,6,3]]).as_matrix()) for s in ('left','right'))
            goal=self.ik._solve(q,targets)
        if np.any(goal<self.ik.low) or np.any(goal>self.ik.high):raise ValueError('Target exceeds pinned YAM joint bounds')
        count=max(1,int(math.ceil(np.max(np.abs(goal-q))/.03)),*(int(math.ceil(abs(float(a[s+'_ee_joint_state'][0])-f[s+'_gripper'])/.3)) for s in ('left','right')))
        if count>=300 or self.control_steps+count>self.max_steps:raise ValueError('Target exceeds remaining packet/waypoint budget')
        path=np.array([q+(goal-q)*t/count for t in range(count+1)])
        for row in path:
            self.ik._forward(row)
            if self.ik.data.ncon:raise ValueError('Pinned predictive robot model reports path contact')
        joint7=[]
        for i,s in enumerate(('left','right')):
            grip=np.linspace(f[s+'_gripper'],float(a[s+'_ee_joint_state'][0]),count+1)
            joint7.append(np.column_stack((path[:,i*6:(i+1)*6],grip)))
        reply=self.bridge.call('trajectory',timestamps=(np.arange(count+1)/10).tolist(),
            left=joint7[0].tolist(),right=joint7[1].tolist(),playback_speed=1.,start_interp_s=0.)
        if reply.get('success') is not True:raise RuntimeError('Physical packet did not return measured completion')
        feedback=reply['feedback'];self.control_steps+=count
        self.truncated=self.control_steps>=self.max_steps
        self.observe(self._build_observation(feedback))
        return self.transition(0.)

    def close(self):
        # The parent RunnerController exclusively releases the actual session.
        pass
