export type EvidenceMode = 'boards' | 'boards-rdap' | 'loading' | 'local' | 'rdap' | 'unavailable';

export function evidenceModeLabel(mode: EvidenceMode): string {
  switch (mode) {
    case 'boards': return 'LOCAL + EMPLOYER BOARDS';
    case 'boards-rdap': return 'EMPLOYER BOARDS + CONSENT-GATED RDAP';
    case 'local': return 'LOCAL EVIDENCE MODE';
    case 'rdap': return 'LOCAL + CONSENT-GATED RDAP';
    case 'unavailable': return 'SOURCE POLICY UNAVAILABLE';
    case 'loading': return 'LOADING SOURCE POLICY';
  }
}
