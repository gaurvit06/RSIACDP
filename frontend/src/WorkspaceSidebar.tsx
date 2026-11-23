import { useEffect, useRef, useState } from 'react';
import { LogOut, Menu, PanelLeftClose, PanelLeftOpen, ShieldCheck, X, type LucideIcon } from 'lucide-react';

import type { Dashboard } from './dashboard-navigation';

const preference = 'casework.sidebar.collapsed';
const mobileQuery = '(max-width: 700px)';

type Props = {
  entries: [Dashboard, LucideIcon][];
  section: string;
  count: number;
  user: { email: string; role: string };
  onNavigate: (label: Dashboard) => void;
  onLogout: () => void;
};

export function WorkspaceSidebar({ entries, section, count, user, onNavigate, onLogout }: Props) {
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem(preference) === 'true'; }
    catch { return false; }
  });
  const [mobileOpen, setMobileOpen] = useState(false);
  const mobileToggle = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const breakpoint = window.matchMedia(mobileQuery);
    const close = () => setMobileOpen(false);
    breakpoint.addEventListener('change', close);
    return () => breakpoint.removeEventListener('change', close);
  }, []);
  function toggleDesktop() {
    setCollapsed(!collapsed);
    try { localStorage.setItem(preference, String(!collapsed)); }
    catch { /* The current tab still retains the chosen layout. */ }
  }
  function closeMobile() {
    if (mobileOpen) {
      setMobileOpen(false);
      mobileToggle.current?.focus();
    }
  }
  const desktopLabel = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
  const mobileLabel = mobileOpen ? 'Close navigation' : 'Open navigation';
  return <aside className="sidebar" data-collapsed={collapsed} data-mobile-open={mobileOpen}
    onKeyDown={event => { if (event.key === 'Escape') closeMobile(); }}>
    <div className="sidebar-header">
      <span className="workspace-caption">Workspace</span>
      <button type="button" className="sidebar-toggle desktop-toggle" aria-label={desktopLabel} title={desktopLabel}
        aria-controls="workspace-navigation" aria-expanded={!collapsed} onClick={toggleDesktop}>
        {collapsed ? <PanelLeftOpen size={19}/> : <PanelLeftClose size={19}/>}
      </button>
      <button ref={mobileToggle} type="button" className="sidebar-toggle mobile-toggle" aria-label={mobileLabel}
        aria-controls="workspace-navigation" aria-expanded={mobileOpen} onClick={() => setMobileOpen(!mobileOpen)}>
        {mobileOpen ? <X size={20}/> : <Menu size={20}/>}
      </button>
    </div>
    <div className="sidebar-drawer"><div className="sidebar-drawer-body">
    <nav id="workspace-navigation" aria-label="Workspace">
      {entries.map(([label, Icon]) => <button type="button" key={label} aria-label={label} title={label}
        aria-current={section === label ? 'page' : undefined} className={`nav-item ${section === label ? 'active' : ''}`}
        onClick={() => { onNavigate(label); closeMobile(); }}>
        <Icon size={18}/><span>{label}</span>{label === 'Cases' && <small>{count}</small>}
      </button>)}
    </nav>
    <div className="sidebar-foot">
      <div className="privacy-chip"><ShieldCheck size={15}/><span>Private workspace</span></div>
      <div className="user-chip"><div className="avatar">{user.email.slice(0, 1).toUpperCase()}</div>
        <div className="user-label"><b>{user.email}</b><span>{user.role}</span></div>
        <button type="button" title="Sign out" aria-label="Sign out" onClick={onLogout}><LogOut size={16}/></button>
      </div>
    </div>
    </div></div>
  </aside>;
}
