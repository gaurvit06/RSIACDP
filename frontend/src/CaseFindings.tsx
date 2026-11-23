import { ChevronRight } from 'lucide-react';
import { Assessment } from './Assessment';
import type { SystemFinding } from './App';
import { displayLabel } from './case-display';

export function CaseFindings({ findings }: { findings: SystemFinding[] }) {
  const claims = findings.filter(f => f.scope !== 'case').sort((a, b) => Number(b.scope === 'vacancy') - Number(a.scope === 'vacancy'));
  if (!claims.length) return null;
  return <section className="panel">
    <div className="panel-heading"><h2>Findings by claim</h2><span className="count-pill">{claims.length}</span></div>
    <div className="finding-list">{claims.map(finding =>
      <details key={finding.id} className="claim-detail" open={finding.scope === "vacancy" || undefined}>
        <summary><ChevronRight size={16} aria-hidden="true" className="finding-chevron"/><span>{finding.claim.replaceAll('_', ' ')}</span><Assessment>{finding.assessment}</Assessment></summary>
        <div className="claim-body">
          <p>{finding.observation}</p>
          {finding.evidence_snapshot.map(source =>
            <div className="finding-source" key={source.evidence_id}>
              <strong>#{source.evidence_id} · {source.source_name}</strong>
              <span>{displayLabel(source.outcome)} · {displayLabel(source.authority)} · {new Date(source.retrieved_at).toLocaleString()}</span>
              <p>{source.claim}</p>{source.source_type === 'official_employer_board' && /^https:\/\/job-boards\.greenhouse\.io\/[a-z0-9_-]+\/jobs\/\d+$/.test(source.source_ref)
                ? <a href={source.source_ref} target="_blank" rel="noreferrer">Open employer listing</a>
                : <small>{source.source_ref}</small>}
            </div>)}
          {([['Supports this claim', finding.supporting_evidence_ids], ['Conflicting evidence', finding.conflict_evidence_ids],
            ['Awaiting review', finding.unreviewed_evidence_ids]] as const).map(([label, ids]) =>
            ids.length > 0 && <small key={label}>{label} · {ids.map(id => '#' + id).join(', ')}</small>)}
          <p>{finding.limitations}</p>
          <small>Rule · {finding.rule_name === finding.rule_version ? finding.rule_name : finding.rule_name + ' · ' + finding.rule_version}</small>
        </div>
      </details>)}</div>
  </section>;
}
