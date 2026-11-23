import assert from 'node:assert/strict';
import test from 'node:test';
import { dashboardHref, dashboardRoute, dashboardSections } from '../src/dashboard-navigation.ts';

test('every dashboard and case breadcrumb resolves to its own section', () => {
  for (const section of dashboardSections) {
    assert.deepEqual(dashboardRoute(dashboardHref(section), 'admin'), { section, caseId: null });
    assert.deepEqual(dashboardRoute(dashboardHref(section, 12), 'admin'), { section, caseId: 12 });
  }
});

test('direct dashboard links respect role access', () => {
  assert.equal(dashboardRoute('#accounts', 'investigator').section, 'Cases');
  assert.equal(dashboardRoute('#accounts', 'reviewer').section, 'Accounts');
  assert.deepEqual(dashboardRoute('#evidence-graph/case/7', 'analyst'), { section: 'Cases', caseId: null });
  assert.equal(dashboardRoute('#campaigns', 'analyst').section, 'Campaigns');
});

test('default case dashboard, demo bookmarks and malformed detail links', () => {
  for (const hash of ['', '#casework', '#unknown', '#cases/case/0', '#cases/case/-1', '#cases/case/5/extra'])
    assert.deepEqual(dashboardRoute(hash, 'investigator'), { section: 'Cases', caseId: null });
  assert.deepEqual(dashboardRoute('#casework/case/12', 'investigator'), { section: 'Cases', caseId: 12 });
  assert.equal(dashboardRoute('#vacancy-demo', 'investigator').section, 'Vacancy demo');
});
