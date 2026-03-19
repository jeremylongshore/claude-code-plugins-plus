import type { IntentEdge, IntentGraph } from "./edge.js";
import type { IntentNode } from "./node.js";

/**
 * Build a parent → children adjacency map from parent_ids and derives_from edges.
 * Shared by propagation and query engines.
 */
export function buildChildMap(graph: IntentGraph): Map<string, string[]> {
	const childrenOf = new Map<string, string[]>();
	for (const node of graph.nodes) {
		for (const parentId of node.parent_ids) {
			const children = childrenOf.get(parentId) ?? [];
			children.push(node.node_id);
			childrenOf.set(parentId, children);
		}
	}
	// Also consider derives_from edges
	for (const edge of graph.edges) {
		if (edge.edge_type === "derives_from") {
			// source derives_from target, so target is the parent
			const children = childrenOf.get(edge.target_id) ?? [];
			children.push(edge.source_id);
			childrenOf.set(edge.target_id, children);
		}
	}
	return childrenOf;
}

/**
 * Mark a node as invalidated and propagate to all downstream children.
 * Implements the SemanticForge invalidation rule:
 *   When a node's content changes, mark all children as stale.
 *   Re-derive stale children. If hash unchanged, stop propagation.
 *
 * Returns the set of invalidated node IDs.
 */
export function propagateInvalidation(graph: IntentGraph, changedNodeId: string): Set<string> {
	const invalidated = new Set<string>();
	const now = new Date().toISOString();

	const childrenOf = buildChildMap(graph);

	// BFS from changed node
	const queue = [changedNodeId];
	invalidated.add(changedNodeId);

	while (queue.length > 0) {
		const current = queue.shift() as string;
		const children = childrenOf.get(current) ?? [];
		for (const childId of children) {
			if (!invalidated.has(childId)) {
				invalidated.add(childId);
				const node = graph.nodes.find((n) => n.node_id === childId);
				if (node) {
					node.invalidated_at = now;
				}
				queue.push(childId);
			}
		}
	}

	// Mark the changed node itself
	const changedNode = graph.nodes.find((n) => n.node_id === changedNodeId);
	if (changedNode) {
		changedNode.invalidated_at = now;
	}

	return invalidated;
}

/**
 * Get all stale (invalidated) nodes in the graph.
 */
export function getStaleNodes(graph: IntentGraph): IntentNode[] {
	return graph.nodes.filter((n) => n.invalidated_at !== null);
}

/**
 * Clear invalidation for a node (after re-derivation).
 * Bumps the version to track successful re-derivation count.
 */
export function clearInvalidation(graph: IntentGraph, nodeId: string): void {
	const node = graph.nodes.find((n) => n.node_id === nodeId);
	if (node) {
		node.invalidated_at = null;
		node.version += 1;
		node.updated_at = new Date().toISOString();
	}
}

/**
 * Add a node to the graph. If a node with the same ID exists, update it.
 */
export function upsertNode(graph: IntentGraph, node: IntentNode): void {
	const existing = graph.nodes.findIndex((n) => n.node_id === node.node_id);
	if (existing >= 0) {
		graph.nodes[existing] = node;
	} else {
		graph.nodes.push(node);
	}
	graph.updated_at = new Date().toISOString();
}

/**
 * Add an edge to the graph.
 */
export function addEdge(graph: IntentGraph, edge: IntentEdge): void {
	const exists = graph.edges.some(
		(e) =>
			e.source_id === edge.source_id &&
			e.target_id === edge.target_id &&
			e.edge_type === edge.edge_type,
	);
	if (!exists) {
		graph.edges.push(edge);
		graph.updated_at = new Date().toISOString();
	}
}

/**
 * Create an empty IntentGraph.
 */
export function createEmptyGraph(): IntentGraph {
	return {
		version: 1,
		nodes: [],
		edges: [],
		updated_at: new Date().toISOString(),
	};
}
