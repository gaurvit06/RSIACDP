import { PageHeader } from './SiteFrame';
import { useEffect, useMemo, useState } from 'react';
import { GitFork, ArrowUpRight, BriefcaseBusiness, ChevronDown, FileSearch, Fingerprint, GitBranch, SlidersHorizontal, UsersRound } from 'lucide-react';
import { displayLabel } from './case-display';
import { filterGraphData, type GraphNode, type GraphEdge, type GraphFilters } from './graph-filters';

type GraphData = { nodes: GraphNode[]; edges: GraphEdge[] };
type Props = {
  token: string;
  request: (path: string, token: string) => Promise<Response>;
  cases: { id: number; title: string }[];
  onOpenCase: (id: number) => void;
};
const initialFilters: GraphFilters = { entityType: 'all', sourceType: 'all', fromDate: '', toDate: '', reviewStatus: 'all' };
const branches = [
  { key: 'sources', label: 'Source checks', icon: FileSearch },
  { key: 'details', label: 'Extracted details', icon: Fingerprint },
  { key: 'related', label: 'Related cases', icon: UsersRound },
] as const;

export function EvidenceGraph({ token, request, cases, onOpenCase }: Props) {
  const [data, setData] = useState<GraphData | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [focus, setFocus] = useState('');
  const [branch, setBranch] = useState<typeof branches[number]['key']>('sources');
  const [filters, setFilters] = useState(initialFilters);
  useEffect(() => {
    let active = true;
    setError('');
    request('/api/graph', token).then(r => r.json()).then(result => { if (active) setData(result); })
      .catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [request, token, attempt]);

  const graph = useMemo(() => filterGraphData(data?.nodes ?? [], data?.edges ?? [], filters), [data, filters]);
  const nodes = useMemo(() => new Map(graph.nodes.map(n => [n.id, n])), [graph]);
  const titles = useMemo(() => new Map(cases.map(c => [c.id, c.title])), [cases]);
  const choices = graph.nodes.filter(n => n.type === 'case').sort((a, b) => (b.case_id ?? 0) - (a.case_id ?? 0));
  const current = choices.find(n => n.id === focus) ?? choices[0];
  const attached = graph.edges.filter(e => e.from === current?.id || e.to === current?.id);
  const identifiers = attached.filter(e => e.kind === 'contains_identifier');
  const sources = attached.filter(e => e.kind === 'has_evidence')
    .sort((a, b) => Number(nodes.get(b.to)?.outcome === 'result') - Number(nodes.get(a.to)?.outcome === 'result'));
  const related = new Map<string, { shared: GraphNode[]; links: GraphEdge[] }>();
  const identifierIds = new Set(identifiers.filter(e => e.review_status !== 'rejected').map(e => e.to));
  for (const e of graph.edges) {
    const other = e.from === current?.id ? e.to : e.from;
    const shared = e.kind === 'contains_identifier' && e.review_status !== 'rejected' && identifierIds.has(e.to) && e.from !== current?.id;
    const linked = e.kind === 'proposed_campaign_link' && (e.from === current?.id || e.to === current?.id);
    if ((!shared && !linked) || nodes.get(other)?.type !== 'case') continue;
    const group = related.get(other) ?? { shared: [], links: [] };
    const identifier = nodes.get(e.to);
    if (shared && identifier) group.shared.push(identifier);
    if (linked) group.links.push(e);
    related.set(other, group);
  }
  const counts = { sources: sources.length, details: identifiers.length, related: related.size };
  const nodesOf = (key: 'sourceType' | 'entityType') => [...new Set(data?.nodes.flatMap(n => key === 'sourceType'
    ? (n.source_type ? [n.source_type] : []) : (['case', 'evidence'].includes(n.type) ? [] : [n.type])) ?? [])].sort();
  const filtering = Object.keys(initialFilters).some(k => filters[k as keyof GraphFilters] !== initialFilters[k as keyof GraphFilters]);
  function update(key: keyof GraphFilters, value: string) { setFilters(f => ({ ...f, [key]: value })); }
  function caseTitle(node: GraphNode) { return titles.get(node.case_id ?? -1) || node.label; }
  return <div className="ev-workspace">
    <PageHeader title="Evidence graph" icon={GitFork}>Choose a case to trace its sources and see which details appear in other cases.</PageHeader>
    {error ? <div className="ev-empty" role="alert">{error}<button className="secondary" onClick={() => setAttempt(a => a + 1)}>Try again</button></div>
    : !data ? <p role="status">Loading case connections…</p>
    : !current ? <div className="ev-empty"><GitBranch/><h2>No case connections yet</h2><p>Submit a case to start tracing its evidence.</p><a href="#cases">Go to cases</a></div>
    : <>
      <section className="ev-hub">
        <div className="ev-hub-symbol"><GitBranch size={27}/></div><div className="ev-case-picker"><label htmlFor="graph-case">Explore a case</label>
          <select id="graph-case" value={current.id} onChange={e => { setFocus(e.target.value); }}>
            {choices.map(c => <option key={c.id} value={c.id}>{caseTitle(c)}{c.label !== caseTitle(c) ? ' · ' + c.label : ''}</option>)}
          </select></div><button className="secondary" onClick={() => onOpenCase(current.case_id!)}>Open case <ArrowUpRight size={15}/></button>
      </section>
      <div className="ev-branches" role="group" aria-label="Explore connections">{branches.map(({key, label, icon: Icon}) =>
        <button key={key} aria-pressed={key === branch} onClick={() => setBranch(key)}><Icon size={19}/><span>{label}</span><b>{counts[key]}</b></button>)}</div>
      <details className="ev-filters"><summary><SlidersHorizontal size={15}/> Filter connections{filtering && ' · filters applied'}</summary>
        <div className="ev-tools">{(['entityType','sourceType'] as const).map(k => <label key={k}>{k === 'entityType' ? 'Identifier type' : 'Evidence source'}
          <select value={filters[k]} onChange={e => update(k,e.target.value)}><option value="all">All</option>{nodesOf(k).map(v => <option key={v} value={v}>{displayLabel(v)}</option>)}</select></label>)}
          <label>Retrieved from<input type="date" value={filters.fromDate} max={filters.toDate || undefined} onChange={e => update('fromDate',e.target.value)}/></label>
          <label>Retrieved to<input type="date" value={filters.toDate} min={filters.fromDate || undefined} onChange={e => update('toDate',e.target.value)}/></label>
          <label>Review status<select value={filters.reviewStatus} onChange={e => update('reviewStatus',e.target.value)}><option value="all">All</option>
            {[...new Set(data.edges.map(e => e.review_status).filter((s): s is string => !!s))].sort().map(s => <option key={s} value={s}>{s.replaceAll('_',' ')}</option>)}</select></label>
          <button className="secondary" onClick={() => setFilters(initialFilters)}>Clear filters</button></div></details>
      <section key={current.id + branch} className="ev-panel">
        <h2>{branches.find(b => b.key === branch)?.label}</h2>
        <p className="ev-hint">{branch === 'sources' ? 'Open a check to see where it came from, when it ran, and what it found.' : branch === 'details' ? 'Open an extracted detail to see its checks and where else it appears. Personal identifiers are masked.' : 'Shared details and campaign links are leads for investigation. Each connection below shows its basis.'}</p>
        {!counts[branch] && <div className="ev-empty">{filtering ? <><p>No connections match these filters.</p><button className="secondary" onClick={() => setFilters(initialFilters)}>Clear filters</button></> :
          branch === 'related' ? 'No shared details or recorded campaign links connect this case to another case in the graph.' :
          branch === 'details' ? 'No extracted details have been recorded for this case.' : 'No source checks have been recorded for this case.'}</div>}
        {branch === 'sources' && sources.map(e => {
          const n = nodes.get(e.to); if (!n) return null;
          const checked = graph.edges.filter(x => x.kind === 'checks_identifier' && x.from === n.id).map(x => nodes.get(x.to)).filter(Boolean);
          return <details key={n.id} className="ev-record"><summary><FileSearch/><span><strong>{displayLabel(n.source_type || 'source')}</strong><small>{checked.map(v => displayLabel(v!.type) + ' · ' + v!.label).join(', ') || 'Case evidence'}</small></span><span className="ev-chip">{displayLabel(n.outcome || 'unknown')}</span><ChevronDown/></summary>
            <dl><dt>Retrieved</dt><dd>{n.retrieved_at ? new Date(n.retrieved_at).toLocaleString() : 'Unknown'}</dd><dt>Source reference</dt><dd>{n.source_ref || 'Unavailable'}</dd><dt>Source authority</dt><dd>{displayLabel(n.authority || 'unknown')}</dd><dt>Review status</dt><dd>{displayLabel(e.review_status || 'unreviewed')}</dd></dl>
            <button className="secondary" onClick={() => onOpenCase(current.case_id!)}>Read case evidence <ArrowUpRight size={14}/></button></details>;
        })}
        {branch === 'details' && identifiers.map(e => {
          const n = nodes.get(e.to); if (!n) return null;
          const checks = graph.edges.filter(x => x.kind === 'checks_identifier' && x.to === n.id && nodes.get(x.from)?.case_id === current.case_id);
          const others = [...related].filter(([,r]) => r.shared.some(v => v.id === n.id));
          return <details key={n.id} className="ev-record"><summary><Fingerprint/><span><strong>{displayLabel(n.type)}</strong><small>{n.label}</small></span><span className="ev-chip">{displayLabel(e.review_status || 'needs_review')}</span><ChevronDown/></summary>
            <p>{checks.length ? checks.map(x => { const source = nodes.get(x.from)!; return displayLabel(source.source_type || 'source') + ' · ' + displayLabel(source.outcome || 'unknown'); }).join(', ') : 'No matching source check in this view.'}</p>
            {others.length ? others.map(([id]) => <button key={id} className="secondary" onClick={() => setFocus(id)}>Explore {caseTitle(nodes.get(id)!)}</button>) : <p>No other case shares this detail in this view.</p>}</details>;
        })}
        {branch === 'related' && [...related].map(([id,r]) => <details key={id} className="ev-record"><summary><BriefcaseBusiness/><span><strong>{caseTitle(nodes.get(id)!)}</strong><small>{nodes.get(id)?.label}</small></span><ChevronDown/></summary>
          {r.shared.length > 0 && <p>Shared details · {r.shared.map(n => displayLabel(n.type) + ' · ' + n.label).join(', ')}</p>}
          {r.links.map((l,i) => <p key={i}>Campaign link · {displayLabel(l.review_status || 'proposed')} · signal {l.strength}/100<br/>{l.reasons?.join(' · ')} <small>{l.rule_version}</small></p>)}
          <button className="secondary" onClick={() => { setFocus(id); setBranch('sources'); }}>Explore this case <ArrowUpRight size={14}/></button></details>)}
      </section>
    </>}
  </div>;
}
