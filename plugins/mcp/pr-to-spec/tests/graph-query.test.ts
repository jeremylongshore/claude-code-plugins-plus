import { describe, expect, it } from "vitest";
import type { IntentGraph } from "../src/core/graph/edge.js";
import type { IntentNode } from "../src/core/graph/node.js";
import {
	addEdge,
	buildChildMap,
	createEmptyGraph,
	upsertNode,
} from "../src/core/graph/propagation.js";
import {
	computeAggregateConfidence,
	computeGraphStats,
	findImpactedNodes,
	getAncestors,
	getDescendants,
	getNodesByType,
} from "../src/core/graph/query.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeNode(
	id: string,
	type: IntentNode["node_type"] = "spec_fragment",
	overrides: Partial<IntentNode> = {},
): IntentNode {
	return {
		node_id: id,
		node_type: type,
		content: { data: id },
		parent_ids: [],
		confidence: 1,
		source: "heuristic",
		invalidated_at: null,
		version: 1,
		created_at: "2026-03-17T00:00:00.000Z",
		updated_at: "2026-03-17T00:00:00.000Z",
		...overrides,
	};
}

/**
 * Build a simple DAG:
 *   A → B → D
 *   A → C → D
 *       C → E
 */
function buildTestGraph(): IntentGraph {
	const graph = createEmptyGraph();
	upsertNode(graph, makeNode("A", "project_intent", { confidence: 0.9 }));
	upsertNode(graph, makeNode("B", "task_plan", { parent_ids: ["A"], confidence: 0.8 }));
	upsertNode(graph, makeNode("C", "change_intent", { parent_ids: ["A"], confidence: 0.7 }));
	upsertNode(graph, makeNode("D", "spec_fragment", { parent_ids: ["B", "C"], confidence: 1.0 }));
	upsertNode(graph, makeNode("E", "decision", { parent_ids: ["C"], confidence: 0.6 }));
	return graph;
}

// ---------------------------------------------------------------------------
// buildChildMap
// ---------------------------------------------------------------------------

describe("buildChildMap", () => {
	it("builds adjacency from parent_ids", () => {
		const graph = buildTestGraph();
		const childMap = buildChildMap(graph);
		expect(childMap.get("A")?.sort()).toEqual(["B", "C"]);
		expect(childMap.get("B")).toEqual(["D"]);
		expect(childMap.get("C")?.sort()).toEqual(["D", "E"]);
	});

	it("includes derives_from edges", () => {
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("X"));
		upsertNode(graph, makeNode("Y"));
		addEdge(graph, {
			source_id: "Y",
			target_id: "X",
			edge_type: "derives_from",
		});
		const childMap = buildChildMap(graph);
		expect(childMap.get("X")).toEqual(["Y"]);
	});

	it("returns empty map for empty graph", () => {
		const graph = createEmptyGraph();
		const childMap = buildChildMap(graph);
		expect(childMap.size).toBe(0);
	});
});

// ---------------------------------------------------------------------------
// getDescendants
// ---------------------------------------------------------------------------

describe("getDescendants", () => {
	it("returns all downstream nodes from root", () => {
		const graph = buildTestGraph();
		const desc = getDescendants(graph, "A");
		expect(desc.sort()).toEqual(["B", "C", "D", "E"]);
	});

	it("returns partial subtree from mid-node", () => {
		const graph = buildTestGraph();
		const desc = getDescendants(graph, "C");
		expect(desc.sort()).toEqual(["D", "E"]);
	});

	it("returns empty for leaf node", () => {
		const graph = buildTestGraph();
		expect(getDescendants(graph, "D")).toEqual([]);
		expect(getDescendants(graph, "E")).toEqual([]);
	});

	it("handles node with no children gracefully", () => {
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("solo"));
		expect(getDescendants(graph, "solo")).toEqual([]);
	});
});

// ---------------------------------------------------------------------------
// getAncestors
// ---------------------------------------------------------------------------

describe("getAncestors", () => {
	it("returns all upstream nodes from leaf", () => {
		const graph = buildTestGraph();
		const anc = getAncestors(graph, "D");
		expect(anc.sort()).toEqual(["A", "B", "C"]);
	});

	it("returns direct parents from mid-node", () => {
		const graph = buildTestGraph();
		const anc = getAncestors(graph, "B");
		expect(anc).toEqual(["A"]);
	});

	it("returns empty for root node", () => {
		const graph = buildTestGraph();
		expect(getAncestors(graph, "A")).toEqual([]);
	});

	it("follows derives_from edges backward", () => {
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("X"));
		upsertNode(graph, makeNode("Y"));
		addEdge(graph, {
			source_id: "Y",
			target_id: "X",
			edge_type: "derives_from",
		});
		const anc = getAncestors(graph, "Y");
		expect(anc).toEqual(["X"]);
	});
});

// ---------------------------------------------------------------------------
// getNodesByType
// ---------------------------------------------------------------------------

describe("getNodesByType", () => {
	it("filters nodes by type", () => {
		const graph = buildTestGraph();
		const decisions = getNodesByType(graph, "decision");
		expect(decisions).toHaveLength(1);
		expect(decisions[0].node_id).toBe("E");
	});

	it("returns empty array when no match", () => {
		const graph = buildTestGraph();
		const feedback = getNodesByType(graph, "feedback");
		expect(feedback).toEqual([]);
	});

	it("returns multiple nodes of same type", () => {
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("f1", "spec_fragment"));
		upsertNode(graph, makeNode("f2", "spec_fragment"));
		upsertNode(graph, makeNode("d1", "decision"));
		const frags = getNodesByType(graph, "spec_fragment");
		expect(frags).toHaveLength(2);
	});
});

// ---------------------------------------------------------------------------
// computeAggregateConfidence
// ---------------------------------------------------------------------------

describe("computeAggregateConfidence", () => {
	it("returns MIN confidence across ancestor chain (weakest-link)", () => {
		const graph = buildTestGraph();
		// D has ancestors A(0.9), B(0.8), C(0.7). D itself is 1.0. Min = 0.7
		expect(computeAggregateConfidence(graph, "D")).toBe(0.7);
	});

	it("returns own confidence for root node (no ancestors)", () => {
		const graph = buildTestGraph();
		expect(computeAggregateConfidence(graph, "A")).toBe(0.9);
	});

	it("considers self confidence in the minimum", () => {
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("parent", "project_intent", { confidence: 0.9 }));
		upsertNode(
			graph,
			makeNode("child", "spec_fragment", { parent_ids: ["parent"], confidence: 0.3 }),
		);
		expect(computeAggregateConfidence(graph, "child")).toBe(0.3);
	});

	it("returns 0 for non-existent node", () => {
		const graph = createEmptyGraph();
		expect(computeAggregateConfidence(graph, "nonexistent")).toBe(0);
	});
});

// ---------------------------------------------------------------------------
// findImpactedNodes
// ---------------------------------------------------------------------------

describe("findImpactedNodes", () => {
	it("finds all downstream nodes with distances", () => {
		const graph = buildTestGraph();
		const report = findImpactedNodes(graph, ["A"]);
		expect(report.total_impacted).toBe(4);
		// B and C are distance 1, D is distance 2 (via B or C), E is distance 2 (via C)
		const byId = Object.fromEntries(report.impacted_nodes.map((n) => [n.node_id, n]));
		expect(byId.B.distance).toBe(1);
		expect(byId.C.distance).toBe(1);
		expect(byId.D.distance).toBe(2);
		expect(byId.E.distance).toBe(2);
	});

	it("handles multiple changed nodes", () => {
		const graph = buildTestGraph();
		const report = findImpactedNodes(graph, ["B", "C"]);
		expect(report.changed_node_ids).toEqual(["B", "C"]);
		const ids = report.impacted_nodes.map((n) => n.node_id).sort();
		expect(ids).toEqual(["D", "E"]);
	});

	it("returns empty for leaf node changes", () => {
		const graph = buildTestGraph();
		const report = findImpactedNodes(graph, ["D"]);
		expect(report.total_impacted).toBe(0);
	});

	it("does not mutate the graph (read-only)", () => {
		const graph = buildTestGraph();
		const beforeInvalidated = graph.nodes.map((n) => n.invalidated_at);
		findImpactedNodes(graph, ["A"]);
		const afterInvalidated = graph.nodes.map((n) => n.invalidated_at);
		expect(afterInvalidated).toEqual(beforeInvalidated);
	});
});

// ---------------------------------------------------------------------------
// computeGraphStats
// ---------------------------------------------------------------------------

describe("computeGraphStats", () => {
	it("computes stats for test graph", () => {
		const graph = buildTestGraph();
		const stats = computeGraphStats(graph);
		expect(stats.total_nodes).toBe(5);
		expect(stats.total_edges).toBe(0); // no explicit edges, only parent_ids
		expect(stats.stale_nodes).toBe(0);
		expect(stats.nodes_by_type).toEqual({
			project_intent: 1,
			task_plan: 1,
			change_intent: 1,
			spec_fragment: 1,
			decision: 1,
		});
	});

	it("computes confidence stats", () => {
		const graph = buildTestGraph();
		const stats = computeGraphStats(graph);
		// Confidences: 0.9, 0.8, 0.7, 1.0, 0.6 → min=0.6, avg=0.8
		expect(stats.min_confidence).toBe(0.6);
		expect(stats.avg_confidence).toBeCloseTo(0.8, 5);
	});

	it("counts stale nodes", () => {
		const graph = buildTestGraph();
		const node = graph.nodes.find((n) => n.node_id === "B") as (typeof graph.nodes)[number];
		node.invalidated_at = "2026-03-17T00:00:00.000Z";
		const stats = computeGraphStats(graph);
		expect(stats.stale_nodes).toBe(1);
	});

	it("counts edge types", () => {
		const graph = buildTestGraph();
		addEdge(graph, { source_id: "B", target_id: "A", edge_type: "derives_from" });
		addEdge(graph, { source_id: "C", target_id: "A", edge_type: "derives_from" });
		addEdge(graph, { source_id: "D", target_id: "B", edge_type: "satisfies" });
		const stats = computeGraphStats(graph);
		expect(stats.total_edges).toBe(3);
		expect(stats.edges_by_type).toEqual({
			derives_from: 2,
			satisfies: 1,
		});
	});

	it("handles empty graph", () => {
		const graph = createEmptyGraph();
		const stats = computeGraphStats(graph);
		expect(stats.total_nodes).toBe(0);
		expect(stats.total_edges).toBe(0);
		expect(stats.avg_confidence).toBe(0);
		expect(stats.min_confidence).toBe(0);
	});
});
