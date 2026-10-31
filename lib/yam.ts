export const YAM_ORIGIN='https://yam-session-api.n5hthc3gj4cqy.us-east-1.cs.amazonlightsail.com';
export const YAM_ROBOT='yam-1';
export const mediaName=(v:string)=>/^(?:(?:practice|physical|scene-(?:[1-9]|1[0-9]|2[0-5]))-(?:head|left|right)\.mp4|programs\.json)$/.test(v);
export function confirmedRunner(v:any){
 const runnerName=typeof v.runner_name==='string'?v.runner_name.trim():'';
 const email=typeof v.email==='string'?v.email.trim():'';
 if(v.identity_confirmed!==true||runnerName.length<2||runnerName.length>120||/[\u0000-\u001f\u007f]/.test(runnerName)||!/^\S+@\S+\.\S+$/.test(email)||email.length>254)throw Error('Confirm a real runner name and valid email before joining YAM.');
 return {runner_name:runnerName,email};
}
export function hardwareConfig(v:any){
 if(!v||v.robot!==YAM_ROBOT||typeof v.task!=='string'||v.task.trim().length<5||v.task.length>2000||!Number.isInteger(v.seconds)||v.seconds<60||v.seconds>600||!Number.isInteger(v.budget)||v.budget<1||v.budget>100)throw Error('Choose YAM, a task, 1–100 executions and a 60–600 second trial.');
 return {method:'EmbodiedEvo',robot:YAM_ROBOT,task:v.task.trim(),seconds:v.seconds,budget:v.budget,...confirmedRunner(v)};
}
export function canRequestSession(s:any,o:any,now=Date.now()/1000){const age=now-o?.observed_at;return s?.connected===true&&o?.source==='hardware'&&Number.isFinite(age)&&age>=-2&&age<=10&&o?.safety?.estop_engaged!==true&&(o?.safety?.ok===true||o?.safety?.reason==='hardware_not_initialized');}
export async function station(){const paths=['queue','observation','calibration'];const values=await Promise.all(paths.map(async p=>{const r=await fetch(`${YAM_ORIGIN}/v1/robots/${YAM_ROBOT}/${p}`,{redirect:'manual',signal:AbortSignal.timeout(8000)});if(!r.ok)throw Error('Station '+p+' is unavailable ('+r.status+').');return r.json() as Promise<any>;}));const [q,o,c]=values;const s=q.stations?.find((x:any)=>x.jetson_id===YAM_ROBOT);return {robot:YAM_ROBOT,connected:s?.connected===true,queueReady:s?.queue_ready===true,mode:o.mode,observedAt:o.observed_at,ageSeconds:Date.now()/1000-o.observed_at,source:o.source,safety:o.safety,homed:o.homed===true,settled:o.settled===true,measuredGrippers:typeof o.left_gripper==='number'&&typeof o.right_gripper==='number',calibrationId:c.calibration_id,calibrationQuality:c.quality?.status,baseSpacing:c.base_geometry?.spacing_m,queueLength:q.entries?.length??0,cameras:['top','left','right'],canRequestSession:canRequestSession(s,o),admissionReady:s?.queue_ready===true&&canRequestSession(s,o)};}
