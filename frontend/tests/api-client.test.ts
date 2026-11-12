import assert from 'node:assert/strict';
import { test } from 'node:test';
import { fetchApi, parseApiResponse } from '../src/api-client.ts';

test('missing non-JSON API route produces an actionable deployment message', async () => {
  const response = new Response('Not Found', { status: 404, headers: { 'content-type': 'text/plain' } });
  await assert.rejects(parseApiResponse(response, 'Could not sign in'), /backend is deployed and API routing is configured/);
});

test('non-JSON upstream server errors do not leak a JSON parsing exception', async () => {
  const response = new Response('Internal Server Error', { status: 500, headers: { 'content-type': 'text/plain' } });
  await assert.rejects(parseApiResponse(response, 'Could not sign in'), /investigation service returned a server error \(HTTP 500\)/);
});

test('unavailable API gateway produces a retry and deployment message', async () => {
  const response = new Response('', { status: 502, headers: { 'content-type': 'text/plain' } });
  await assert.rejects(parseApiResponse(response, 'Could not sign in'), /temporarily unavailable.*backend deployment/i);
});

test('structured API validation errors remain visible', async () => {
  const response = Response.json({ detail: [{ loc: ['body', 'email'], msg: 'Invalid email' }] }, { status: 422 });
  await assert.rejects(parseApiResponse(response, 'Could not sign in'), /email: Invalid email/);
});

test('successful JSON response is parsed', async () => {
  const response = Response.json({ csrf_token: 'synthetic-token' });
  assert.deepEqual(await parseApiResponse(response, 'Request failed'), { csrf_token: 'synthetic-token' });
});

test('network failures use a clear service connection message', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new TypeError('Failed to fetch'); };
  try {
    await assert.rejects(fetchApi('/api/auth/login'), /Could not reach the investigation service/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
