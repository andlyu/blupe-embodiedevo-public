"""Local-preview-only direct YAM API checks. Never starts a worker or robot."""
import json
import os
import time
from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
from http.cookiejar import CookieJar
from urllib.error import HTTPError

ORIGIN = os.environ.get('BLUPE_TEST_ORIGIN', 'http://127.0.0.1:8798')
TOKEN = 'local-fixture-worker-token-for-api-validation-only'
opener = build_opener(HTTPCookieProcessor(CookieJar()))
checks = 0


def call(path, payload=None, *, signed_in=True, token=None):
    headers = {'Origin': ORIGIN, 'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = Request(ORIGIN + path,
                      data=None if payload is None else json.dumps(payload).encode(),
                      headers=headers)
    try:
        opener_fn = opener.open if signed_in else urlopen
        with opener_fn(request, timeout=15) as response:
            raw = response.read()
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.status, json.loads(raw)
            return response.status, raw
    except HTTPError as error:
        return error.code, json.loads(error.read())


def expect(value, message):
    global checks
    assert value, message
    checks += 1


started = time.monotonic()
status, value = call('/api/bootstrap', signed_in=False)
expect(status == 200 and value.get('user') is False,
       'the public demo bootstrap must work without signing in')
expect(value.get('operatorAllowed') is True,
       'anonymous visitors can open the public YAM demo controls')

# The direct-only workflow must reject both legacy simulator entry points.
status, _ = call('/api/campaigns', {}, signed_in=False)
expect(status == 410, 'simulator campaign creation is disabled')
status, _ = call('/api/jobs', {}, signed_in=False)
expect(status == 410, 'simulator campaign jobs are disabled')

# No physical work is submitted by this check. Invalid requests fail before
# station readiness is queried. A valid-shaped request must pass validation,
# then stop at the disconnected local worker gate before a YAM job is created.
status, _ = call('/api/direct-yam', {'skill_id': 'not-a-pinned-skill',
                                     'task': 'fixture task'}, signed_in=False)
expect(status == 400, 'public direct YAM rejects skills absent from the pinned library')

base = {'skill_id': 'stack_blocks', 'task': 'Stack the blue cube on the orange cube.',
        'hardware': {'robot': 'yam-1', 'seconds': 600, 'budget': 100,
                     'runner_name': 'Local API fixture',
                     'email': 'fixture@example.invalid',
                     'identity_confirmed': False}}
status, value = call('/api/direct-yam', base, signed_in=False)
expect(status == 400, 'public direct YAM still requires confirmed runner identity')

confirmed = {**base, 'hardware': {**base['hardware'], 'identity_confirmed': True}}
status, value = call('/api/direct-yam', confirmed, signed_in=False)
expect(status == 409 and 'YAM compute worker is disconnected' in value.get('error', ''),
       'valid YAM input passes validation and is rejected before insertion without a local worker')

status, value = call('/api/worker/probe', {'worker': 'local-api-probe'}, token=TOKEN)
expect(status in (401, 503),
       'worker probe remains unavailable without the private token')
status, value = call('/api/worker/claim', {'worker': 'local-api-probe'},
                     token='invalid-worker-token')
expect(status in (401, 503), 'worker claims require a configured private token')

print(json.dumps({'passed': checks,
                  'seconds': round(time.monotonic() - started, 3),
                  'scope': 'local API validation only; no model, worker, simulator or robot run'}))
