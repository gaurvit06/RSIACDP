import { useRef, useState, type ReactNode } from 'react';
import { ArrowRight, ArrowUpRight, Files, GitFork, Link2, Mail, ScanText, SearchCheck, ShieldCheck, X } from 'lucide-react';

import { SiteFrame } from './SiteFrame';

const stages = [
  { title: 'Offer', icon: Mail, heading: 'A fee before the interview', source: 'Submitted message', quote: '“Your interview is confirmed. Please pay a ₹1,500 registration fee to reserve your slot.”', label: 'Extracted detail', value: '₹1,500 upfront fee', note: 'The request is visible in the message. Who sent it is still unverified.' },
  { title: 'Source', icon: SearchCheck, heading: 'Check the employer’s policy', source: 'Sample employer policy · record S-04', quote: '“Our recruitment team never asks applicants to pay for interviews.”', label: 'Evidence supports concern', value: 'The fee conflicts with policy', note: 'This source addresses the payment request. It cannot establish the sender’s identity.' },
  { title: 'Link', icon: GitFork, heading: 'A detail appears twice', source: 'Exact identifier match · two sample cases', quote: 'The same payment identifier appears in this offer and an earlier submission.', label: 'Investigative lead', value: 'Two cases, one identifier', note: 'An investigator can inspect both submissions. A shared identifier alone cannot establish who was responsible.' },
] as const;

function StageContent({ index }: { index: number }) {
  const stage = stages[index];
  const Icon = stage.icon;
  return <div className="dossier-content" aria-live="polite" aria-atomic="true"><div key={index}>
    <div className="dossier-glyph"><Icon size={22} aria-hidden="true"/></div>
    <h2>{stage.heading}</h2><div className="dossier-source">{stage.source}</div>
    <blockquote>{stage.quote}</blockquote>
    <div className="dossier-fact"><span>{stage.label}</span><strong>{stage.value}</strong></div>
    <p>{stage.note}</p>
  </div></div>;
}

export function PublicDashboard({ signedIn, onWorkspace, onRegister, children, notice }: {
  signedIn: boolean; onWorkspace: () => void; onRegister: () => void; children: ReactNode; notice: string;
}) {
  const [active, setActive] = useState(0);
  const [walkthroughStep, setWalkthroughStep] = useState(0);
  const walkthrough = useRef<HTMLDialogElement>(null);
  const guide = useRef<HTMLElement>(null);
  function openWalkthrough() {
    setWalkthroughStep(0);
    walkthrough.current?.showModal();
  }
  function jump(node: HTMLElement | null) {
    if (!node) return;
    node.focus({ preventScroll: true });
    node.scrollIntoView({ block: 'center', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  }
  return <SiteFrame tools={<nav className="public-nav" aria-label="Introduction"><button onClick={() => jump(guide.current)}>How it works</button>
          <button className="desk-access" onClick={onWorkspace}>{signedIn ? 'Open workspace' : 'Sign in'} <ArrowUpRight size={16}/></button>
          {!signedIn && <button className="desk-access" onClick={onRegister}>Create account</button>}
        </nav>}>
    <main className="public-main">
      {notice && <p role="status" className="desk-notice">{notice}</p>}
      <div className="public-hero">
        <div className="public-intro">
          <h1>Before you trust<br/>the offer,<br/><em>trace it.</em></h1>
          <p>Casework investigates suspicious job offers. It pulls details from messages and screenshots, checks claims against sources, and connects cases that reuse the same identifiers.</p>
          <button className="desk-primary" aria-haspopup="dialog" onClick={openWalkthrough}>Explore a sample case <ArrowRight size={18}/></button>
        </div>
        <section className="dossier-stage" aria-label="Interactive sample case">
          <div className="dossier-folder"><div className="folder-tab"><Files size={15}/> Sample case</div>
            <div className="dossier-page">
              <div className="dossier-top"><span>CASE / 014</span><span>FICTIONAL</span></div>
              <div className="dossier-selector" role="group" aria-label="Sample investigation steps">{stages.map((entry, index) =>
                <button key={entry.title} aria-pressed={active === index} onClick={() => setActive(index)}>{entry.title}</button>)}</div>
              <StageContent index={active}/>
              <button className="dossier-next" onClick={() => setActive((active + 1) % stages.length)}>{['Check the source', 'See the case link', 'Back to the offer'][active]} <ArrowRight size={15}/></button>
            </div>
          </div>
        </section>
      </div>
      <dialog ref={walkthrough} className="sample-walkthrough" aria-labelledby="walkthrough-title">
        <header><h2 id="walkthrough-title">Sample case walkthrough</h2>
          <button className="walkthrough-close" aria-label="Close walkthrough" onClick={() => walkthrough.current?.close()}><X size={18}/></button>
        </header>
        <p className="dossier-source">Fictional case 014 · Step {walkthroughStep + 1} of {stages.length} · {stages[walkthroughStep].title}</p>
        <StageContent index={walkthroughStep}/>
        <footer>
          <button className="walkthrough-back" disabled={walkthroughStep === 0} onClick={() => setWalkthroughStep(walkthroughStep - 1)}>Back</button>
          <button className="desk-primary" onClick={() => {
            if (walkthroughStep === stages.length - 1) walkthrough.current?.close();
            else setWalkthroughStep(walkthroughStep + 1);
          }}>{['Check the source', 'See the case link', 'Finish walkthrough'][walkthroughStep]} <ArrowRight size={16}/></button>
        </footer>
      </dialog>
      <section className="public-guide" ref={guide} tabIndex={-1} aria-labelledby="desk-guide-title">
        <h2 id="desk-guide-title">How a case comes together</h2>
        <div className="guide-grid">
          <div><ScanText/><h3>Read the offer</h3><p>Extract names, contact details and payment requests from text, images or PDFs.</p></div>
          <div><ShieldCheck/><h3>Check the claim</h3><p>Compare the offer with traceable records. See the source finding alongside the model’s risk estimate.</p></div>
          <div><Link2/><h3>Follow the connection</h3><p>Inspect identifiers shared across cases and export a report with the evidence behind each finding.</p></div>
        </div>
      </section>
    </main>
      <footer className="public-footer"><span>Casework · Recruitment investigation</span>{children}</footer>
  </SiteFrame>;
}
