import assert from 'node:assert/strict';
import test from 'node:test';
import { resultStyle } from '../src/result-tone.ts';

test('model and evidence labels each communicate their own level of support', () => {
  for (const [tone, labels] of Object.entries({
    positive: ['Confirmed by an authoritative source', 'Lower fraud risk'],
    risk: ['Evidence supports concern', 'Higher fraud risk'],
    uncertain: ['Insufficient evidence', 'More posting text needed'],
    neutral: ['Awaiting processing', 'Unscored', 'No adverse evidence found', 'Unknown status'],
  })) {
    for (const label of labels) assert.equal(resultStyle(label)[0], tone, label);
  }
});
