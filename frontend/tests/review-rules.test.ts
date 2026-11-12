import assert from 'node:assert/strict';
import test from 'node:test';

import { canApproveDisposition, correctionApplyValid, correctionCaseChangeOpen, correctionEvidenceActions, correctionReviewValid, retainEligibleEvidenceIds } from '../src/review-rules.ts';

const reviewedEvidence = (overrides: Record<string, unknown> = {}) => ({
  outcome: 'result',
  authority: 'government',
  review_status: 'relevant',
  ...overrides,
});

test('allows review of concern when all cited current evidence is relevant', () => {
  assert.equal(canApproveDisposition({
    disposition: 'evidence_supports_concern',
    evidence: [reviewedEvidence()],
  }), true);
});

test('blocks approval when any cited evidence was withdrawn', () => {
  assert.equal(canApproveDisposition({
    disposition: 'evidence_supports_concern',
    evidence: [reviewedEvidence({ details: { source_record_withdrawn: true } })],
  }), false);
});

test('blocks approval when cited evidence is no longer relevant or result-bearing', () => {
  assert.equal(canApproveDisposition({
    disposition: 'evidence_supports_concern',
    evidence: [reviewedEvidence({ review_status: 'irrelevant' })],
  }), false);
  assert.equal(canApproveDisposition({
    disposition: 'evidence_supports_concern',
    evidence: [reviewedEvidence({ outcome: 'no_result' })],
  }), false);
});

test('authoritative disposition requires at least one authoritative source', () => {
  assert.equal(canApproveDisposition({
    disposition: 'confirmed_authoritative',
    evidence: [reviewedEvidence({ authority: 'registry_data' })],
  }), false);
  assert.equal(canApproveDisposition({
    disposition: 'confirmed_authoritative',
    evidence: [reviewedEvidence()],
  }), true);
});

test('weaker dispositions do not require source evidence to be approved', () => {
  assert.equal(canApproveDisposition({ disposition: 'insufficient_evidence' }), true);
});

test('removes withdrawn and no-longer-relevant selections from the disposition form', () => {
  const evidence = [
    { id: 1, ...reviewedEvidence() },
    { id: 2, ...reviewedEvidence({ details: { source_record_withdrawn: true } }) },
    { id: 3, ...reviewedEvidence({ review_status: 'irrelevant' }) },
    { id: 4, ...reviewedEvidence({ outcome: 'no_result' }) },
  ];
  assert.deepEqual(retainEligibleEvidenceIds([4, 2, 1, 3], evidence), [1]);
});

test('correction actions keep withdrawn evidence historical', () => {
  assert.deepEqual(correctionEvidenceActions({ details: { source_record_withdrawn: true } }), ['irrelevant', 'needs_review']);
  assert.deepEqual(correctionEvidenceActions({ details: { source_record_withdrawn: false } }), ['irrelevant', 'relevant', 'needs_review', 'contradicts']);
});

test('correction review rationale validation matches the API limits', () => {
  assert.equal(correctionReviewValid('1234'), false);
  assert.equal(correctionReviewValid('  short  '), true);
  assert.equal(correctionReviewValid('x'.repeat(4001)), false);
});

test('case changes are available only while a correction request is open', () => {
  assert.equal(correctionCaseChangeOpen('received'), true);
  assert.equal(correctionCaseChangeOpen('investigating'), true);
  assert.equal(correctionCaseChangeOpen('resolved'), false);
  assert.equal(correctionCaseChangeOpen('rejected'), false);
});

test('applying a correction requires a valid rationale and, when replacing a value, a valid replacement', () => {
  assert.equal(correctionApplyValid('123456789'), false);
  assert.equal(correctionApplyValid('  A sufficiently detailed reason  '), true);
  assert.equal(correctionApplyValid('A sufficiently detailed reason', 'x'), false);
  assert.equal(correctionApplyValid('A sufficiently detailed reason', 'corrected@example.org'), true);
  assert.equal(correctionApplyValid('A sufficiently detailed reason', 'x'.repeat(1001)), false);
});
