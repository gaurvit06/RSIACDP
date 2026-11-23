import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { CaseworkBrand } from './CaseworkBrand';

type FrameProps = {
  workspace?: boolean;
  trail?: ReactNode;
  tools: ReactNode;
  children: ReactNode;
};

export function SiteFrame({ workspace = false, trail, tools, children }: FrameProps) {
  return <div className={'site-frame ' + (workspace ? 'workspace-frame' : 'public-desk')}>
    <div className={'site-sheet ' + (workspace ? 'shell' : 'public-sheet')}>
      <header className="site-masthead">
        <a className="site-home" href="#home" aria-label="Casework home"><CaseworkBrand/></a>
        {trail}
        <div className="site-tools">{tools}</div>
      </header>
      {children}
    </div>
  </div>;
}

export function PageHeader({ title, icon: Icon, children, action, meta }: {
  title: string; icon: LucideIcon; children?: ReactNode; action?: ReactNode; meta?: ReactNode;
}) {
  return <header className="page-heading route-intro">
    <div className="route-title"><span className="route-icon"><Icon size={22} aria-hidden="true"/></span>
      <div>{meta}<h1>{title}</h1>{children && <p>{children}</p>}</div>
    </div>{action}
  </header>;
}
