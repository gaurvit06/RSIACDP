export const dashboardSections = [
  'Cases', 'Campaigns', 'Posting insights', 'Evidence graph', 'Evidence corpus',
  'Corrections', 'Disposition reviews', 'Accounts', 'Vacancy demo',
] as const;

export type Dashboard = typeof dashboardSections[number];

export function dashboardHref(section: Dashboard, caseId?: number) {
  const slug = section.toLowerCase().replaceAll(' ', '-');
  return caseId ? `#${slug}/case/${caseId}` : `#${slug}`;
}

export function dashboardRoute(hash: string, role?: string) {
  const [slug, kind, value, ...extra] = hash.split('/');
  const found = slug === '#casework' ? 'Cases' : dashboardSections.find(label => dashboardHref(label) === slug);
  const section = found && dashboardAvailable(found, role) ? found : 'Cases';
  const id = Number(value);
  const caseId = found === section && kind === 'case' && /^[1-9]\d*$/.test(value ?? '')
    && Number.isSafeInteger(id) && extra.length === 0 ? id : null;
  return { section, caseId };
}

export function dashboardAvailable(section: Dashboard, role?: string) {
  if (role === "personal") return section === "Cases";
  if (['Accounts', 'Disposition reviews'].includes(section)) return role === 'reviewer' || role === 'admin';
  if (['Posting insights', 'Evidence graph', 'Evidence corpus', 'Corrections'].includes(section))
    return ['investigator', 'reviewer', 'admin'].includes(role ?? '');
  return true;
}
