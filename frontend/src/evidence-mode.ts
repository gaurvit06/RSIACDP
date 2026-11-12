export type EvidenceMode = 'loading' | 'local' | 'rdap' | 'unavailable';

export function evidenceModeLabel(mode: EvidenceMode): string {
  switch (mode) {
    case 'local': return 'LOCAL EVIDENCE MODE';
    case 'rdap': return 'LOCAL + CONSENT-GATED RDAP';
    case 'unavailable': return 'SOURCE POLICY UNAVAILABLE';
    case 'loading': return 'LOADING SOURCE POLICY';
  }
}
