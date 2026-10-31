import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync,readFileSync} from 'node:fs';
import {PUBLIC_DEMO_OWNER,publicDemoPayload} from '../lib/public-demo.mjs';

test('anonymous visitors share the public demo run namespace',()=>{
  assert.equal(PUBLIC_DEMO_OWNER,'public-demo');
});

test('public run details remove email fields and redact email in text',()=>{
  const value=publicDemoPayload({
    runner_name:'Demo Runner',
    email:'private@example.com',
    hardware:{runner_name:'Demo Runner',email:'private@example.com'},
    report:{summary:'Contact private@example.com for the run.'},
  });
  assert.equal(value.runner_name,'Demo Runner');
  assert.equal('email' in value,false);
  assert.equal('email' in value.hardware,false);
  assert.equal(value.report.summary,'Contact [private email] for the run.');
});

test('public hardware history uses the reviewed YAM safety failure over the old generic wrapper',()=>{
  const value=publicDemoPayload({kind:'hardware',report:{
    outcomes:[{scene:1,reason:'simulator_failed'}],
    summary:'stopped · agent failed simulator_failed',
    reviews:[{outcome:'failure',note:'Final trajectory rejected before motion by YAM Safety Guardrails (joint_9_outside_limits); controller stopped safely.'}],
  }});
  assert.equal(value.report.outcomes[0].reason,'hardware_safety_guardrail_rejected (joint_9_outside_limits)');
  assert.equal(value.report.summary,'stopped · agent failed YAM Safety Guardrails rejected the trajectory before motion (joint_9_outside_limits)');
});

test('public hardware history preserves generic failures without a matching reviewed diagnosis',()=>{
  const value=publicDemoPayload({kind:'hardware',report:{
    outcomes:[{scene:1,reason:'simulator_failed'}],
    reviews:[{outcome:'failure',note:'Method did not complete.'}],
  }});
  assert.equal(value.report.outcomes[0].reason,'simulator_failed');
});

test('curated real YAM replay manifest points to hash-verified public camera clips',()=>{
  const manifest=JSON.parse(readFileSync(new URL('../public/physical-evidence/manifest.json',import.meta.url),'utf8'));
  const run=manifest.runs['17bfc338-248f-470f-be6a-faf5fa814bab'];
  assert.equal(run.media.length,3);
  for(const clip of run.media){
    const url=new URL(clip.url);
    assert.equal(url.origin,'https://blupe-embodiedevo.andlyu.chatgpt.site');
    const path=new URL('../public'+url.pathname,import.meta.url);
    assert.equal(existsSync(path),true,clip.name);
    assert.equal(createHash('sha256').update(readFileSync(path)).digest('hex'),clip.sha256,clip.name);
  }
});
