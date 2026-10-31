"""Local-preview-only API fixtures. Does not execute a simulator, model or robot."""
import base64
import struct
import zlib
import hashlib
import json
import os
import time
import uuid
from urllib.request import Request,urlopen,build_opener,HTTPCookieProcessor
from http.cookiejar import CookieJar
from urllib.error import HTTPError
ORIGIN=os.environ.get('BLUPE_TEST_ORIGIN','http://127.0.0.1:8797')
TOKEN='local-fixture-worker-token-for-api-validation-only'
USER='local-api-fixture-'+uuid.uuid4().hex
RUN_ID=uuid.uuid4().hex[:6]
checks=0
opener=build_opener(HTTPCookieProcessor(CookieJar()))

def call(path,payload=None,user=USER,token=None):
 if path=='/api/jobs' and isinstance(payload,dict) and user==USER:
  payload=dict(payload)
  if payload.get('kind')=='hardware':
   hardware=dict(payload.get('hardware') or {})
   hardware.setdefault('runner_name','Local API fixture')
   hardware.setdefault('email','fixture@example.invalid')
   hardware.setdefault('identity_confirmed',True)
   payload['hardware']=hardware
  else:
   payload.setdefault('runner_name','Local API fixture')
   payload.setdefault('email','fixture@example.invalid')
   payload.setdefault('identity_confirmed',True)
 headers={'Origin':ORIGIN,'Content-Type':'application/json'}
 # Portable preview owns identity; use its real local sign-in cookie.
 if token:headers['Authorization']='Bearer '+token
 try:
  with (opener.open if user==USER else urlopen)(Request(ORIGIN+path,data=None if payload is None else json.dumps(payload).encode(),headers=headers),timeout=15) as r:
   raw=r.read();return r.status,json.loads(raw) if r.headers.get('content-type','').startswith('application/json') else raw
 except HTTPError as e:return e.code,json.loads(e.read())
def expect(value,message):
 global checks
 assert value,message;checks+=1

def create(name):
 s,v=call('/api/campaigns',dict(name='API FIXTURE '+name+' '+RUN_ID,task='stack_blocks',budget=2,scenes=2,seed=0,seconds=60));expect(s==201,'create: HTTP '+str(s)+' '+str(v.get('error','response omitted')));return v['id']
def w(path,value,worker='fixture-worker'):return call('/api/worker/'+path,dict(value,worker=worker),user=None,token=TOKEN)
started=time.monotonic()
s,v=call('/api/campaigns',{},user=None);expect(s==401,'authentication')
opener.open(ORIGIN+'/signin-with-chatgpt?return_to=/').read()
c=create('freeze and evaluate')
s,v=call('/api/jobs',{'campaign':c,'kind':'hardware'});expect(s==400,'hardware denied')
s,v=call('/api/jobs',{'campaign':c,'kind':'sim_test'});expect(s==400,'test requires freeze')
s,v=call('/api/jobs',{'campaign':c,'kind':'practice'});expect(s==201,'queue');jid=v['id']
s,v=call('/api/jobs',{'campaign':c,'kind':'practice'});expect(s in [400,409],'duplicate denied')
s,v=call('/api/jobs/stop',{'campaign':c},user='other-owner');expect(s==401,'unauthenticated campaign access denied')
s,v=call('/api/worker/claim',{'worker':'fixture-worker'},user=None,token='wrong');expect(s==401,'worker authentication status '+str(s)+' '+str(v.get('error','')))
s,v=w('probe',{},worker='probe-'+RUN_ID);expect(s==200 and v.get('claimsJobs') is False and v.get('startsExecution') is False,'probe never starts execution')
s,v=call('/api/bootstrap');expect(v.get('operatorAllowed') is True,'signed-in operator is enabled by the production-style allowlist');expect(all(x['id']!='probe-'+RUN_ID for x in v['workers']),'probe does not announce an online worker')
record=next(x for x in v['campaigns'] if x['id']==c);expect(record['jobs'][0]['state']=='queued','probe leaves queued job unclaimed')
s,v=w('claim',{});expect(s==200 and v['job']['id']==jid,'atomic claim')
s,v=w('claim',{});expect(v['job'] is None,'no duplicate claim')
base={'job':jid,'state':'completed','protocolValid':True,'summary':'LOCAL TEST FIXTURE; no simulation ran'}
s,v=w('report',dict(base,files=[{'path':'submission/x.py','content':'fixture','sha256':'a'*64}]));expect(s==400,'package scope')
s,v=w('report',dict(base,files=[{'path':'skills/x.py','content':'fixture','sha256':'a'*64}]));expect(s==400,'file digest')
content='LOCAL TEST FIXTURE, not a learned controller\n';files=[{'path':'skills/fixture.md','content':content,'sha256':hashlib.sha256(content.encode()).hexdigest()}]
binary=b'\xa7\r\n\x00compiled-cache';files.append({'path':'skills/__pycache__/fixture.pyc','content':base64.b64encode(binary).decode(),'encoding':'base64','sha256':hashlib.sha256(binary).hexdigest()})
s,v=w('report',dict(base,files=files));expect(s==200 and bool(v['artifact']),'freeze package');aid=v['artifact']
s,v=call('/api/artifacts/'+aid);expect(s==200 and v['files']==files,'durable package download')
s,v=call('/api/artifacts/'+aid,user='other-owner');expect(s==401,'unauthenticated artifact access denied')
s,v=call('/api/jobs',{'campaign':c,'kind':'sim_test'});expect(s==201,'test after freeze');testid=v['id']
s,v=w('claim',{},worker='different-worker');expect(v['job'] is None,'persistent worker affinity')
s,v=w('claim',{});expect(v['job']['id']==testid,'fresh test claim')
# Original 32x32 flat-color PNG fixture, never a simulator result.
def chunk(k,d):return struct.pack('!I',len(d))+k+d+struct.pack('!I',zlib.crc32(k+d)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',32,32,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+bytes([90,130,100])*32 for _ in range(32))))+chunk(b'IEND',b'')
s,v=w('observation',{'job':testid,'png':base64.b64encode(png).decode()});expect(s==200,'observation upload')
s,v=w('report',{'job':testid,'state':'completed','summary':'LOCAL TEST FIXTURE','outcomes':[{'scene':1,'success':False,'valid':True},{'scene':2,'success':False,'valid':False,'reason':'fixture infrastructure failure'}]});expect(s==200,'native outcomes retained')
s,v=call('/api/bootstrap');record=next(x for x in v['campaigns'] if x['id']==c);expect(record['state']=='evaluated' and len(record['jobs'][-1]['report']['outcomes'])==2,'invalid trials retained')
expect(bool(record['jobs'][-1]['report'].get('observationAt')),'terminal report preserves observation metadata')
s,v=call('/api/observations/'+testid);expect(s==200 and v==png,'terminal observation remains available')
c=create('export recovery');s,v=call('/api/jobs',{'campaign':c,'kind':'practice'});recoveryid=v['id'];s,v=w('claim',{});expect(v['job']['id']==recoveryid,'claim export fixture')
s,v=w('report',{'job':recoveryid,'state':'failed','failureCode':'knowledge_export_failed','summary':'LOCAL EXPORT FAILURE FIXTURE'});expect(s==200,'retain failed export')
recovery={'job':recoveryid,'state':'completed','protocolValid':True,'files':files,'summary':'LOCAL RECOVERED EXPORT FIXTURE; no execution'}
s,v=w('recover-freeze',recovery,worker='different-worker');expect(s==409,'recovery worker affinity')
s,v=w('recover-freeze',dict(recovery,files=[dict(files[-1],sha256='a'*64)]));expect(s==400,'recovery checks original byte digest')
s,v=w('recover-freeze',recovery);expect(s==200 and bool(v['artifact']),'recover binary package without a model retry')
s,v=call('/api/bootstrap');record=next(x for x in v['campaigns'] if x['id']==c);expect(record['state']=='frozen' and record['jobs'][0]['report']['recovery']['previousReport']['summary']=='LOCAL EXPORT FAILURE FIXTURE','retain original export failure')
s,v=w('recover-freeze',recovery);expect(s==409,'no duplicate recovery or replacement artifact')
c=create('stop race');s,v=call('/api/jobs',{'campaign':c,'kind':'practice'});jid=v['id'];s,v=w('claim',{});expect(v['job']['id']==jid,'claim before stop')
s,v=call('/api/jobs/stop',{'campaign':c});expect(v['state']=='cancel_requested','running stop waits for worker')
s,v=w('report',{'job':jid,'state':'completed','protocolValid':True,'files':[]});expect(s==409,'stop wins terminal race')
s,v=w('report',{'job':jid,'state':'cancelled','summary':'LOCAL TEST FIXTURE'});expect(s==200,'cancel acknowledged')
s,v=call('/api/bootstrap');record=next(x for x in v['campaigns'] if x['id']==c);expect(record['state']=='stopped','confirmed stopped')


s,v=w('recover-freeze',{'job':jid,'state':'completed','protocolValid':True,'files':[]});expect(s==409,'cancellation cannot be recovered')
print(json.dumps({'passed':checks,'seconds':round(time.monotonic()-started,3),'scope':'local D1/R2/API fixtures only; no simulator/model/robot execution'}))
# Immutable source evidence and byte ranges are local fixtures, never robot recordings.
raw=json.dumps({'programs':[{'source':'print("LOCAL FIXTURE")'}]}).encode()
def media_upload(name,data,who='fixture-worker'):
 headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json','X-Worker-ID':who,'X-Content-SHA256':hashlib.sha256(data).hexdigest()}
 try:
  with urlopen(Request(ORIGIN+'/api/worker/media/'+jid+'/'+name,data=data,headers=headers),timeout=10) as r:return r.status,json.load(r)
 except HTTPError as e:return e.code,json.load(e)
s,v=media_upload('programs.json',raw,'other-worker');expect(s==409,'evidence worker ownership')
s,v=media_upload('programs.json',raw);expect(s==200,'immutable evidence upload')
s,v=media_upload('programs.json',b'{"replacement":true}');expect(s==409,'original evidence cannot be replaced')
s,v=call('/api/media/'+jid+'/programs.json');expect(s==200 and v['programs'][0]['source']=='print("LOCAL FIXTURE")','exact submitted source download')
s,v=call('/api/media/'+jid+'/programs.json',user='other-owner');expect(s==401,'evidence requires campaign owner')
with opener.open(Request(ORIGIN+'/api/media/'+jid+'/programs.json',headers={'Range':'bytes=0-8'}),timeout=10) as r:expect(r.status==206 and r.read()==raw[:9],'recording byte range playback')
print(json.dumps({'passed_total':checks,'scope':'local API fixtures; no actual physical or model execution'}))

# Physical API fixtures use only the station's public read-only preflight; no worker process executes them.
c=create('physical transfer');s,v=call('/api/jobs',{'campaign':c,'kind':'practice'});jid=v['id'];w('claim',{});w('report',dict(base,job=jid,files=files))
s,v=call('/api/jobs',{'campaign':c,'kind':'sim_test'});jid=v['id'];w('claim',{});w('report',{'job':jid,'state':'completed','outcomes':[{'scene':1,'success':True,'valid':True}]})
h={'method':'EmbodiedEvo','robot':'yam-1','task':'LOCAL API FIXTURE — no robot execution','seconds':60,'budget':1,'identity_confirmed':False}
s,v=call('/api/jobs',{'campaign':c,'kind':'hardware','hardware':h});expect(s==400,'physical run requires confirmed runner identity')
request_h=dict(h,runner_name='Local fixture, no robot',email='fixture@example.invalid',identity_confirmed=True)
expected_h={k:v for k,v in request_h.items() if k!='identity_confirmed'}
s,v=call('/api/jobs',{'campaign':c,'kind':'hardware','hardware':dict(request_h,robot='arbitrary')});expect(s==400,'fixed physical station')
s,v=call('/api/jobs',{'campaign':c,'kind':'hardware','hardware':request_h})
if s==409 and 'station' in v.get('error','').lower():
 print(json.dumps({'passed_total':checks,'physical_claim_review_fixture':'not run because station admission returned a read-only readiness conflict','scope':'local fixtures; no hardware execution'}))
 raise SystemExit(0)
expect(s==201,'qualified physical transfer queues: '+str(v));jid=v['id']
w('heartbeat',{'version':'470278c478bdb5e4b6f17dde1ea0393761f230f0','yam':False})
s,v=w('claim',{});expect(v['job'] is None,'simulation-only worker cannot claim physical job')
s,v=w('heartbeat',{'version':'470278c478bdb5e4b6f17dde1ea0393761f230f0','yam':True});expect(s==200,'YAM capability registered')
s,v=w('claim',{});expect(v['job']['id']==jid and v['job']['hardware']==expected_h,'qualified worker receives exact physical task and confirmed attribution')
s,v=w('progress',{'job':jid,'progress':{'status':'LOCAL FIXTURE','packets_submitted':0,'secret':'discard'}});expect(s==200,'bounded progress retained')
s,v=w('report',{'job':jid,'state':'completed','summary':'LOCAL API FIXTURE; no physical execution','recording':{'source':'live_yam_cameras','continuous':True,'fps':2,'frames':{'top':2,'left':2,'right':2}},'outcomes':[{'scene':1,'success':True,'valid':True}]});expect(s==200,'physical report accepted')
s,v=call('/api/bootstrap');record=next(x for x in v['campaigns'] if x['id']==c);physical_report=record['jobs'][-1]['report'];expect(record['state']=='hardware_review' and physical_report['outcomes'][0]['success'] is None,'worker cannot self-award physical success');expect(physical_report['recording']=={'source':'live_yam_cameras','continuous':True,'fps':2,'frames':{'top':2,'left':2,'right':2}},'continuous physical recording provenance preserved')
s,v=call('/api/hardware/review',{'job':jid,'outcome':'intervention','note':'LOCAL API FIXTURE, no actual physical trial'});expect(s==200,'operator review explicit')
s,v=call('/api/bootstrap');record=next(x for x in v['campaigns'] if x['id']==c);expect(record['jobs'][-1]['report']['outcomes'][0]['intervention'] is True and record['jobs'][-1]['report']['hardware']==expected_h,'intervention and runner attribution retained')
print(json.dumps({'passed_total':checks,'seconds':round(time.monotonic()-started,3),'scope':'local API fixtures only; no simulator/model/robot execution'}))

s,v=w('progress',{'job':jid,'progress':{'status':'finished','executions_used':9,'native_steps_used':102,'unknown':'discarded'}});expect(s==200,'terminal progress can be reconciled without changing outcomes')
s,v=call('/api/bootstrap');record=next(x for x in v['campaigns'] if x['id']==c);expect(record['jobs'][-1]['report']['outcomes'][0]['intervention'] is True and record['jobs'][-1]['report']['progress']['native_steps_used']==102,'progress reconciliation preserves operator review')
print(json.dumps({'passed_total':checks,'scope':'local fixtures only; no robot/model execution'}))
