import type { ContractResult } from "../contracts/schema.js";
import type { GateResult } from "../gate/policy.js";
import { computeContentHash, computeFragmentId } from "../schema/prompt-spec.js";
import type { IntentGraph } from "./edge.js";
import type { IntentNode } from "./node.js";
import { upsertNode } from "./propagation.js";

/**
 * Materialize a gate result into the graph as gate_check nodes.
 * Returns the IDs of the created nodes.
 */
export function materializeGateResult(graph: IntentGraph, gateResult: GateResult): string[] {
	const now = new Date().toISOString();
	const ids: string[] = [];

	for (const check of gateResult.checks) {
		const content = {
			check_name: check.name,
			passed: check.passed,
			detail: check.detail,
			evaluated_at: now,
		};
		const hash = computeContentHash(content);
		const nodeId = computeFragmentId(hash);

		const node: IntentNode = {
			node_id: nodeId,
			node_type: "gate_check",
			content,
			parent_ids: [],
			confidence: check.passed ? 1 : 0,
			source: "heuristic",
			invalidated_at: null,
			version: 1,
			created_at: now,
			updated_at: now,
		};

		upsertNode(graph, node);
		ids.push(nodeId);
	}

	return ids;
}

/**
 * Materialize contract results into the graph as contract_check nodes.
 * Returns the IDs of the created nodes.
 */
export function materializeContractResult(
	graph: IntentGraph,
	contractResults: ContractResult[],
): string[] {
	const now = new Date().toISOString();
	const ids: string[] = [];

	for (const result of contractResults) {
		const content = {
			contract_id: result.contract_id,
			contract_type: result.contract_type,
			passed: result.passed,
			severity: result.severity,
			detail: result.detail,
			evaluated_at: now,
		};
		const hash = computeContentHash(content);
		const nodeId = computeFragmentId(hash);

		const node: IntentNode = {
			node_id: nodeId,
			node_type: "contract_check",
			content,
			parent_ids: [],
			confidence: result.passed ? 1 : 0,
			source: "heuristic",
			invalidated_at: null,
			version: 1,
			created_at: now,
			updated_at: now,
		};

		upsertNode(graph, node);
		ids.push(nodeId);
	}

	return ids;
}
