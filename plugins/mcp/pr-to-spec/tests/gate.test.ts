import { mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
	type IntentGatePolicy,
	IntentGatePolicySchema,
	evaluateGate,
} from "../src/core/gate/policy.js";
import { getPolicyPath, readPolicy, writePolicy } from "../src/core/gate/storage.js";
import type { IntentGraph } from "../src/core/graph/edge.js";
import type { IntentNode } from "../src/core/graph/node.js";
import { createEmptyGraph, upsertNode } from "../src/core/graph/propagation.js";
import { type Intent, IntentSchema } from "../src/core/intent/schema.js";
import { buildEnvelope } from "../src/core/protocol/envelope.js";
import type { DiffSource } from "../src/core/sources/types.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeIntent(overrides: Partial<Intent> = {}): Intent {
	return IntentSchema.parse({
		goal: "Add rate limiting",
		expected_scope: ["src/middleware/**"],
		...overrides,
	});
}

function makeNode(id: string, overrides: Partial<IntentNode> = {}): IntentNode {
	return {
		node_id: id,
		node_type: "project_intent",
		content: {},
		parent_ids: [],
		confidence: 1,
		source: "declared",
		invalidated_at: null,
		version: 1,
		...overrides,
	};
}

function makeDiff(overrides: Partial<DiffSource> = {}): DiffSource {
	return {
		title: "test",
		base_ref: "main",
		head_ref: "feat/test",
		author: "dev",
		files: [
			{
				filename: "src/middleware/rate-limit.ts",
				status: "added",
				additions: 20,
				deletions: 0,
			},
		],
		commits: 1,
		source_type: "local_branch",
		...overrides,
	};
}

// ---------------------------------------------------------------------------
// IntentGatePolicySchema
// ---------------------------------------------------------------------------

describe("IntentGatePolicySchema", () => {
	it("parses with all defaults", () => {
		const policy = IntentGatePolicySchema.parse({});
		expect(policy.require_approval).toBe(true);
		expect(policy.min_confidence).toBe(0.7);
		expect(policy.require_no_stale).toBe(true);
		expect(policy.require_no_must_ask).toBe(true);
		expect(policy.require_contracts_pass).toBe(false);
	});

	it("accepts custom values", () => {
		const policy = IntentGatePolicySchema.parse({
			require_approval: false,
			min_confidence: 0.5,
			require_no_stale: false,
			require_no_must_ask: false,
		});
		expect(policy.require_approval).toBe(false);
		expect(policy.min_confidence).toBe(0.5);
	});
});

// ---------------------------------------------------------------------------
// evaluateGate
// ---------------------------------------------------------------------------

describe("evaluateGate", () => {
	it("passes when intent is approved and graph is clean", () => {
		const intent = makeIntent({ status: "approved", approved_by: "alice" });
		const graph = createEmptyGraph();
		const policy = IntentGatePolicySchema.parse({});
		const result = evaluateGate(graph, intent, makeDiff(), policy);
		expect(result.passed).toBe(true);
		expect(result.blocking_checks).toHaveLength(0);
	});

	it("fails when intent is draft and approval required", () => {
		const intent = makeIntent({ status: "draft" });
		const graph = createEmptyGraph();
		const policy = IntentGatePolicySchema.parse({ require_approval: true });
		const result = evaluateGate(graph, intent, makeDiff(), policy);
		expect(result.passed).toBe(false);
		const approvalCheck = result.checks.find((c) => c.name === "approval");
		expect(approvalCheck?.passed).toBe(false);
	});

	it("passes when approval not required and intent is draft", () => {
		const intent = makeIntent({ status: "draft" });
		const graph = createEmptyGraph();
		const policy = IntentGatePolicySchema.parse({ require_approval: false });
		const result = evaluateGate(graph, intent, makeDiff(), policy);
		expect(result.passed).toBe(true);
	});

	it("fails when graph has stale nodes and require_no_stale is true", () => {
		const intent = makeIntent({ status: "approved" });
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("n1", { invalidated_at: "2026-03-17T00:00:00.000Z" }));
		const policy = IntentGatePolicySchema.parse({});
		const result = evaluateGate(graph, intent, makeDiff(), policy);
		expect(result.passed).toBe(false);
		const staleCheck = result.checks.find((c) => c.name === "no_stale");
		expect(staleCheck?.passed).toBe(false);
	});

	it("fails when confidence below threshold", () => {
		const intent = makeIntent({ status: "approved" });
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("n1", { confidence: 0.3 }));
		const policy = IntentGatePolicySchema.parse({ min_confidence: 0.7 });
		const result = evaluateGate(graph, intent, makeDiff(), policy);
		expect(result.passed).toBe(false);
		const confCheck = result.checks.find((c) => c.name === "confidence");
		expect(confCheck?.passed).toBe(false);
	});

	it("passes when confidence meets threshold", () => {
		const intent = makeIntent({ status: "approved" });
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("n1", { confidence: 0.8 }));
		const policy = IntentGatePolicySchema.parse({ min_confidence: 0.7 });
		const result = evaluateGate(graph, intent, makeDiff(), policy);
		// approval passes (approved), confidence passes (0.8 >= 0.7), no_stale passes (no stale nodes)
		expect(result.passed).toBe(true);
	});

	it("fails when must_ask decisions exist and require_no_must_ask is true", () => {
		const intent = makeIntent({ status: "approved", forbidden_scope: ["src/db/**"] });
		const graph = createEmptyGraph();
		// Diff touches forbidden scope → triggers must_ask decision
		const diff = makeDiff({
			files: [{ filename: "src/db/migration.sql", status: "added", additions: 10, deletions: 0 }],
		});
		const policy = IntentGatePolicySchema.parse({ require_no_must_ask: true });
		const result = evaluateGate(graph, intent, diff, policy);
		expect(result.passed).toBe(false);
		const mustAskCheck = result.checks.find((c) => c.name === "no_must_ask");
		expect(mustAskCheck?.passed).toBe(false);
	});

	it("skips must_ask check when diff is null", () => {
		const intent = makeIntent({ status: "approved" });
		const graph = createEmptyGraph();
		const policy = IntentGatePolicySchema.parse({ require_no_must_ask: true });
		const result = evaluateGate(graph, intent, null, policy);
		// Should not have a no_must_ask check at all
		const mustAskCheck = result.checks.find((c) => c.name === "no_must_ask");
		expect(mustAskCheck).toBeUndefined();
	});

	it("locked intent passes approval check", () => {
		const intent = makeIntent({ status: "locked" });
		const graph = createEmptyGraph();
		const policy = IntentGatePolicySchema.parse({ require_approval: true });
		const result = evaluateGate(graph, intent, makeDiff(), policy);
		const approvalCheck = result.checks.find((c) => c.name === "approval");
		expect(approvalCheck?.passed).toBe(true);
	});

	it("returns all checks in result", () => {
		const intent = makeIntent({ status: "approved" });
		const graph = createEmptyGraph();
		upsertNode(graph, makeNode("n1"));
		const policy = IntentGatePolicySchema.parse({});
		const result = evaluateGate(graph, intent, makeDiff(), policy);
		const checkNames = result.checks.map((c) => c.name);
		expect(checkNames).toContain("approval");
		expect(checkNames).toContain("confidence");
		expect(checkNames).toContain("no_stale");
		expect(checkNames).toContain("no_must_ask");
	});
});

// ---------------------------------------------------------------------------
// IntentSchema — status/approval fields (backwards compatibility)
// ---------------------------------------------------------------------------

describe("IntentSchema — status and approval", () => {
	it("defaults status to draft", () => {
		const intent = IntentSchema.parse({ goal: "Test" });
		expect(intent.status).toBe("draft");
	});

	it("accepts approved status", () => {
		const result = IntentSchema.safeParse({
			goal: "Test",
			status: "approved",
			approved_by: "alice",
			approved_at: "2026-03-17T00:00:00.000Z",
		});
		expect(result.success).toBe(true);
		if (result.success) {
			expect(result.data.status).toBe("approved");
			expect(result.data.approved_by).toBe("alice");
		}
	});

	it("accepts locked status", () => {
		const result = IntentSchema.safeParse({ goal: "Test", status: "locked" });
		expect(result.success).toBe(true);
	});

	it("backwards compatible — old intent without status parses", () => {
		const result = IntentSchema.safeParse({
			goal: "Old intent",
			expected_scope: ["src/**"],
			forbidden_scope: [],
			max_risk: "medium",
		});
		expect(result.success).toBe(true);
		if (result.success) {
			expect(result.data.status).toBe("draft");
			expect(result.data.approved_by).toBeUndefined();
			expect(result.data.approved_at).toBeUndefined();
		}
	});
});

// ---------------------------------------------------------------------------
// Policy storage round-trip
// ---------------------------------------------------------------------------

describe("Policy storage round-trip", () => {
	let tmpDir: string;

	beforeEach(() => {
		tmpDir = join(tmpdir(), `pr-to-spec-gate-test-${Date.now()}`);
		mkdirSync(tmpDir, { recursive: true });
	});

	afterEach(() => {
		rmSync(tmpDir, { recursive: true, force: true });
	});

	it("returns null when no policy file exists", () => {
		expect(readPolicy(tmpDir)).toBeNull();
	});

	it("round-trips a policy", () => {
		const policy = IntentGatePolicySchema.parse({
			require_approval: true,
			min_confidence: 0.8,
		});
		writePolicy(policy, tmpDir);
		const loaded = readPolicy(tmpDir);
		expect(loaded).not.toBeNull();
		expect(loaded?.require_approval).toBe(true);
		expect(loaded?.min_confidence).toBe(0.8);
	});

	it("getPolicyPath returns correct path", () => {
		const path = getPolicyPath(tmpDir);
		expect(path).toContain(".pr-to-spec");
		expect(path).toContain("policy.yaml");
	});
});

// ---------------------------------------------------------------------------
// Protocol envelope — gate_failed status
// ---------------------------------------------------------------------------

describe("buildEnvelope — gate integration", () => {
	function makeSpec() {
		return {
			version: 1 as const,
			generated_at: "2026-03-17T00:00:00.000Z",
			source: { repo: "local", base_branch: "main", head_branch: "feat/test", author: "dev" },
			title: "test",
			summary: "test",
			intent: { likely_goal: "test", change_type: "feature" as const },
			scope: { include: [], exclude: [] },
			affected_files: [],
			constraints: [],
			acceptance_criteria: [],
			verification: { tests_required: [], manual_checks: [] },
			risk_flags: [],
			open_questions: [],
			generation_prompt: "",
			decision_prompt: "",
			stats: { files_changed: 0, additions: 0, deletions: 0, commits: 0 },
		};
	}

	it("returns gate_failed status when gate fails", () => {
		const envelope = buildEnvelope("check", makeSpec(), {
			gate_result: {
				passed: false,
				checks: [{ name: "approval", passed: false, detail: "not approved" }],
				blocking_checks: [{ name: "approval", passed: false, detail: "not approved" }],
			},
		});
		expect(envelope.status).toBe("gate_failed");
		expect(envelope.exit_code).toBe(4);
	});

	it("gate_failed takes priority over drift_detected", () => {
		const envelope = buildEnvelope("check", makeSpec(), {
			signals: [{ type: "scope_creep", description: "test", severity: "medium" }],
			gate_result: {
				passed: false,
				checks: [{ name: "approval", passed: false, detail: "not approved" }],
				blocking_checks: [{ name: "approval", passed: false, detail: "not approved" }],
			},
		});
		expect(envelope.status).toBe("gate_failed");
		expect(envelope.exit_code).toBe(4);
	});

	it("passing gate does not affect other statuses", () => {
		const envelope = buildEnvelope("check", makeSpec(), {
			gate_result: {
				passed: true,
				checks: [],
				blocking_checks: [],
			},
		});
		expect(envelope.status).toBe("clean");
		expect(envelope.exit_code).toBe(0);
	});

	it("includes gate_result in envelope", () => {
		const gateResult = {
			passed: true,
			checks: [{ name: "approval", passed: true, detail: "approved" }],
			blocking_checks: [],
		};
		const envelope = buildEnvelope("check", makeSpec(), { gate_result: gateResult });
		expect(envelope.gate_result).toEqual(gateResult);
	});
});
