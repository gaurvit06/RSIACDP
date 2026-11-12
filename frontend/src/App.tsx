import { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, ArrowDownToLine, BriefcaseBusiness, Check, ChevronRight, CircleHelp, Clock3, FileSearch, FileText, Fingerprint, LayoutDashboard, LogOut, Plus, Search, ShieldCheck, Upload, UsersRound, X } from 'lucide-react';
import { redactSelectedText } from './text-redaction';
import { canApproveDisposition, correctionApplyValid, correctionCaseChangeOpen, correctionEvidenceActions, correctionReviewValid, retainEligibleEvidenceIds } from './review-rules';
import { filterGraphData, graphNodeReviewLabel, type GraphEdge, type GraphNode } from './graph-filters';
import { clearExpiredSession, shouldExpireSession } from './auth-session';
import { evidenceModeLabel, type EvidenceMode } from './evidence-mode';

const API = import.meta.env.VITE_API_URL ?? '';
type User = { id: number; email: string; role: string };
type Entity = { id: number; type: string; value: string; normalized: string; excerpt: string; source_location: string; source_start_char: number | null; source_end_char: number | null; extraction_confidence: number | null; extraction_uncertainty: string; review_status: string };
type Evidence = { id: number; source_name: string; source_type: string; source_ref: string; claim: string; outcome: string; excerpt: string; authority: string; retrieved_at: string; details?: Record<string, unknown>; review_status: string; review_reason: string; reviewed_at: string | null };
type CorpusRecord = { record_id: string; entity_type: string; normalized_value: string; source_name: string; source_type: string; source_ref: string; claim: string; outcome: string; excerpt: string; authority: string; retrieved_at: string; active: boolean; retired_at: string | null; retirement_reason: string };
type SystemFinding = { id: number; entity_id: number | null; scope: string; claim: string; assessment: string; observation: string; evidence_ids: number[]; evidence_snapshot: { evidence_id: number; source_name: string; source_type: string; source_ref: string; claim: string; outcome: string; authority: string; retrieved_at: string }[]; conflict_evidence_ids: number[]; unreviewed_evidence_ids: number[]; supporting_evidence_ids: number[]; rule_name: string; rule_version: string; limitations: string; created_at: string };
type HumanDisposition = { id: number; disposition: string; display_label?: string; rationale: string; evidence_ids: number[]; status: string; review_rationale: string; created_at: string; reviewed_at: string | null; case_ref?: string; case_title?: string; proposer_id?: number; evidence?: Evidence[] };
type Case = { id: number; case_ref: string; title: string; input_kind: string; status: string; assessment: string; created_at: string; entities: Entity[]; evidence: Evidence[]; human_dispositions?: HumanDisposition[]; findings?: SystemFinding[]; submitted_text?: string; timeline?: { action: string; created_at: string; detail: Record<string, unknown> }[]; links?: { id: number; left_case_id: number; right_case_id: number; strength: number; reasons: string[]; review_status: string; rule_version: string }[]; processing?: { status: string; attempts: number; error: string } };
type CampaignGroup = { campaign_ref: string; classification: string; case_count: number; strength: number; rule_versions: string[]; review_statuses: string[]; note: string; cases: { id: number; case_ref: string; title: string; assessment: string; created_at: string }[]; links: { left_case_id: number; right_case_id: number; strength: number; reasons: string[]; review_status: string; rule_version: string; matched_entities: (Entity & { case_id: number })[]; related_evidence: Evidence[]; empty_or_failed_checks: Evidence[] }[] };
const DISPOSITION_LABELS: Record<string, string> = { confirmed_authoritative: 'Confirmed by an authoritative source', evidence_supports_concern: 'Evidence supports concern', insufficient_evidence: 'Insufficient evidence', no_adverse_evidence: 'No adverse evidence found' };

async function request(path: string, token: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (!['GET', 'HEAD', 'OPTIONS'].includes((init.method || 'GET').toUpperCase()) && token) headers.set('X-CSRF-Token', token);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${API}${path}`, { ...init, headers, credentials: 'include' });
  if (shouldExpireSession(response.status, path)) window.dispatchEvent(new Event('casework:unauthorized'));
  if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(apiErrorMessage(data.detail, `Request failed (${response.status})`)); }
  return response;
}

function apiErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const issues = detail.map(issue => {
      if (!issue || typeof issue !== 'object') return '';
      const item = issue as { loc?: unknown; msg?: unknown };
      const location = Array.isArray(item.loc) ? item.loc.filter(part => part !== 'body').join('.') : '';
      const message = typeof item.msg === 'string' ? item.msg : 'Invalid request';
      return location ? `${location}: ${message}` : message;
    }).filter(Boolean);
    if (issues.length) return issues.join('; ');
  }
  if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') return detail.message;
  return fallback;
}

function formatSourceLocation(location: string): string {
  const region = /^(image|pdf_page_(\d+))_ocrpx_(\d+)_(\d+)_(\d+)_(\d+)$/.exec(location);
  if (region) {
    const source = region[1] === 'image' ? 'Image OCR' : `PDF page ${region[2]} OCR`;
    return `${source} region · x ${region[3]}, y ${region[4]}, width ${region[5]}, height ${region[6]} px`;
  }
  if (location === 'image_ocr_text') return 'Image OCR text';
  if (location === 'submitted_text') return 'Submitted text';
  const page = /^pdf_page_(\d+)$/.exec(location);
  return page ? `PDF page ${page[1]}` : location;
}

function useDialogFocus(open: boolean, onClose: () => void) {
  const dialogRef = useRef<HTMLElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    const focusable = () => dialog?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])');
    const initial = focusable()?.[0] ?? dialog;
    initial?.focus();
    const handleKeys = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeRef.current();
        return;
      }
      if (event.key !== 'Tab' || !dialog) return;
      const items = focusable();
      if (!items?.length) {
        event.preventDefault();
        dialog.focus();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (!dialog.contains(document.activeElement)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener('keydown', handleKeys);
    return () => {
      window.removeEventListener('keydown', handleKeys);
      previouslyFocused?.focus();
    };
  }, [open]);
  return dialogRef;
}

export default function App() {
  const [token, setToken] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [cases, setCases] = useState<Case[]>([]);
  const [selected, setSelected] = useState<Case | null>(null);
  const [section, setSection] = useState('Cases');
  const [query, setQuery] = useState('');
  const [modal, setModal] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const helpTriggerRef = useRef<HTMLButtonElement>(null);
  const helpDialogRef = useRef<HTMLElement>(null);
  const helpCloseRef = useRef<HTMLButtonElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [consentPolicy, setConsentPolicy] = useState({ consent_version: 'consent-v2', retention_days: 180, max_upload_bytes: 10485760, allowed_upload_media_types: ['image/png', 'image/jpeg', 'image/webp', 'application/pdf'], rdap_enabled: false, rdap_disclosure: 'External RDAP lookups are disabled. Evidence checks use the configured local corpus only.', campaign_rule_version: 'campaign-signals-v3-threshold-40', campaign_link_threshold: 40, campaign_signal_weights: { phone: 40, email: 40, upi_id: 40, bank_account: 40, url: 25, domain: 15 } });
  const [sourceMode, setSourceMode] = useState<EvidenceMode>('loading');

  async function loadCases(auth = token) {
    const response = await request('/api/cases', auth);
    setCases(await response.json());
  }
  async function loadCase(id: number, auth = token) {
    const response = await request(`/api/cases/${id}`, auth);
    setSelected(await response.json());
  }
  useEffect(() => {
    let stopped = false;
    fetch(`${API}/api/auth/me`, { credentials: 'include' }).then(async response => {
      if (response.status === 401) return null;
      const data = await response.json();
      if (!response.ok) throw new Error(apiErrorMessage(data.detail, 'Could not restore the session'));
      return data as User & { csrf_token: string };
    }).then(async session => {
      if (!session || stopped) return;
      setToken(session.csrf_token || ''); setUser(session);
      await loadCases(session.csrf_token || '');
    }).catch(error => { if (!stopped) setError((error as Error).message); })
      .finally(() => { if (!stopped) setSessionLoading(false); });
    return () => { stopped = true; };
  }, []);
  useEffect(() => {
    const expireSession = () => {
      clearExpiredSession(() => {
        setToken(''); setUser(null); setCases([]); setSelected(null);
        setError('Your session has expired or was revoked. Sign in again.');
      });
    };
    window.addEventListener('casework:unauthorized', expireSession);
    return () => window.removeEventListener('casework:unauthorized', expireSession);
  }, []);
  useEffect(() => {
    if (!helpOpen) return;
    helpCloseRef.current?.focus();
    const handleDialogKeys = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setHelpOpen(false);
        helpTriggerRef.current?.focus();
        return;
      }
      if (event.key !== 'Tab') return;
      const focusable = helpDialogRef.current?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])');
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!helpDialogRef.current?.contains(document.activeElement)) {
        event.preventDefault();
        first.focus();
      } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener('keydown', handleDialogKeys);
    return () => window.removeEventListener('keydown', handleDialogKeys);
  }, [helpOpen]);
  useEffect(() => { fetch(`${API}/api/policy`).then(r => { if (!r.ok) throw new Error('Policy request failed'); return r.json(); }).then(policy => { setConsentPolicy(policy); setSourceMode(policy.rdap_enabled ? 'rdap' : 'local'); }).catch(() => setSourceMode('unavailable')); }, []);
  const pendingCaseIds = cases.filter(item => ['queued', 'processing'].includes(item.status)).map(item => item.id).join(',');
  useEffect(() => {
    if (!token || !pendingCaseIds) return;
    let stopped = false;
    let inFlight = false;
    const poll = async () => {
      if (inFlight || stopped) return;
      inFlight = true;
      try {
        const response = await request('/api/processing-status', token);
        const { items } = await response.json() as { items: { case_id: number; case_status: string; status: string; attempts: number; error: string | null }[] };
        if (stopped) return;
        const byCase = new Map(items.map(item => [item.case_id, item]));
        setCases(current => current.map(item => {
          const status = byCase.get(item.id);
          return status ? { ...item, status: status.case_status } : item;
        }));
        const completedPendingCase = cases.some(item => ['queued', 'processing'].includes(item.status) && !['queued', 'processing'].includes(byCase.get(item.id)?.case_status || item.status));
        if (completedPendingCase) {
          await loadCases();
          if (selected && ['queued', 'processing'].includes(selected.status) && !['queued', 'processing'].includes(byCase.get(selected.id)?.case_status || selected.status)) {
            await loadCase(selected.id);
          }
        }
      } catch {
        // Keep showing the last known processing state and retry on the next interval.
      } finally {
        inFlight = false;
      }
    };
    void poll();
    const timer = window.setInterval(() => { void poll(); }, 1500);
    return () => { stopped = true; window.clearInterval(timer); };
  }, [token, pendingCaseIds, selected?.id, selected?.status]);
  async function logout() {
    if (user) { try { await request('/api/auth/logout', token, { method: 'POST' }); } catch { /* Clear local state even if the server has already revoked or expired this session. */ } }
    setToken(''); setUser(null); setCases([]); setSelected(null);
  }
  async function login(email: string, password: string, create: boolean, setupCode: string) {
    setBusy(true); setError('');
    try {
      const response = await fetch(`${API}/api/auth/${create ? 'register' : 'login'}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ email, password, setup_code: setupCode, session_mode: 'cookie' }) });
      const data = await response.json(); if (!response.ok) throw new Error(apiErrorMessage(data.detail, 'Could not sign in'));
      setToken(data.csrf_token || ''); setUser(data.user); await loadCases(data.csrf_token || '');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function createCase(form: { title: string; kind: string; text: string; rdapConsent: boolean }) {
    setBusy(true); setError('');
    try {
      const response = await request('/api/cases', token, { method: 'POST', body: JSON.stringify({ title: form.title, input_kind: form.kind, submitted_text: form.text, consent_version: consentPolicy.consent_version, consent: true, rdap_consent: form.rdapConsent }) });
      const result = await response.json(); await loadCases(); await loadCase(result.id); setSection('Cases'); setModal(false); setNotice('Case submitted. The background worker will extract identifiers and check the local evidence corpus.');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function uploadCase(title: string, file: File, rdapConsent: boolean) {
    setBusy(true); setError('');
    try {
      const form = new FormData(); form.set('title', title); form.set('consent_version', consentPolicy.consent_version); form.set('consent', 'true'); form.set('rdap_consent', String(rdapConsent)); form.set('file', file);
      const response = await request('/api/cases/upload', token, { method: 'POST', body: form }); const result = await response.json();
      await loadCases(); await loadCase(result.id); setSection('Cases'); setModal(false); setNotice('Private upload received. The background worker will extract text and update this case.');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function updateEntity(caseId: number, entityId: number, status: string) {
    try { await request(`/api/cases/${caseId}/entities/${entityId}/review`, token, { method: 'POST', body: JSON.stringify({ status, rationale: `Investigator marked entity ${status}.` }) }); await loadCase(caseId); }
    catch (e) { setError((e as Error).message); }
  }
  async function updateEvidence(caseId: number, evidenceId: number, status: string, rationale: string) {
    try { await request(`/api/cases/${caseId}/evidence/${evidenceId}/review`, token, { method: 'POST', body: JSON.stringify({ status, rationale }) }); await loadCase(caseId); }
    catch (e) { setError((e as Error).message); throw e; }
  }
  async function submitDisposition(caseId: number, disposition: string, evidenceIds: number[], rationale: string) {
    try { const response = await request(`/api/cases/${caseId}/disposition`, token, { method: 'POST', body: JSON.stringify({ disposition, evidence_ids: evidenceIds, rationale }) }); const result = await response.json(); await loadCase(caseId); setNotice(result.status === 'pending_review' ? 'Human disposition submitted for separate reviewer approval. System assessment remains unchanged.' : 'Human disposition recorded separately from system assessment.'); }
    catch (e) { setError((e as Error).message); }
  }
  async function refreshLinks(caseId: number) {
    try { await request(`/api/cases/${caseId}/link/refresh`, token, { method: 'POST' }); await loadCase(caseId); setNotice('Exact identifier links recomputed. Review them as leads, not proof.'); }
    catch (e) { setError((e as Error).message); }
  }
  async function retryProcessing(caseId: number) {
    try { await request(`/api/cases/${caseId}/retry-processing`, token, { method: 'POST' }); await loadCase(caseId); setNotice('Processing was queued again.'); }
    catch (e) { setError((e as Error).message); }
  }
  async function reviewLink(caseId: number, linkId: number, status: string) {
    try { await request(`/api/cases/${caseId}/links/${linkId}/review`, token, { method: 'POST', body: JSON.stringify({ status, rationale: `Investigator marked the proposed case link ${status}.` }) }); await loadCase(caseId); await loadCases(); }
    catch (e) { setError((e as Error).message); }
  }
  async function downloadReport(caseId: number, format: 'json' | 'markdown') {
    try { const response = await request(`/api/cases/${caseId}/report?format=${format}`, token); const blob = await response.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${selected?.case_ref || 'case'}-report.${format === 'markdown' ? 'md' : 'json'}`; a.click(); URL.revokeObjectURL(url); }
    catch (e) { setError((e as Error).message); }
  }
  function closeHelp() {
    setHelpOpen(false);
    helpTriggerRef.current?.focus();
  }
  const filteredCases = useMemo(() => cases.filter(c => `${c.case_ref} ${c.title} ${c.assessment}`.toLowerCase().includes(query.toLowerCase())), [cases, query]);
  const navEntries: [string, any][] = [['Cases', BriefcaseBusiness], ['Campaigns', UsersRound]];
  if (['investigator', 'reviewer', 'admin'].includes(user?.role || '')) navEntries.push(['Evidence graph', LayoutDashboard], ['Evidence corpus', FileText], ['Corrections', Clock3]);
  if (['reviewer', 'admin'].includes(user?.role || '')) navEntries.push(['Disposition reviews', ShieldCheck], ['Accounts', UsersRound]);
  if (sessionLoading) return <div className="session-loading" role="status">Restoring your secure session…</div>;
  if (!token || !user) return <><AuthScreen onSubmit={login} busy={busy} error={error} /><CorrectionAccess /></>;

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Fingerprint size={21}/></div><div><b>CASEWORK</b><span>INVESTIGATION DESK</span></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav>{navEntries.map(([label, Icon]) => <button key={label} className={`nav-item ${section === label ? 'active' : ''}`} onClick={() => { setSection(label); setSelected(null); }}><Icon size={17}/><span>{label}</span>{label === 'Cases' && <small>{cases.length}</small>}</button>)}</nav>
      <div className="sidebar-foot"><div className="privacy-chip"><ShieldCheck size={15}/><span>Private workspace</span></div><div className="user-chip"><div className="avatar">{user.email.slice(0,1).toUpperCase()}</div><div className="user-label"><b>{user.email}</b><span>{user.role}</span></div><button aria-label="Sign out" onClick={logout}><LogOut size={16}/></button></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="crumb">CASEWORK <ChevronRight size={13}/> <span>{selected ? selected.case_ref : section.toUpperCase()}</span></div><div className="top-actions"><span className="system-status"><i/> {evidenceModeLabel(sourceMode)}</span><button ref={helpTriggerRef} className="icon-button" type="button" title="Help and workflow guide" aria-label="Help and workflow guide" aria-haspopup="dialog" aria-expanded={helpOpen} onClick={() => setHelpOpen(true)}><CircleHelp size={18}/></button></div></header>
      <div className="content">
        {error && <div className="alert error"><AlertTriangle size={17}/>{error}<button onClick={() => setError('')}><X size={15}/></button></div>}
        {notice && <div className="alert success"><Check size={17}/>{notice}<button onClick={() => setNotice('')}><X size={15}/></button></div>}
        {!selected && section === 'Cases' && <>
          <div className="page-heading"><div><div className="eyebrow">INVESTIGATION QUEUE</div><h1>Recruitment cases</h1><p>Review submitted offers, trace evidence, and inspect repeated identifiers.</p></div><button className="primary" onClick={() => setModal(true)}><Plus size={17}/> New case</button></div>
          <div className="metric-row"><Metric label="Open cases" value={cases.filter(c => c.status !== 'completed').length.toString().padStart(2, '0')} icon={<FileSearch/>}/><Metric label="Cases received" value={cases.length.toString().padStart(2, '0')} icon={<BriefcaseBusiness/>}/><Metric label="Needs review" value={cases.filter(c => c.entities.some(e => e.review_status === 'needs_review')).length.toString().padStart(2, '0')} icon={<Clock3/>}/><div className="metric-note"><ShieldCheck size={16}/><span>Findings are evidence leads.<br/><b>They are not proof of wrongdoing.</b></span></div></div>
          <div className="list-card"><div className="list-toolbar"><div><h2>Recent cases</h2><span>{filteredCases.length} records</span></div><label className="search"><Search size={16}/><input placeholder="Search case reference or title" value={query} onChange={e => setQuery(e.target.value)}/></label></div>
            {filteredCases.length ? <div className="table-wrap"><table><thead><tr><th>CASE</th><th>INPUT</th><th>IDENTIFIERS</th><th>SYSTEM ASSESSMENT</th><th>STATUS</th><th>RECEIVED</th><th></th></tr></thead><tbody>{filteredCases.map(c => <tr key={c.id} onClick={() => loadCase(c.id)}><td><b className="case-ref">{c.case_ref}</b><span className="cell-title">{c.title}</span></td><td><span className="tag">{c.input_kind}</span></td><td>{c.entities.length} extracted</td><td><Assessment>{c.assessment}</Assessment></td><td><span className="status"><i className={c.status}/>{c.status.replace('_',' ')}</span></td><td>{new Date(c.created_at).toLocaleDateString()}</td><td><ChevronRight size={16}/></td></tr>)}</tbody></table></div> : <Empty onCreate={() => setModal(true)}/>}</div>
          <div className="footnote"><span><ShieldCheck size={14}/> No adverse evidence found is not proof of legitimacy.</span><span>Evidence access and review actions are audited.</span></div>
        </>}
        {selected && <CaseDetail item={selected} investigator={['investigator','reviewer','admin'].includes(user.role)} onBack={() => setSelected(null)} onRefresh={() => refreshLinks(selected.id)} onDownload={format => downloadReport(selected.id, format)} onRetry={() => retryProcessing(selected.id)} onReview={(id, status) => updateEntity(selected.id, id, status)} onReviewEvidence={(id, status, rationale) => updateEvidence(selected.id, id, status, rationale)} onReviewLink={(id, status) => reviewLink(selected.id, id, status)} />}
        {selected && <CaseActions item={selected} investigator={['investigator','reviewer','admin'].includes(user.role)} onRetry={() => retryProcessing(selected.id)} onReviewLink={(id, status) => reviewLink(selected.id, id, status)}/>}
        {selected && ['investigator','reviewer','admin'].includes(user.role) && <HumanDispositionPanel item={selected} onSubmit={(kind, ids, rationale) => submitDisposition(selected.id, kind, ids, rationale)}/>}
        {!selected && section === 'Campaigns' && <Campaigns token={token} onOpen={id => loadCase(id)} ruleVersion={consentPolicy.campaign_rule_version} threshold={consentPolicy.campaign_link_threshold} weights={consentPolicy.campaign_signal_weights}/>}
        {!selected && section === 'Evidence graph' && <Graph token={token} onOpenCase={id => loadCase(id)}/>}
        {!selected && section === 'Evidence corpus' && <EvidenceCorpus token={token} reviewer={['reviewer','admin'].includes(user.role)} onError={setError} onNotice={setNotice}/>}
        {!selected && section === 'Corrections' && <CorrectionQueue token={token} onError={setError} onNotice={setNotice}/>}
        {!selected && section === 'Disposition reviews' && <DispositionReviewQueue token={token} currentUserId={user.id} onError={setError} onNotice={setNotice}/>}
        {!selected && section === 'Accounts' && <AccountManagement token={token} currentUserId={user.id} onError={setError} onNotice={setNotice}/>}
      </div>
    </main>
    {helpOpen && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && closeHelp()}><section ref={helpDialogRef} className="modal help-modal" role="dialog" aria-modal="true" aria-labelledby="workflow-help-title"><header><div><div className="eyebrow">CASEWORK GUIDE</div><h2 id="workflow-help-title">Investigate with traceable evidence</h2></div><button ref={helpCloseRef} className="icon-button" type="button" aria-label="Close workflow guide" onClick={closeHelp}><X size={18}/></button></header><div className="modal-intro"><p><b>1. Submit the offer.</b> Start a case with text or a supported file. Review the consent notice, remove unrelated personal details where possible, and submit only material you are authorized to share.</p><p><b>2. Review extraction.</b> Processing identifies candidate companies, roles, contact details, payment requests and source locations. Confirm, correct or reject each candidate; an extracted value is not verified just because it was detected.</p><p><b>3. Inspect evidence.</b> Open each source result to see its source, retrieval time, outcome and excerpt. Empty, failed or unavailable checks do not establish fraud or legitimacy. Mark evidence relevant or irrelevant with a reason.</p><p><b>4. Review case links.</b> Reused identifiers and linked cases are investigative leads. Similar wording or a shared domain alone does not prove a campaign or wrongdoing.</p><p><b>5. Share carefully.</b> Downloadable reports mask personal identifiers by default. Machine assessments remain separate from investigator dispositions; a stronger human disposition requires supporting evidence and reviewer approval.</p><p><b>6. Request a correction.</b> Use “Request a correction” on the sign-in page to ask for a record to be reviewed. Save the one-time status token shown after submission.</p><p className="help-safety-note"><ShieldCheck size={15}/> The system never determines that a person is a scammer. “Confirmed by an authoritative source” applies only to the specific claim supported by verifiable source evidence.</p></div><footer><button className="primary" type="button" onClick={closeHelp}>Close guide</button></footer></section></div>}
    {modal && <NewCase onClose={() => setModal(false)} onSubmit={createCase} onUpload={uploadCase} busy={busy} retentionDays={consentPolicy.retention_days} maxUploadBytes={consentPolicy.max_upload_bytes} allowedUploadTypes={consentPolicy.allowed_upload_media_types} rdapEnabled={consentPolicy.rdap_enabled} rdapDisclosure={consentPolicy.rdap_disclosure}/>}
  </div>;
}

function Metric({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) { return <div className="metric"><div className="metric-icon">{icon}</div><div><span>{label}</span><b>{value}</b></div></div>; }
function Assessment({ children }: { children: string }) { return <span className="assessment"><i/>{children}</span>; }
function Empty({ onCreate }: { onCreate: () => void }) { return <div className="empty"><div className="empty-icon"><FileSearch size={23}/></div><h3>No cases yet</h3><p>Submit a suspicious recruitment offer to begin an evidence-led investigation.</p><button className="secondary" onClick={onCreate}><Plus size={15}/> Create first case</button></div>; }

function AuthScreen({ onSubmit, busy, error }: { onSubmit: (email: string, password: string, create: boolean, setupCode: string) => void; busy: boolean; error: string }) {
  const [create, setCreate] = useState(false);
  const [resetMode, setResetMode] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [setupCode, setSetupCode] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [resetPassword, setResetPassword] = useState('');
  const [resetBusy, setResetBusy] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetNotice, setResetNotice] = useState('');
  async function submitReset(event: React.FormEvent) {
    event.preventDefault(); setResetBusy(true); setResetError(''); setResetNotice('');
    try {
      const response = await fetch(`${API}/api/auth/reset-password`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token: resetToken, new_password: resetPassword }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(apiErrorMessage(data.detail, 'Could not reset password'));
      setResetNotice(data.sign_in_message || 'Password updated. Sign in with the new password.');
      setResetToken(''); setResetPassword(''); setResetMode(false); setCreate(false);
    } catch (e) { setResetError((e as Error).message); }
    finally { setResetBusy(false); }
  }
  return <div className="auth-screen"><div className="auth-card"><div className="brand auth-brand"><div className="brand-mark"><Fingerprint size={22}/></div><div><b>CASEWORK</b><span>INVESTIGATION DESK</span></div></div><div className="eyebrow">SECURE CASE MANAGEMENT</div>{resetMode ? <><h1>Set a new password</h1><p>Enter the one-time reset token supplied through your verified recovery channel.</p>{resetError && <div className="alert error">{resetError}</div>}{resetNotice && <div className="alert success">{resetNotice}</div>}<form onSubmit={submitReset}><label>One-time reset token<input required minLength={32} maxLength={128} value={resetToken} onChange={e => setResetToken(e.target.value)} autoComplete="one-time-code"/></label><label>New password<input type="password" required minLength={12} maxLength={128} value={resetPassword} onChange={e => setResetPassword(e.target.value)} autoComplete="new-password"/><small>Use at least 12 characters.</small></label><button className="primary full" disabled={resetBusy}>{resetBusy ? 'Updating…' : 'Update password'}</button></form><div className="auth-switch"><button onClick={() => { setResetMode(false); setResetError(''); }}>Back to sign in</button></div></> : <><h1>{create ? 'Create your account' : 'Welcome back'}</h1><p>Sign in to review recruitment evidence and case links.</p>{error && <div className="alert error">{error}</div>}{resetNotice && <div className="alert success">{resetNotice}</div>}<form onSubmit={e => { e.preventDefault(); onSubmit(email, password, create, setupCode); }}><label>Email address<input type="email" required value={email} onChange={e => setEmail(e.target.value)} autoComplete="email"/></label><label>Password<input type="password" required minLength={create ? 12 : 1} value={password} onChange={e => setPassword(e.target.value)} autoComplete={create ? 'new-password' : 'current-password'}/>{create && <small>Use at least 12 characters.</small>}</label>{create && <label>Investigator or reviewer setup code (optional)<input type="password" maxLength={200} value={setupCode} onChange={e => setSetupCode(e.target.value)} autoComplete="one-time-code"/><small>Leave blank for an analyst account. Enter a one-time code supplied by the deployment operator for an investigator or reviewer account.</small></label>}<button className="primary full" disabled={busy}>{busy ? 'Please wait…' : create ? 'Create account' : 'Sign in'}</button></form><div className="auth-switch">{create ? 'Already registered?' : 'New to the workspace?'} <button onClick={() => { setCreate(!create); setResetNotice(''); }}>{create ? 'Sign in' : 'Create an account'}</button></div>{!create && <div className="auth-switch"><button onClick={() => { setResetMode(true); setResetError(''); setResetNotice(''); }}>Have a one-time reset token?</button></div>}</>}<div className="auth-note"><ShieldCheck size={15}/> Private workspace. Access is logged.</div></div><div className="auth-side"><div className="side-content"><div className="eyebrow">EVIDENCE BEFORE CONCLUSIONS</div><h2>Investigate the connections behind a job offer.</h2><p>Trace identifiers to their sources. Review repeated patterns. Keep every finding open to inspection.</p><div className="side-points"><span><Check size={15}/> Traceable evidence</span><span><Check size={15}/> Reviewable case links</span><span><Check size={15}/> Privacy-aware reporting</span></div></div><div className="side-bottom">A casework system for investigative leads, not automated accusations.</div></div></div>;
}

function NewCase({ onClose, onSubmit, onUpload, busy, retentionDays, maxUploadBytes, allowedUploadTypes, rdapEnabled, rdapDisclosure }: { onClose: () => void; onSubmit: (f: { title: string; kind: string; text: string; rdapConsent: boolean }) => void; onUpload: (title: string, file: File, rdapConsent: boolean) => void; busy: boolean; retentionDays: number; maxUploadBytes: number; allowedUploadTypes: string[]; rdapEnabled: boolean; rdapDisclosure: string }) {
  const [title, setTitle] = useState('');
  const [kind, setKind] = useState('message');
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState('');
  const [consent, setConsent] = useState(false);
  const [rdapConsent, setRdapConsent] = useState(false);
  const [selectedRange, setSelectedRange] = useState<{ start: number; end: number } | null>(null);
  const dialogRef = useDialogFocus(true, () => { if (!busy) onClose(); });

  function selectFile(candidate?: File) {
    setFileError('');
    if (!candidate) { setFile(null); return; }
    if (!allowedUploadTypes.includes(candidate.type)) { setFile(null); setFileError('Choose a PNG, JPEG, WEBP, or PDF file.'); return; }
    if (candidate.size > maxUploadBytes) { setFile(null); setFileError(`This file is larger than the ${formatBytes(maxUploadBytes)} upload limit.`); return; }
    setFile(candidate);
  }
  function redactSelection() {
    if (!selectedRange || selectedRange.start >= selectedRange.end) return;
    setText(current => redactSelectedText(current, selectedRange.start, selectedRange.end));
    setSelectedRange(null);
  }

  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
    <section ref={dialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="new-case-title" tabIndex={-1}>
      <header><div><div className="eyebrow">NEW INVESTIGATION</div><h2 id="new-case-title">Submit a recruitment case</h2></div><button type="button" className="icon-button" aria-label="Close case submission" disabled={busy} onClick={onClose}><X size={18}/></button></header>
      <p className="modal-intro">Submit the material you received. Extracted identifiers are candidates for investigator review, not findings of wrongdoing.</p>
      <form onSubmit={e => { e.preventDefault(); if (!consent || (rdapEnabled && !rdapConsent) || fileError) return; file ? onUpload(title, file, rdapConsent) : onSubmit({ title, kind, text, rdapConsent }); }}>
        <label>Case title<input required minLength={3} maxLength={240} placeholder="e.g. Remote data entry offer via messaging app" value={title} onChange={e => setTitle(e.target.value)}/></label>
        <div className="field-row">
          <label>Material type<select value={kind} onChange={e => setKind(e.target.value)}><option value="message">Message</option><option value="email">Email</option><option value="url">Job posting URL</option><option value="text">Other text</option></select></label>
          <label>Attach screenshot or PDF<input type="file" accept={allowedUploadTypes.join(',')} onChange={e => selectFile(e.target.files?.[0])}/><small>Maximum {formatBytes(maxUploadBytes)}. Text extraction runs in the background.</small></label>
        </div>
        {fileError && <div className="alert error" role="alert">{fileError}<button type="button" aria-label="Dismiss upload error" onClick={() => setFileError('')}><X size={14}/></button></div>}
        {!file && <>
          <label htmlFor="case-submission-text">Paste the offer or message<textarea id="case-submission-text" required minLength={1} maxLength={100000} rows={7} placeholder="Include the text as received. Remove or redact details you do not wish to submit." value={text} onSelect={event => { const start = event.currentTarget.selectionStart; const end = event.currentTarget.selectionEnd; setSelectedRange(start < end ? { start, end } : null); }} onChange={e => { setText(e.target.value); setSelectedRange(null); }}/></label>
          <div className="redact-actions"><small>Select sensitive text, then replace it before submission. Redacted text will not be available for extraction.</small><button type="button" className="secondary" disabled={!selectedRange} onClick={redactSelection}>Redact selected text</button></div>
        </>}
        {file && <div className="file-chip"><FileText size={16}/>{file.name} · {formatBytes(file.size)}<button type="button" aria-label="Remove selected file" onClick={() => selectFile()}><X size={14}/></button></div>}
        <label className="consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/><span>I consent to use this material for investigation. The submission, extracted identifiers, evidence and review history are stored for the case. Signed-in workspace users can access it; contact identifiers are masked for analysts and downloads. Case records and original uploads are deleted after {retentionDays} days.</span></label>
        {rdapEnabled && <><p className="modal-intro">{rdapDisclosure}</p><label className="consent"><input type="checkbox" checked={rdapConsent} onChange={e => setRdapConsent(e.target.checked)}/><span>I separately consent to sending extracted domain names to the corresponding public RDAP registry for registration metadata checks. This does not send the submitted text, complete URLs, email addresses, or other identifiers.</span></label></>}
        <div className="modal-warning"><AlertTriangle size={15}/> A match or repeated identifier is an investigative lead, not proof of wrongdoing.</div>
        <footer><button className="secondary" type="button" onClick={onClose}>Cancel</button><button className="primary" disabled={!consent || (rdapEnabled && !rdapConsent) || busy || Boolean(fileError)}>{busy ? 'Submitting…' : <><Upload size={15}/> Submit case</>}</button></footer>
      </form>
    </section>
  </div>;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(bytes % (1024 * 1024) === 0 ? 0 : 1)} MB`;
}

function CaseDetail({ item, investigator, onBack, onRefresh, onDownload, onReview, onReviewEvidence, onRetry, onReviewLink }: { item: Case; investigator: boolean; onBack: () => void; onRefresh: () => void; onDownload: (format: 'json' | 'markdown') => void; onReview: (id: number, status: string) => void; onReviewEvidence: (id: number, status: string, rationale: string) => Promise<void>; onRetry: () => void; onReviewLink: (id: number, status: string) => void }) {
  const [evidenceReview, setEvidenceReview] = useState<{ id: number; status: string } | null>(null);
  const [evidenceRationale, setEvidenceRationale] = useState('');
  const [evidenceReviewBusy, setEvidenceReviewBusy] = useState(false);
  const evidenceDialogRef = useDialogFocus(Boolean(evidenceReview), () => { if (!evidenceReviewBusy) setEvidenceReview(null); });
  async function submitEvidenceReview(event: React.FormEvent) {
    event.preventDefault();
    if (!evidenceReview || evidenceRationale.trim().length < 10) return;
    setEvidenceReviewBusy(true);
    try {
      await onReviewEvidence(evidenceReview.id, evidenceReview.status, evidenceRationale.trim());
      setEvidenceReview(null);
      setEvidenceRationale('');
    } catch { /* The page-level alert reports the API error; keep the dialog available for correction or retry. */ }
    finally { setEvidenceReviewBusy(false); }
  }
  return <><button className="back-link" onClick={onBack}>← All cases</button><div className="page-heading detail-heading"><div><div className="eyebrow">CASE FILE / {item.case_ref}</div><h1>{item.title}</h1><p>Submitted {new Date(item.created_at).toLocaleString()} · {item.input_kind}</p></div><div className="heading-buttons"><button className="secondary" onClick={() => onDownload('json')}><ArrowDownToLine size={15}/> Export JSON</button><button className="secondary" onClick={() => onDownload('markdown')}><ArrowDownToLine size={15}/> Export Markdown</button>{investigator && <button className="primary" onClick={onRefresh}><Fingerprint size={15}/> Recompute links</button>}</div></div><div className="detail-grid"><div className="detail-main"><section className="panel"><div className="panel-heading"><div><h2>System assessment</h2><p>Based on evidence currently recorded for this case.</p></div><span className="status"><i className={item.status}/>{item.status}</span></div><div className="assessment-box"><div className="assessment-mark"><CircleHelp size={18}/></div><div><b>{item.assessment}</b><p>This category applies only to the source-record claim shown below; it does not determine wrongdoing or guilt. Missing, empty, failed, or unavailable checks are not proof of fraud or legitimacy.</p></div></div></section><section className="panel"><div className="panel-heading"><div><h2>Extracted entities and claims</h2><p>Review each candidate against its source excerpt. Extraction confidence describes parser certainty, not whether a claim is true.</p></div><span className="count-pill">{item.entities.length} items</span></div>{item.entities.length ? <div className="entity-list">{item.entities.map(e => <div className="entity" key={e.id}><div className="entity-icon"><Fingerprint size={16}/></div><div className="entity-info"><div><span className="entity-type">{e.type.replaceAll('_',' ')}</span><b>{e.value}</b></div><p>{e.excerpt}</p><div className="entity-meta"><small className="entity-source">{formatSourceLocation(e.source_location)}{e.source_start_char !== null && e.source_end_char !== null ? ` · characters ${e.source_start_char}–${e.source_end_char}` : ''}{e.extraction_confidence !== null ? ` · extraction confidence ${(e.extraction_confidence * 100).toFixed(0)}%` : ''}</small><span className="review-state">{e.review_status.replace('_',' ')}</span><small className="entity-uncertainty">{e.extraction_uncertainty}</small></div></div>{investigator && e.review_status === 'needs_review' && <div className="review-buttons"><button title="Confirm extraction" onClick={() => onReview(e.id, 'confirmed')}><Check size={15}/></button><button title="Reject extraction" onClick={() => onReview(e.id, 'rejected')}><X size={15}/></button></div>}</div>)}</div> : <div className="inline-empty">No entities detected in the submitted text.</div>}</section>{item.findings && item.findings.length > 0 && <section className="panel"><div className="panel-heading"><div><h2>Machine findings</h2><p>Rule-based assessments are linked to persisted evidence records and remain separate from investigator dispositions.</p></div><span className="count-pill">{item.findings.length}</span></div><div className="finding-list">{item.findings.map(finding => <article className="finding-item" key={finding.id}><div><b>{finding.assessment}</b><span className="tag">{finding.scope} · {finding.rule_name} · {finding.rule_version}</span></div><p>{finding.claim}</p><p>{finding.observation}</p><small>Evidence records: {finding.evidence_ids.length ? finding.evidence_ids.map(id => `#${id}`).join(', ') : 'none linked'}{finding.supporting_evidence_ids.length ? ` · supporting records: ${finding.supporting_evidence_ids.map(id => `#${id}`).join(', ')}` : ''}{finding.conflict_evidence_ids.length ? ` · conflict records: ${finding.conflict_evidence_ids.map(id => `#${id}`).join(', ')}` : ''}{finding.unreviewed_evidence_ids.length ? ` · awaiting review: ${finding.unreviewed_evidence_ids.map(id => `#${id}`).join(', ')}` : ''}</small>{finding.evidence_snapshot.map(source => <small key={`${finding.id}-${source.evidence_id}`}>#{source.evidence_id} · {source.source_name} · {source.authority} · {source.outcome} · retrieved {new Date(source.retrieved_at).toLocaleString()} · {source.source_ref || 'no stable reference'} · {source.claim}</small>)}<small>{finding.limitations}</small></article>)}</div></section>}<section className="panel"><div className="panel-heading"><div><h2>Evidence record</h2><p>Source outcomes and retrieval details.</p></div></div><div className="evidence-list">{item.evidence.map(ev => <div className="evidence" key={ev.id}><div className="evidence-icon"><FileText size={16}/></div><div><b>{ev.source_name}</b><span className="evidence-meta">{ev.source_type} · {ev.outcome} · {new Date(ev.retrieved_at).toLocaleString()}</span><small>Source reference: {typeof ev.details?.source_record_ref === 'string' && ev.details.source_record_ref ? ev.details.source_record_ref : ev.source_ref || 'not available'}</small><p>{ev.claim}</p><small>{ev.excerpt}</small><p className="review-state">Investigator relevance: {ev.review_status.replace('_',' ')}{ev.review_reason ? ` · ${ev.review_reason}` : ''}</p>{ev.details?.source_record_withdrawn === true && <small className="review-state">This source record was withdrawn. Its result is historical and cannot be used as current evidence.</small>}{investigator && <div className="review-buttons">{ev.details?.source_record_withdrawn !== true && <button title="Mark evidence relevant" onClick={() => { setEvidenceReview({ id: ev.id, status: 'relevant' }); setEvidenceRationale(''); }}><Check size={15}/></button>}<button title="Mark evidence irrelevant" onClick={() => { setEvidenceReview({ id: ev.id, status: 'irrelevant' }); setEvidenceRationale(''); }}><X size={15}/></button>{ev.details?.source_record_withdrawn !== true && <button title="Mark as contradicting evidence" onClick={() => { setEvidenceReview({ id: ev.id, status: 'contradicts' }); setEvidenceRationale(''); }}><AlertTriangle size={15}/></button>}</div>}</div></div>)}</div></section>{item.links && item.links.length > 0 && <section className="panel"><div className="panel-heading"><div><h2>Possible campaign links</h2><p>These are proposed investigative links, not proof of wrongdoing.</p></div></div>{item.links.map((link, i) => <div className="link-row" key={i}><UsersRound size={16}/><div><b>Case {link.left_case_id} ↔ Case {link.right_case_id}</b><span>{link.reasons.join(' · ')}</span></div><span className="tag">{link.strength}/100 · {link.review_status.replaceAll("_", " ")} · {link.rule_version}</span></div>)}</section>}</div><aside className="detail-aside"><section className="panel"><div className="panel-heading"><div><h2>Evidence timeline</h2><p>Recorded case activity</p></div></div><div className="timeline">{(item.timeline || []).map((event, i) => <div className="timeline-item" key={i}><i/><div><b>{event.action.replaceAll('_',' ')}</b><span>{new Date(event.created_at).toLocaleString()}</span></div></div>)}{!item.timeline?.length && <div className="inline-empty">No review events recorded.</div>}</div></section><section className="privacy-box"><ShieldCheck size={17}/><div><b>Privacy and source access</b><p>{investigator ? 'Authorized investigators and reviewers can inspect case source content. Downloaded reports restrict free-text evidence by default.' : 'This analyst view masks identifiers and withholds free-text evidence. Ask an authorized investigator to review source material.'}</p></div></section><section className="panel note-panel"><div className="panel-heading"><div><h2>Interpretation</h2></div></div><p>A shared identifier can be reused, compromised, or misreported. Verify its context and source before drawing conclusions.</p></section></aside></div>{evidenceReview && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && !evidenceReviewBusy && setEvidenceReview(null)}><section ref={evidenceDialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="evidence-review-title" tabIndex={-1}><header><div><div className="eyebrow">EVIDENCE REVIEW</div><h2 id="evidence-review-title">Mark evidence {evidenceReview.status.replace('_', ' ')}</h2></div><button type="button" className="icon-button" aria-label="Close evidence review" disabled={evidenceReviewBusy} onClick={() => setEvidenceReview(null)}><X size={18}/></button></header><p className="modal-intro">Record why you marked this source {evidenceReview.status.replace("_", " ")}. This is an investigator interpretation, not an automatic source verdict.</p><form onSubmit={submitEvidenceReview}><label htmlFor="evidence-review-rationale">Review rationale<textarea id="evidence-review-rationale" required minLength={10} maxLength={2000} rows={4} value={evidenceRationale} onChange={event => setEvidenceRationale(event.target.value)} placeholder="Explain what the source does and does not support."/></label><footer><button className="secondary" type="button" disabled={evidenceReviewBusy} onClick={() => setEvidenceReview(null)}>Cancel</button><button className="primary" disabled={evidenceReviewBusy || evidenceRationale.trim().length < 10}>{evidenceReviewBusy ? 'Saving…' : 'Save review'}</button></footer></form></section></div>}</>;
}

function HumanDispositionPanel({ item, onSubmit }: { item: Case; onSubmit: (disposition: string, evidenceIds: number[], rationale: string) => void }) {
  const [disposition, setDisposition] = useState('insufficient_evidence');
  const [evidenceIds, setEvidenceIds] = useState<number[]>([]);
  const [rationale, setRationale] = useState('');
  useEffect(() => {
    setDisposition('insufficient_evidence');
    setEvidenceIds([]);
    setRationale('');
  }, [item.id]);
  useEffect(() => {
    setEvidenceIds(current => retainEligibleEvidenceIds(current, item.evidence));
  }, [item.id, item.evidence]);
  const needsSupport = ['confirmed_authoritative', 'evidence_supports_concern'].includes(disposition);
  const supporting = item.evidence.filter(e => e.outcome === 'result' && e.review_status === 'relevant' && e.details?.source_record_withdrawn !== true);
  return <section className="panel disposition-panel"><div className="panel-heading"><div><h2>Human investigator disposition</h2><p>This is a separate human record. Stronger conclusions require relevant evidence and approval by a different authorized reviewer.</p></div></div><form onSubmit={e => { e.preventDefault(); onSubmit(disposition, evidenceIds, rationale); setRationale(''); }}><label>Proposed disposition<select value={disposition} onChange={e => setDisposition(e.target.value)}>{Object.entries(DISPOSITION_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>{needsSupport && <fieldset className="disposition-evidence"><legend>Relevant source evidence (required)</legend>{supporting.length ? supporting.map(e => <label key={e.id}><input type="checkbox" checked={evidenceIds.includes(e.id)} onChange={event => setEvidenceIds(event.target.checked ? [...evidenceIds, e.id] : evidenceIds.filter(id => id !== e.id))}/><span>{e.source_name} · {e.authority} · {e.claim}</span></label>) : <p>No evidence has both a result and investigator relevance review. Review evidence first.</p>}</fieldset>}<label>Rationale<textarea required minLength={10} maxLength={4000} rows={3} value={rationale} onChange={e => setRationale(e.target.value)} placeholder="Describe the evidence and limitations for this human assessment."/></label><button className="secondary" disabled={rationale.trim().length < 10 || (needsSupport && evidenceIds.length === 0)}>Record human disposition</button></form>{item.human_dispositions?.length ? <div className="disposition-history"><h3>Recorded dispositions</h3>{item.human_dispositions.map(d => <article key={d.id}><b>{d.display_label || DISPOSITION_LABELS[d.disposition] || 'Human disposition'} · {d.status.replaceAll('_',' ')}</b><span>{new Date(d.created_at).toLocaleString()} · evidence IDs: {d.evidence_ids.join(', ') || 'none'}</span><p>{d.rationale}</p>{d.review_rationale && <small>Reviewer: {d.review_rationale}</small>}</article>)}</div> : null}</section>;
}

function DispositionReviewQueue({ token, currentUserId, onError, onNotice }: { token: string; currentUserId: number; onError: (message: string) => void; onNotice: (message: string) => void }) {
  const [items, setItems] = useState<HumanDisposition[]>([]);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);
  async function load() { try { const response = await request('/api/dispositions/pending', token); setItems(await response.json()); } catch (e) { onError((e as Error).message); } }
  useEffect(() => { void load(); }, [token]);
  async function review(id: number, status: string) {
    const rationale = drafts[id]?.trim() || '';
    if (rationale.length < 10) { onError('Enter a reviewer rationale of at least 10 characters.'); return; }
    setBusy(id);
    try { await request(`/api/dispositions/${id}/review`, token, { method: 'PATCH', body: JSON.stringify({ status, rationale }) }); await load(); onNotice(`Human disposition ${status}. The system assessment remains unchanged.`); }
    catch (e) { onError((e as Error).message); }
    finally { setBusy(null); }
  }
  return <><div className="page-heading"><div><div className="eyebrow">SEPARATION OF DUTIES</div><h1>Disposition reviews</h1><p>Review stronger human conclusions against case evidence. A human disposition is not a finding of guilt.</p></div></div><section className="panel disposition-queue"><div className="panel-heading"><div><h2>Awaiting a second reviewer</h2><p>{items.length} pending</p></div></div>{items.length ? items.map(item => <article className="disposition-review-item" key={item.id}><b>{item.case_ref} · {item.case_title}</b><span>{item.display_label || DISPOSITION_LABELS[item.disposition] || 'Human disposition'} · proposed {new Date(item.created_at).toLocaleString()}</span><p>{item.rationale}</p><p>Supporting evidence IDs: {item.evidence_ids.join(', ')}</p>{!canApproveDisposition(item) && <div className="inline-empty">Supporting evidence is withdrawn, no longer relevant, or does not meet the authoritative-source requirement. Approval is disabled; reject this disposition or request a current source review.</div>}{item.evidence?.map(e => <div className="review-evidence" key={e.id}><b>{e.source_name} · {e.authority} · {e.outcome} · {e.review_status}</b><span>{e.claim} · retrieved {new Date(e.retrieved_at).toLocaleString()}</span><p>{e.excerpt}</p></div>)}{item.proposer_id === currentUserId ? <div className="inline-empty">You proposed this disposition. Another authorized reviewer must decide.</div> : <><label>Reviewer rationale<textarea rows={3} minLength={10} maxLength={4000} value={drafts[item.id] || ''} onChange={e => setDrafts({ ...drafts, [item.id]: e.target.value })}/></label><div className="review-buttons"><button className="secondary" disabled={busy === item.id || (drafts[item.id] || '').trim().length < 10 || !canApproveDisposition(item)} onClick={() => review(item.id, 'approved')}>Approve disposition</button><button className="secondary" disabled={busy === item.id || (drafts[item.id] || '').trim().length < 10} onClick={() => review(item.id, 'rejected')}>Reject disposition</button></div></>}</article>) : <div className="inline-empty">No dispositions are awaiting review.</div>}</section></>;
}

type ManagedAccount = { id: number; email: string; role: string; active: boolean; created_at: string };
type AccountDialog =
  | { kind: 'status'; account: ManagedAccount; active: boolean }
  | { kind: 'reset'; account: ManagedAccount }
  | { kind: 'token'; account: ManagedAccount; token: string; expiresAt: string };
function AccountManagement({ token, currentUserId, onError, onNotice }: { token: string; currentUserId: number; onError: (message: string) => void; onNotice: (message: string) => void }) {
  const [accounts, setAccounts] = useState<ManagedAccount[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [dialog, setDialog] = useState<AccountDialog | null>(null);
  const [rationale, setRationale] = useState('');
  const [tokenCopied, setTokenCopied] = useState(false);
  const accountDialogRef = useDialogFocus(Boolean(dialog), () => { if (busyId === null) setDialog(null); });
  async function load() {
    try { const response = await request('/api/accounts', token); setAccounts(await response.json()); }
    catch (e) { onError((e as Error).message); }
  }
  useEffect(() => { void load(); }, [token]);
  async function submitDialog(event: React.FormEvent) {
    event.preventDefault();
    if (!dialog || dialog.kind === 'token' || rationale.trim().length < 10) return;
    const { account } = dialog;
    setBusyId(account.id);
    try {
      if (dialog.kind === 'status') {
        await request(`/api/accounts/${account.id}/status`, token, { method: 'PATCH', body: JSON.stringify({ active: dialog.active, rationale: rationale.trim() }) });
        await load();
        onNotice(`${account.email} ${dialog.active ? 'reactivated' : 'suspended'}. Existing sessions were revoked.`);
        setDialog(null);
      } else {
        const response = await request(`/api/accounts/${account.id}/password-reset`, token, { method: 'POST', body: JSON.stringify({ rationale: rationale.trim() }) });
        const result = await response.json();
        setRationale('');
        setTokenCopied(false);
        setDialog({ kind: 'token', account, token: result.reset_token, expiresAt: result.expires_at });
      }
    } catch (e) { onError((e as Error).message); }
    finally { setBusyId(null); }
  }
  return <><div className="page-heading"><div><div className="eyebrow">REVIEWER ADMINISTRATION</div><h1>Workspace accounts</h1><p>Review access, suspend or reactivate accounts, or issue a short-lived reset token for delivery through a separately verified channel.</p></div></div><section className="panel"><div className="panel-heading"><div><h2>Registered accounts</h2><p>{accounts.length} accounts · roles cannot be changed here</p></div></div>{accounts.length ? <div className="table-wrap"><table><thead><tr><th>ACCOUNT</th><th>ROLE</th><th>STATUS</th><th>CREATED</th><th>ACCESS</th><th>RECOVERY</th></tr></thead><tbody>{accounts.map(account => <tr key={account.id}><td><b>{account.email}</b></td><td><span className="tag">{account.role}</span></td><td><span className={`tag ${account.active ? '' : 'tag-muted'}`}>{account.active ? 'Active' : 'Suspended'}</span></td><td>{new Date(account.created_at).toLocaleString()}</td><td><button className="secondary" disabled={busyId === account.id || (account.id === currentUserId && account.active)} onClick={() => { setRationale(''); setDialog({ kind: 'status', account, active: !account.active }); }}>{busyId === account.id ? 'Saving…' : account.active ? 'Suspend' : 'Reactivate'}</button>{account.id === currentUserId && <small className="account-self-note">Current account</small>}</td><td><button className="secondary" disabled={busyId === account.id} onClick={() => { setRationale(''); setDialog({ kind: 'reset', account }); }}>{busyId === account.id ? 'Working…' : 'Issue reset token'}</button></td></tr>)}</tbody></table></div> : <div className="inline-empty">No workspace accounts found.</div>}</section><div className="modal-warning account-warning"><ShieldCheck size={15}/> At least one active reviewer must remain. Reviewers cannot suspend their own account. Reset tokens expire after the configured period, are single-use, and must be delivered out of band. Every action is audited.</div>{dialog && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && busyId === null && setDialog(null)}><section ref={accountDialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="account-dialog-title" tabIndex={-1}><header><div><div className="eyebrow">REVIEWER ADMINISTRATION</div><h2 id="account-dialog-title">{dialog.kind === 'token' ? 'One-time reset token' : dialog.kind === 'status' ? `${dialog.active ? 'Reactivate' : 'Suspend'} account` : 'Issue password reset'}</h2></div><button className="icon-button" aria-label="Close dialog" disabled={busyId !== null} onClick={() => setDialog(null)}><X size={18}/></button></header>{dialog.kind === 'token' ? <><p className="modal-intro">This token is shown once. Deliver it to {dialog.account.email} only through a separately verified secure channel. It expires {new Date(dialog.expiresAt).toLocaleString()}. Closing this dialog loses the token; issuing a replacement invalidates this one.</p><label htmlFor="issued-reset-token">Reset token<input id="issued-reset-token" type="text" readOnly value={dialog.token} onFocus={event => event.currentTarget.select()}/></label><footer><button type="button" className="secondary" onClick={async () => { try { await navigator.clipboard.writeText(dialog.token); setTokenCopied(true); } catch { onError('Clipboard access is unavailable. Select the token field and copy it manually.'); } }}>{tokenCopied ? 'Copied' : 'Copy token'}</button><button type="button" className="primary" onClick={() => { setDialog(null); onNotice(`One-time reset token issued for ${dialog.account.email}. Deliver it through a separately verified channel.`); }}>Done</button></footer></> : <><p className="modal-intro">{dialog.kind === 'status' ? `This changes access for ${dialog.account.email} and revokes all active sessions. Record the reason for this reviewer action.` : `A short-lived, single-use reset token will be created for ${dialog.account.email}. Record why it is needed; you must deliver the token out of band.`}</p><form onSubmit={submitDialog}><label htmlFor="account-action-rationale">{dialog.kind === 'status' ? 'Access-change rationale' : 'Reset rationale'}<textarea id="account-action-rationale" required minLength={10} maxLength={2000} rows={4} value={rationale} onChange={event => setRationale(event.target.value)} placeholder="Enter at least 10 characters."/></label><footer><button type="button" className="secondary" disabled={busyId !== null} onClick={() => setDialog(null)}>Cancel</button><button className="primary" disabled={busyId !== null || rationale.trim().length < 10}>{busyId !== null ? 'Saving…' : dialog.kind === 'status' ? 'Confirm change' : 'Issue token'}</button></footer></form></>}</section></div>}</>;
}

function Campaigns({ token, onOpen, ruleVersion, threshold, weights }: { token: string; onOpen: (id: number) => void; ruleVersion: string; threshold: number; weights: Record<string, number> }) {
  const [groups, setGroups] = useState<CampaignGroup[]>([]);
  const [error, setError] = useState('');
  useEffect(() => { request('/api/campaigns', token).then(r => r.json()).then(setGroups).catch(e => setError((e as Error).message)); }, [token]);
  return <><div className="page-heading"><div><div className="eyebrow">CROSS-CASE ANALYSIS</div><h1>Campaign leads</h1><p>Connected cases are investigation leads. A shared identifier does not establish wrongdoing.</p></div></div><div className="panel campaign-panel"><div className="panel-heading"><div><h2>Candidate groups</h2><p>{groups.length} connected group{groups.length === 1 ? '' : 's'}</p><small>{ruleVersion} · threshold {threshold}/100 · weights: {Object.entries(weights).map(([kind, weight]) => `${kind} ${weight}`).join(', ')}. Score is not a probability. URL and domain matches on the same host count once.</small></div></div>{error && <div className="inline-empty">{error}</div>}{groups.length ? groups.map(group => <article className="campaign-group" key={group.campaign_ref}><div className="campaign-group-heading"><div><b>{group.campaign_ref} · {group.classification.replaceAll('_',' ')}</b><span>{group.case_count} cases · score {group.strength}/100 · {group.review_statuses.join(', ')} · rules {group.rule_versions.join(', ')}</span></div></div><p className="campaign-warning">{group.note}</p><div className="campaign-members">{group.cases.map(item => <button className="campaign-case" key={item.id} onClick={() => onOpen(item.id)}><div className="metric-icon"><UsersRound size={17}/></div><div><b>{item.case_ref} · {item.title}</b><span>{item.assessment} · received {new Date(item.created_at).toLocaleDateString()}</span></div><ChevronRight size={16}/></button>)}</div>{group.links.map((link, index) => <details className="campaign-link-detail" key={`${link.left_case_id}-${link.right_case_id}-${link.rule_version}-${index}`}><summary>Case {link.left_case_id} ↔ Case {link.right_case_id} · score {link.strength}/100 · {link.review_status} · {link.rule_version}</summary><div className="campaign-link-body"><b>Matched identifiers and rule signals</b>{link.reasons.map((reason, i) => <span key={i}>{reason}</span>)}{link.matched_entities.map(entity => <span key={entity.id}>Case {entity.case_id} · {entity.type}: {entity.value} · {entity.review_status} · {formatSourceLocation(entity.source_location)} {entity.source_start_char === null ? '' : `characters ${entity.source_start_char}–${entity.source_end_char}`}</span>)}<b>Related evidence</b>{link.related_evidence.length ? link.related_evidence.map(e => <span key={e.id}>{e.source_name} · {e.outcome} · {e.authority} · {e.claim} · retrieved {new Date(e.retrieved_at).toLocaleString()}</span>) : <span>No source evidence record was linked to these entity matches.</span>}{link.empty_or_failed_checks.length > 0 && <span>Empty or failed checks are visible above and do not count as adverse evidence.</span>}</div></details>)}</article>) : !error ? <div className="empty compact"><div className="empty-icon"><UsersRound size={22}/></div><h3>No candidate case groups</h3><p>Open a case and recompute exact identifier links to find possible connections.</p></div> : null}</div></>;
}

function CaseActions({ item, investigator, onRetry, onReviewLink }: { item: Case; investigator: boolean; onRetry: () => void; onReviewLink: (id: number, status: string) => void }) {
  const proposed = item.links?.filter(link => link.review_status === 'proposed') || [];
  if ((!investigator || proposed.length === 0) && !(investigator && item.processing?.error)) return null;
  return <section className="panel case-actions">{item.processing?.error && investigator && <div className="processing-error"><div><b>Processing needs attention</b><p>{item.processing.error}</p></div><button className="secondary" onClick={onRetry}>Retry processing</button></div>}{proposed.length > 0 && <><div className="panel-heading"><div><h2>Review proposed case links</h2><p>Confirm only that the identifiers are linked in this data. This does not prove wrongdoing.</p></div></div>{proposed.map(link => <div className="link-row" key={link.id}><UsersRound size={16}/><div><b>Case {link.left_case_id} ↔ Case {link.right_case_id}</b><span>{link.reasons.join(' · ')}</span></div><div className="review-buttons"><button title="Confirm link" onClick={() => onReviewLink(link.id, 'confirmed')}><Check size={15}/></button><button title="Reject link" onClick={() => onReviewLink(link.id, 'rejected')}><X size={15}/></button></div></div>)}</>}</section>;
}

function Graph({ token, onOpenCase }: { token: string; onOpenCase: (id: number) => void }) {
  const [data, setData] = useState<{nodes: GraphNode[]; edges: GraphEdge[]; note?: string; projection?: string} | null>(null);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const [filters, setFilters] = useState({ entityType: 'all', sourceType: 'all', fromDate: '', toDate: '', reviewStatus: 'all' });
  useEffect(() => { request('/api/graph', token).then(r => r.json()).then(setData).catch(e => setError(e.message)); }, [token]);
  const entityTypes = useMemo(() => [...new Set((data?.nodes ?? []).filter(n => !['case', 'evidence'].includes(n.type)).map(n => n.type))].sort(), [data]);
  const sourceTypes = useMemo(() => [...new Set((data?.nodes ?? []).filter(n => n.type === 'evidence' && n.source_type).map(n => n.source_type!))].sort(), [data]);
  const filteredGraph = useMemo(() => filterGraphData(data?.nodes ?? [], data?.edges ?? [], filters), [data, filters]);
  const visibleNodes = filteredGraph.nodes;
  const visibleEdges = filteredGraph.edges;
  const visibleNodesById = useMemo(() => new Map(visibleNodes.map(node => [node.id, node])), [visibleNodes]);
  const selectedNode = visibleNodes.find(node => node.id === selectedId);
  function updateFilter(key: keyof typeof filters, value: string) { setFilters(current => ({ ...current, [key]: value })); }
  function resetFilters() { setFilters({ entityType: 'all', sourceType: 'all', fromDate: '', toDate: '', reviewStatus: 'all' }); }
  return <>
    <div className="page-heading"><div><div className="eyebrow">IDENTIFIER RELATIONSHIPS</div><h1>Evidence graph</h1><p>Inspect case, identifier and source-evidence links. Campaign links are leads, not proof of wrongdoing.</p></div></div>
    <section className="panel">
      <div className="panel-heading"><div><h2>Graph projection</h2><p>Personal identifiers are masked in this view. Projection: {data?.projection ?? 'loading'}.</p></div></div>
      <div className="field-row graph-filters">
        <label>Identifier type<select value={filters.entityType} onChange={e => updateFilter('entityType', e.target.value)}><option value="all">All types</option>{entityTypes.map(type => <option key={type} value={type}>{type}</option>)}</select></label>
        <label>Evidence source<select value={filters.sourceType} onChange={e => updateFilter('sourceType', e.target.value)}><option value="all">All sources</option>{sourceTypes.map(type => <option key={type} value={type}>{type}</option>)}</select></label>
        <label>Retrieved from<input type="date" value={filters.fromDate} onChange={e => updateFilter('fromDate', e.target.value)}/></label>
        <label>Retrieved to<input type="date" value={filters.toDate} onChange={e => updateFilter('toDate', e.target.value)}/></label>
        <label>Review status<select value={filters.reviewStatus} onChange={e => updateFilter('reviewStatus', e.target.value)}><option value="all">All statuses</option>{['proposed','confirmed','rejected','needs_review','unreviewed','relevant','irrelevant','contradicts','low_signal'].map(status => <option key={status} value={status}>{status.replaceAll('_', ' ')}</option>)}</select></label>
        <button className="secondary" type="button" onClick={resetFilters}>Reset filters</button>
      </div>
      {error && <div className="inline-empty">{error}</div>}
      {data && <div className="graph-summary"><b>{visibleNodes.length}</b> visible nodes <b>{visibleEdges.length}</b> relationships</div>}
      {data && visibleNodes.length === 0 && <div className="inline-empty">No graph records match these filters.</div>}
      <div className="graph-list">{visibleNodes.map(node => <button type="button" className={`graph-node graph-node-button ${node.id === selectedId ? 'selected' : ''}`} key={node.id} onClick={() => setSelectedId(node.id)}><span className={`node-dot ${node.type === 'case' ? 'case-dot' : ''}`}/><span className="node-type">{node.type}</span><b>{node.label}</b><small>{graphNodeReviewLabel(node, data?.edges ?? [])}</small></button>)}</div>
      <div className="graph-edges">{visibleEdges.slice(0, 160).map((edge, i) => <span key={`${edge.from}-${edge.to}-${i}`}><b>{visibleNodesById.get(edge.from)?.label ?? 'Node'} → {visibleNodesById.get(edge.to)?.label ?? 'Node'}</b><small>{edge.kind.replaceAll('_', ' ')}{edge.review_status ? ` · ${edge.review_status}` : ''}{edge.strength !== undefined ? ` · signal ${edge.strength}/100` : ''}{edge.rule_version ? ` · ${edge.rule_version}` : ''}</small></span>)}</div>
    </section>
    {selectedNode && <section className="panel graph-inspector"><div className="panel-heading"><div><h2>Selected {selectedNode.type}</h2><p>{selectedNode.label}</p></div></div>
      {selectedNode.type === 'case' && <><small>Case created: {selectedNode.created_at ?? 'unknown'}</small><p>Open the case record to inspect its source material and review history.</p><button className="secondary" onClick={() => onOpenCase(selectedNode.case_id!)}>Open case</button></>}
      {selectedNode.type === 'evidence' && <><dl className="graph-details"><div><dt>Source category</dt><dd>{selectedNode.source_type}</dd></div><div><dt>Outcome and authority</dt><dd>{selectedNode.outcome} · {selectedNode.authority}</dd></div><div><dt>Retrieved</dt><dd>{selectedNode.retrieved_at ?? 'unknown'}</dd></div><div><dt>Review status</dt><dd>{selectedNode.review_status}</dd></div><div><dt>Source reference</dt><dd>{selectedNode.source_ref || 'No source reference supplied'}</dd></div></dl><p>Source text is available in the authorized case view.</p><button className="secondary" onClick={() => onOpenCase(selectedNode.case_id!)}>Open case evidence</button></>}
      {visibleEdges.filter(edge => edge.from === selectedNode.id || edge.to === selectedNode.id).map((edge, i) => <p key={i} className="graph-edge-detail">{edge.kind.replaceAll('_', ' ')}{edge.review_status ? ` · ${edge.review_status}` : ''}{edge.strength !== undefined ? ` · signal ${edge.strength}/100` : ''}{edge.rule_version ? ` · ${edge.rule_version}` : ''}{edge.reasons?.length ? ` · ${edge.reasons.join('; ')}` : ''}</p>)}
    </section>}
    {data && <p className="evidence-meta">{data.note}</p>}
  </>;
}
function EvidenceCorpus({ token, reviewer, onError, onNotice }: { token: string; reviewer: boolean; onError: (message: string) => void; onNotice: (message: string) => void }) {
  const [records, setRecords] = useState<CorpusRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [retiring, setRetiring] = useState<CorpusRecord | null>(null);
  const [retirementRationale, setRetirementRationale] = useState('');
  const retireDialogRef = useDialogFocus(Boolean(retiring), () => { if (!busy) setRetiring(null); });
  const [form, setForm] = useState({ entity_type: 'phone', value: '', source_name: '', source_type: 'government', source_ref: '', claim: '', outcome: 'result', excerpt: '', authority: 'government' });
  async function reload() { try { const response = await request('/api/evidence-corpus', token); setRecords(await response.json()); } catch (e) { onError((e as Error).message); } }
  useEffect(() => { reload(); }, [token]);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true);
    try { await request('/api/evidence-corpus', token, { method: 'POST', body: JSON.stringify(form) }); setForm({ ...form, value: '', source_ref: '', claim: '', excerpt: '' }); await reload(); onNotice('Local source record saved with its retrieval time. Matching cases will use it when processed.'); }
    catch (error) { onError((error as Error).message); }
    finally { setBusy(false); }
  }
  async function retireRecord() {
    if (!retiring || retirementRationale.trim().length < 10) return;
    setBusy(true);
    try {
      const response = await request(`/api/evidence-corpus/${encodeURIComponent(retiring.record_id)}/retire`, token, { method: 'POST', body: JSON.stringify({ rationale: retirementRationale.trim() }) });
      const result = await response.json();
      await reload();
      onNotice(`Source record retired. ${result.affected_evidence_count} prior evidence item(s) require review across ${result.affected_case_count} case(s).`);
      setRetiring(null); setRetirementRationale('');
    } catch (error) { onError((error as Error).message); }
    finally { setBusy(false); }
  }
  return <><div className="page-heading"><div><div className="eyebrow">INVESTIGATOR CONTROLLED SOURCES</div><h1>Local evidence corpus</h1><p>Add traceable source results. Reviewers can retire inaccurate or outdated records; prior case findings are recalculated.</p></div></div><div className="detail-grid corpus-grid"><section className="panel"><div className="panel-heading"><div><h2>Add a source record</h2><p>Records are matched by exact normalized identifier during case processing.</p></div></div><form className="corpus-form" onSubmit={submit}><div className="field-row"><label>Identifier type<select value={form.entity_type} onChange={e => setForm({ ...form, entity_type: e.target.value })}><option value="phone">Phone</option><option value="email">Email</option><option value="upi_id">UPI ID</option><option value="bank_account">Bank account (sensitive)</option><option value="ifsc_code">IFSC code</option><option value="url">URL</option><option value="domain">Domain</option></select></label><label>Identifier value<input required value={form.value} onChange={e => setForm({ ...form, value: e.target.value })}/></label></div><label>Source name<input required value={form.source_name} onChange={e => setForm({ ...form, source_name: e.target.value })}/></label><div className="field-row"><label>Source category<select value={form.source_type} onChange={e => setForm({ ...form, source_type: e.target.value })}><option value="government">Government record</option><option value="company_official">Official company source</option><option value="platform">Platform action</option><option value="news">News report</option><option value="complaint">Complaint</option><option value="other">Other</option></select></label><label>Authority level<select value={form.authority} onChange={e => setForm({ ...form, authority: e.target.value })}><option value="government">Government</option><option value="platform_action">Platform action</option><option value="authoritative_source">Other authoritative source</option><option value="curated">Curated record</option><option value="unverified_public_report">Unverified public report</option></select></label></div><label>Source URL or record reference<input value={form.source_ref} onChange={e => setForm({ ...form, source_ref: e.target.value })}/></label><label>What does the source say?<input required value={form.claim} onChange={e => setForm({ ...form, claim: e.target.value })}/></label><div className="field-row"><label>Retrieval outcome<select value={form.outcome} onChange={e => setForm({ ...form, outcome: e.target.value })}><option value="result">Result returned</option><option value="no_result">No result</option><option value="unavailable">Source unavailable</option><option value="error">Lookup error</option></select></label></div><label>Relevant excerpt<textarea rows={4} value={form.excerpt} onChange={e => setForm({ ...form, excerpt: e.target.value })}/></label><div className="modal-warning"><AlertTriangle size={15}/> A source allegation is not automatically an authoritative finding. Record only evidence you can cite.</div><button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save source record'}</button></form></section><section className="panel"><div className="panel-heading"><div><h2>Stored records</h2><p>{records.length} local evidence entries</p></div></div>{records.length ? records.map(record => <div className="evidence" key={record.record_id}><div className="evidence-icon"><FileText size={16}/></div><div><b>{record.source_name} · {record.record_id}</b><span className="evidence-meta">{record.entity_type} · {record.outcome} · {record.authority} · {record.active ? 'active' : 'retired'}</span><p>{record.claim}</p><small>{record.source_ref || 'No source reference provided'}</small>{!record.active && <small>Retired {record.retired_at ? new Date(record.retired_at).toLocaleString() : ''}: {record.retirement_reason}</small>}{reviewer && record.active && <div className="review-buttons"><button className="secondary" type="button" onClick={() => { setRetiring(record); setRetirementRationale(''); }}>Retire source record</button></div>}</div></div>) : <div className="inline-empty">The local corpus has no records yet. Add a source result to support traceable checks.</div>}</section></div>{retiring && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && !busy && setRetiring(null)}><section ref={retireDialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="retire-source-title" tabIndex={-1}><header><div><div className="eyebrow">SOURCE RECORD WITHDRAWAL</div><h2 id="retire-source-title">Retire {retiring.record_id}</h2></div><button className="icon-button" aria-label="Close retirement form" disabled={busy} onClick={() => setRetiring(null)}><X size={18}/></button></header><p className="modal-intro">Retirement prevents future local matches. Existing case evidence is retained for history, flagged for review, and current findings are recalculated. Approved strong human dispositions that cite it return to pending review.</p><label htmlFor="source-retirement-rationale">Reviewer rationale<textarea id="source-retirement-rationale" required minLength={10} maxLength={2000} rows={4} value={retirementRationale} onChange={event => setRetirementRationale(event.target.value)}/></label><footer><button className="secondary" type="button" disabled={busy} onClick={() => setRetiring(null)}>Cancel</button><button className="primary" type="button" disabled={busy || retirementRationale.trim().length < 10} onClick={retireRecord}>{busy ? 'Retiring…' : 'Retire source record'}</button></footer></section></div>}</>;
}

function CorrectionAccess() {
  const [open, setOpen] = useState(false); const [caseRef, setCaseRef] = useState(''); const [email, setEmail] = useState(''); const [description, setDescription] = useState(''); const [retentionDays, setRetentionDays] = useState(180); const [receipt, setReceipt] = useState<any>(null); const [statusRef, setStatusRef] = useState(''); const [statusToken, setStatusToken] = useState(''); const [statusResult, setStatusResult] = useState<any>(null); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const correctionDialogRef = useDialogFocus(open, () => setOpen(false));
  useEffect(() => { fetch(`${API}/api/policy`).then(r => r.json()).then(p => setRetentionDays(p.retention_days)).catch(() => undefined); }, []);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try { const response = await fetch(`${API}/api/corrections`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ case_ref: caseRef.toUpperCase(), requester_email: email, description }) }); const data = await response.json(); if (!response.ok) throw new Error(apiErrorMessage(data.detail, 'Could not submit request')); setReceipt(data); setStatusRef(data.request_ref); setStatusToken(data.status_token); setCaseRef(''); setEmail(''); setDescription(''); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function checkStatus(e: React.FormEvent) { e.preventDefault(); setBusy(true); setError(''); setStatusResult(null); try { const response = await fetch(`${API}/api/corrections/${encodeURIComponent(statusRef)}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status_token: statusToken }) }); const data = await response.json(); if (!response.ok) throw new Error(apiErrorMessage(data.detail, 'Could not check request')); setStatusResult(data); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }
  return <div className="correction-access"><button className="secondary" onClick={() => setOpen(true)}>Request a correction</button>{open && <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && setOpen(false)}><section ref={correctionDialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="correction-dialog-title" tabIndex={-1}><header><div><div className="eyebrow">RECORD REVIEW REQUEST</div><h2 id="correction-dialog-title">Request a correction</h2></div><button type="button" className="icon-button" aria-label="Close correction request" onClick={() => setOpen(false)}><X size={18}/></button></header><p className="modal-intro">Provide the case reference and explain what information you believe is incorrect. Requests are deleted after {retentionDays} days. This form does not confirm whether a case reference exists.</p>{error && <div className="alert error">{error}</div>}{receipt && <div className="alert success">Request received. Reference: <b>{receipt.request_ref}</b><br/>Save this status token; it is shown only once: <code>{receipt.status_token}</code></div>}<form onSubmit={submit}><label>Case reference<input required pattern="RC-[A-Fa-f0-9]{8}" value={caseRef} onChange={e => setCaseRef(e.target.value.toUpperCase())} placeholder="RC-1234ABCD"/></label><label>Your email<input type="email" required value={email} onChange={e => setEmail(e.target.value)}/></label><label>What should be reviewed?<textarea required minLength={15} maxLength={5000} rows={5} value={description} onChange={e => setDescription(e.target.value)}/></label><footer><button className="secondary" type="button" onClick={() => setOpen(false)}>Close</button><button className="primary" disabled={busy}>{busy ? 'Submitting…' : 'Submit request'}</button></footer></form><hr/><h3>Check request status</h3><form onSubmit={checkStatus}><label>Request reference<input required value={statusRef} onChange={e => setStatusRef(e.target.value.toUpperCase())} placeholder="CR-…"/></label><label>Status token<input required minLength={32} value={statusToken} onChange={e => setStatusToken(e.target.value)}/></label><button className="secondary" disabled={busy}>{busy ? 'Checking…' : 'Check status'}</button></form>{statusResult && <div className="alert success">Status: <b>{statusResult.status}</b><p>{statusResult.status_message}</p></div>}</section></div>}</div>;
}

function CorrectionQueue({ token, onError, onNotice }: { token: string; onError: (message: string) => void; onNotice: (message: string) => void }) {
  const [items, setItems] = useState<any[]>([]);
  const [cases, setCases] = useState<any[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [targets, setTargets] = useState<Record<string, string>>({});
  const [actions, setActions] = useState<Record<string, string>>({});
  const [correctedValues, setCorrectedValues] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState('');

  async function reload() {
    try {
      const [response, caseResponse] = await Promise.all([request('/api/corrections', token), request('/api/cases', token)]);
      setItems(await response.json());
      setCases(await caseResponse.json());
    } catch (e) {
      onError((e as Error).message);
    }
  }
  useEffect(() => { reload(); }, [token]);

  async function review(requestRef: string, status: string, priorResolution: string) {
    const resolution = drafts[requestRef] ?? priorResolution;
    if (!correctionReviewValid(resolution)) {
      onError('Enter a review rationale with 5 to 4,000 non-space characters before updating the request.');
      return;
    }
    setBusy(requestRef);
    try { await request(`/api/corrections/${requestRef}`, token, { method: 'PATCH', body: JSON.stringify({ status, resolution }) }); await reload(); onNotice(`Correction request ${requestRef} updated.`); }
    catch (e) { onError((e as Error).message); } finally { setBusy(''); }
  }
  async function apply(item: any) {
    const requestRef = item.request_ref as string;
    const target = targets[requestRef] || '';
    const [kind, id] = target.split(':');
    const linkedCase = cases.find(c => c.case_ref === item.case_ref);
    const selectedEvidence = kind === 'evidence' ? linkedCase?.evidence.find((evidence: any) => evidence.id === Number(id)) : undefined;
    const permittedActions = correctionEvidenceActions(selectedEvidence);
    const requestedAction = actions[requestRef] || (kind === 'evidence' ? 'irrelevant' : 'reject');
    const action = kind === 'evidence' && !permittedActions.includes(requestedAction as any) ? 'irrelevant' : requestedAction;
    const resolution = drafts[requestRef] ?? item.resolution ?? '';
    const correctedValue = correctedValues[requestRef] ?? '';
    if (!target) {
      onError('Select exactly one case entity or evidence item before applying a correction.');
      return;
    }
    if (!correctionApplyValid(resolution, action === 'correct' ? correctedValue : undefined)) {
      onError(action === 'correct'
        ? 'Enter a rationale with 10 to 4,000 non-space characters and a replacement value with 2 to 1,000 characters.'
        : 'Enter a rationale with 10 to 4,000 non-space characters before applying the correction.');
      return;
    }
    const body = kind === 'evidence'
      ? { evidence_id: Number(id), evidence_action: action, resolution }
      : { entity_id: Number(id), entity_action: action, corrected_value: action === 'correct' ? correctedValue : undefined, resolution };
    setBusy(requestRef);
    try {
      await request(`/api/corrections/${requestRef}/apply`, token, { method: 'POST', body: JSON.stringify(body) });
      await reload();
      onNotice(`Correction ${requestRef} applied and case findings recalculated.`);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy('');
    }
  }

  return <>
    <div className="page-heading"><div><div className="eyebrow">DATA QUALITY AND APPEALS</div><h1>Correction requests</h1><p>Review information challenges and record the action taken with a rationale. Applying a correction requires exactly one entity or evidence target.</p></div></div>
    <section className="panel correction-queue">
      <div className="panel-heading"><div><h2>Incoming requests</h2><p>{items.length} requests</p></div></div>
      {items.length ? items.map(item => {
        const requestRef = item.request_ref as string;
        const linkedCase = cases.find(c => c.case_ref === item.case_ref);
        const selectedTarget = targets[requestRef] || '';
        const evidenceTarget = selectedTarget.startsWith('evidence:');
        const selectedEvidence = evidenceTarget ? linkedCase?.evidence.find((evidence: any) => selectedTarget === `evidence:${evidence.id}`) : undefined;
        const allowedActions = correctionEvidenceActions(selectedEvidence);
        const requestedAction = actions[requestRef] || (evidenceTarget ? 'irrelevant' : 'reject');
        const selectedAction = evidenceTarget && !allowedActions.includes(requestedAction as any) ? 'irrelevant' : requestedAction;
        const resolution = drafts[requestRef] ?? item.resolution ?? '';
        const correctedValue = correctedValues[requestRef] ?? '';
        const caseChangeOpen = correctionCaseChangeOpen(item.status);
        const reviewReady = correctionReviewValid(resolution);
        const applyReady = caseChangeOpen && Boolean(selectedTarget) && correctionApplyValid(resolution, selectedAction === 'correct' ? correctedValue : undefined);

        return <article className="correction-item" key={requestRef}>
          <div className="correction-meta"><b>{requestRef} · {item.case_ref}</b><span>{item.requester_email} · {new Date(item.created_at).toLocaleString()} · {item.status}</span></div>
          <p>{item.description}</p>
          {item.resolution && <div className="inline-empty">Recorded response: {item.resolution}</div>}
          <label>Investigator rationale<textarea rows={2} minLength={5} maxLength={4000} placeholder="Record investigator action and rationale" value={resolution} onChange={e => setDrafts({ ...drafts, [requestRef]: e.target.value })}/></label>
          <small>Use at least 5 characters to update request status. Applying a case change requires at least 10 characters.</small>
          <div className="review-buttons">
            <button className="secondary" disabled={busy === requestRef || !reviewReady} onClick={() => review(requestRef, 'investigating', item.resolution ?? '')}>Investigating</button>
            <button className="secondary" disabled={busy === requestRef || !reviewReady} onClick={() => review(requestRef, 'resolved', item.resolution ?? '')}>Resolved</button>
            <button className="secondary" disabled={busy === requestRef || !reviewReady} onClick={() => review(requestRef, 'rejected', item.resolution ?? '')}>Reject</button>
          </div>
          {linkedCase && caseChangeOpen && <div className="field-row correction-apply">
            <label>Case record<select value={selectedTarget} onChange={e => { const value = e.target.value; setTargets({ ...targets, [requestRef]: value }); setActions({ ...actions, [requestRef]: value.startsWith('evidence:') ? 'irrelevant' : 'reject' }); }}>
              <option value="">Choose one record</option>
              <optgroup label="Extracted entities">{linkedCase.entities.map((entity: any) => <option key={`entity:${entity.id}`} value={`entity:${entity.id}`}>{entity.type}: {entity.value} · {entity.review_status}</option>)}</optgroup>
              <optgroup label="Evidence">{linkedCase.evidence.map((evidence: any) => <option key={`evidence:${evidence.id}`} value={`evidence:${evidence.id}`}>{evidence.source_name} · {evidence.outcome}{evidence.details?.source_record_withdrawn === true ? ' · withdrawn (historical)' : ''} · {evidence.claim}</option>)}</optgroup>
            </select></label>
            <label>Action<select value={selectedAction} onChange={e => setActions({ ...actions, [requestRef]: e.target.value })}>
              {evidenceTarget
                ? allowedActions.map(action => <option key={action} value={action}>{action === 'irrelevant' ? 'Mark evidence irrelevant' : action === 'relevant' ? 'Mark evidence relevant' : action === 'needs_review' ? 'Needs further review' : 'Mark as contradicting'}</option>)
                : <><option value="reject">Reject disputed entity</option><option value="confirm">Confirm entity</option><option value="correct">Replace extracted value</option></>}
            </select></label>
            {selectedEvidence?.details?.source_record_withdrawn === true && <p className="inline-empty">This source record was withdrawn. It is historical and can only be marked irrelevant or sent for further review.</p>}
            {!evidenceTarget && selectedAction === 'correct' && <label>Corrected value<input required minLength={2} maxLength={1000} value={correctedValue} onChange={e => setCorrectedValues({ ...correctedValues, [requestRef]: e.target.value })}/></label>}
            <button className="primary" disabled={busy === requestRef || !applyReady} onClick={() => apply(item)}>Apply to case</button>
          </div>}
          {linkedCase && !caseChangeOpen && <div className="inline-empty">This request is closed. Move it back to investigating before making case changes.</div>}
          {!linkedCase && <div className="inline-empty">No matching case is currently available. Record the review outcome without changing case data.</div>}
        </article>;
      }) : <div className="inline-empty">No correction requests have been submitted.</div>}
    </section>
  </>;
}
