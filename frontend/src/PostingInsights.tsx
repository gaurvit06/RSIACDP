import { PageHeader } from './SiteFrame';
import { Assessment } from './Assessment';
import { useMemo, useState } from 'react';
import { ChartColumn, ChevronRight } from 'lucide-react';
import { dimensions, groupPostings, type Dimension, type PostingCase } from './posting';

export function PostingInsights({ cases, onOpen }: { cases: PostingCase[]; onOpen: (id: number) => void }) {
  const [dimension, setDimension] = useState<Dimension>('location_claim');
  const [confirmedOnly, setConfirmedOnly] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const groups = useMemo(() => groupPostings(cases, dimension, confirmedOnly), [cases, dimension, confirmedOnly]);
  const active = groups.find(group => group.key === selected);
  return <>
    <PageHeader title="Posting insights" icon={ChartColumn}>Explore advertised details across the {cases.length} most recent workspace cases (up to 200).</PageHeader>
    <section className="panel">
      <div className="insight-controls">
        <label>Group cases by <select value={dimension} onChange={e => { setDimension(e.target.value as Dimension); setSelected(null); }}>
          {Object.entries(dimensions).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
        </select></label>
        <label><input type="checkbox" checked={confirmedOnly} onChange={e => { setConfirmedOnly(e.target.checked); setSelected(null); }}/> Confirmed extractions only</label>
      </div>
      {!groups.length ? <p>Submit a case to see posting details here.</p> :
        <><p>Each row counts distinct cases. A case listing two locations can appear under both.</p>
        <div className="insight-bars">{groups.map(group =>
          <button key={group.key} type="button" aria-pressed={active?.key === group.key} onClick={() => setSelected(group.key)}>
            <span>{group.label}</span><span aria-hidden="true" className="insight-track"><i style={{width: (100 * group.cases.length / cases.length) + '%'}}/></span>
            <b>{group.cases.length} {group.cases.length === 1 ? 'case' : 'cases'}</b>
          </button>)}</div></>}
    </section>
    {active && <section key={active.key} className="panel insight-cases"><h2>{active.label}</h2>
      {active.cases.map(item => <button className="campaign-case" key={item.id} onClick={() => onOpen(item.id)}>
        <div><small>{item.case_ref}</small><b>{item.title}</b><Assessment>{item.assessment}</Assessment></div><ChevronRight size={16}/>
      </button>)}
    </section>}
  </>;
}
