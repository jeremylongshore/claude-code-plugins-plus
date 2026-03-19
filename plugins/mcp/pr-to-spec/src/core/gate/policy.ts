import { z } from "zod";
import type { ContractResult } from "../contracts/schema.js";
import { analyzeAssumptions } from "../decisions/classifier.js";
import type { IntentGraph } from "../graph/edge.js";
import { getStaleNodes } from "../graph/propagation.js";
import { computeAggregateConfidence, getNodesByType } from "../graph/query.js";
import type { Intent } from "../intent/schema.js";
import type { DiffSource } from "../sources/types.js";

export const IntentGatePolicySchema = z.object({
	require_approval: z.boolean().default(true),
	min_confidence: z.number().min(0).max(1).default(0.7),
	require_no_stale: z.boolean().default(true),
	require_no_must_ask: z.boolean().default(true),
	require_contracts_pass: z.boolean().default(false),
});

export type IntentGatePolicy = z.infer<typeof IntentGatePolicySchema>;

export interface GateCheck {
	name: string;
	passed: boolean;
	detail: string;
}

export interface GateResult {
	passed: boolean;
	checks: GateCheck[];
	blocking_checks: GateCheck[];
}

/**
 * Evaluate the intent gate policy against the current state.
 * Returns a GateResult with pass/fail and individual check details.
 */
export function evaluateGate(
	graph: IntentGraph,
	intent: Intent,
	diff: DiffSource | null,
	policy: IntentGatePolicy,
	contractResults?: ContractResult[],
): GateResult {
	const checks: GateCheck[] = [];

	// Check 1: Approval status
	if (policy.require_approval) {
		const approved = intent.status === "approved" || intent.status === "locked";
		checks.push({
			name: "approval",
			passed: approved,
			detail: approved
				? `Intent ${intent.status} by ${intent.approved_by ?? "unknown"}`
				: `Intent is "${intent.status}", requires approval`,
		});
	}

	// Check 2: Min confidence across graph
	if (graph.nodes.length > 0) {
		// Find the minimum aggregate confidence across all project_intent and change_intent nodes
		const intentNodes = [
			...getNodesByType(graph, "project_intent"),
			...getNodesByType(graph, "change_intent"),
		];
		let minAgg = 1;
		for (const node of intentNodes) {
			const agg = computeAggregateConfidence(graph, node.node_id);
			minAgg = Math.min(minAgg, agg);
		}
		// If no intent nodes, check all nodes
		if (intentNodes.length === 0) {
			for (const node of graph.nodes) {
				minAgg = Math.min(minAgg, node.confidence);
			}
		}
		const passed = minAgg >= policy.min_confidence;
		checks.push({
			name: "confidence",
			passed,
			detail: passed
				? `Min aggregate confidence ${minAgg.toFixed(2)} >= ${policy.min_confidence}`
				: `Min aggregate confidence ${minAgg.toFixed(2)} < ${policy.min_confidence}`,
		});
	}

	// Check 3: No stale nodes
	if (policy.require_no_stale) {
		const stale = getStaleNodes(graph);
		const passed = stale.length === 0;
		checks.push({
			name: "no_stale",
			passed,
			detail: passed
				? "No stale nodes in graph"
				: `${stale.length} stale node(s): ${stale.map((n) => n.node_id).join(", ")}`,
		});
	}

	// Check 4: No must_ask decisions
	if (policy.require_no_must_ask && diff) {
		const decisions = analyzeAssumptions(diff, intent);
		const mustAsk = decisions.filter((d) => d.action === "must_ask");
		const passed = mustAsk.length === 0;
		checks.push({
			name: "no_must_ask",
			passed,
			detail: passed
				? "No must_ask decisions detected"
				: `${mustAsk.length} must_ask decision(s): ${mustAsk.map((d) => d.question).join("; ")}`,
		});
	}

	// Check 5: Contracts pass
	if (policy.require_contracts_pass && contractResults) {
		const failed = contractResults.filter((cr) => !cr.passed && cr.severity === "blocking");
		const passed = failed.length === 0;
		checks.push({
			name: "contracts",
			passed,
			detail: passed
				? "All blocking contracts pass"
				: `${failed.length} blocking contract(s) failed: ${failed.map((f) => f.contract_id).join(", ")}`,
		});
	}

	const blockingChecks = checks.filter((c) => !c.passed);

	return {
		passed: blockingChecks.length === 0,
		checks,
		blocking_checks: blockingChecks,
	};
}
