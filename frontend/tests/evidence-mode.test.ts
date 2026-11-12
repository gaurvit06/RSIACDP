import assert from 'node:assert/strict';
import test from 'node:test';
import { evidenceModeLabel } from '../src/evidence-mode.ts';

test('shows local evidence mode when optional external lookup is disabled', () => {
  assert.equal(evidenceModeLabel('local'), 'LOCAL EVIDENCE MODE');
});

test('makes the separately consented RDAP option visible when enabled', () => {
  assert.equal(evidenceModeLabel('rdap'), 'LOCAL + CONSENT-GATED RDAP');
});

test('does not claim a source mode before policy loads or when it is unavailable', () => {
  assert.equal(evidenceModeLabel('loading'), 'LOADING SOURCE POLICY');
  assert.equal(evidenceModeLabel('unavailable'), 'SOURCE POLICY UNAVAILABLE');
});
