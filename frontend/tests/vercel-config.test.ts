import assert from 'node:assert/strict';
import test from 'node:test';
import { config } from '../vercel.mjs';

test('Vercel keeps API requests same-origin and uses the protected project API_ORIGIN setting', () => {
  assert.equal(config.framework, 'vite');
  assert.equal(config.outputDirectory, 'dist');
  assert.equal(config.rewrites?.length, 1);
  const rewrite = config.rewrites?.[0];
  assert.ok(rewrite);
  assert.match(JSON.stringify(rewrite), /\/api/);
  assert.equal(rewrite?.destination, '$API_ORIGIN/api/:path*');
});

test('Vercel static deployment retains the restrictive browser security headers', () => {
  const headers = JSON.stringify(config.headers);
  for (const name of ['Content-Security-Policy', 'Permissions-Policy', 'X-Content-Type-Options', 'Referrer-Policy', 'X-Frame-Options']) {
    assert.ok(headers.includes(name), `Missing ${name}`);
  }
});
