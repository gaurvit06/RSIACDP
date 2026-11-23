import test from 'node:test';
import assert from 'node:assert/strict';
import { matchesCase, displayLabel } from '../src/case-display.ts';

const item = { title: 'Example offer', case_ref: 'RC-123', assessment: 'Insufficient evidence', entities: [
  { type: 'location_claim', value: 'Pune', review_status: 'needs_review' },
  { type: 'job_title_claim', value: 'Engineer', review_status: 'confirmed' },
  { type: 'company_claim', value: 'Old name', review_status: 'rejected' },
] };

test('desk combines posting-field search with the assessment filter', () => {
  for (const term of ['example', 'rc-123', ' pune ', 'engineer']) assert.ok(matchesCase(item, term, item.assessment));
  assert.equal(matchesCase(item, 'Pune', 'Evidence supports concern'), false);
  assert.equal(matchesCase(item, 'Old name', ''), false);
  assert.ok(matchesCase(item, '', ''));
});
test('workspace labels preserve acronyms and translate unknown keys', () => {
  assert.equal(displayLabel('upi_id'), 'UPI ID');
  assert.equal(displayLabel('no_result'), 'No match');
  assert.equal(displayLabel('pending_review'), 'Pending review');
});

test('model decisions can be filtered independently of the source assessment', () => {
  const classified = { ...item, posting_prediction: { label: 'Higher fraud risk' } };
  assert.ok(matchesCase(classified, 'Pune', 'Higher fraud risk'));
  assert.ok(matchesCase(classified, 'higher fraud risk', item.assessment));
  assert.equal(matchesCase(classified, '', 'Lower fraud risk'), false);
});
