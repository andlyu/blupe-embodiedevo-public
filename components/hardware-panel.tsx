'use client';
import {useEffect,useState,type FormEvent} from 'react';
import {Play,Square,RefreshCw,Box,ArrowUpRight,BookOpen,ShieldCheck} from 'lucide-react';
import {RecordedEvidence} from './recorded-evidence';
import {SKILL_LIBRARY,UPSTREAM_SKILLS} from '../lib/domain.mjs';

type SkillFile={source:string;destination:string;git_blob_sha1:string;bytes:number};
type SkillDefinition={name:string;task:string;files:SkillFile[]};
type HardwareInfo={skill_id?:string;skill_name?:string;skill_revision?:string;task?:string;runner_name?:string};
type ProgressInfo={status?:string;session_id?:string;queue_position?:number|null;commands_submitted?:number;packets_submitted?:number;executions_used?:number;native_steps_used?:number;agent_state?:string;safety_error?:string|{message?:string;code?:string}};
type SkillReceipt={status:string;files?:SkillFile[];error?:string};
type RunOutcome={evaluator?:string;intervention?:boolean;success?:boolean;valid?:boolean;reason?:string};
type RunReview={at:number;outcome:string;note?:string};
type RunReport={hardware?:HardwareInfo;progress?:ProgressInfo;skill_source?:SkillReceipt;summary?:string;outcomes?:RunOutcome[];reviews?:RunReview[]};
export type DirectJob={id:string;kind:string;state:string;created:number;report?:RunReport};
export type DirectCampaign={id:string;updated:number;config:{direct_yam?:boolean};jobs:DirectJob[]};
type Worker={id:string;seen:number;yam?:boolean};
type RunnerDefaults={name:string;email:string};
type StationStatus={connected:boolean;canRequestSession:boolean;queueReady:boolean;mode:string;queueLength:number;calibrationQuality?:string;ageSeconds:number;homed:boolean;settled:boolean;safety?:{ok?:boolean;reason?:string}|null};

const skillOptions=Object.entries(UPSTREAM_SKILLS as Record<string,SkillDefinition>).sort((a,b)=>a[1].name.localeCompare(b[1].name));
const defaultTask='Stack the small blue cube on the orange cube. Leave the other objects undisturbed.';

export function HardwarePanel({campaigns,workers,identityDefaults,busy,mutate}:{campaigns:DirectCampaign[];workers:Worker[];identityDefaults:RunnerDefaults|null;busy:boolean;mutate:(path:string,value:unknown)=>Promise<unknown>}){
 const [station,setStation]=useState<StationStatus|null>(null);
 const [error,setError]=useState('');
 const [stamp,setStamp]=useState(0);
 const [skillId,setSkillId]=useState('stack_blocks');
 const [task,setTask]=useState(defaultTask);
 const [seconds,setSeconds]=useState(600);
 const [budget,setBudget]=useState(100);
 const [note,setNote]=useState('');
 const [runnerName,setRunnerName]=useState('');
 const [runnerEmail,setRunnerEmail]=useState('');
 const [identityConfirmed,setIdentityConfirmed]=useState(false);

 async function refresh(){
  try{
   const response=await fetch('/api/yam/status');
   const value=await response.json() as StationStatus&{error?:string};
   if(!response.ok)throw Error(value.error||'Station status unavailable.');
   setStation(value);setError('');
  }catch(cause){setError((cause as Error).message);}
 }
 // This effect synchronizes the displayed station state with the read-only status API.
 // eslint-disable-next-line react-hooks/set-state-in-effect
 useEffect(()=>{void refresh();const statusTimer=setInterval(()=>{if(!document.hidden)void refresh();},5000),cameraTimer=setInterval(()=>{if(!document.hidden)setStamp(Date.now());},1000);return()=>{clearInterval(statusTimer);clearInterval(cameraTimer);};},[]);
 // eslint-disable-next-line react-hooks/set-state-in-effect
 useEffect(()=>{if(identityDefaults){setRunnerName(current=>current||identityDefaults.name);setRunnerEmail(current=>current||identityDefaults.email);}},[identityDefaults]);

 const directCampaigns=campaigns.filter(c=>c.config.direct_yam===true).sort((a,b)=>b.updated-a.updated);
 const attempts=directCampaigns.flatMap(c=>c.jobs.filter(job=>job.kind==='hardware').map(job=>({...job,campaignRecord:c}))).sort((a,b)=>b.created-a.created);
 const latestActive=attempts.find(job=>['queued','running','cancel_requested'].includes(job.state));
 const selectedSkill=(UPSTREAM_SKILLS as Record<string,SkillDefinition>)[skillId];
 const ready=workers.some(worker=>worker.yam===true);
 const identityValid=runnerName.trim().length>=2&&runnerName.trim().length<=120&&/^\S+@\S+\.\S+$/.test(runnerEmail.trim());
 const reason=latestActive?'A YAM run is already active.':!selectedSkill?'Choose one of the pinned EmbodiedEvo skill sets.':!task.trim()||task.trim().length<5?'Describe the matching task and objects set up on the physical table.':!ready?'The YAM compute worker is disconnected. Start the configured worker before queuing a run.':!station?.canRequestSession?'Waiting for a connected station with fresh, safe hardware feedback.':!identityValid?'Enter a real runner name and valid email.':!identityConfirmed?'Confirm the runner name and email for this run.':'';
 const progress=latestActive?.report?.progress;
 const safetyError=typeof progress?.safety_error==='string'?progress.safety_error:progress?.safety_error?.message||progress?.safety_error?.code;
 const runStatus=!latestActive?reason||'Ready to request a bounded physical session.':latestActive.state==='queued'?'Queued for the YAM-capable worker, then the normal BluPe robot queue. No method motion is claimed yet.':latestActive.state==='cancel_requested'?'Stop requested; waiting for controller confirmation and normal parking.':safetyError?'Controller safety stop: '+safetyError+'. No automatic retry will occur.':progress?.status==='preparing'?'Preparing the pinned EmbodiedEvo session and camera recording. No method motion is claimed yet.':progress?.status==='queued'?'Waiting for the normal YAM robot lease. No method motion is claimed yet.':progress?.status==='running'?'Controller reports a running lease. Watch the live camera views to confirm whether the adapted method moves the arms.':'Worker claimed the run and is preparing the physical session.';
 async function run(event:FormEvent){event.preventDefault();if(reason)return;await mutate('/api/direct-yam',{skill_id:skillId,task:task.trim(),hardware:{robot:'yam-1',seconds,budget,runner_name:runnerName.trim(),email:runnerEmail.trim(),identity_confirmed:true}});}

 return <div className="physical-workspace">
  <section className="run-panel">
   <div className="run-heading"><div><span className="state-label">{station?.connected?'YAM station connected':'Checking YAM station'}</span><h2>EmbodiedEvo skills · direct YAM run</h2></div><button className="icon-button" aria-label="Refresh YAM status" onClick={()=>{void refresh();setStamp(Date.now());}}><RefreshCw size={16}/></button></div>
   <div className="physical-cameras">{(['top','left','right'] as const).map(role=><figure key={role}><img src={'/api/yam/camera/'+role+'?v='+stamp} alt={'Live YAM '+role+' camera'} onError={event=>{event.currentTarget.alt='YAM '+role+' camera unavailable; refresh station status.';}}/><figcaption>{role==='top'?'Table view':role+' wrist'} · live 1 s snapshots</figcaption></figure>)}</div>
   <div className="physical-status"><p>{error||(!station?'Reading station status…':station.canRequestSession?(station.queueReady?'Station is connected; the normal queue can admit a run.':'Station is connected. A run can wait for its turn in the BluPe queue.'):'Station feedback is unavailable or reports a safety fault. Refresh to retry.')}</p>{station&&<p className="subtle">Mode {station.mode} · {station.queueLength} queued · calibration {station.calibrationQuality?.replaceAll('_',' ')||'published'} · feedback {station.ageSeconds.toFixed(1)} s old · {station.homed?'homed':'not homed'} · {station.settled?'settled':'not settled'} · safety {station.safety?.reason||(station.safety?.ok?'OK':'not verified')}. Motors initialize under the admitted lease; fresh measured feedback is required before agent control. Active runs retain actual camera footage at 2 fps across the top and both wrist views.</p>}</div>
   <div className="physical-records"><h3>Physical attempts · {attempts.length}</h3><p>Each attempt stays in the record. The selected upstream skill files and exact revision are shown with the result. Physical evidence and outcomes are public; the agent cannot award itself success.</p>{!attempts.length?<p className="subtle">No physical attempts recorded yet.</p>:attempts.map(job=><article className="physical-attempt" key={job.id}><h4>{job.report?.hardware?.skill_name||'EmbodiedEvo'} · {job.report?.hardware?.task||'YAM task'}</h4><p>Run by {job.report?.hardware?.runner_name||'identity not recorded'} · {job.state.replaceAll('_',' ')} · {new Date(job.created).toLocaleString()}</p>{job.report?.hardware?.skill_revision&&<p><a className="text-link" href={`${SKILL_LIBRARY.repository_url}/tree/${job.report.hardware.skill_revision}/${SKILL_LIBRARY.library_path}/${job.report.hardware.skill_id}`} target="_blank" rel="noreferrer">Pinned source · {job.report.hardware.skill_revision.slice(0,7)} <ArrowUpRight size={13}/></a></p>}{job.report?.skill_source&&<p className="subtle">Skill files: {job.report.skill_source.status==='verified'?'hash verified':job.report.skill_source.status==='failed'?'verification failed':'verification not recorded'}{job.report.skill_source.files?.length?' · '+job.report.skill_source.files.length+' files':''}{job.report.skill_source.error?' · '+job.report.skill_source.error:''}</p>}{job.report?.progress&&<p className="subtle">{job.report.progress.status} · {typeof job.report.progress.packets_submitted==='number'?job.report.progress.packets_submitted+' packets submitted':'Packet count not retained'}{typeof job.report.progress.executions_used==='number'?' · '+job.report.progress.executions_used+' code executions':''}{typeof job.report.progress.native_steps_used==='number'?' · '+job.report.progress.native_steps_used+' waypoints':''}{job.report.progress.agent_state?' · agent '+job.report.progress.agent_state:''}{job.report.progress.queue_position!=null?' · queue position '+job.report.progress.queue_position:''}</p>}<p>{job.report?.summary}</p>{job.report?.outcomes?.map((outcome,index)=><p key={index}><strong>{outcome.evaluator==='operator_review'?(outcome.intervention?'Intervention':outcome.success?'Reviewed success':'Reviewed failure'):'Outcome awaiting operator review'}</strong> · protocol {outcome.valid?'valid':'invalid'}{outcome.reason?' · '+outcome.reason:''}</p>)}<RecordedEvidence job={job}/>{['completed','failed','cancelled'].includes(job.state)&&<div className="physical-review"><label>Review note<textarea maxLength={2000} value={note} onChange={event=>setNote(event.target.value)} placeholder="Describe the final scene or an intervention."/></label><div className="review-actions">{(['success','failure','intervention'] as const).map(outcome=><button className="secondary" disabled={busy} key={outcome} onClick={()=>mutate('/api/hardware/review',{job:job.id,outcome,note})}>Record {outcome}</button>)}</div>{job.report?.reviews?.map((review,index)=><p className="subtle" key={index}>{new Date(review.at).toLocaleString()} · {review.outcome}{review.note?' · '+review.note:''}</p>)}</div>}</article>)}</div>
  </section>
  <aside className="setup-panel"><div className="setup-title"><Box size={17}/><h2>Run a learned skill on YAM</h2></div><form onSubmit={run}>
   <p className="form-help">No account or sign-in is required. Choose a skill already learned in RoboDojo sim. Its files are fetched from a pinned public commit, hash-verified, and mounted read-only for a fresh coding session. The session adapts the skill to measured YAM observations and controls; it does not replay sim coordinates or run the example unchanged. Run details, live cameras, recordings and replays are public. Runner email is sent to YAM for attribution but is omitted from public run details.</p>
   <label>EmbodiedEvo skill set<select value={skillId} onChange={event=>{setSkillId(event.target.value);setTask('');}}>{skillOptions.map(([id,skill])=><option key={id} value={id}>{skill.name}</option>)}</select></label>
   {selectedSkill&&<div className="skill-source-card"><BookOpen size={15}/><span>{selectedSkill.files.length} pinned files · {selectedSkill.task}<br/><a href={`${SKILL_LIBRARY.repository_url}/tree/${SKILL_LIBRARY.revision}/${SKILL_LIBRARY.library_path}/${skillId}`} target="_blank" rel="noreferrer">Source at {SKILL_LIBRARY.revision.slice(0,7)} <ArrowUpRight size={12}/></a></span></div>}
   <label>Task and objects set up on YAM<textarea required minLength={5} maxLength={2000} value={task} onChange={event=>setTask(event.target.value)} placeholder="Describe the physical task and the objects currently on the YAM table."/></label>
   <div className="form-pair"><label>Runner name<input type="text" required minLength={2} maxLength={120} autoComplete="name" value={runnerName} onChange={event=>{setRunnerName(event.target.value);setIdentityConfirmed(false);}}/></label><label>Runner email<input type="email" required maxLength={254} autoComplete="email" value={runnerEmail} onChange={event=>{setRunnerEmail(event.target.value);setIdentityConfirmed(false);}}/></label></div>
   <label className="identity-confirm"><input type="checkbox" required checked={identityConfirmed} onChange={event=>setIdentityConfirmed(event.target.checked)}/>I confirm this name and email identify me for this run. Your name appears in public run details. Your email is sent to the YAM Session API for attribution and notifications, and is kept out of the public run record.</label>
   <div className="form-pair"><label>Seconds / trial<input type="number" required min={60} max={600} value={seconds} onChange={event=>setSeconds(Number(event.target.value))}/></label><label>Execution slots<input type="number" required min={1} max={100} value={budget} onChange={event=>setBudget(Number(event.target.value))}/></label></div>
   <div className="skill-adaptation-note"><ShieldCheck size={15}/><span>Fresh session · read-only references · verified at run time. There is no simulation campaign in this workflow, and sim-to-real performance is not assumed.</span></div>
   {latestActive?<button className="stop save" type="button" disabled={busy||latestActive.state==='cancel_requested'} onClick={()=>mutate('/api/jobs/stop',{campaign:latestActive.campaignRecord.id})}><Square size={13}/>{latestActive.state==='cancel_requested'?'Stopping…':'Stop YAM run'}</button>:<button className="primary save" disabled={busy||!!reason}><Play size={14}/>{busy?'Submitting…':'Run on YAM'}</button>}
   <p className="form-help" role="status">{runStatus}</p>
  </form></aside>
 </div>;
}
