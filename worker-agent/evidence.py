"""Publish immutable native recordings and submitted code, without execution."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request

CAMERAS={'cam_head':'head','cam_left_wrist':'left','cam_right_wrist':'right'}

def publish_evidence(client,job,run):
    root=Path(run)
    episodes=[('practice',root/'playground')] if job['kind']=='practice' else [('physical',root/'session')] if job['kind']=='hardware' else [(f'scene-{int(p.name.split("_")[-1])+1}',p) for p in sorted((root/'test').glob('scene_*'))]
    transcript=[]
    for name,episode in episodes:
        for camera,role in CAMERAS.items():
            path=episode/'final'/f'trace_{camera}.mp4'
            if not path.exists() and job['kind']=='hardware':
                pieces=sorted((episode/'workspace/observations').glob(f'*/video_{camera}.mp4'))
                if not pieces:pieces=sorted((episode/'workspace/observations').glob(f'*/*_{camera}.mp4'))
                if pieces:
                    import subprocess
                    folder=root/'recorded';folder.mkdir(exist_ok=True)
                    listing=folder/(role+'.txt');listing.write_text(''.join("file '"+str(p)+"'\n" for p in pieces))
                    path=folder/(role+'.mp4')
                    import imageio_ffmpeg
                    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
                    subprocess.run([ffmpeg,'-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(path)],check=True,timeout=60)
            if path.is_file():upload(client,job['id'],f'{name}-{role}.mp4',path.read_bytes(),'video/mp4')
        for path in sorted((episode/'workspace/observations').glob('*/code.py')):
            raw=path.read_bytes()
            transcript.append({'episode':name,'execution':path.parent.name,'sha256':hashlib.sha256(raw).hexdigest(),'source':raw.decode('ascii')})
    if transcript:
        raw=json.dumps({'schema':'blupe-native-program-history-v1','job':job['id'],'source':'actual submitted native code','programs':transcript},indent=2).encode()
        upload(client,job['id'],'programs.json',raw,'application/json')

def upload(client,job,name,raw,content_type):
    if not raw or len(raw)>64*1024*1024:raise ValueError('Evidence file exceeds the 64 MiB upload limit')
    headers={'Authorization':'Bearer '+client.token,'Content-Type':content_type,
             'X-Content-SHA256':hashlib.sha256(raw).hexdigest(),'X-Worker-ID':client.worker}
    if client.access:headers['OAI-Sites-Authorization']=client.access if client.access.startswith('Bearer ') else 'Bearer '+client.access
    req=Request(client.origin+'/api/worker/media/'+job+'/'+name,data=raw,headers=headers,method='POST')
    with client.open(req,timeout=120) as response:result=json.load(response)
    if result.get('ok') is not True:raise ValueError('Native evidence was not accepted')
