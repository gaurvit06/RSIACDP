import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { parse } from 'yaml';

const manifestPath = new URL('../../hostless.yaml', import.meta.url);
const vercelPath = new URL('../vercel.mjs', import.meta.url);
const manifestSource = readFileSync(manifestPath, 'utf8');
const manifest = parse(manifestSource) as Record<string, any>;

test('Hostless manifest uses the existing Docker backend with no-card resource bounds', () => {
  assert.equal(manifest.build.system, 'docker');
  assert.equal(manifest.working_directory, 'backend');
  assert.equal(manifest.build_context_directory, 'backend');
  assert.equal(manifest.dockerfile_path, 'Dockerfile');
  assert.deepEqual(manifest.scaling, {
    trigger: 'http_requests',
    min_cpu: 0.1,
    max_cpu: 0.1,
    min_memory: 256,
    max_memory: 256,
    min_replicas: 1,
    max_replicas: 1,
  });
  assert.equal(manifest.health_check.http_path, '/health/live');
  assert.equal(manifest.workers.length, 1);
  assert.equal(manifest.workers[0].command, 'python -m app.worker');
  assert.equal(manifest.workers[0].max_cpu_per_replica, 0.1);
  assert.equal(manifest.workers[0].min_memory_per_replica, 256);
  assert.equal(manifest.workers[0].max_memory_per_replica, 256);
  assert.equal(manifest.workers[0].replicas, 1);
});

test('Hostless manifest contains neither secrets nor persistent local storage', () => {
  for (const key of ['DATABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'JWT_SECRET', 'UPLOAD_ENCRYPTION_KEY', 'NEO4J_PASSWORD']) {
    assert.doesNotMatch(manifestSource, new RegExp(`^\\s*${key}\\s*:`, 'm'));
  }
  assert.equal('storage' in manifest, false);
  assert.equal('volumes' in manifest, false);
});

test('deployment config files exist for Vercel and Hostless', () => {
  assert.ok(readFileSync(vercelPath, 'utf8').includes("const apiOrigin = '$API_ORIGIN'"));
});
