import { PageHeader } from './SiteFrame';
import { DialogTransition } from './DialogTransition';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Files, ArrowLeft, BookOpen, ChevronDown, FileText, Plus, Search } from 'lucide-react';
import { displayLabel } from './case-display';

export type CorpusRecord = {
  record_id: string; entity_type: string; normalized_value: string; source_name: string; source_type: string;
  source_ref: string; claim: string; outcome: string; excerpt: string; authority: string; retrieved_at: string;
  active: boolean; retired_at?: string; retirement_reason?: string;
};
const categories: Record<string,string> = { company_official: 'Official company source', government: 'Government record', platform: 'Platform action', news: 'News report', complaint: 'Complaint', other: 'Other' };
const authorities: Record<string,string> = { curated: 'Curated source', unverified_public_report: 'Unverified public report', government: 'Government', platform_action: 'Platform action', authoritative_source: 'Other authoritative source' };
const examples: Record<string,string> = { email: 'recruitment@example.org', phone: 'Phone number with country code', domain: 'example.org', url: 'https://example.org/careers', upi_id: 'name@provider', bank_account: 'Account number shown in the source', ifsc_code: 'IFSC shown in the source' };
const newRecord = { entity_type: 'email', value: '', source_name: '', source_type: 'other', source_ref: '', claim: '', outcome: 'result', excerpt: '', authority: 'curated' };
const authorityChoices = (category: string) => [
  'curated', 'unverified_public_report', ...(category === 'government' ? ['government'] : []),
  ...(category === 'platform' ? ['platform_action'] : []),
  ...(['government','platform','company_official'].includes(category) ? ['authoritative_source'] : []),
];
type Props = {
  token: string; reviewer: boolean; request: (path: string, token: string, init?: RequestInit) => Promise<Response>;
  onNotice: (message: string) => void;
  useDialogFocus: (open: boolean, close: () => void) => React.RefObject<HTMLElement | null>;
};

export function EvidenceCorpus({token, reviewer, request, onNotice, useDialogFocus}: Props) {
  const [records, setRecords] = useState<CorpusRecord[] | null>(null);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('active');
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState(newRecord);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [loadError, setLoadError] = useState('');
  const [revision, setRevision] = useState(0);
  const [retiring, setRetiring] = useState<CorpusRecord | null>(null);
  const [reason, setReason] = useState('');
  const formTitle = useRef<HTMLHeadingElement>(null);
  const addButton = useRef<HTMLButtonElement>(null);
  const retireRef = useDialogFocus(!!retiring, () => { if (!busy) setRetiring(null); });
  useEffect(() => {
    let active = true;
    setLoadError('');
    request('/api/evidence-corpus', token).then(r => r.json()).then(data => { if (active) setRecords(data); })
      .catch(e => { if (active) setLoadError(e.message); });
    return () => { active = false; };
  }, [request, token, revision]);
  useEffect(() => { if (adding) formTitle.current?.focus(); }, [adding]);
  function toLibrary() { setAdding(false); setError(''); requestAnimationFrame(() => addButton.current?.focus()); }
  function field(key: keyof typeof newRecord, value: string) { setForm(f => ({...f, [key]: value})); }
  async function save(e: FormEvent) {
    e.preventDefault(); if (busy) return; setBusy(true); setError('');
    try {
      await request('/api/evidence-corpus', token, {method:'POST', body:JSON.stringify(form)});
      setForm(newRecord); setQuery(''); setStatus('active'); setRevision(v => v+1); toLibrary();
      onNotice('Source saved. New case checks can now match this identifier.');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function retire(e: FormEvent) {
    e.preventDefault(); if (!retiring || busy || reason.trim().length < 10) return;
    setBusy(true); setError('');
    try {
      const response = await request(`/api/evidence-corpus/${encodeURIComponent(retiring.record_id)}/retire`, token, {method:'POST',body:JSON.stringify({rationale:reason.trim()})});
      const result = await response.json(); setRevision(v => v+1); setRetiring(null);
      onNotice(`Source retired. ${result.affected_evidence_count} evidence item(s) flagged for review across ${result.affected_case_count} case(s).`);
    } catch(e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  const term = query.trim().toLowerCase();
  const visible = (records ?? []).filter(r => (status === 'all' || (status === 'active') === r.active) &&
    [r.source_name, r.record_id, r.normalized_value, r.claim, r.source_ref].some(s => s.toLowerCase().includes(term)));
  const requireRef = form.outcome === 'result' && ['government','platform_action','authoritative_source'].includes(form.authority);
  return <div className="ev-workspace">
    <PageHeader title="Evidence corpus" icon={Files} action={!adding && <button className="primary" ref={addButton} onClick={() => { setAdding(true); setError(''); }}><Plus size={17}/>Add source</button>}>Your source library. When a new case contains the same email, phone number or other identifier, Casework attaches the matching record.</PageHeader>
    {adding ? <section key="add-source" className="ev-panel">
      <button className="back-link" onClick={toLibrary} disabled={busy}><ArrowLeft size={14}/> Back to library</button>
      <h2 tabIndex={-1} ref={formTitle}>Add a source record</h2>
      <form onSubmit={save} className="ev-form">
        <fieldset><legend>What should Casework match?</legend><p>Copy the identifier exactly as it appears in the source.</p>
          <div className="ev-form-pair"><label>Identifier type<select value={form.entity_type} onChange={e => field('entity_type', e.target.value)}>{Object.keys(examples).map(k => <option key={k} value={k}>{displayLabel(k)}</option>)}</select></label>
          <label>Identifier value<input required minLength={2} maxLength={1000} value={form.value} placeholder={examples[form.entity_type]} onChange={e => field('value',e.target.value)}/></label></div></fieldset>
        <fieldset><legend>Where did you find it?</legend><div className="ev-form-pair">
          <label>Source name<input required minLength={2} maxLength={160} placeholder="Publisher or issuing organization" value={form.source_name} onChange={e => field('source_name',e.target.value)}/></label>
          <label>Source category<select value={form.source_type} onChange={e => { const category=e.target.value; setForm(f => ({...f,source_type:category,authority:authorityChoices(category).includes(f.authority) ? f.authority : 'curated'})); }}>{Object.entries(categories).map(([k,v]) => <option key={k} value={k}>{v}</option>)}</select></label></div>
          <label>Source URL or reference {requireRef ? '(required)' : '(optional)'}<input required={requireRef} maxLength={1000} placeholder="Link to the page or a traceable record number" value={form.source_ref} onChange={e => field('source_ref',e.target.value)}/></label>
        </fieldset>
        <fieldset><legend>What did the source say?</legend><div className="ev-form-pair"><label>Check outcome<select value={form.outcome} onChange={e => field('outcome',e.target.value)}>{['result','no_result','unavailable','error'].map(k => <option key={k} value={k}>{displayLabel(k)}</option>)}</select></label>
          <label>Source authority<select value={form.authority} onChange={e => field('authority',e.target.value)}>{authorityChoices(form.source_type).map(k => <option key={k} value={k}>{authorities[k]}</option>)}</select></label></div>
          <label>Finding in your own words<input required minLength={3} maxLength={1000} placeholder="For example, the careers page lists this recruitment email." value={form.claim} onChange={e => field('claim',e.target.value)}/></label>
          <label>Supporting excerpt (optional)<textarea rows={3} maxLength={10000} value={form.excerpt} onChange={e => field('excerpt',e.target.value)}/></label>
        </fieldset>
        {error && <p role="alert">{error}</p>}<div className="ev-actions"><button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save source record'}</button></div>
      </form></section> : <section key="library" className="ev-panel">
      <h2><BookOpen size={20}/> Source library</h2>
      <div className="ev-library-tools"><label className="ev-search"><Search size={16}/><input aria-label="Search source library" placeholder="Search by identifier, source or claim" type="search" value={query} onChange={e => setQuery(e.target.value)}/></label>
        <select aria-label="Record status" value={status} onChange={e => setStatus(e.target.value)}><option value="active">Active records</option><option value="retired">Retired records</option><option value="all">All records</option></select></div>
      {loadError ? <div className="ev-empty" role="alert">{loadError}<button className="secondary" onClick={() => setRevision(v => v+1)}>Try again</button></div>
      : !records ? <p role="status">Loading sources…</p> : <>
        <p className="ev-hint" role="status">{visible.length} {visible.length === 1 ? 'record' : 'records'}{records.length === 500 && ' · searching the latest 500'}</p>
        {!visible.length && <div className="ev-empty"><BookOpen/><h3>{records.length ? 'No matching sources' : 'Your source library is empty'}</h3>
          <p>{records.length ? 'Try another identifier or change the record status.' : 'Start with an employer notice or another source you can cite, then choose Add source.'}</p>{!!records.length && <button className="secondary" onClick={() => {setQuery('');setStatus('all');}}>Show all records</button>}</div>}
        {visible.map(r => <details className="ev-record" key={r.record_id}><summary><FileText/><span><strong>{r.source_name}</strong><small>{r.claim}</small></span><span className="ev-chip">{r.active ? 'Active' : 'Retired'}</span><ChevronDown/></summary>
          <dl><dt>Identifier</dt><dd>{displayLabel(r.entity_type)} · {r.normalized_value}</dd><dt>Check outcome</dt><dd>{displayLabel(r.outcome)}</dd><dt>Source</dt><dd>{categories[r.source_type] || displayLabel(r.source_type)} · {authorities[r.authority] || displayLabel(r.authority)}</dd>
            <dt>Reference</dt><dd>{r.source_ref || 'No reference recorded'}</dd><dt>Recorded</dt><dd>{new Date(r.retrieved_at).toLocaleString()} · {r.record_id}</dd>
            {r.excerpt && <><dt>Excerpt</dt><dd>{r.excerpt}</dd></>}{!r.active && <><dt>Retirement</dt><dd>{r.retired_at && new Date(r.retired_at).toLocaleString()} · {r.retirement_reason}</dd></>}</dl>
          {reviewer && r.active && <button className="secondary" onClick={() => {setRetiring(r);setReason('');setError('');}}>Retire source record</button>}</details>)}</>}
    </section>}
    <DialogTransition>{retiring && <div className="modal-backdrop"><section role="dialog" aria-modal="true" aria-labelledby="ev-retire-title" ref={retireRef} tabIndex={-1} className="modal">
      <h2 id="ev-retire-title">Retire {retiring.source_name}?</h2><p>Future checks will skip this record. Existing matches will be flagged for review and their findings recalculated.</p>
      <form onSubmit={retire}><label>Reason for retirement<textarea required minLength={10} maxLength={2000} value={reason} onChange={e => setReason(e.target.value)}/></label>
      {error && <p role="alert">{error}</p>}<footer><button type="button" className="secondary" disabled={busy} onClick={() => setRetiring(null)}>Cancel</button>
      <button className="primary" disabled={busy || reason.trim().length < 10}>Retire record</button></footer></form></section></div>}</DialogTransition>
  </div>;
}
