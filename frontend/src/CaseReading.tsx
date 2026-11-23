import { PageHeader } from './SiteFrame';
import { useRef, type ReactNode } from 'react';
import { ArrowDownToLine, ArrowLeft, ChevronRight, Clock3, FileSearch, Fingerprint, Link2, ShieldCheck, type LucideIcon } from 'lucide-react';
import type { Case } from './App';
import { Assessment } from './Assessment';
import { CaseFindings } from './CaseFindings';
import { PostingPrediction } from './PostingPrediction';
import { displayLabel } from './case-display';
import { formatSourceLocation } from './source-location';
import './case-reading.css';

type ReadingProps = {
  item: Case;
  investigator: boolean;
  children: ReactNode;
  onBack: () => void;
  onRefresh: () => void;
  onRetry: () => void;
  onDownload: (format: 'json' | 'markdown') => void;
  onReview: (id: number, status: string) => void;
  onEvidence: (id: number, status: string) => void;
  onReviewLink: (id: number, status: string) => void;
};

function ReadingSection({ title, description, icon: Icon, children }: {
  title: string; description: string; icon: LucideIcon; children: ReactNode;
}) {
  return <details className="reading-section">
    <summary><span className="reading-icon"><Icon size={19} aria-hidden="true"/></span>
      <span><strong>{title}</strong><small>{description}</small></span>
      <ChevronRight className="reading-chevron" size={18} aria-hidden="true"/>
    </summary>
    <div className="reading-body">{children}</div>
  </details>;
}

function count(n: number, label: string) { return n + ' ' + label + (n === 1 ? '' : 's'); }

export function CaseReading({ item, investigator, children, onBack, onRefresh, onRetry, onDownload, onReview, onEvidence, onReviewLink }: ReadingProps) {
  const findings = item.findings ?? [];
  const overall = findings.find(f => f.scope === 'case');
  const claimCount = findings.filter(f => f.scope !== 'case').length;
  const evidenceSection = useRef<HTMLDivElement>(null);
  const links = item.links ?? [];
  function inspectEvidence() {
    const section = evidenceSection.current?.querySelector('details');
    if (section) {
      section.open = true;
      section.querySelector('summary')?.focus({ preventScroll: true });
      section.scrollIntoView({ block: 'start' });
    }
  }
  return <article className="case-reading">
    <button className="back-link" onClick={onBack}><ArrowLeft size={15}/> All cases</button>
    <PageHeader title={item.title} icon={FileSearch} meta={<div className="reading-meta"><span className="case-reference">{item.case_ref}</span><span className="status"><i className={item.status}/>{displayLabel(item.status)}</span></div>}>
      {displayLabel(item.input_kind)} <span aria-hidden="true">·</span> Submitted {new Date(item.created_at).toLocaleString()}
    </PageHeader>
    {investigator && item.processing?.error && <div className="modal-warning"><strong>Processing needs attention</strong><p>{item.processing.error}</p><button className="secondary" onClick={onRetry}>Retry processing</button></div>}
    <div className="reading-overview">
      <section className="reading-card">
        <h2><ShieldCheck size={19} aria-hidden="true"/>What the evidence shows</h2>
        <Assessment>{item.assessment}</Assessment>
        <p>{overall?.observation || (item.status === 'completed' ? 'A case-level explanation has not been recorded.' : 'The evidence summary will update when processing finishes.')}</p>
        <button className="reading-jump" onClick={inspectEvidence}>Inspect findings and sources <ChevronRight size={15}/></button>
      </section>
      <PostingPrediction prediction={item.posting_prediction} status={item.status} evidence={item.assessment}/>
    </div>
    <div className="reading-sections">
      <div ref={evidenceSection}>
        <ReadingSection title="Findings and sources" icon={FileSearch} description={count(claimCount, 'claim') + ' · ' + count(item.evidence.length, 'source check')}>
          {!!claimCount && <CaseFindings findings={findings}/>}
          <h3>Source checks</h3>
          {item.evidence.length === 0 && <p>No source checks recorded yet.</p>}
          {item.evidence.map(ev => <details className="reading-record" key={ev.id}>
            <summary><strong>{ev.source_name}</strong><span>{displayLabel(ev.outcome)} · #{ev.id}</span></summary>
            <div className="record-body">
              <p><b>Claim checked</b> {ev.claim}</p>{ev.excerpt && <blockquote>{ev.excerpt}</blockquote>}
              <dl><dt>Source</dt><dd>{displayLabel(ev.source_type)} · {displayLabel(ev.authority)}</dd>
                <dt>Reference</dt><dd>{String(ev.details?.source_record_ref || ev.source_ref || 'Unavailable')}</dd>
                <dt>Retrieved</dt><dd>{new Date(ev.retrieved_at).toLocaleString()}</dd>
                <dt>Relevance</dt><dd>{displayLabel(ev.review_status)}{ev.review_reason && ' · ' + ev.review_reason}</dd></dl>
              {ev.details?.source_record_withdrawn === true && <p className="modal-warning">Withdrawn source. This result is kept for the historical record.</p>}
              {investigator && <div className="reading-actions">
                {ev.details?.source_record_withdrawn !== true && <button className="secondary" onClick={() => onEvidence(ev.id, 'relevant')}>Mark relevant</button>}
                <button className="secondary" onClick={() => onEvidence(ev.id, 'irrelevant')}>Mark irrelevant</button>
                {ev.details?.source_record_withdrawn !== true && <button className="secondary" onClick={() => onEvidence(ev.id, 'contradicts')}>Mark as conflicting</button>}
              </div>}
            </div>
          </details>)}
        </ReadingSection>
      </div>
      <ReadingSection title="Submission and extracted details" icon={Fingerprint} description={count(item.entities.length, 'extracted item')}>
        {investigator && item.input_kind === 'posting' && item.submitted_text && <details className="reading-record"><summary>Read original job posting</summary><pre className="submitted-posting">{item.submitted_text}</pre></details>}
        {item.entities.length === 0 && <p>No identifiers or claims were extracted.</p>}
        {item.entities.map(e => <details className="reading-record" key={e.id}>
          <summary><strong>{displayLabel(e.type)} · {e.value}</strong><span>{displayLabel(e.review_status)}</span></summary>
          <div className="record-body">
            {e.excerpt && <blockquote>{e.excerpt}</blockquote>}
            <dl><dt>Found in</dt><dd>{formatSourceLocation(e.source_location)}{e.source_start_char != null && e.source_end_char != null && ' · characters ' + e.source_start_char + '–' + e.source_end_char}</dd>
              {e.extraction_confidence != null && <><dt>Parser confidence</dt><dd>{Math.round(e.extraction_confidence * 100)}% confidence in extracting this value. Its accuracy as a claim requires evidence.</dd></>}
              {e.extraction_uncertainty && <><dt>Extraction notes</dt><dd>{e.extraction_uncertainty}</dd></>}</dl>
            {investigator && e.review_status === 'needs_review' && <div className="reading-actions"><button className="secondary" onClick={() => onReview(e.id, 'confirmed')}>Confirm extraction</button><button className="secondary" onClick={() => onReview(e.id, 'rejected')}>Reject extraction</button></div>}
          </div></details>)}
      </ReadingSection>
      <ReadingSection title="Related cases" icon={Link2} description={count(links.length, 'campaign link')}>
        <p>Shared identifiers are investigative leads. Check their source and context because identifiers can be reused, compromised, or misreported.</p>
        {!links.length && <p>No links recorded for this case.</p>}
        {links.map(link => <div className="reading-record record-body" key={link.id}>
          <strong>Case {link.left_case_id} ↔ Case {link.right_case_id}</strong><p>{link.reasons.join(' · ')}</p>
          <small>Link strength {link.strength}/100 · {displayLabel(link.review_status)} · {link.rule_version}</small>
          {investigator && link.review_status === 'proposed' && <div className="reading-actions"><button className="secondary" onClick={() => onReviewLink(link.id, 'confirmed')}>Confirm link</button><button className="secondary" onClick={() => onReviewLink(link.id, 'rejected')}>Reject link</button></div>}
        </div>)}
        {investigator && <button className="secondary" onClick={onRefresh}>Recompute links</button>}
      </ReadingSection>
      <ReadingSection title="Activity and review" icon={Clock3} description={count(item.timeline?.length ?? 0, 'event') + (investigator ? ' · Investigator decisions' : '')}>
        <h3>Evidence timeline</h3>
        <div className="timeline">{(item.timeline ?? []).map((event, i) => <div className="timeline-item" key={i}><i/><div><b>{displayLabel(event.action)}</b><span>{new Date(event.created_at).toLocaleString()}</span></div></div>)}</div>
        {!item.timeline?.length && <p>No review events recorded.</p>}
        {children}
      </ReadingSection>
      <ReadingSection title="Download report" icon={ArrowDownToLine} description="Markdown or JSON · Redacted by default">
        <p>{investigator ? 'Investigators and reviewers can inspect source content here. Downloads restrict free-text evidence by default.' : 'Your analyst view masks identifiers and withholds free-text evidence. An authorized investigator can review the original material.'}</p>
        <div className="reading-actions"><button className="secondary" onClick={() => onDownload('markdown')}>Export Markdown</button><button className="secondary" onClick={() => onDownload('json')}>Export JSON</button></div>
      </ReadingSection>
    </div>
  </article>;
}
