import { Check, CircleAlert, CircleHelp, Minus } from 'lucide-react';
import { resultStyle } from './result-tone';

const icons = { positive: Check, risk: CircleAlert, uncertain: CircleHelp, neutral: Minus };

export function Assessment({ children }: { children: string }) {
  const [tone, explanation] = resultStyle(children);
  const Icon = icons[tone];
  return <span className="assessment" data-tone={tone} title={explanation}>
    <Icon aria-hidden="true" size={13} strokeWidth={2}/>{children}
  </span>;
}
