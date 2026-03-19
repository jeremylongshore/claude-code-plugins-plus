import { describe, expect, it } from "vitest";
import type { ContractResult } from "../src/core/contracts/schema.js";
import type { GateResult } from "../src/core/gate/policy.js";
import { materializeContractResult, materializeGateResult } from "../src/core/graph/materialize.js";
import { createEmptyGraph } from "../src/core/graph/propagation.js";
import { getNodesByType } from "../src/core/graph/query.js";

// ---------------------------------------------------------------------------
// materializeGateResult
// ---------------------------------------------------------------------------

describe("materializeGateResult", () => {
	it("creates gate_check nodes for each check", () => {
		const graph = createEmptyGraph();
		const gateResult: GateResult = {
			passed: false,
			checks: [
				{ name: "approval", passed: true, detail: "Intent approved by alice" },
				{ name: "confidence", passed: false, detail: "Min confidence 0.5 < 0.7" },
			],
			blocking_checks: [{ name: "confidence", passed: false, detail: "Min confidence 0.5 < 0.7" }],
		};

		const ids = materializeGateResult(graph, gateResult);
		expect(ids).toHaveLength(2);

		const gateNodes = getNodesByType(graph, "gate_check");
		expect(gateNodes).toHaveLength(2);
	});

	it("passing checks get confidence 1, failing get 0", () => {
		const graph = createEmptyGraph();
		const gateResult: GateResult = {
			passed: false,
			checks: [
				{ name: "approval", passed: true, detail: "ok" },
				{ name: "no_stale", passed: false, detail: "2 stale nodes" },
			],
			blocking_checks: [{ name: "no_stale", passed: false, detail: "2 stale nodes" }],
		};

		materializeGateResult(graph, gateResult);
		const gateNodes = getNodesByType(graph, "gate_check");
		const confidences = gateNodes.map((n) => n.confidence).sort();
		expect(confidences).toEqual([0, 1]);
	});

	it("nodes contain check details in content", () => {
		const graph = createEmptyGraph();
		const gateResult: GateResult = {
			passed: true,
			checks: [{ name: "approval", passed: true, detail: "Intent approved by bob" }],
			blocking_checks: [],
		};

		materializeGateResult(graph, gateResult);
		const node = getNodesByType(graph, "gate_check")[0];
		const content = node.content as Record<string, unknown>;
		expect(content.check_name).toBe("approval");
		expect(content.passed).toBe(true);
		expect(content.detail).toBe("Intent approved by bob");
	});

	it("returns empty for no checks", () => {
		const graph = createEmptyGraph();
		const gateResult: GateResult = {
			passed: true,
			checks: [],
			blocking_checks: [],
		};
		const ids = materializeGateResult(graph, gateResult);
		expect(ids).toHaveLength(0);
	});
});

// ---------------------------------------------------------------------------
// materializeContractResult
// ---------------------------------------------------------------------------

describe("materializeContractResult", () => {
	it("creates contract_check nodes for each result", () => {
		const graph = createEmptyGraph();
		const contractResults: ContractResult[] = [
			{
				contract_id: "c1",
				contract_type: "no_new_dependencies",
				passed: true,
				severity: "blocking",
				detail: "No dependency changes",
			},
			{
				contract_id: "c2",
				contract_type: "max_files_changed",
				passed: false,
				severity: "warning",
				detail: "11 files > 10 max",
			},
		];

		const ids = materializeContractResult(graph, contractResults);
		expect(ids).toHaveLength(2);

		const contractNodes = getNodesByType(graph, "contract_check");
		expect(contractNodes).toHaveLength(2);
	});

	it("passing contracts get confidence 1, failing get 0", () => {
		const graph = createEmptyGraph();
		const contractResults: ContractResult[] = [
			{
				contract_id: "c1",
				contract_type: "no_new_dependencies",
				passed: true,
				severity: "blocking",
				detail: "ok",
			},
			{
				contract_id: "c2",
				contract_type: "no_pattern_in_diff",
				passed: false,
				severity: "blocking",
				detail: "found console.log",
			},
		];

		materializeContractResult(graph, contractResults);
		const contractNodes = getNodesByType(graph, "contract_check");
		const confidences = contractNodes.map((n) => n.confidence).sort();
		expect(confidences).toEqual([0, 1]);
	});

	it("nodes contain contract details in content", () => {
		const graph = createEmptyGraph();
		const contractResults: ContractResult[] = [
			{
				contract_id: "c1",
				contract_type: "no_new_dependencies",
				passed: false,
				severity: "blocking",
				detail: "package.json changed",
			},
		];

		materializeContractResult(graph, contractResults);
		const node = getNodesByType(graph, "contract_check")[0];
		const content = node.content as Record<string, unknown>;
		expect(content.contract_id).toBe("c1");
		expect(content.contract_type).toBe("no_new_dependencies");
		expect(content.passed).toBe(false);
	});

	it("returns empty for no results", () => {
		const graph = createEmptyGraph();
		const ids = materializeContractResult(graph, []);
		expect(ids).toHaveLength(0);
	});
});

// ---------------------------------------------------------------------------
// Combined materialization
// ---------------------------------------------------------------------------

describe("combined materialization", () => {
	it("gate and contract nodes coexist in the same graph", () => {
		const graph = createEmptyGraph();

		const gateResult: GateResult = {
			passed: true,
			checks: [{ name: "approval", passed: true, detail: "ok" }],
			blocking_checks: [],
		};
		const contractResults: ContractResult[] = [
			{
				contract_id: "c1",
				contract_type: "no_new_dependencies",
				passed: true,
				severity: "blocking",
				detail: "ok",
			},
		];

		materializeGateResult(graph, gateResult);
		materializeContractResult(graph, contractResults);

		expect(getNodesByType(graph, "gate_check")).toHaveLength(1);
		expect(getNodesByType(graph, "contract_check")).toHaveLength(1);
		expect(graph.nodes).toHaveLength(2);
	});
});
