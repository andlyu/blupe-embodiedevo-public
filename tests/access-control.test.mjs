import test from 'node:test';
import assert from 'node:assert/strict';
import { operatorIdAllowed } from '../lib/access-control.mjs';

test('operator access fails closed when no account is configured', () => {
  assert.equal(operatorIdAllowed('local_seedy'), false);
  assert.equal(operatorIdAllowed('local_seedy', ''), false);
});

test('only an exact configured account can operate the shared worker', () => {
  assert.equal(operatorIdAllowed('local_seedy', 'local_seedy'), true);
  assert.equal(operatorIdAllowed('local_seedy', 'other-user'), false);
  assert.equal(operatorIdAllowed('local_seedy', 'local_seedy-typo'), false);
});

test('operator allowlists accept comma-separated IDs with surrounding whitespace', () => {
  assert.equal(operatorIdAllowed('second-user', ' first-user, second-user '), true);
  assert.equal(operatorIdAllowed('second-user', 'first-user,third-user'), false);
});
