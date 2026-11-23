import { PageHeader } from './SiteFrame';
import { FileSearch } from 'lucide-react';
import { useEffect, useState } from 'react';
import message from './JL-204-message.txt?raw';
import type { GraphNode, GraphEdge } from './graph-filters';

const email = 'careers@juniper-loom.invalid';
const title = 'TRAINING · JL-204 · Junior Data Analyst';
const sourceName = 'Synthetic employer register · JL-204';
const sourceRef = '/training/JL-204.txt';
const excerpt = 'Recruitment contact for JL-204: ' + email;
const claim = 'The fictional employer lists this recruitment mailbox for vacancy JL-204.';
type Api = (path: string, body?: object) => Promise<Response>;
type Detail = {
  id: number; case_ref: string; status: string; assessment: string; submitted_text: string;
  entities: {id: number; type: string; value: string; review_status: string}[];
  evidence: {id: number; source_name: string; source_ref: string; outcome: string; review_status: string; retrieved_at: string; details?: {source_record_ref?:string}}[];
};
type Graph = { nodes: GraphNode[]; edges: GraphEdge[] };

export function VacancyWalkthrough({api, openCase, permitted, onCreated, retentionDays}: {
  api: Api; openCase:(id:number)=>void; permitted:boolean; onCreated:()=>Promise<void>; retentionDays:number;
}) {
  const [item, setItem] = useState<Detail | null>(null);
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState('');
  const [graph, setGraph] = useState<Graph | null>(null);
  const [graphEvidence, setGraphEvidence] = useState('');
  const original = item?.entities.find(e => e.type === 'email' && e.value === email);
  const match = item?.evidence.find(e => e.source_name === sourceName && e.details?.source_record_ref === sourceRef && e.outcome === 'result');
  async function lookup() {
    const cases: {id:number;title:string}[] = await (await api('/api/cases')).json();
    for (const c of cases.filter(c => c.title === title)) {
      const record: Detail = await (await api('/api/cases/' + c.id)).json();
      if (record.submitted_text === message.trim()) return record;
    }
    return null;
  }
  useEffect(() => {
    if (!permitted) return;
    let active = true;
    lookup().then(record => {if (active) {setItem(record); setReady(true);}})
      .catch(e => {if (active) setError(e.message);});
    return () => {active = false;};
  }, [permitted]);
  useEffect(() => {
    if (!item || !['queued','processing'].includes(item.status)) return;
    let active = true;
    const timer = window.setTimeout(async () => {
      try { const updated = await (await api('/api/cases/' + item.id)).json(); if (active) setItem(updated); }
      catch (e) { if (active) setError((e as Error).message); }
    }, 1000);
    return () => {active = false; clearTimeout(timer);};
  }, [item]);
  async function run(action:()=>Promise<void>) {
    setBusy(true); setError('');
    try {await action();} catch (e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  async function create() {
    const existing = await lookup();
    if (existing) {setItem(existing); return;}
    const records: {active:boolean; source_name:string; normalized_value:string; source_ref:string; claim:string}[] = await (await api('/api/evidence-corpus')).json();
    if (!records.some(r => r.active && r.source_name === sourceName && r.normalized_value === email && r.source_ref === sourceRef && r.claim === claim)) {
      await api('/api/evidence-corpus', {entity_type:'email',value:email,source_name:sourceName,source_type:'company_official',
        authority:'authoritative_source',source_ref:sourceRef,claim,outcome:'result',excerpt});
    }
    const policy = await (await api('/api/policy')).json();
    const created = await (await api('/api/cases',{title,input_kind:'email',submitted_text:message.trim(),
      consent_version:policy.consent_version,consent:true,rdap_consent:false})).json();
    setItem(await (await api('/api/cases/' + created.id)).json()); await onCreated();
  }
  async function review() {
    if (!item || !original || !match) return;
    const path = '/api/cases/' + item.id;
    if (original.review_status === 'needs_review') await api(path + '/entities/' + original.id + '/review',
      {status:'confirmed',rationale:'Training review: the mailbox is present in the submitted JL-204 email.'});
    if (match.review_status === 'unreviewed') await api(path + '/evidence/' + match.id + '/review',
      {status:'relevant',rationale:'Training review: the JL-204 register lists the matching vacancy contact.'});
    setItem(await (await api(path)).json()); await onCreated();
  }
  async function trace() {
    if (!match) return;
    const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('evidence:' + match.id));
    setGraphEvidence('evidence:' + Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2,'0')).join('').slice(0,24));
    setGraph(await (await api('/api/graph')).json());
  }
  const caseNode = 'case:' + item?.id;
  const target = graph?.edges.find(e=> e.from === graphEvidence && e.kind === 'checks_identifier')?.to;
  const mailbox = graph?.nodes.find(n=>n.id === target && n.type === 'email');
  const connected = mailbox && graph?.edges.some(e=>e.from === caseNode && e.to === graphEvidence && e.kind === 'has_evidence')
    && graph.edges.some(e=>e.from === caseNode && e.to === target && e.kind === 'contains_identifier');
  const canReview = original && match && ['needs_review','confirmed'].includes(original.review_status) && ['unreviewed','relevant'].includes(match.review_status)
    && (original.review_status !== 'confirmed' || match.review_status !== 'relevant');
  return <><PageHeader title="Verify a vacancy contact" icon={FileSearch}>Follow a fictional Junior Data Analyst offer from the employer register to the evidence graph.</PageHeader>
    {!permitted ? <p className="panel">Sign in as an investigator or reviewer to run this walkthrough.</p> :
    <div className="vacancy-demo">
      {error && <p className="alert error" role="alert">{error} · Refresh to reload this walkthrough.</p>}
      <section className="panel"><h2>1. Compare the source and the offer</h2><p>The training register lists this mailbox for the Pune vacancy.</p>
        <blockquote>{excerpt}</blockquote><a href={sourceRef} target="_blank" rel="noreferrer">Open the fictional employer register</a>
        <details><summary>Read the submitted offer</summary><pre className="submitted-posting">{message}</pre></details>
        {!item && <><label className="demo-consent"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>
          I agree to store this fictional email and register entry for investigation for {retentionDays} days. Workspace members can see cases, and investigators can inspect the original.</label>
          <button className="primary" disabled={!ready || !consent || busy} onClick={()=>run(create)}>Create training case</button></>}
      </section>
      {item && <><section className="panel"><h2>2. Review the corpus match</h2>
        <p><strong>{item.case_ref}</strong> · {item.status} · {item.assessment}</p>
        {match && <p>{match.source_name} · {match.source_ref} · retrieved {new Date(match.retrieved_at).toLocaleString()}</p>}
        {canReview && <button className="primary" disabled={busy} onClick={()=>run(review)}>Confirm email and mark source relevant</button>}
        <button className="secondary" onClick={()=>openCase(item.id)}>Open case and findings</button>
        <p>The register confirms the listed mailbox. Verifying a candidate’s personal offer or acceptance requires separate evidence.</p>
      </section>
      <section className="panel"><h2>3. Trace the evidence graph</h2>
        <button className="secondary" disabled={busy || !match} onClick={()=>run(trace)}>{graph ? 'Refresh graph' : 'Show case connections'}</button>
        {graph && (connected ? <figure className="demo-trace"><div><b>{item.case_ref}</b><span>has evidence ↓</span>
          <b>{sourceName}</b><span>checks identifier ↓</span><b>{mailbox.label}</b></div>
          <figcaption>The submitted email also connects {item.case_ref} directly to this mailbox.</figcaption></figure>
          : <p>The graph has not returned the three connections yet. Refresh the graph after processing.</p>)}
      </section></>}
    </div>}</>;
}
