import assert from 'node:assert/strict';
import test from 'node:test';
import { clearExpiredSession, shouldExpireSession } from '../src/auth-session.ts';

test('expires the local session when a protected request returns unauthorized', () => {
  assert.equal(shouldExpireSession(401, '/api/cases'), true);
  assert.equal(shouldExpireSession(401, '/api/auth/me'), true);
});

test('does not expire a session for the expected logout response or non-auth errors', () => {
  assert.equal(shouldExpireSession(401, '/api/auth/logout'), false);
  assert.equal(shouldExpireSession(403, '/api/cases'), false);
  assert.equal(shouldExpireSession(429, '/api/cases'), false);
  assert.equal(shouldExpireSession(500, '/api/cases'), false);
});

test('clears the in-memory session state after session expiry', () => {
  let reset = false;
  clearExpiredSession(() => { reset = true; });
  assert.equal(reset, true);
});
