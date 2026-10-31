import test from 'node:test';
import assert from 'node:assert/strict';
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
