/**
 * features/steps/policy.ts — Step definitions for policy_evaluation.feature.
 *
 * Exercises evaluate() from policy.ts. Context carries the ToolCall,
 * PolicyRule list, approval map, and the returned PolicyDecision.
 *
 * SPDX-License-Identifier: MIT
 */

import { expect } from "bun:test";
import {
	type ApprovalKey,
	approvalKey,
	DEFAULT_REQUIRE_AUTHORED_POLICY,
	evaluate,
	type PolicyDecision,
	type PolicyRule,
	type ToolCall,
} from "../../policy.ts";
import type { StepRegistry } from "../runner.ts";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const SESSION = { channel: "C_TEST", thread: "1000.0001" };
const BASE_CALL: ToolCall = {
	tool: "read_file",
	input: { path: "/tmp/test.txt" },
	sessionKey: SESSION,
	actor: "session_owner",
};

function makeAutoApproveRule(id = "rule-allow"): PolicyRule {
	return {
		id,
		priority: 100,
		effect: "auto_approve",
		match: { tool: BASE_CALL.tool },
	};
}

function makeDenyRule(id = "rule-deny", reason = "not allowed"): PolicyRule {
	return {
		id,
		priority: 100,
		effect: "deny",
		reason,
		match: { tool: BASE_CALL.tool },
	};
}

function makeRequireRule(
	id = "rule-require",
	ttlMs = 5 * 60 * 1000,
): PolicyRule {
	return {
		id,
		priority: 100,
		effect: "require_approval",
		ttlMs,
		approvers: 1,
		match: { tool: BASE_CALL.tool },
	};
}

// ---------------------------------------------------------------------------
// Step registrations
// ---------------------------------------------------------------------------

export function registerPolicySteps(registry: StepRegistry): void {
	// -------------------------------------------------------------------------
	// Background steps
	// -------------------------------------------------------------------------

	registry.register(
		"a tool call addressed at a session with a known channel and actor",
		(ctx) => {
			ctx.call = { ...BASE_CALL };
			ctx.now = Date.now();
		},
	);

	registry.register("an approvals map seeded for this session", (ctx) => {
		ctx.approvals = new Map<ApprovalKey, { ttlExpires: number }>();
	});

	// -------------------------------------------------------------------------
	// Scenario: The first auto_approve match short-circuits evaluation
	// -------------------------------------------------------------------------

	registry.register(
		"a rule list whose first matching rule has an auto_approve effect",
		(ctx) => {
			ctx.rules = [makeAutoApproveRule("r-allow")];
		},
	);

	registry.register("the evaluator processes a matching tool call", (ctx) => {
		const call = ctx.call as ToolCall;
		const rules = ctx.rules as PolicyRule[];
		const now = ctx.now as number;
		const approvals = ctx.approvals as Map<ApprovalKey, { ttlExpires: number }>;
		ctx.decision = evaluate(call, rules, now, { approvals });
	});

	registry.register("the decision is allow", (ctx) => {
		const decision = ctx.decision as PolicyDecision;
		expect(decision.kind).toBe("allow");
	});

	registry.register("the decision cites the matched rule id", (ctx) => {
		const decision = ctx.decision as PolicyDecision;
		expect(decision.kind).toBe("allow");
		if (decision.kind === "allow") {
			expect(decision.rule).toBeDefined();
		}
	});

	// -------------------------------------------------------------------------
	// Scenario: The first deny match short-circuits with the authored reason
	// -------------------------------------------------------------------------

	registry.register(
		"a rule list whose first matching rule has a deny effect",
		(ctx) => {
			ctx.rules = [makeDenyRule("r-deny", "tool is forbidden")];
		},
	);

	registry.register("the decision is deny", (ctx) => {
		const decision = ctx.decision as PolicyDecision;
		expect(decision.kind).toBe("deny");
	});

	registry.register(
		"the decision carries the authored reason string",
		(ctx) => {
			const decision = ctx.decision as PolicyDecision;
			expect(decision.kind).toBe("deny");
			if (decision.kind === "deny") {
				expect(decision.reason).toBe("tool is forbidden");
			}
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: require_approval with no prior approval yields require
	// -------------------------------------------------------------------------

	registry.register(
		"a rule list whose first matching rule requires human approval",
		(ctx) => {
			ctx.rules = [makeRequireRule("r-require", 5 * 60 * 1000)];
		},
	);

	registry.register(
		"no approval is recorded for the rule and session key",
		(ctx) => {
			// approvals map already empty from background
			const approvals = ctx.approvals as Map<
				ApprovalKey,
				{ ttlExpires: number }
			>;
			expect(approvals.size).toBe(0);
		},
	);

	registry.register("the decision is require", (ctx) => {
		const decision = ctx.decision as PolicyDecision;
		expect(decision.kind).toBe("require");
	});

	registry.register(
		"the decision carries the configured approval TTL",
		(ctx) => {
			const decision = ctx.decision as PolicyDecision;
			expect(decision.kind).toBe("require");
			if (decision.kind === "require") {
				expect(decision.ttlMs).toBe(5 * 60 * 1000);
			}
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: require_approval with a live approval yields allow
	// -------------------------------------------------------------------------

	registry.register(
		"a live approval is recorded for the rule and session key",
		(ctx) => {
			const rules = ctx.rules as PolicyRule[];
			const ruleId = rules[0]!.id;
			const now = ctx.now as number;
			const key = approvalKey(ruleId, SESSION);
			const approvals = ctx.approvals as Map<
				ApprovalKey,
				{ ttlExpires: number }
			>;
			// TTL expires in the future
			approvals.set(key, { ttlExpires: now + 5 * 60 * 1000 });
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: require_approval with an expired approval re-triggers require
	// -------------------------------------------------------------------------

	registry.register(
		"an expired approval is recorded for the rule and session key",
		(ctx) => {
			const rules = ctx.rules as PolicyRule[];
			const ruleId = rules[0]!.id;
			const now = ctx.now as number;
			const key = approvalKey(ruleId, SESSION);
			const approvals = ctx.approvals as Map<
				ApprovalKey,
				{ ttlExpires: number }
			>;
			// TTL already expired
			approvals.set(key, { ttlExpires: now - 1 });
		},
	);

	registry.register(
		"the evaluator processes a matching tool call at a later time",
		(ctx) => {
			const call = ctx.call as ToolCall;
			const rules = ctx.rules as PolicyRule[];
			const now = ctx.now as number;
			const approvals = ctx.approvals as Map<
				ApprovalKey,
				{ ttlExpires: number }
			>;
			// Evaluate at `now` — the approval already expired before `now`
			ctx.decision = evaluate(call, rules, now, { approvals });
		},
	);

	registry.register(
		"the expired approval does not satisfy the check",
		(ctx) => {
			const decision = ctx.decision as PolicyDecision;
			expect(decision.kind).toBe("require");
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: No matching rule + not in requireAuthoredPolicy → allow
	// -------------------------------------------------------------------------

	registry.register(
		"a rule list where no rule matches the tool call",
		(ctx) => {
			// Rule on a completely different tool — will never match BASE_CALL
			ctx.rules = [
				{
					id: "r-nomatch",
					priority: 100,
					effect: "deny" as const,
					reason: "other tool",
					match: { tool: "upload_file" },
				} satisfies PolicyRule,
			];
		},
	);

	registry.register(
		"the require-authored-policy set does not contain the tool name",
		(ctx) => {
			// BASE_CALL.tool is 'read_file'; DEFAULT set only has 'upload_file'
			ctx.requireAuthoredPolicy = DEFAULT_REQUIRE_AUTHORED_POLICY;
		},
	);

	registry.register("the evaluator processes the tool call", (ctx) => {
		const call = ctx.call as ToolCall;
		const rules = ctx.rules as PolicyRule[];
		const now = ctx.now as number;
		const approvals = ctx.approvals as Map<ApprovalKey, { ttlExpires: number }>;
		const requireAuthoredPolicy = ctx.requireAuthoredPolicy as
			| ReadonlySet<string>
			| undefined;
		ctx.decision = evaluate(call, rules, now, {
			approvals,
			requireAuthoredPolicy,
		});
	});

	// -------------------------------------------------------------------------
	// Scenario: No matching rule + in requireAuthoredPolicy → deny
	// -------------------------------------------------------------------------

	registry.register(
		"the require-authored-policy set contains the tool name",
		(ctx) => {
			// Use the call tool name 'read_file' in the set
			ctx.requireAuthoredPolicy = new Set(["read_file"]);
		},
	);

	registry.register(
		"the decision reason names the default-deny branch",
		(ctx) => {
			const decision = ctx.decision as PolicyDecision;
			expect(decision.kind).toBe("deny");
			if (decision.kind === "deny") {
				expect(decision.rule).toBe("default");
				expect(decision.reason).toContain("no policy authored");
			}
		},
	);
}
