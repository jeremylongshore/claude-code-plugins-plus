import type { IntentGraph } from "./edge.js";
import type { IntentNode, IntentNodeType } from "./node.js";
import { buildChildMap } from "./propagation.js";

export interface ImpactReport {
	changed_node_ids: string[];
	impacted_nodes: Array<{
		node_id: string;
		node_type: IntentNodeType;
		distance: number;
		confidence: number;
	}>;
	total_impacted: number;
}

export interface GraphStats {
	total_nodes: number;
	nodes_by_type: Record<string, number>;
	total_edges: number;
	edges_by_type: Record<string, number>;
	stale_nodes: number;
	avg_confidence: number;
	min_confidence: number;
}

/**
 * BFS forward: get all descendants of a node via the child map.
 */
export function getDescendants(graph: IntentGraph, nodeId: string): string[] {
	const childMap = buildChildMap(graph);
	const visited = new Set<string>();
	const queue = [nodeId];
	visited.add(nodeId);

	while (queue.length > 0) {
		const current = queue.shift() as (typeof queue)[number];
		const children = childMap.get(current) ?? [];
		for (const childId of children) {
			if (!visited.has(childId)) {
				visited.add(childId);
				queue.push(childId);
			}
		}
	}

	// Remove the starting node itself — return only descendants
	visited.delete(nodeId);
	return [...visited];
}

/**
 * BFS backward: get all ancestors of a node via parent_ids and derives_from edges.
 */
export function getAncestors(graph: IntentGraph, nodeId: string): string[] {
	// Build child → parents map (reverse of childMap)
	const parentsOf = new Map<string, string[]>();
	for (const node of graph.nodes) {
		for (const parentId of node.parent_ids) {
			const parents = parentsOf.get(node.node_id) ?? [];
			parents.push(parentId);
			parentsOf.set(node.node_id, parents);
		}
	}
	for (const edge of graph.edges) {
		if (edge.edge_type === "derives_from") {
			const parents = parentsOf.get(edge.source_id) ?? [];
			parents.push(edge.target_id);
			parentsOf.set(edge.source_id, parents);
		}
	}

	const visited = new Set<string>();
	const queue = [nodeId];
	visited.add(nodeId);

	while (queue.length > 0) {
		const current = queue.shift() as (typeof queue)[number];
		const parents = parentsOf.get(current) ?? [];
		for (const parentId of parents) {
			if (!visited.has(parentId)) {
				visited.add(parentId);
				queue.push(parentId);
			}
		}
	}

	visited.delete(nodeId);
	return [...visited];
}

/**
 * Filter graph nodes by type.
 */
export function getNodesByType(graph: IntentGraph, type: IntentNodeType): IntentNode[] {
	return graph.nodes.filter((n) => n.node_type === type);
}

/**
 * Compute aggregate confidence for a node: MIN confidence across the ancestor chain.
 * Weakest-link model — the chain is only as strong as its weakest ancestor.
 */
export function computeAggregateConfidence(graph: IntentGraph, nodeId: string): number {
	const node = graph.nodes.find((n) => n.node_id === nodeId);
	if (!node) return 0;

	const ancestorIds = getAncestors(graph, nodeId);
	let minConfidence = node.confidence;

	for (const ancestorId of ancestorIds) {
		const ancestor = graph.nodes.find((n) => n.node_id === ancestorId);
		if (ancestor) {
			minConfidence = Math.min(minConfidence, ancestor.confidence);
		}
	}

	return minConfidence;
}

/**
 * Read-only impact analysis: find all nodes impacted by changes to the given node IDs.
 * Unlike propagateInvalidation, this does NOT mutate the graph.
 */
export function findImpactedNodes(graph: IntentGraph, changedNodeIds: string[]): ImpactReport {
	const childMap = buildChildMap(graph);
	const impacted = new Map<string, number>(); // node_id → distance

	for (const changedId of changedNodeIds) {
		const queue: Array<{ id: string; distance: number }> = [{ id: changedId, distance: 0 }];
		const visited = new Set<string>();
		visited.add(changedId);

		while (queue.length > 0) {
			const { id, distance } = queue.shift() as (typeof queue)[number];
			const children = childMap.get(id) ?? [];
			for (const childId of children) {
				if (!visited.has(childId)) {
					visited.add(childId);
					const existing = impacted.get(childId);
					const newDist = distance + 1;
					if (existing === undefined || newDist < existing) {
						impacted.set(childId, newDist);
					}
					queue.push({ id: childId, distance: newDist });
				}
			}
		}
	}

	const impactedNodes = [...impacted.entries()].map(([nodeId, distance]) => {
		const node = graph.nodes.find((n) => n.node_id === nodeId) as IntentNode;
		return {
			node_id: nodeId,
			node_type: node.node_type,
			distance,
			confidence: node.confidence,
		};
	});

	// Sort by distance (closest first), then by node_id for stability
	impactedNodes.sort((a, b) => a.distance - b.distance || a.node_id.localeCompare(b.node_id));

	return {
		changed_node_ids: changedNodeIds,
		impacted_nodes: impactedNodes,
		total_impacted: impactedNodes.length,
	};
}

/**
 * Compute aggregate stats for the graph.
 */
export function computeGraphStats(graph: IntentGraph): GraphStats {
	const nodesByType: Record<string, number> = {};
	const edgesByType: Record<string, number> = {};
	let totalConfidence = 0;
	let minConfidence = graph.nodes.length > 0 ? 1 : 0;
	let staleCount = 0;

	for (const node of graph.nodes) {
		nodesByType[node.node_type] = (nodesByType[node.node_type] ?? 0) + 1;
		totalConfidence += node.confidence;
		minConfidence = Math.min(minConfidence, node.confidence);
		if (node.invalidated_at !== null) staleCount++;
	}

	for (const edge of graph.edges) {
		edgesByType[edge.edge_type] = (edgesByType[edge.edge_type] ?? 0) + 1;
	}

	return {
		total_nodes: graph.nodes.length,
		nodes_by_type: nodesByType,
		total_edges: graph.edges.length,
		edges_by_type: edgesByType,
		stale_nodes: staleCount,
		avg_confidence: graph.nodes.length > 0 ? totalConfidence / graph.nodes.length : 0,
		min_confidence: minConfidence,
	};
}
