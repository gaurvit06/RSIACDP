export type DispositionReviewEvidence = {
  id?: number;
  outcome: string;
  authority: string;
  review_status: string;
  details?: Record<string, unknown>;
};

export type DispositionReviewCandidate = {
  disposition: string;
  evidence?: DispositionReviewEvidence[];
};

export type CorrectionEvidenceAction = 'irrelevant' | 'relevant' | 'needs_review' | 'contradicts';

/** Match the server schema for updating a correction request. */
export function correctionReviewValid(resolution: string): boolean {
  const length = resolution.trim().length;
  return length >= 5 && length <= 4000;
}

/** Case records can only be changed while the requester appeal is open. */
export function correctionCaseChangeOpen(status: string): boolean {
  return status === 'received' || status === 'investigating';
}

/** Match the server schema before applying a correction to a case record. */
export function correctionApplyValid(resolution: string, correctedValue?: string): boolean {
  const length = resolution.trim().length;
  if (length < 10 || length > 4000) return false;
  if (correctedValue !== undefined) {
    const correctedLength = correctedValue.trim().length;
    if (correctedLength < 2 || correctedLength > 1000) return false;
  }
  return true;
}

/** Retired corpus evidence remains correctable as historical, but cannot be reinstated as current support. */
export function correctionEvidenceActions(evidence?: Pick<DispositionReviewEvidence, 'details'>): CorrectionEvidenceAction[] {
  if (evidence?.details?.source_record_withdrawn === true) return ['irrelevant', 'needs_review'];
  return ['irrelevant', 'relevant', 'needs_review', 'contradicts'];
}

/** Mirror the backend approval prerequisites to prevent a futile UI action. */
export function canApproveDisposition(item: DispositionReviewCandidate): boolean {
  if (!['confirmed_authoritative', 'evidence_supports_concern'].includes(item.disposition)) return true;
  const evidence = item.evidence || [];
  if (!evidence.length || evidence.some(record => (
    record.review_status !== 'relevant'
    || record.outcome !== 'result'
    || record.details?.source_record_withdrawn === true
  ))) return false;
  return item.disposition !== 'confirmed_authoritative'
    || evidence.some(record => ['government', 'platform_action', 'authoritative_source'].includes(record.authority));
}

export function retainEligibleEvidenceIds(
  selectedIds: number[],
  evidence: Array<DispositionReviewEvidence & { id: number }>,
): number[] {
  const eligibleIds = new Set(evidence.filter(record => (
    record.outcome === 'result'
    && record.review_status === 'relevant'
    && record.details?.source_record_withdrawn !== true
  )).map(record => record.id));
  return selectedIds.filter(id => eligibleIds.has(id));
}
