import { PageHeader } from './SiteFrame';
import { Assessment } from './Assessment';
import { ChevronRight, FolderOpen, UsersRound } from 'lucide-react';
import type { CampaignGroup } from './App';
import { displayLabel } from './case-display';
import { formatSourceLocation } from './source-location';

type Props = {
  groups: CampaignGroup[] | null; error: string; onOpen: (id: number) => void;
  ruleVersion: string; threshold: number; weights: Record<string, number>;
};

export function CampaignResults({ groups, error, onOpen, ruleVersion, threshold, weights }: Props) {
  return <>
    <PageHeader title="Campaign leads" icon={UsersRound}>Cases connected by shared contact or payment details. Each connection needs independent review.</PageHeader>
    <section className="panel campaign-panel">
      <div className="campaign-toolbar">
        <h2>Linked groups {groups && <span className="count-pill">{groups.length}</span>}</h2>
        <details className="rule-guide"><summary>How matching works</summary>
          <p>Matching identifiers earn points. A link with at least {threshold} points is proposed for review.
          A URL and its domain count once. Points describe the match strength, never the likelihood of fraud.</p>
          <dl>{Object.entries(weights).map(([type, points]) =>
            <div key={type}><dt>{displayLabel(type)}</dt><dd>{points} points</dd></div>)}</dl>
          <small>Current rule · {ruleVersion}</small>
        </details>
      </div>
      {error ? <p className="alert error" role="alert">{error}</p> :
        groups === null ? <p role="status">Loading linked cases…</p> :
        groups.length === 0 ? <div className="empty compact"><FolderOpen size={24}/>
          <h3>No linked groups yet</h3><p>Open a case and choose Recompute links to check for shared identifiers.</p></div> :
        groups.map(group => {
          const reference = (id: number) => group.cases.find(item => item.id === id)?.case_ref ?? `Case ${id}`;
          return <article className="campaign-group" key={group.campaign_ref}>
            <div className="lead-heading"><UsersRound size={20}/><div>
              <h3>{group.case_count} connected cases</h3><small>{group.campaign_ref}</small>
            </div><span className="lead-score">Match strength <b>{group.strength}/100</b></span></div>
            <p className="lead-status">{group.classification === 'low_signal_lead' ? 'Weak match' : 'Possible campaign'} · {group.review_statuses.map(displayLabel).join(', ')}</p>
            <div className="campaign-members">{group.cases.map(item =>
              <button className="campaign-case" key={item.id} onClick={() => onOpen(item.id)}>
                <div><small>{item.case_ref}</small><b>{item.title}</b><Assessment>{item.assessment}</Assessment><span>{new Date(item.created_at).toLocaleDateString()}</span></div><ChevronRight size={16}/>
              </button>)}</div>
            {group.links.map(link => <details className="campaign-link-detail" key={`${link.left_case_id}-${link.right_case_id}-${link.rule_version}`}>
              <summary>Why {reference(link.left_case_id)} and {reference(link.right_case_id)} are linked</summary>
              <div className="campaign-link-body">
                <b>Matching details</b><span>{displayLabel(link.review_status)} · {link.strength}/100 · {link.rule_version}</span>
                {link.reasons.map(reason => <span key={reason}>{reason}</span>)}
                {link.matched_entities.map(entity => <span key={entity.id}>{reference(entity.case_id)} · {displayLabel(entity.type)} · {entity.value} · {displayLabel(entity.review_status)} · {formatSourceLocation(entity.source_location)} {entity.source_start_char !== null && `(characters ${entity.source_start_char}–${entity.source_end_char})`}</span>)}
                <b>Source checks</b>{link.related_evidence.length ? link.related_evidence.map(e =>
                  <span key={e.id}>{e.source_name} · {displayLabel(e.outcome)} · {displayLabel(e.authority)} · {e.claim} · {new Date(e.retrieved_at).toLocaleString()}</span>) : <span>No source linked to this match.</span>}
                {!!link.empty_or_failed_checks.length && <span>Empty and failed checks contribute no adverse evidence.</span>}
              </div>
            </details>)}
          </article>;
        })}
    </section>
  </>;
}
