export type GraphNode = {
  id: string;
  type: string;
  label: string;
  case_id?: number;
  created_at?: string | null;
  source_type?: string;
  source_ref?: string;
  outcome?: string;
  authority?: string;
  retrieved_at?: string | null;
  review_status?: string;
};

export type GraphEdge = {
  from: string;
  to: string;
  kind: string;
  review_status?: string;
  reasons?: string[];
  strength?: number;
  rule_version?: string;
};

export type GraphFilters = {
  entityType: string;
  sourceType: string;
  fromDate: string;
  toDate: string;
  reviewStatus: string;
};

export function filterGraphData(nodes: GraphNode[], edges: GraphEdge[], filters: GraphFilters) {
  const hasEvidenceDimension = filters.sourceType !== 'all' || Boolean(filters.fromDate || filters.toDate);
  const evidenceDimensionNodes = nodes.filter(node => {
    if (filters.entityType !== 'all' && !['case', 'evidence'].includes(node.type) && node.type !== filters.entityType) return false;
    if (filters.sourceType !== 'all' && node.type === 'evidence' && node.source_type !== filters.sourceType) return false;
    if ((filters.fromDate || filters.toDate) && node.type === 'evidence') {
      const date = node.retrieved_at?.slice(0, 10) ?? '';
      if (!date || (filters.fromDate && date < filters.fromDate) || (filters.toDate && date > filters.toDate)) return false;
    }
    return true;
  });
  const matchingEvidenceIds = new Set(evidenceDimensionNodes.filter(node => node.type === 'evidence').map(node => node.id));
  const matchingCaseEntityPairs = new Set<string>();
  const matchingEntityIds = new Set<string>();
  if (hasEvidenceDimension) {
    for (const evidence of evidenceDimensionNodes.filter(node => node.type === 'evidence' && node.case_id !== undefined)) {
      for (const edge of edges.filter(item => item.kind === 'checks_identifier' && (item.from === evidence.id || item.to === evidence.id))) {
        const entityId = edge.from === evidence.id ? edge.to : edge.from;
        matchingCaseEntityPairs.add(`case:${evidence.case_id}|${entityId}`);
        matchingEntityIds.add(entityId);
      }
    }
  }
  const dimensionFilteredNodes = evidenceDimensionNodes.filter(node => (
    !hasEvidenceDimension
    || ['case', 'evidence'].includes(node.type)
    || matchingEntityIds.has(node.id)
  ));
  const dimensionFilteredIds = new Set(dimensionFilteredNodes.map(node => node.id));
  const dimensionFilteredEdges = edges.filter(edge => {
    if (!dimensionFilteredIds.has(edge.from) || !dimensionFilteredIds.has(edge.to)) return false;
    if (!hasEvidenceDimension) return true;
    if (edge.kind === 'has_evidence' || edge.kind === 'checks_identifier') {
      return matchingEvidenceIds.has(edge.from) || matchingEvidenceIds.has(edge.to);
    }
    if (edge.kind === 'contains_identifier') return matchingCaseEntityPairs.has(`${edge.from}|${edge.to}`);
    return true;
  });
  if (filters.reviewStatus === 'all') return { nodes: dimensionFilteredNodes, edges: dimensionFilteredEdges };

  // Entity review is per case-to-identifier relationship. A shared identifier's
  // node property can reflect only one of several cases, so filter by edges.
  const matchingEdges = dimensionFilteredEdges.filter(edge => edge.review_status === filters.reviewStatus);
  const matchingNodeIds = new Set(matchingEdges.flatMap(edge => [edge.from, edge.to]));
  return {
    nodes: dimensionFilteredNodes.filter(node => node.type === 'case' || matchingNodeIds.has(node.id)),
    edges: matchingEdges,
  };
}

export function graphNodeReviewLabel(node: GraphNode, edges: GraphEdge[]): string {
  if (node.type === 'case') return '';
  const relationshipKind = node.type === 'evidence' ? 'has_evidence' : 'contains_identifier';
  const statuses = new Set(edges
    .filter(edge => edge.kind === relationshipKind && edge.review_status && (edge.from === node.id || edge.to === node.id))
    .map(edge => edge.review_status!));
  if (statuses.size > 1) return 'varies by case';
  if (statuses.size === 1) return [...statuses][0];
  return node.type === 'evidence' ? node.review_status ?? '' : 'No linked case review';
}
