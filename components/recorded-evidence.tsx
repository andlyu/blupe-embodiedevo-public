'use client';

import {useEffect,useRef,useState} from 'react';

type CameraClip={name:string;sha256:string;camera:'head'|'left'|'right';label:string;url?:string};
type SimulationScene={name:string;number:number;clips:CameraClip[]};

const cameraLabels={head:'Head camera',left:'Left wrist',right:'Right wrist'};

function simulationScenes(media:any[]):SimulationScene[]{
 const scenes=new Map<string,SimulationScene>();
 for(const item of media){
  const match=/^(scene-(\d+))-(head|left|right)\.mp4$/.exec(item.name||'');
  if(!match)continue;
  const name=match[1],number=match[2],camera=match[3] as CameraClip['camera'];
  let scene=scenes.get(name);
  if(!scene){scene={name,number:Number(number),clips:[]};scenes.set(name,scene);}
  scene.clips.push({name:item.name,sha256:item.sha256,camera,label:cameraLabels[camera]});
 }
 return [...scenes.values()].sort((a,b)=>a.number-b.number).map(scene=>({...scene,clips:scene.clips.sort((a,b)=>['head','left','right'].indexOf(a.camera)-['head','left','right'].indexOf(b.camera))}));
}

function timeLabel(seconds:number){
 if(!Number.isFinite(seconds)||seconds<0)return '0:00';
 const whole=Math.floor(seconds);
 return `${Math.floor(whole/60)}:${String(whole%60).padStart(2,'0')}`;
}

function physicalRecordingLabel(recording:any,recordingError:any,hasPhysicalVideos:boolean){
 if(recording?.source==='live_yam_cameras'){
  if(recording.continuous===true)return 'Continuous live YAM camera footage at '+recording.fps+' fps across '+Object.values(recording.frames||{}).reduce((a:any,b:any)=>a+b,0)+' frames. These are real camera views; physical commands are never replayed.';
  return 'Live YAM camera recording incomplete'+(recording.error?': '+recording.error:'')+'. Physical commands are never replayed.';
 }
 if(recordingError)return 'Live YAM camera recording incomplete: '+String(recordingError).slice(0,180)+'. Physical commands are never replayed.';
 return hasPhysicalVideos?'Sampled YAM camera clips are available, but continuous live capture was not verified. Physical commands are never replayed.':'No continuous YAM camera footage was retained for this attempt. Physical commands are never replayed; task outcome remains unknown until operator review.';
}

function SimulationSceneReplay({jobId,scene,outcome}:{jobId:string;scene:SimulationScene;outcome?:any}){
 const videos=useRef<Record<string,HTMLVideoElement|null>>({});
 const [playing,setPlaying]=useState(false);
 const [currentTime,setCurrentTime]=useState(0);
 const [duration,setDuration]=useState(0);
 const [status,setStatus]=useState('');
 const masterCamera=scene.clips.find(clip=>clip.camera==='head')?.camera||scene.clips[0]?.camera||'head';

 useEffect(()=>{
  if(!playing)return;
  const timer=window.setInterval(()=>{
   const master=videos.current[masterCamera];
   if(!master)return;
   setCurrentTime(master.currentTime);
   for(const [camera,video] of Object.entries(videos.current)){
    if(!video||camera===masterCamera||video.paused)continue;
    if(Math.abs(video.currentTime-master.currentTime)>.2)video.currentTime=master.currentTime;
   }
  },250);
  return()=>window.clearInterval(timer);
 },[masterCamera,playing]);

 function pauseAll(){
  for(const video of Object.values(videos.current))video?.pause();
  setPlaying(false);
 }

 function togglePlayback(){
  const available=Object.values(videos.current).filter((video):video is HTMLVideoElement=>!!video);
  if(playing){pauseAll();return;}
  if(!available.length)return;
  const master=videos.current[masterCamera];
  const target=master?.currentTime||0;
  for(const video of available)if(Math.abs(video.currentTime-target)>.15)video.currentTime=target;
  setStatus('');
  void Promise.all(available.map(video=>video.play().then(()=>true).catch(()=>false))).then(results=>{
   const started=results.some(Boolean);
   setPlaying(started);
   if(!started)setStatus('The camera recordings could not be started. Try again.');
  });
 }

 function seek(value:string){
  const target=Number(value);
  for(const video of Object.values(videos.current))if(video&&Number.isFinite(target))video.currentTime=target;
  setCurrentTime(target);
 }

 const outcomeLabel=outcome?.success===true?'Success':outcome?.success===false?'Failure':'Outcome unknown';
 const outcomeClass=outcome?.success===true?'success':outcome?.success===false?'failure':'unknown';

 return <section className="simulation-scene" aria-label={`Simulation Test scene ${scene.number}`}>
  <div className="simulation-scene-heading">
   <h5>Test scene {scene.number}</h5>
   <span className={`replay-result ${outcomeClass}`}>{outcomeLabel}</span>
  </div>
  <div className="recording-grid replay-grid">
   {scene.clips.map(clip=><figure key={clip.name}>
    <video
     ref={element=>{videos.current[clip.camera]=element;}}
     aria-label={`${clip.label}, Test scene ${scene.number}`}
     muted
     playsInline
     preload="metadata"
     src={`/api/media/${jobId}/${clip.name}`}
     onLoadedMetadata={event=>{
      if(clip.camera===masterCamera&&Number.isFinite(event.currentTarget.duration))setDuration(event.currentTarget.duration);
     }}
     onTimeUpdate={event=>{if(clip.camera===masterCamera)setCurrentTime(event.currentTarget.currentTime);}}
     onEnded={()=>{if(clip.camera===masterCamera)pauseAll();}}
     onError={()=>setStatus(`${clip.label} recording could not be loaded.`)}
    />
    <figcaption>{clip.label}<details><summary>Recording digest</summary><code>{clip.sha256}</code></details></figcaption>
   </figure>)}
  </div>
  <div className="replay-controls">
   <button type="button" className="primary replay-button" onClick={togglePlayback} disabled={!scene.clips.length}>
    {playing?'Pause all views':'Play all views'}
   </button>
   <label className="replay-timeline">
    <span className="sr-only">Seek Test scene {scene.number}</span>
    <input type="range" min="0" max={duration||0} step="0.05" value={Math.min(currentTime,duration||0)} disabled={!duration} onChange={event=>seek(event.currentTarget.value)}/>
   </label>
   <span className="replay-time" aria-live="off">{timeLabel(currentTime)} / {timeLabel(duration)}</span>
  </div>
  <p className="replay-status" role="status">{status||'The camera views stay synchronized during playback.'}</p>
 </section>;
}

export function RecordedEvidence({job}:{job:any}){
 const storedMedia=Array.isArray(job.report?.media)?job.report.media:[],[curatedMedia,setCuratedMedia]=useState<any[]>([]),[programs,setPrograms]=useState<any[]>([]),[error,setError]=useState('');
 const media=storedMedia.length?storedMedia:curatedMedia;
 const source=media.find((item:any)=>item.name==='programs.json');
 useEffect(()=>{
  let alive=true;
  setCuratedMedia([]);
  if(job.kind!=='hardware'||storedMedia.length)return()=>{alive=false;};
  fetch('/physical-evidence/manifest.json').then(response=>{
   if(!response.ok)throw Error('Public physical recordings could not be loaded.');
   return response.json();
  }).then((value:any)=>{if(alive)setCuratedMedia(value.runs?.[job.id]?.media||[]);}).catch(()=>{if(alive)setCuratedMedia([]);});
  return()=>{alive=false;};
 },[job.id,job.kind,storedMedia.length]);
 useEffect(()=>{
  let alive=true;
  setPrograms([]);
  setError('');
  if(source)fetch('/api/media/'+job.id+'/programs.json').then(response=>{
   if(!response.ok)throw Error('Submitted code could not be loaded.');
   return response.json();
  }).then((value:any)=>{if(alive)setPrograms(value.programs||[]);}).catch(reason=>{if(alive)setError(reason.message);});
  return()=>{alive=false;};
 },[job.id,source?.sha256]);

 if(!media.length)return null;
 const scenes=job.kind==='sim_test'?simulationScenes(media):[];
 const physicalVideos=media.some((item:any)=>/^physical-(head|left|right)\.mp4$/.test(item.name||''));
 const outcomes=job.report?.outcomes||[];
 return <section className="recorded-evidence">
  <h4>{job.kind==='hardware'?'Physical observation record':job.kind==='sim_test'?'Watch the simulation run':'Simulation replay & submitted code'}</h4>
  <p className="subtle">{job.kind==='hardware'
   ?physicalRecordingLabel(job.report?.recording,job.report?.recording_error,physicalVideos)
   :job.kind==='sim_test'
    ?'Native RoboDojo recordings from each Test scene. Play all three camera views together and scrub through the run.'
    :'Native simulator replay recordings from this attempt.'}</p>
  {scenes.length>0?<div className="simulation-replays">{scenes.map(scene=>{
   const outcome=outcomes.find((item:any)=>Number(item.scene)===scene.number);
   return <SimulationSceneReplay key={scene.name} jobId={job.id} scene={scene} outcome={outcome}/>;
  })}</div>:<div className="recording-grid">{media.filter((item:any)=>item.name.endsWith('.mp4')).map((item:any)=><figure key={item.name}>
   <video controls preload="metadata" playsInline src={item.url||'/api/media/'+job.id+'/'+item.name}/>
   <figcaption>{item.name.replace('.mp4','').replaceAll('-',' · ')}<details><summary>Recording digest</summary><code>{item.sha256}</code></details></figcaption>
  </figure>)}</div>}
  {error&&<p role="alert">{error}</p>}
  {programs.length>0&&<details className="program-history"><summary>Inspect {programs.length} submitted programs</summary>{programs.map((program:any,index:number)=><details key={index}>
   <summary>{program.episode} · execution {program.execution}</summary>
   <code className="digest">SHA-256 {program.sha256}</code>
   <pre>{program.source}</pre>
  </details>)}</details>}
 </section>;
}
