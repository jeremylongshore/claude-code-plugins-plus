import { describe, expect, it } from "vitest";
import type { DriftSignal } from "../src/core/drift/signals.js";
import { buildEnvelope } from "../src/core/protocol/envelope.js";
import type { AgentProtocolEnvelope } from "../src/core/protocol/envelope.js";
import type { PromptSpec } from "../src/core/schema/prompt-spec.js";

function makeSpec(overrides: Partial<PromptSpec> = {}): PromptSpec {
	return {
		version: 1,
		generated_at: "2026-03-17T00:00:00.000Z",
		source: {
			repo: "owner/repo",
			pr_number: 42,
			pr_url: "https://github.com/owner/repo/pull/42",
			base_branch: "main",
			head_branch: "feat/test",
			author: "developer",
		},
		title: "Test PR",
		summary: 'Feature PR by developer: "Test PR" — 1 file changed (+10/-5)',
		intent: {
			likely_goal: "Add a feature",
			change_type: "feature",
		},
		scope: {
			include: ["src/**"],
			exclude: [],
		},
		affected_files: [{ filename: "src/a.ts", status: "modified", additions: 10, deletions: 5 }],
		constraints: ["Preserve existing behavior"],
		acceptance_criteria: ["Tests pass"],
		verification: {
			tests_required: ["unit"],
			manual_checks: [],
		},
		risk_flags: [],
		open_questions: [],
		generation_prompt: "Re-implement this change.",
		decision_prompt: "Should this be approved?",
		stats: { files_changed: 1, additions: 10, deletions: 5, commits: 1 },
		...overrides,
	};
}

describe("buildEnvelope", () => {
	it("version is always 1", () => {
		const envelope = buildEnvelope("analyze", makeSpec());
		expect(envelope.version).toBe(1);
	});

	it("command field is set correctly", () => {
		const envelope = buildEnvelope("scan", makeSpec());
		expect(envelope.command).toBe("scan");
	});

	it("status is clean with no risk and no drift", () => {
		const envelope = buildEnvelope("scan", makeSpec());
		expect(envelope.status).toBe("clean");
		expect(envelope.exit_code).toBe(0);
	});

	it("status is high_risk when spec has high-severity risk flags", () => {
		const spec = makeSpec({
			risk_flags: [{ category: "auth", description: "Auth change", severity: "high" }],
		});
		const envelope = buildEnvelope("scan", spec);
		expect(envelope.status).toBe("high_risk");
		expect(envelope.exit_code).toBe(2);
	});

	it("status is drift_detected when signals present", () => {
		const signals: DriftSignal[] = [
			{
				type: "scope_creep",
				description: "File outside scope",
				severity: "medium",
				details: ["src/db/schema.ts"],
			},
		];
		const envelope = buildEnvelope("check", makeSpec(), { signals });
		expect(envelope.status).toBe("drift_detected");
		expect(envelope.exit_code).toBe(3);
	});

	it("drift_detected takes priority over high_risk", () => {
		const spec = makeSpec({
			risk_flags: [{ category: "auth", description: "Auth change", severity: "high" }],
		});
		const signals: DriftSignal[] = [
			{ type: "scope_creep", description: "Out of scope", severity: "medium" },
		];
		const envelope = buildEnvelope("check", spec, { signals });
		expect(envelope.status).toBe("drift_detected");
		expect(envelope.exit_code).toBe(3);
	});

	it("includes spec in envelope", () => {
		const spec = makeSpec();
		const envelope = buildEnvelope("analyze", spec);
		expect(envelope.spec).toBeDefined();
		expect(envelope.spec?.title).toBe("Test PR");
	});

	it("includes intent in envelope when provided", () => {
		const intent = {
			goal: "Add rate limiting",
			expected_scope: ["src/**"],
			forbidden_scope: [],
			max_risk: "medium" as const,
		};
		const envelope = buildEnvelope("check", makeSpec(), { intent });
		expect(envelope.intent).toBeDefined();
		expect(envelope.intent?.goal).toBe("Add rate limiting");
	});

	it("signals is undefined when not provided", () => {
		const envelope = buildEnvelope("scan", makeSpec());
		expect(envelope.signals).toBeUndefined();
	});

	it("envelope is serializable to JSON", () => {
		const envelope = buildEnvelope("scan", makeSpec());
		const json = JSON.stringify(envelope);
		const parsed = JSON.parse(json) as AgentProtocolEnvelope;
		expect(parsed.version).toBe(1);
		expect(parsed.status).toBe("clean");
	});

	it("all commands produce envelopes with consistent structure", () => {
		const commands = ["analyze", "scan", "check"] as const;
		for (const command of commands) {
			const envelope = buildEnvelope(command, makeSpec());
			expect(envelope.version).toBe(1);
			expect(typeof envelope.command).toBe("string");
			expect(["clean", "high_risk", "drift_detected", "error"]).toContain(envelope.status);
			expect([0, 1, 2, 3]).toContain(envelope.exit_code);
		}
	});
});

describe("buildEnvelope — exit code / status mapping precision", () => {
	it("medium-risk-only flags do not trigger high_risk (status stays clean)", () => {
		const spec = makeSpec({
			risk_flags: [{ category: "deps", description: "Dep change", severity: "medium" }],
		});
		const envelope = buildEnvelope("scan", spec);
		expect(envelope.status).toBe("clean");
		expect(envelope.exit_code).toBe(0);
	});

	it("low-risk-only flags do not trigger high_risk", () => {
		const spec = makeSpec({
			risk_flags: [{ category: "large-change", description: "Big file", severity: "low" }],
		});
		const envelope = buildEnvelope("scan", spec);
		expect(envelope.status).toBe("clean");
		expect(envelope.exit_code).toBe(0);
	});

	it("exit_code is exactly 2 for high_risk status", () => {
		const spec = makeSpec({
			risk_flags: [{ category: "auth", description: "Auth change", severity: "high" }],
		});
		const envelope = buildEnvelope("scan", spec);
		expect(envelope.exit_code).toBe(2);
		expect(envelope.status).toBe("high_risk");
	});

	it("exit_code is exactly 3 for drift_detected status", () => {
		const signals: DriftSignal[] = [
			{
				type: "forbidden_touch",
				description: "Forbidden file touched",
				severity: "high",
				details: ["src/db/schema.ts"],
			},
		];
		const envelope = buildEnvelope("check", makeSpec(), { signals });
		expect(envelope.exit_code).toBe(3);
		expect(envelope.status).toBe("drift_detected");
	});

	it("exit_code is 0 for clean status with no risk and no drift", () => {
		const envelope = buildEnvelope("scan", makeSpec());
		expect(envelope.exit_code).toBe(0);
		expect(envelope.status).toBe("clean");
	});
});

describe("buildEnvelope — envelope structure completeness", () => {
	it("command field exactly matches what was passed in", () => {
		expect(buildEnvelope("analyze", makeSpec()).command).toBe("analyze");
		expect(buildEnvelope("scan", makeSpec()).command).toBe("scan");
		expect(buildEnvelope("check", makeSpec()).command).toBe("check");
	});

	it("spec.stats values are preserved in envelope spec", () => {
		const spec = makeSpec();
		const envelope = buildEnvelope("scan", spec);
		expect(envelope.spec?.stats.files_changed).toBe(1);
		expect(envelope.spec?.stats.additions).toBe(10);
		expect(envelope.spec?.stats.deletions).toBe(5);
		expect(envelope.spec?.stats.commits).toBe(1);
	});

	it("signals array is passed through unchanged when provided", () => {
		const signals: DriftSignal[] = [
			{ type: "type_mismatch", description: "Type mismatch", severity: "low" },
			{ type: "size_overrun", description: "Too big", severity: "low" },
		];
		const envelope = buildEnvelope("check", makeSpec(), { signals });
		expect(envelope.signals).toHaveLength(2);
		expect(envelope.signals?.[0].type).toBe("type_mismatch");
		expect(envelope.signals?.[1].type).toBe("size_overrun");
	});

	it("envelope with only low-severity drift signals still has drift_detected status", () => {
		const signals: DriftSignal[] = [
			{ type: "size_overrun", description: "Slightly over budget", severity: "low" },
		];
		const envelope = buildEnvelope("check", makeSpec(), { signals });
		expect(envelope.status).toBe("drift_detected");
		expect(envelope.exit_code).toBe(3);
	});
});
