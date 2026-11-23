const labels: Record<string, string> = {
  posting: 'Job posting', industry_claim: 'Industry', employment_type_claim: 'Employment type',
  upi_id: 'UPI ID', url: 'Web address', domain: 'Domain', phone: 'Phone number',
  bank_account: 'Bank account', ifsc_code: 'IFSC code', email: 'Email',
  company_claim: 'Company', job_title_claim: 'Job title', location_claim: 'Location',
  compensation_amount_claim: 'Pay offered', payment_amount_claim: 'Requested amount',
  fee_request: 'Payment request', recruiter_claim: 'Recruiter', date_claim: 'Date',
  official_employer_board: 'Official employer board', curated_local_corpus: 'Local evidence collection', submitted_material: 'Original submission',
  uploaded_file: 'Uploaded document', no_result: 'No match', result: 'Result found',
  needs_review: 'Awaiting review', low_signal: 'Weak match', proposed: 'Awaiting link review',
  text: 'Text', file: 'File', message: 'Message', unreviewed: 'Awaiting review',
};

export function displayLabel(value: string) {
  const words = value.replaceAll('_', ' ');
  return labels[value] ?? words.charAt(0).toUpperCase() + words.slice(1);
}

type SearchableCase = {
  posting_prediction?: { label: string } | null;
  title: string; case_ref: string; assessment: string;
  entities: { type: string; value: string; review_status: string }[];
};

const postingFields = new Set(['job_title_claim', 'company_claim', 'location_claim']);
export function matchesCase(item: SearchableCase, search: string, assessment: string) {
  if (assessment && item.assessment !== assessment && item.posting_prediction?.label !== assessment) return false;
  const term = search.trim().toLowerCase();
  if (!term) return true;
  const fields = [item.title, item.case_ref, item.assessment, item.posting_prediction?.label ?? ''];
  for (const entity of item.entities) {
    if (postingFields.has(entity.type) && entity.review_status !== 'rejected') fields.push(entity.value);
  }
  return fields.some(field => field.toLowerCase().includes(term));
}
