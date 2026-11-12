import assert from 'node:assert/strict';
import test from 'node:test';

import { filterGraphData, graphNodeReviewLabel } from '../src/graph-filters.ts';

const nodes = [
  { id: 'case:1', type: 'case', label: 'RC-00000001' },
  { id: 'case:2', type: 'case', label: 'RC-00000002' },
  { id: 'phone:shared', type: 'phone', label: '••••1234', review_status: 'confirmed' },
  { id: 'email:other', type: 'email', label: 'a***@example.org', review_status: 'unreviewed' },
  { id: 'evidence:1', type: 'evidence', label: 'local · result', case_id: 1, source_type: 'curated_local_corpus', retrieved_at: '2026-10-20T10:00:00Z', review_status: 'relevant' },
  { id: 'evidence:2', type: 'evidence', label: 'platform · result', case_id: 2, source_type: 'platform', retrieved_at: '2026-10-25T10:00:00Z', review_status: 'irrelevant' },
];
const edges = [
  { from: 'case:1', to: 'phone:shared', kind: 'contains_identifier', review_status: 'confirmed' },
  { from: 'case:2', to: 'phone:shared', kind: 'contains_identifier', review_status: 'needs_review' },
  { from: 'case:1', to: 'email:other', kind: 'contains_identifier', review_status: 'unreviewed' },
  { from: 'case:1', to: 'evidence:1', kind: 'has_evidence', review_status: 'relevant' },
  { from: 'evidence:1', to: 'phone:shared', kind: 'checks_identifier', review_status: 'relevant' },
  { from: 'case:2', to: 'evidence:2', kind: 'has_evidence', review_status: 'irrelevant' },
];
const noFilters = { entityType: 'all', sourceType: 'all', fromDate: '', toDate: '', reviewStatus: 'all' };

test('review status filters shared identifiers using each relationship, not the node property', () => {
  const result = filterGraphData(nodes, edges, { ...noFilters, reviewStatus: 'needs_review' });
  assert.deepEqual(result.nodes.map(node => node.id), ['case:1', 'case:2', 'phone:shared']);
  assert.deepEqual(result.edges.map(edge => [edge.from, edge.to]), [['case:2', 'phone:shared']]);
  assert.equal(graphNodeReviewLabel(nodes[2], edges), 'varies by case');
});

test('identifier label does not mix extraction review with evidence relevance', () => {
  const singleCaseEdges = [
    { from: 'case:1', to: 'phone:shared', kind: 'contains_identifier', review_status: 'confirmed' },
    { from: 'evidence:1', to: 'phone:shared', kind: 'checks_identifier', review_status: 'relevant' },
  ];
  assert.equal(graphNodeReviewLabel(nodes[2], singleCaseEdges), 'confirmed');
  assert.equal(graphNodeReviewLabel(nodes[2], []), 'No linked case review');
});

test('entity type, source type, and retrieval date filters narrow graph records', () => {
  const result = filterGraphData(nodes, edges, {
    ...noFilters,
    entityType: 'phone',
    sourceType: 'curated_local_corpus',
    fromDate: '2026-10-19',
    toDate: '2026-10-21',
  });
  assert.deepEqual(result.nodes.map(node => node.id), ['case:1', 'case:2', 'phone:shared', 'evidence:1']);
  assert.deepEqual(result.edges.map(edge => [edge.from, edge.to]), [
    ['case:1', 'phone:shared'],
    ['case:1', 'evidence:1'],
    ['evidence:1', 'phone:shared'],
  ]);
});

test('date bounds exclude evidence with missing retrieval timestamps', () => {
  const missingDate = { id: 'evidence:missing', type: 'evidence', label: 'source · result', source_type: 'curated_local_corpus' };
  const result = filterGraphData([...nodes, missingDate], [...edges, { from: 'case:2', to: 'evidence:missing', kind: 'has_evidence' }], {
    ...noFilters,
    fromDate: '2026-10-01',
  });
  assert.equal(result.nodes.some(node => node.id === 'evidence:missing'), false);
});
