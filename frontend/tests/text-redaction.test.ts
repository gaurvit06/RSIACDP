import assert from 'node:assert/strict';
import test from 'node:test';
import { redactSelectedText, SUBMITTER_REDACTION_MARKER } from '../src/text-redaction.ts';

test('redacts a middle selection and retains text around it', () => {
  assert.equal(redactSelectedText('A secret B', 2, 8), `A ${SUBMITTER_REDACTION_MARKER} B`);
});

test('redacts selections at the start and end', () => {
  assert.equal(redactSelectedText('secret tail', 0, 6), `${SUBMITTER_REDACTION_MARKER} tail`);
  assert.equal(redactSelectedText('head secret', 5, 11), `head ${SUBMITTER_REDACTION_MARKER}`);
});

test('uses the textarea UTF-16 selection offsets for supplementary characters', () => {
  const value = 'Offer 😀 phone 9876543210';
  const start = value.indexOf('phone');
  const end = value.length;
  assert.equal(redactSelectedText(value, start, end), `Offer 😀 ${SUBMITTER_REDACTION_MARKER}`);
});

test('leaves empty or invalid selections unchanged', () => {
  assert.equal(redactSelectedText('unchanged', 4, 4), 'unchanged');
  assert.equal(redactSelectedText('unchanged', -1, 4), 'unchanged');
  assert.equal(redactSelectedText('unchanged', 2, 99), 'unchanged');
  assert.equal(redactSelectedText('unchanged', 3.5, 5), 'unchanged');
});
