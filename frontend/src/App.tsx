import { SiteFrame, PageHeader } from './SiteFrame';
import { PublicDashboard } from './PublicDashboard';
import { DialogTransition, DialogClosing } from './DialogTransition';
import { Assessment } from './Assessment';
import { useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, ChartColumn, BriefcaseBusiness, Check, ChevronRight, CircleHelp, Clock3, FileSearch, FileText, Fingerprint, LayoutDashboard, ContactRound, Plus, Search, ShieldCheck, Upload, UsersRound, X, type LucideIcon } from 'lucide-react';
import { redactSelectedText } from './text-redaction';
import { canApproveDisposition, correctionApplyValid, correctionCaseChangeOpen, correctionEvidenceActions, correctionReviewValid, retainEligibleEvidenceIds } from './review-rules';
import { EvidenceGraph } from './EvidenceGraph';
import { EvidenceCorpus } from './EvidenceCorpus';
import { clearExpiredSession, shouldExpireSession } from './auth-session';
import { evidenceModeLabel, type EvidenceMode } from './evidence-mode';
import { fetchApi, parseApiResponse } from './api-client';
import { predictionLabel, type Prediction } from './PostingPrediction';
import { CaseReading } from './CaseReading';
import { PostingInsights } from './PostingInsights';
import { dashboardAvailable, dashboardHref, dashboardRoute, type Dashboard } from './dashboard-navigation';
import { WorkspaceSidebar } from './WorkspaceSidebar';
import { VacancyWalkthrough } from './VacancyWalkthrough';
import { postingFields, postingMaterial, type PostingDraft } from './posting';
import { CampaignResults } from './CampaignResults';
import { matchesCase, displayLabel } from './case-display';

const API = import.meta.env.VITE_API_URL ?? '';
type User = { id: number; email: string; role: string };
type Entity = { id: number; type: string; value: string; normalized: string; excerpt: string; source_location: string; source_start_char: number | null; source_end_char: number | null; extraction_confidence: number | null; extraction_uncertainty: string; review_status: string };
type Evidence = { id: number; source_name: string; source_type: string; source_ref: string; claim: string; outcome: string; excerpt: string; authority: string; retrieved_at: string; details?: Record<string, unknown>; review_status: string; review_reason: string; reviewed_at: string | null };
export type SystemFinding = { id: number; entity_id: number | null; scope: string; claim: string; assessment: string; observation: string; evidence_ids: number[]; evidence_snapshot: { evidence_id: number; source_name: string; source_type: string; source_ref: string; claim: string; outcome: string; authority: string; retrieved_at: string }[]; conflict_evidence_ids: number[]; unreviewed_evidence_ids: number[]; supporting_evidence_ids: number[]; rule_name: string; rule_version: string; limitations: string; created_at: string };
type HumanDisposition = { id: number; disposition: string; display_label?: string; rationale: string; evidence_ids: number[]; status: string; review_rationale: string; created_at: string; reviewed_at: string | null; case_ref?: string; case_title?: string; proposer_id?: number; evidence?: Evidence[] };
export type Case = { posting_prediction?: Prediction | null; id: number; case_ref: string; title: string; input_kind: string; status: string; assessment: string; created_at: string; entities: Entity[]; evidence: Evidence[]; human_dispositions?: HumanDisposition[]; findings?: SystemFinding[]; submitted_text?: string; timeline?: { action: string; created_at: string; detail: Record<string, unknown> }[]; links?: { id: number; left_case_id: number; right_case_id: number; strength: number; reasons: string[]; review_status: string; rule_version: string }[]; processing?: { status: string; attempts: number; error: string } };
export type CampaignGroup = { campaign_ref: string; classification: string; case_count: number; strength: number; rule_versions: string[]; review_statuses: string[]; note: string; cases: { id: number; case_ref: string; title: string; assessment: string; created_at: string }[]; links: { left_case_id: number; right_case_id: number; strength: number; reasons: string[]; review_status: string; rule_version: string; matched_entities: (Entity & { case_id: number })[]; related_evidence: Evidence[]; empty_or_failed_checks: Evidence[] }[] };
const DISPOSITION_LABELS: Record<string, string> = { confirmed_authoritative: 'Confirmed by an authoritative source', evidence_supports_concern: 'Evidence supports concern', insufficient_evidence: 'Insufficient evidence', no_adverse_evidence: 'No adverse evidence found' };

async function request(path: string, token: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (!['GET', 'HEAD', 'OPTIONS'].includes((init.method || 'GET').toUpperCase()) && token) headers.set('X-CSRF-Token', token);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetchApi(`${API}${path}`, { ...init, headers, credentials: 'include' });
  if (shouldExpireSession(response.status, path)) window.dispatchEvent(new Event('casework:unauthorized'));
  if (!response.ok) await parseApiResponse(response, 'Request failed');
  return response;
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
  const [signInOpen, setSignInOpen] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [cases, setCases] = useState<Case[]>([]);
  const [loadedCase, setSelected] = useState<Case | null>(null);
  const [hash, setHash] = useState(() => window.location.hash);
  const { section, caseId: routeCaseId } = dashboardRoute(hash, user?.role);
  const selected = loadedCase?.id === routeCaseId ? loadedCase : null;
  const mainRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const syncRoute = () => {
      if (/^#casework(?:\/|$)/.test(window.location.hash)) {
        const { caseId } = dashboardRoute(window.location.hash);
        window.history.replaceState(window.history.state, '', dashboardHref('Cases', caseId ?? undefined));
      }
      setHash(window.location.hash);
      mainRef.current?.scrollTo(0, 0);
      window.scrollTo(0, 0);
    };
    syncRoute();
    window.addEventListener('hashchange', syncRoute);
    return () => window.removeEventListener('hashchange', syncRoute);
  }, []);
  const [query, setQuery] = useState('');
  const [assessmentFilter, setAssessmentFilter] = useState('');
  const [modal, setModal] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const helpTriggerRef = useRef<HTMLButtonElement>(null);
  const helpDialogRef = useRef<HTMLElement>(null);
  const helpCloseRef = useRef<HTMLButtonElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [consentPolicy, setConsentPolicy] = useState({ consent_version: 'consent-v2', retention_days: 180, max_upload_bytes: 10485760, allowed_upload_media_types: ['image/png', 'image/jpeg', 'image/webp', 'application/pdf'], rdap_enabled: false, rdap_disclosure: 'Source availability will be shown when the workspace policy loads.', campaign_rule_version: 'campaign-signals-v3-threshold-40', campaign_link_threshold: 40, campaign_signal_weights: { phone: 40, email: 40, upi_id: 40, bank_account: 40, url: 25, domain: 15 } });
  const [sourceMode, setSourceMode] = useState<EvidenceMode>('loading');

  async function loadCases(auth = token) {
    const response = await request('/api/cases', auth);
    setCases(await response.json());
  }
  async function loadCase(id: number) {
    const currentHash = window.location.hash;
    const response = await request(`/api/cases/${id}`, token);
    const data = await response.json();
    if (window.location.hash === currentHash && dashboardRoute(currentHash, user?.role).caseId === id) setSelected(data);
  }
  useEffect(() => {
    if (!token || !routeCaseId) return;
    let active = true;
    request(`/api/cases/${routeCaseId}`, token).then(r => r.json()).then(data => {
      if (active) setSelected(data);
    }).catch(e => { if (active) setError((e as Error).message); });
    return () => { active = false; };
  }, [routeCaseId, token]);

  const [dashboardVisit, setDashboardVisit] = useState(0);
  function resetDashboard() {
    setError('');
    setNotice('');
    setQuery('');
    setAssessmentFilter('');

    mainRef.current?.scrollTo(0, 0);
    window.scrollTo(0, 0);
  }
  function followDashboard(event: React.MouseEvent<HTMLAnchorElement>) {
    if (event.button || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
    event.preventDefault();
    navigate(dashboardRoute(event.currentTarget.hash, user?.role).section);
  }
  function navigate(section: Dashboard, id?: number) {
    if (id) {
      setError('');
      setNotice('');
    } else {
      if (section === dashboardRoute(window.location.hash, user?.role).section && !routeCaseId) setDashboardVisit(visit => visit + 1);
      resetDashboard();
    }
    window.location.hash = dashboardHref(section, id);
  }
  useEffect(() => {
    if (!token || selected?.id || section !== 'Posting insights' || !['investigator', 'reviewer', 'admin'].includes(user?.role ?? '')) return;
    let active = true;
    request('/api/cases', token).then(r => r.json()).then(items => {
      if (active) setCases(items);
    }).catch(e => { if (active) setError((e as Error).message); });
    return () => { active = false; };
  }, [section, selected?.id, token, user?.role]);
  useEffect(() => {
    let stopped = false;
    fetchApi(`${API}/api/auth/me`, { credentials: 'include' }).then(async response => {
      if (response.status === 401) return null;
      return await parseApiResponse<User & { csrf_token: string }>(response, 'Could not restore the session');
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
        setSignInOpen(true);
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
  useEffect(() => { fetch(`${API}/api/policy`).then(r => { if (!r.ok) throw new Error('Policy request failed'); return r.json(); }).then(policy => { setConsentPolicy(policy); setSourceMode(policy.official_board_employers?.length ? (policy.rdap_enabled ? 'boards-rdap' : 'boards') : (policy.rdap_enabled ? 'rdap' : 'local')); }).catch(() => setSourceMode('unavailable')); }, []);
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
    setToken(''); setUser(null); setCases([]); setSelected(null); setSignInOpen(false); window.location.hash = '#home';
  }
  async function login(email: string, password: string) {
    setBusy(true); setError('');
    try {
      const response = await fetchApi(`${API}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ email, password, session_mode: 'cookie' }) });
      const data = await parseApiResponse<{ csrf_token?: string; user: User }>(response, 'Could not sign in');
      setSignInOpen(false);
      if (!window.location.hash || window.location.hash === '#home') navigate('Cases');
      setToken(data.csrf_token || ''); setUser(data.user); await loadCases(data.csrf_token || '');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function createCase(form: { title: string; kind: string; text: string; rdapConsent: boolean }) {
    setBusy(true); setError('');
    try {
      const response = await request('/api/cases', token, { method: 'POST', body: JSON.stringify({ title: form.title, input_kind: form.kind, submitted_text: form.text, consent_version: consentPolicy.consent_version, consent: true, rdap_consent: form.rdapConsent }) });
      const result = await response.json(); await loadCases(); navigate('Cases', result.id); setModal(false); setNotice('Case submitted. The background worker will extract identifiers and check the local evidence corpus.');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function uploadCase(title: string, file: File, rdapConsent: boolean) {
    setBusy(true); setError('');
    try {
      const form = new FormData(); form.set('title', title); form.set('consent_version', consentPolicy.consent_version); form.set('consent', 'true'); form.set('rdap_consent', String(rdapConsent)); form.set('file', file);
      const response = await request('/api/cases/upload', token, { method: 'POST', body: form }); const result = await response.json();
      await loadCases(); navigate('Cases', result.id); setModal(false); setNotice('Private upload received. The background worker will extract text and update this case.');
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
  const filteredCases = useMemo(() => cases.filter(item => matchesCase(item, query, assessmentFilter)), [cases, query, assessmentFilter]);
  const sections: [Dashboard, LucideIcon][] = [
    ['Cases', BriefcaseBusiness], ['Campaigns', UsersRound], ['Posting insights', ChartColumn],
    ['Evidence graph', LayoutDashboard], ['Evidence corpus', FileText], ['Corrections', Clock3],
    ['Disposition reviews', ShieldCheck], ['Accounts', ContactRound],
  ];
  const navEntries = sections.filter(([label]) => dashboardAvailable(label, user?.role));
  if (sessionLoading) return <div className="session-loading" role="status">Restoring your secure session…</div>;
  if (!user || !token || !hash || hash === '#home') return <>
    <PublicDashboard signedIn={Boolean(token && user)} notice={signInOpen ? '' : error}
      onWorkspace={() => { if (token && user) navigate('Cases'); else setSignInOpen(true); }}>
      <CorrectionAccess/>
    </PublicDashboard>
    {signInOpen && <SignInDialog onSubmit={login} busy={busy} error={error}
      onClose={() => { setSignInOpen(false); setError(''); }}/>}
  </>;

  return <SiteFrame workspace trail={<nav className="crumb" aria-label="Breadcrumb">
      <a onClick={followDashboard} href={dashboardHref(section)} aria-current={routeCaseId ? undefined : 'page'}>{section}</a>
      {selected && <><ChevronRight size={13} aria-hidden="true"/><span aria-current="page">{selected.case_ref}</span></>}
    </nav>} tools={<>
      <span className="system-status"><i/>{evidenceModeLabel(sourceMode)}</span>
      <button ref={helpTriggerRef} className="masthead-action" type="button" aria-label="Help and workflow guide" aria-haspopup="dialog" aria-expanded={helpOpen} onClick={() => setHelpOpen(true)}>
        <CircleHelp size={16}/><span>Workflow guide</span>
      </button>
    </>}>
    <WorkspaceSidebar entries={navEntries} section={section} count={cases.length} user={user} onLogout={logout} onNavigate={navigate}/>
    <main ref={mainRef} className="main">
      <div className="content" data-loading-case={Boolean(routeCaseId && !selected && !error)} key={section + "/" + (routeCaseId ?? "") + "/" + dashboardVisit}>
        {error && <div className="alert error"><AlertTriangle size={17}/>{error}<button onClick={() => setError('')}><X size={15}/></button></div>}
        {notice && <div className="alert success"><Check size={17}/>{notice}<button onClick={() => setNotice('')}><X size={15}/></button></div>}
        {routeCaseId && !selected && !error && <p role="status">Loading case…</p>}
        {!routeCaseId && section === 'Cases' && <>
          <PageHeader title="Recruitment cases" icon={BriefcaseBusiness} action={<button className="primary" onClick={() => setModal(true)}><Plus size={17}/> New case</button>}>
            Open a case to compare the model’s prediction with the evidence behind the offer.
          </PageHeader>
          <div className="metric-row"><Metric label="Awaiting completion" value={cases.filter(c => c.status !== 'completed').length.toString()} icon={<FileSearch/>}/><Metric label="Cases received" value={cases.length.toString()} icon={<BriefcaseBusiness/>}/><Metric label="Needs review" value={cases.filter(c => c.entities.some(e => e.review_status === 'needs_review')).length.toString()} icon={<Clock3/>}/><Metric label="Higher model risk" value={String(cases.filter(c => c.posting_prediction?.label === 'Higher fraud risk').length)} icon={<AlertTriangle/>}/></div>
          <div className="list-card"><div className="list-toolbar"><div><h2>Recent cases</h2><span>{filteredCases.length} records</span></div><div className="queue-tools"><select aria-label="Filter by assessment" value={assessmentFilter} onChange={e => setAssessmentFilter(e.target.value)}><option value="">All results</option><optgroup label="Model decision">{['Higher fraud risk', 'Lower fraud risk', 'More posting text needed'].map(label => <option key={label}>{label}</option>)}</optgroup><optgroup label="Evidence assessment">{Object.values(DISPOSITION_LABELS).map(label => <option key={label}>{label}</option>)}</optgroup></select><label className="search"><Search size={16}/><input aria-label="Search cases" placeholder="Case, company, role or location" value={query} onChange={e => setQuery(e.target.value)}/></label></div></div>
            {filteredCases.length ? <div className="table-wrap case-queue"><table aria-label="Recent cases">
              <thead><tr><th>Case</th><th>Input</th><th>Identifiers</th><th>Model decision</th><th>Evidence</th><th>Status</th><th>Received</th><th aria-label="Open case"/></tr></thead>
              <tbody>{filteredCases.map(c => <tr key={c.id} onClick={() => navigate(section, c.id)}>
                <td className="queue-title"><button className="case-open" onClick={event => { event.stopPropagation(); navigate(section, c.id); }}>{c.title}</button><span className="case-reference">{c.case_ref}</span></td>
                <td><span className="tag">{displayLabel(c.input_kind)}</span></td>
                <td>{c.entities.length} extracted</td>
                <td><span className="mobile-column-label" aria-hidden="true">Model decision</span><Assessment>{predictionLabel(c.posting_prediction, c.status)}</Assessment></td>
                <td><span className="mobile-column-label" aria-hidden="true">Evidence</span><Assessment>{c.assessment}</Assessment></td>
                <td><span className="status"><i className={c.status}/>{displayLabel(c.status)}</span></td>
                <td><span className="mobile-column-label date-label" aria-hidden="true">Received </span>{new Date(c.created_at).toLocaleDateString()}</td>
                <td className="queue-chevron"><ChevronRight size={16} aria-hidden="true"/></td>
              </tr>)}</tbody></table></div> : cases.length ? <div className="empty compact"><Search size={22}/><h3>No matching cases</h3><button className="secondary" onClick={() => { setQuery(''); setAssessmentFilter(''); }}>Clear filters</button></div> : <Empty onCreate={() => setModal(true)}/>}</div>
          <div className="footnote"><span><ShieldCheck size={14}/> No adverse evidence found is not proof of legitimacy.</span><span>Evidence access and review actions are audited.</span></div>
        </>}
        {selected && <CaseDetail key={selected.id} item={selected} onDisposition={(kind, ids, rationale) => submitDisposition(selected.id, kind, ids, rationale)} investigator={['investigator','reviewer','admin'].includes(user.role)} onBack={() => navigate('Cases')} onRefresh={() => refreshLinks(selected.id)} onDownload={format => downloadReport(selected.id, format)} onRetry={() => retryProcessing(selected.id)} onReview={(id, status) => updateEntity(selected.id, id, status)} onReviewEvidence={(id, status, rationale) => updateEvidence(selected.id, id, status, rationale)} onReviewLink={(id, status) => reviewLink(selected.id, id, status)} />}
        {!routeCaseId && section === 'Posting insights' && ['investigator','reviewer','admin'].includes(user.role) && <PostingInsights cases={cases} onOpen={id => navigate(section, id)}/>}
        {!routeCaseId && section === 'Vacancy demo' && <VacancyWalkthrough
          permitted={['investigator','reviewer','admin'].includes(user.role)}
          api={(path, body) => request(path, token, body ? {method:'POST', body:JSON.stringify(body)} : {})}
          openCase={id => navigate(section, id)} onCreated={() => loadCases()} retentionDays={consentPolicy.retention_days}/>}
        {!routeCaseId && section === 'Campaigns' && <Campaigns token={token} onOpen={id => navigate(section, id)} ruleVersion={consentPolicy.campaign_rule_version} threshold={consentPolicy.campaign_link_threshold} weights={consentPolicy.campaign_signal_weights}/>}
        {!routeCaseId && section === 'Evidence graph' && <EvidenceGraph token={token} cases={cases} request={request} onOpenCase={id => navigate(section, id)}/>}
        {!routeCaseId && section === 'Evidence corpus' && <EvidenceCorpus token={token} request={request} useDialogFocus={useDialogFocus} reviewer={['reviewer','admin'].includes(user.role)} onNotice={setNotice}/>}
        {!routeCaseId && section === 'Corrections' && <CorrectionQueue token={token} onError={setError} onNotice={setNotice}/>}
        {!routeCaseId && section === 'Disposition reviews' && <DispositionReviewQueue token={token} currentUserId={user.id} onError={setError} onNotice={setNotice}/>}
        {!routeCaseId && section === 'Accounts' && <AccountManagement token={token} currentUserId={user.id} onError={setError} onNotice={setNotice}/>}
      </div>
    </main>
    <DialogTransition>{helpOpen && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && closeHelp()}><section ref={helpDialogRef} className="modal help-modal" role="dialog" aria-modal="true" aria-labelledby="workflow-help-title"><header><div><div className="eyebrow">CASEWORK GUIDE</div><h2 id="workflow-help-title">Investigate with traceable evidence</h2></div><button ref={helpCloseRef} className="icon-button" type="button" aria-label="Close workflow guide" onClick={closeHelp}><X size={18}/></button></header><div className="modal-intro"><p><b>1. Submit the offer.</b> Start a case with text or a supported file. Review the consent notice, remove unrelated personal details where possible, and submit only material you are authorized to share.</p><p><b>2. Review extraction.</b> Processing identifies candidate companies, roles, contact details, payment requests and source locations. Confirm, correct or reject each candidate; an extracted value is not verified just because it was detected.</p><p><b>3. Inspect evidence.</b> Open each source result to see its source, retrieval time, outcome and excerpt. Empty, failed or unavailable checks do not establish fraud or legitimacy. Mark evidence relevant or irrelevant with a reason.</p><p><b>4. Review case links.</b> Reused identifiers and linked cases are investigative leads. Similar wording or a shared domain alone does not prove a campaign or wrongdoing.</p><p><b>5. Share carefully.</b> Downloadable reports mask personal identifiers by default. Machine assessments remain separate from investigator dispositions; a stronger human disposition requires supporting evidence and reviewer approval.</p><p><b>6. Request a correction.</b> Use “Request a correction” on the sign-in page to ask for a record to be reviewed. Save the one-time status token shown after submission.</p><p className="help-safety-note"><ShieldCheck size={15}/> The system never determines that a person is a scammer. “Confirmed by an authoritative source” applies only to the specific claim supported by verifiable source evidence.</p></div><footer><button className="primary" type="button" onClick={closeHelp}>Close guide</button></footer></section></div>}</DialogTransition>
    <DialogTransition>{modal && <NewCase onClose={() => setModal(false)} onSubmit={createCase} onUpload={uploadCase} busy={busy} retentionDays={consentPolicy.retention_days} maxUploadBytes={consentPolicy.max_upload_bytes} allowedUploadTypes={consentPolicy.allowed_upload_media_types} rdapEnabled={consentPolicy.rdap_enabled} rdapDisclosure={consentPolicy.rdap_disclosure}/>}</DialogTransition>
  </SiteFrame>;
}

function Metric({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) { return <div className="metric"><div className="metric-icon">{icon}</div><div><span>{label}</span><b>{value}</b></div></div>; }
function Empty({ onCreate }: { onCreate: () => void }) { return <div className="empty"><div className="empty-icon"><FileSearch size={23}/></div><h3>No cases yet</h3><p>Submit a suspicious recruitment offer to begin an evidence-led investigation.</p><button className="secondary" onClick={onCreate}><Plus size={15}/> Create first case</button></div>; }

function SignInDialog({ onSubmit, busy, error, onClose }: {
  onSubmit: (email: string, password: string) => void; busy: boolean; error: string; onClose: () => void;
}) {
  const [resetMode, setResetMode] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [resetPassword, setResetPassword] = useState('');
  const [resetBusy, setResetBusy] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetNotice, setResetNotice] = useState('');
  const close = () => { if (!busy && !resetBusy) onClose(); };
  const dialogRef = useDialogFocus(true, close);
  async function submitReset(event: React.FormEvent) {
    event.preventDefault(); setResetBusy(true); setResetError(''); setResetNotice('');
    try {
      const response = await fetchApi(`${API}/api/auth/reset-password`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token: resetToken, new_password: resetPassword }) });
      const data = await parseApiResponse<{ sign_in_message?: string }>(response, 'Could not reset password');
      setResetNotice(data.sign_in_message || 'Password updated. Sign in with the new password.');
      setResetToken(''); setResetPassword(''); setResetMode(false);
    } catch (e) { setResetError((e as Error).message); }
    finally { setResetBusy(false); }
  }
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) close(); }}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="desk-sign-in" tabIndex={-1} ref={dialogRef}>
      <header><h2 id="desk-sign-in">{resetMode ? 'Set a new password' : 'Sign in to Casework'}</h2>
        <button className="icon-button" aria-label="Close sign in" onClick={close} disabled={busy || resetBusy}><X size={18}/></button></header>
      {resetMode ? <>
        <p className="modal-intro">Use the one-time reset token supplied through your verified recovery channel.</p>
        {resetError && <p role="alert" className="alert error">{resetError}</p>}
        <form onSubmit={submitReset}><label>One-time reset token<input required minLength={32} maxLength={128} autoComplete="one-time-code" value={resetToken} onChange={e => setResetToken(e.target.value)}/></label>
          <label>New password (12 characters minimum)<input type="password" required minLength={12} maxLength={128} autoComplete="new-password" value={resetPassword} onChange={e => setResetPassword(e.target.value)}/></label>
          <footer><button type="button" className="secondary" disabled={resetBusy} onClick={() => setResetMode(false)}>Back to sign in</button>
            <button className="primary" disabled={resetBusy}>{resetBusy ? 'Updating…' : 'Update password'}</button></footer></form>
      </> : <>
        <p className="modal-intro">Access your private investigation workspace.</p>
        {error && <p role="alert" className="alert error">{error}</p>}
        {resetNotice && <p role="status" className="alert success">{resetNotice}</p>}
        <form onSubmit={e => { e.preventDefault(); onSubmit(email, password); }}>
          <label>Email address<input type="email" required autoComplete="username" value={email} onChange={e => setEmail(e.target.value)}/></label>
          <label>Password<input type="password" required autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)}/></label>
          <footer><button type="button" className="secondary" disabled={busy} onClick={() => setResetMode(true)}>Use a reset token</button>
            <button className="primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button></footer></form>
      </>}
    </section>
  </div>;

}

function NewCase({ onClose, onSubmit, onUpload, busy, retentionDays, maxUploadBytes, allowedUploadTypes, rdapEnabled, rdapDisclosure }: { onClose: () => void; onSubmit: (f: { title: string; kind: string; text: string; rdapConsent: boolean }) => void; onUpload: (title: string, file: File, rdapConsent: boolean) => void; busy: boolean; retentionDays: number; maxUploadBytes: number; allowedUploadTypes: string[]; rdapEnabled: boolean; rdapDisclosure: string }) {
  const [title, setTitle] = useState('');
  const [kind, setKind] = useState('message');
  const [posting, setPosting] = useState<PostingDraft>({});
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState('');
  const [consent, setConsent] = useState(false);
  const [rdapConsent, setRdapConsent] = useState(false);
  const [selectedRange, setSelectedRange] = useState<{ start: number; end: number } | null>(null);
  const closing = useContext(DialogClosing);
  const dialogRef = useDialogFocus(!closing, () => { if (!busy) onClose(); });

  const guided = kind === 'posting';
  const material = guided ? postingMaterial(posting, text) : text;
  const exceedsLimit = !file && material.length > 100000;
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
      <header><div><h2 id="new-case-title">Submit a recruitment case</h2></div><button type="button" className="icon-button" aria-label="Close case submission" disabled={busy} onClick={onClose}><X size={18}/></button></header>
      <p className="modal-intro">Submit the material you received. Extracted identifiers are candidates for investigator review, not findings of wrongdoing.</p>
      <form onSubmit={e => { e.preventDefault(); if (!consent || (rdapEnabled && !rdapConsent) || fileError || exceedsLimit || (!file && !material.trim())) return; file ? onUpload(title, file, rdapConsent) : onSubmit({ title, kind, text: material, rdapConsent }); }}>
        <label>Case title<input required minLength={3} maxLength={240} placeholder="e.g. Remote data entry offer via messaging app" value={title} onChange={e => setTitle(e.target.value)}/></label>
        <div className="field-row">
          <label>Material type<select value={kind} disabled={Boolean(file)} onChange={e => { setKind(e.target.value); setFileError(''); }}><option value="posting">Job posting (guided form)</option><option value="message">Message</option><option value="email">Email</option><option value="url">Job posting URL</option><option value="text">Other text</option></select></label>
          {!guided && <label>Attach screenshot or PDF<input type="file" accept={allowedUploadTypes.join(',')} onChange={e => selectFile(e.target.files?.[0])}/><small>Maximum {formatBytes(maxUploadBytes)}. Text extraction runs in the background.</small></label>}
        </div>
        {fileError && <div className="alert error" role="alert">{fileError}<button type="button" aria-label="Dismiss upload error" onClick={() => setFileError('')}><X size={14}/></button></div>}
        {!file && <>
          {guided && <fieldset className="posting-fields"><legend>Advertised details</legend>
            <p>Copy the wording from the offer. Leave missing details blank.</p>
            <div className="field-row">{postingFields.map(label => <label key={label}>{label}
              {label === 'Salary disclosed' || label === 'Company logo present' ? <select value={posting[label] ?? ''} onChange={e => setPosting({...posting,[label]:e.target.value})}>
                <option value="">Unspecified</option><option>Yes</option><option>No</option>
              </select> : label === 'Employment type' ? <select value={posting[label] ?? ''} onChange={e => setPosting({...posting, [label]:e.target.value})}>
                <option value="">Unspecified</option>{['Full-time','Part-time','Contract','Temporary','Internship','Apprenticeship'].map(v => <option key={v}>{v}</option>)}
              </select> : <input maxLength={label === 'Requirements' || label === 'Benefits' ? 2000 : 120} value={posting[label] ?? ''} onChange={e => setPosting({...posting,[label]:e.target.value})}/>}
            </label>)}</div></fieldset>}
          <label htmlFor="case-submission-text">{guided ? 'Job description or offer wording' : 'Paste the offer or message'}<textarea id="case-submission-text" required={!guided} minLength={1} maxLength={100000} rows={7} placeholder="Include the text as received. Remove or redact details you do not wish to submit." value={text} onSelect={event => { const start = event.currentTarget.selectionStart; const end = event.currentTarget.selectionEnd; setSelectedRange(start < end ? { start, end } : null); }} onChange={e => { setText(e.target.value); setSelectedRange(null); }}/></label>
          <div className="redact-actions"><small>Select sensitive text, then replace it before submission. Redacted text will not be available for extraction.</small><button type="button" className="secondary" disabled={!selectedRange} onClick={redactSelection}>Redact selected text</button></div>
        </>}
        {file && <div className="file-chip"><FileText size={16}/>{file.name} · {formatBytes(file.size)}<button type="button" aria-label="Remove selected file" onClick={() => selectFile()}><X size={14}/></button></div>}
        {exceedsLimit && <p role="alert">Shorten the posting to 100,000 characters including field labels.</p>}
        <label className="consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/><span>I consent to use this material for investigation. The submission, extracted identifiers, evidence and review history are stored for the case. Signed-in workspace users can access it; contact identifiers are masked for analysts and downloads. Case records and original uploads are deleted after {retentionDays} days.</span></label>
        <p className="modal-intro">{rdapDisclosure}</p>
        {rdapEnabled && <><label className="consent"><input type="checkbox" checked={rdapConsent} onChange={e => setRdapConsent(e.target.checked)}/><span>I separately consent to sending extracted domain names to the corresponding public RDAP registry for registration metadata checks. This does not send the submitted text, complete URLs, email addresses, or other identifiers.</span></label></>}
        <div className="modal-warning"><AlertTriangle size={15}/> A match or repeated identifier is an investigative lead, not proof of wrongdoing.</div>
        <footer><button className="secondary" type="button" onClick={onClose}>Cancel</button><button className="primary" disabled={!consent || (rdapEnabled && !rdapConsent) || busy || Boolean(fileError) || exceedsLimit || (!file && !material.trim())}>{busy ? 'Submitting…' : <><Upload size={15}/> Submit case</>}</button></footer>
      </form>
    </section>
  </div>;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(bytes % (1024 * 1024) === 0 ? 0 : 1)} MB`;
}

function CaseDetail({ item, investigator, onBack, onRefresh, onDownload, onReview, onReviewEvidence, onRetry, onReviewLink, onDisposition }: { onDisposition: (kind: string, ids: number[], rationale: string) => void; item: Case; investigator: boolean; onBack: () => void; onRefresh: () => void; onDownload: (format: 'json' | 'markdown') => void; onReview: (id: number, status: string) => void; onReviewEvidence: (id: number, status: string, rationale: string) => Promise<void>; onRetry: () => void; onReviewLink: (id: number, status: string) => void }) {
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
  return <>
    <CaseReading item={item} investigator={investigator} onBack={onBack} onRefresh={onRefresh}
      onDownload={onDownload} onReview={onReview} onRetry={onRetry} onReviewLink={onReviewLink}
      onEvidence={(id, status) => { setEvidenceReview({ id, status }); setEvidenceRationale(''); }}>
      {investigator && <HumanDispositionPanel item={item} onSubmit={onDisposition}/>}
    </CaseReading>
    <DialogTransition>{evidenceReview && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && !evidenceReviewBusy && setEvidenceReview(null)}><section ref={evidenceDialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="evidence-review-title" tabIndex={-1}><header><div><div className="eyebrow">EVIDENCE REVIEW</div><h2 id="evidence-review-title">Mark evidence {evidenceReview.status.replace('_', ' ')}</h2></div><button type="button" className="icon-button" aria-label="Close evidence review" disabled={evidenceReviewBusy} onClick={() => setEvidenceReview(null)}><X size={18}/></button></header><p className="modal-intro">Record why you marked this source {evidenceReview.status.replace("_", " ")}. This is an investigator interpretation, not an automatic source verdict.</p><form onSubmit={submitEvidenceReview}><label htmlFor="evidence-review-rationale">Review rationale<textarea id="evidence-review-rationale" required minLength={10} maxLength={2000} rows={4} value={evidenceRationale} onChange={event => setEvidenceRationale(event.target.value)} placeholder="Explain what the source does and does not support."/></label><footer><button className="secondary" type="button" disabled={evidenceReviewBusy} onClick={() => setEvidenceReview(null)}>Cancel</button><button className="primary" disabled={evidenceReviewBusy || evidenceRationale.trim().length < 10}>{evidenceReviewBusy ? 'Saving…' : 'Save review'}</button></footer></form></section></div>}</DialogTransition></>;
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
  return <><PageHeader title="Disposition reviews" icon={ShieldCheck}>Review stronger human conclusions against case evidence. A human disposition is not a finding of guilt.</PageHeader><section className="panel disposition-queue"><div className="panel-heading"><div><h2>Awaiting a second reviewer</h2><p>{items.length} pending</p></div></div>{items.length ? items.map(item => <article className="disposition-review-item" key={item.id}><b>{item.case_ref} · {item.case_title}</b><span>{item.display_label || DISPOSITION_LABELS[item.disposition] || 'Human disposition'} · proposed {new Date(item.created_at).toLocaleString()}</span><p>{item.rationale}</p><p>Supporting evidence IDs: {item.evidence_ids.join(', ')}</p>{!canApproveDisposition(item) && <div className="inline-empty">Supporting evidence is withdrawn, no longer relevant, or does not meet the authoritative-source requirement. Approval is disabled; reject this disposition or request a current source review.</div>}{item.evidence?.map(e => <div className="review-evidence" key={e.id}><b>{e.source_name} · {e.authority} · {e.outcome} · {e.review_status}</b><span>{e.claim} · retrieved {new Date(e.retrieved_at).toLocaleString()}</span><p>{e.excerpt}</p></div>)}{item.proposer_id === currentUserId ? <div className="inline-empty">You proposed this disposition. Another authorized reviewer must decide.</div> : <><label>Reviewer rationale<textarea rows={3} minLength={10} maxLength={4000} value={drafts[item.id] || ''} onChange={e => setDrafts({ ...drafts, [item.id]: e.target.value })}/></label><div className="review-buttons"><button className="secondary" disabled={busy === item.id || (drafts[item.id] || '').trim().length < 10 || !canApproveDisposition(item)} onClick={() => review(item.id, 'approved')}>Approve disposition</button><button className="secondary" disabled={busy === item.id || (drafts[item.id] || '').trim().length < 10} onClick={() => review(item.id, 'rejected')}>Reject disposition</button></div></>}</article>) : <div className="inline-empty">No dispositions are awaiting review.</div>}</section></>;
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
  return <><PageHeader title="Workspace accounts" icon={ContactRound}>Review access, suspend or reactivate accounts, or issue a short-lived reset token for delivery through a separately verified channel.</PageHeader><section className="panel"><div className="panel-heading"><div><h2>Registered accounts</h2><p>{accounts.length} accounts · roles cannot be changed here</p></div></div>{accounts.length ? <div className="table-wrap"><table><thead><tr><th>ACCOUNT</th><th>ROLE</th><th>STATUS</th><th>CREATED</th><th>ACCESS</th><th>RECOVERY</th></tr></thead><tbody>{accounts.map(account => <tr key={account.id}><td><b>{account.email}</b></td><td><span className="tag">{account.role}</span></td><td><span className={`tag ${account.active ? '' : 'tag-muted'}`}>{account.active ? 'Active' : 'Suspended'}</span></td><td>{new Date(account.created_at).toLocaleString()}</td><td><button className="secondary" disabled={busyId === account.id || (account.id === currentUserId && account.active)} onClick={() => { setRationale(''); setDialog({ kind: 'status', account, active: !account.active }); }}>{busyId === account.id ? 'Saving…' : account.active ? 'Suspend' : 'Reactivate'}</button>{account.id === currentUserId && <small className="account-self-note">Current account</small>}</td><td><button className="secondary" disabled={busyId === account.id} onClick={() => { setRationale(''); setDialog({ kind: 'reset', account }); }}>{busyId === account.id ? 'Working…' : 'Issue reset token'}</button></td></tr>)}</tbody></table></div> : <div className="inline-empty">No workspace accounts found.</div>}</section><div className="modal-warning account-warning"><ShieldCheck size={15}/> At least one active reviewer must remain. Reviewers cannot suspend their own account. Reset tokens expire after the configured period, are single-use, and must be delivered out of band. Every action is audited.</div><DialogTransition>{dialog && <div className="modal-backdrop" onMouseDown={event => event.target === event.currentTarget && busyId === null && setDialog(null)}><section ref={accountDialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="account-dialog-title" tabIndex={-1}><header><div><h2 id="account-dialog-title">{dialog.kind === 'token' ? 'One-time reset token' : dialog.kind === 'status' ? `${dialog.active ? 'Reactivate' : 'Suspend'} account` : 'Issue password reset'}</h2></div><button className="icon-button" aria-label="Close dialog" disabled={busyId !== null} onClick={() => setDialog(null)}><X size={18}/></button></header>{dialog.kind === 'token' ? <><p className="modal-intro">This token is shown once. Deliver it to {dialog.account.email} only through a separately verified secure channel. It expires {new Date(dialog.expiresAt).toLocaleString()}. Closing this dialog loses the token; issuing a replacement invalidates this one.</p><label htmlFor="issued-reset-token">Reset token<input id="issued-reset-token" type="text" readOnly value={dialog.token} onFocus={event => event.currentTarget.select()}/></label><footer><button type="button" className="secondary" onClick={async () => { try { await navigator.clipboard.writeText(dialog.token); setTokenCopied(true); } catch { onError('Clipboard access is unavailable. Select the token field and copy it manually.'); } }}>{tokenCopied ? 'Copied' : 'Copy token'}</button><button type="button" className="primary" onClick={() => { setDialog(null); onNotice(`One-time reset token issued for ${dialog.account.email}. Deliver it through a separately verified channel.`); }}>Done</button></footer></> : <><p className="modal-intro">{dialog.kind === 'status' ? `This changes access for ${dialog.account.email} and revokes all active sessions. Record the reason for this reviewer action.` : `A short-lived, single-use reset token will be created for ${dialog.account.email}. Record why it is needed; you must deliver the token out of band.`}</p><form onSubmit={submitDialog}><label htmlFor="account-action-rationale">{dialog.kind === 'status' ? 'Access-change rationale' : 'Reset rationale'}<textarea id="account-action-rationale" required minLength={10} maxLength={2000} rows={4} value={rationale} onChange={event => setRationale(event.target.value)} placeholder="Enter at least 10 characters."/></label><footer><button type="button" className="secondary" disabled={busyId !== null} onClick={() => setDialog(null)}>Cancel</button><button className="primary" disabled={busyId !== null || rationale.trim().length < 10}>{busyId !== null ? 'Saving…' : dialog.kind === 'status' ? 'Confirm change' : 'Issue token'}</button></footer></form></>}</section></div>}</DialogTransition></>;
}

function Campaigns({ token, onOpen, ruleVersion, threshold, weights }: { token: string; onOpen: (id: number) => void; ruleVersion: string; threshold: number; weights: Record<string, number> }) {
  const [groups, setGroups] = useState<CampaignGroup[] | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { request('/api/campaigns', token).then(r => r.json()).then(setGroups).catch(e => setError((e as Error).message)); }, [token]);
  return <CampaignResults groups={groups} error={error} onOpen={onOpen} ruleVersion={ruleVersion} threshold={threshold} weights={weights}/>;
}





function CorrectionAccess() {
  const [open, setOpen] = useState(false); const [caseRef, setCaseRef] = useState(''); const [email, setEmail] = useState(''); const [description, setDescription] = useState(''); const [retentionDays, setRetentionDays] = useState(180); const [receipt, setReceipt] = useState<any>(null); const [statusRef, setStatusRef] = useState(''); const [statusToken, setStatusToken] = useState(''); const [statusResult, setStatusResult] = useState<any>(null); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const correctionDialogRef = useDialogFocus(open, () => setOpen(false));
  useEffect(() => { fetch(`${API}/api/policy`).then(r => r.json()).then(p => setRetentionDays(p.retention_days)).catch(() => undefined); }, []);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try { const response = await fetchApi(`${API}/api/corrections`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ case_ref: caseRef.toUpperCase(), requester_email: email, description }) }); const data = await parseApiResponse<any>(response, 'Could not submit request'); setReceipt(data); setStatusRef(data.request_ref); setStatusToken(data.status_token); setCaseRef(''); setEmail(''); setDescription(''); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function checkStatus(e: React.FormEvent) { e.preventDefault(); setBusy(true); setError(''); setStatusResult(null); try { const response = await fetchApi(`${API}/api/corrections/${encodeURIComponent(statusRef)}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status_token: statusToken }) }); const data = await parseApiResponse<any>(response, 'Could not check request'); setStatusResult(data); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }
  return <div className="correction-access"><button className="secondary" onClick={() => setOpen(true)}>Request a correction</button><DialogTransition>{open && <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && setOpen(false)}><section ref={correctionDialogRef} className="modal" role="dialog" aria-modal="true" aria-labelledby="correction-dialog-title" tabIndex={-1}><header><div><h2 id="correction-dialog-title">Request a correction</h2></div><button type="button" className="icon-button" aria-label="Close correction request" onClick={() => setOpen(false)}><X size={18}/></button></header><p className="modal-intro">Provide the case reference and explain what information you believe is incorrect. Requests are deleted after {retentionDays} days. This form does not confirm whether a case reference exists.</p>{error && <div className="alert error">{error}</div>}{receipt && <div className="alert success">Request received. Reference: <b>{receipt.request_ref}</b><br/>Save this status token; it is shown only once: <code>{receipt.status_token}</code></div>}<form onSubmit={submit}><label>Case reference<input required pattern="RC-[A-Fa-f0-9]{8}" value={caseRef} onChange={e => setCaseRef(e.target.value.toUpperCase())} placeholder="RC-1234ABCD"/></label><label>Your email<input type="email" required value={email} onChange={e => setEmail(e.target.value)}/></label><label>What should be reviewed?<textarea required minLength={15} maxLength={5000} rows={5} value={description} onChange={e => setDescription(e.target.value)}/></label><footer><button className="secondary" type="button" onClick={() => setOpen(false)}>Close</button><button className="primary" disabled={busy}>{busy ? 'Submitting…' : 'Submit request'}</button></footer></form><hr/><h3>Check request status</h3><form onSubmit={checkStatus}><label>Request reference<input required value={statusRef} onChange={e => setStatusRef(e.target.value.toUpperCase())} placeholder="CR-…"/></label><label>Status token<input required minLength={32} value={statusToken} onChange={e => setStatusToken(e.target.value)}/></label><button className="secondary" disabled={busy}>{busy ? 'Checking…' : 'Check status'}</button></form>{statusResult && <div className="alert success">Status: <b>{statusResult.status}</b><p>{statusResult.status_message}</p></div>}</section></div>}</DialogTransition></div>;
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
    <PageHeader title="Correction requests" icon={Clock3}>Review information challenges and record the action taken with a rationale. Applying a correction requires exactly one entity or evidence target.</PageHeader>
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
