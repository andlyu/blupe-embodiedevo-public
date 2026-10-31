import test from 'node:test';
import assert from 'node:assert/strict';
import {canRequestSession,hardwareConfig} from '../lib/yam.ts';
const station={connected:true,queue_ready:false};
const observation={source:'hardware',observed_at:100,mode:'API_ACTIVE',homed:true,settled:true,safety:{ok:true,estop_engaged:false}};
test('busy station permits joining the ordinary queue without immediate assignment',()=>assert.equal(canRequestSession(station,observation,101),true));
test('parked uninitialized station may queue before normal Home initialization',()=>assert.equal(canRequestSession(station,{...observation,mode:'DISABLED',homed:false,settled:false,safety:{ok:false,reason:'hardware_not_initialized',estop_engaged:false}},101),true));
test('disconnected and nonhardware sources do not request sessions',()=>{assert.equal(canRequestSession({...station,connected:false},observation,101),false);assert.equal(canRequestSession(station,{...observation,source:'simulation'},101),false);});
test('stale, invalid and excessively future telemetry cannot request sessions',()=>{for(const observed_at of [80,103,NaN,undefined])assert.equal(canRequestSession(station,{...observation,observed_at},100),false);});
test('emergency stops and unresolved hardware faults block requests',()=>{for(const safety of [{ok:true,estop_engaged:true},{ok:false,reason:'motor_fault'},{ok:false}])assert.equal(canRequestSession(station,{...observation,safety},101),false);});
test('physical runs require a confirmed real runner and carry identity to the queue job',()=>{
 const input={robot:'yam-1',task:'stack the blue cube',seconds:600,budget:100,runner_name:'Ada Operator',email:'ada@example.com',identity_confirmed:true};
 assert.deepEqual(hardwareConfig(input),{method:'EmbodiedEvo',robot:'yam-1',task:'stack the blue cube',seconds:600,budget:100,runner_name:'Ada Operator',email:'ada@example.com'});
 for(const bad of [{...input,identity_confirmed:false},{...input,runner_name:' '},{...input,email:'not-an-email'}])assert.throws(()=>hardwareConfig(bad));
});
