export const postingFields = ['Job title', 'Company', 'Location', 'Industry', 'Employment type', 'Department', 'Required experience', 'Requirements', 'Benefits', 'Salary disclosed', 'Company logo present'] as const;
export type PostingDraft = Partial<Record<typeof postingFields[number], string>>;

export function postingMaterial(fields: PostingDraft, description: string) {
  const lines = postingFields.filter(label => fields[label]?.trim()).map(label => label + ': ' + fields[label]!.trim());
  if (description.trim()) lines.push('Job description:\n' + description);
  return lines.join('\n');
}

export const dimensions = {
  industry_claim: 'Industry', location_claim: 'Location', job_title_claim: 'Job title', employment_type_claim: 'Employment type',
} as const;
export type Dimension = keyof typeof dimensions;
export type PostingCase = {
  id: number; title: string; case_ref: string; assessment: string;
  entities: { type: string; value: string; review_status: string }[];
};

export function groupPostings(cases: PostingCase[], dimension: Dimension, confirmedOnly: boolean) {
  const groups = new Map<string, { key: string; label: string; cases: PostingCase[] }>();
  for (const item of cases) {
    const values = new Map<string, string>();
    for (const entity of item.entities) {
      if (entity.type !== dimension || entity.review_status === 'rejected' ||
          (confirmedOnly && entity.review_status !== 'confirmed')) continue;
      const label = entity.value.normalize('NFC').trim().replace(/\s+/g, ' ');
      if (label) values.set(label.toLowerCase(), label);
    }
    if (!values.size) values.set('', confirmedOnly ? 'No confirmed value' : 'No recorded value');
    for (const [key, label] of values) {
      const group = groups.get(key) ?? { key, label, cases: [] };
      group.cases.push(item);
      groups.set(key, group);
    }
  }
  return [...groups.values()].sort((a, b) => b.cases.length - a.cases.length || a.key.localeCompare(b.key, 'en'));
}
