export type ResultTone = 'positive' | 'risk' | 'uncertain' | 'neutral';

const results: ReadonlyMap<string, [ResultTone, string]> = new Map([
  ['Confirmed by an authoritative source', ['positive', 'A source confirms the specific claim. Open the case to see what was verified.']],
  ['Lower fraud risk', ['positive', 'The model estimated lower risk from the posting.']],
  ['Higher fraud risk', ['risk', 'The model estimated higher risk from the posting.']],
  ['Evidence supports concern', ['risk', 'Evidence supports a specific concern. Open the finding to inspect its sources.']],
  ['Insufficient evidence', ['uncertain', 'The available evidence is inconclusive.']],
  ['More posting text needed', ['uncertain', 'The model needs more posting text to estimate risk.']],
  ['No adverse evidence found', ['neutral', 'The checks found no adverse evidence. The offer is still unverified.']],
  ['Awaiting processing', ['neutral', 'The model has not finished scoring this posting.']],
  ['Unscored', ['neutral', 'No model score is available.']],
]);

export function resultStyle(label: string): [ResultTone, string] {
  return results.get(label) ?? ['neutral', label];
}
