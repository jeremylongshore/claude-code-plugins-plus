import { mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { evaluateContracts } from "../src/core/contracts/evaluator.js";
import { type Contract, ContractSchema } from "../src/core/contracts/schema.js";
import { getContractsPath, readContracts, writeContracts } from "../src/core/contracts/storage.js";
import type { PromptSpec } from "../src/core/schema/prompt-spec.js";
import type { DiffSource } from "../src/core/sources/types.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeDiff(overrides: Partial<DiffSource> = {}): DiffSource {
	return {
		title: "test",
		base_ref: "main",
		head_ref: "feat/test",
		author: "dev",
		files: [
			{
				filename: "src/feature.ts",
				status: "added",
				additions: 20,
				deletions: 0,
				patch: "+export function hello() { return 'world'; }",
			},
		],
		commits: 1,
		source_type: "local_branch",
		...overrides,
	};
}

function makeSpec(): PromptSpec {
	return {
		version: 1,
		generated_at: "2026-03-17T00:00:00.000Z",
		source: { repo: "local", base_branch: "main", head_branch: "feat/test", author: "dev" },
		title: "test",
		summary: "test",
		intent: { likely_goal: "test", change_type: "feature" },
		scope: { include: [], exclude: [] },
		affected_files: [],
		constraints: [],
		acceptance_criteria: [],
		verification: { tests_required: [], manual_checks: [] },
		risk_flags: [],
		open_questions: [],
		generation_prompt: "",
		decision_prompt: "",
		stats: { files_changed: 1, additions: 20, deletions: 0, commits: 1 },
	} as PromptSpec;
}

function makeContract(overrides: Partial<Contract> = {}): Contract {
	return ContractSchema.parse({
		id: "test-contract",
		type: "no_new_dependencies",
		...overrides,
	});
}

// ---------------------------------------------------------------------------
// ContractSchema
// ---------------------------------------------------------------------------

describe("ContractSchema", () => {
	it("parses a minimal contract", () => {
		const c = ContractSchema.parse({ id: "c1", type: "no_new_dependencies" });
		expect(c.severity).toBe("blocking");
		expect(c.description).toBe("");
	});

	it("accepts all contract types", () => {
		const types = [
			"no_new_dependencies",
			"no_file_outside_scope",
			"max_files_changed",
			"no_pattern_in_diff",
			"require_pattern_in_diff",
			"no_new_exports",
			"custom_command",
		];
		for (const t of types) {
			const result = ContractSchema.safeParse({ id: "c1", type: t });
			expect(result.success).toBe(true);
		}
	});

	it("rejects invalid type", () => {
		const result = ContractSchema.safeParse({ id: "c1", type: "invalid_type" });
		expect(result.success).toBe(false);
	});
});

// ---------------------------------------------------------------------------
// evaluateContracts — no_new_dependencies
// ---------------------------------------------------------------------------

describe("evaluateContracts — no_new_dependencies", () => {
	it("passes when no dependency files changed", () => {
		const results = evaluateContracts(
			[makeContract({ type: "no_new_dependencies" })],
			makeDiff(),
			makeSpec(),
		);
		expect(results).toHaveLength(1);
		expect(results[0].passed).toBe(true);
	});

	it("fails when package.json dependency section is modified", () => {
		const diff = makeDiff({
			files: [
				{
					filename: "package.json",
					status: "modified",
					additions: 5,
					deletions: 1,
					patch: '+  "dependencies": {\n+    "new-pkg": "^1.0.0"\n+  }',
				},
			],
		});
		const results = evaluateContracts(
			[makeContract({ type: "no_new_dependencies" })],
			diff,
			makeSpec(),
		);
		expect(results[0].passed).toBe(false);
		expect(results[0].detail).toContain("package.json");
	});

	it("passes when package.json scripts section is modified (no deps)", () => {
		const diff = makeDiff({
			files: [
				{
					filename: "package.json",
					status: "modified",
					additions: 1,
					deletions: 1,
					patch: '+  "scripts": { "test": "vitest" }',
				},
			],
		});
		const results = evaluateContracts(
			[makeContract({ type: "no_new_dependencies" })],
			diff,
			makeSpec(),
		);
		expect(results[0].passed).toBe(true);
	});

	it("fails when lock file is added", () => {
		const diff = makeDiff({
			files: [{ filename: "pnpm-lock.yaml", status: "added", additions: 100, deletions: 0 }],
		});
		const results = evaluateContracts(
			[makeContract({ type: "no_new_dependencies" })],
			diff,
			makeSpec(),
		);
		expect(results[0].passed).toBe(false);
	});
});

// ---------------------------------------------------------------------------
// evaluateContracts — no_file_outside_scope
// ---------------------------------------------------------------------------

describe("evaluateContracts — no_file_outside_scope", () => {
	it("passes when all files within scope", () => {
		const results = evaluateContracts(
			[makeContract({ type: "no_file_outside_scope", params: { scope: ["src/**"] } })],
			makeDiff(),
			makeSpec(),
		);
		expect(results[0].passed).toBe(true);
	});

	it("fails when file outside scope", () => {
		const diff = makeDiff({
			files: [{ filename: "docs/readme.md", status: "added", additions: 10, deletions: 0 }],
		});
		const results = evaluateContracts(
			[makeContract({ type: "no_file_outside_scope", params: { scope: ["src/**"] } })],
			diff,
			makeSpec(),
		);
		expect(results[0].passed).toBe(false);
		expect(results[0].detail).toContain("docs/readme.md");
	});

	it("passes when no scope defined", () => {
		const results = evaluateContracts(
			[makeContract({ type: "no_file_outside_scope", params: {} })],
			makeDiff(),
			makeSpec(),
		);
		expect(results[0].passed).toBe(true);
	});
});

// ---------------------------------------------------------------------------
// evaluateContracts — max_files_changed
// ---------------------------------------------------------------------------

describe("evaluateContracts — max_files_changed", () => {
	it("passes when under limit", () => {
		const results = evaluateContracts(
			[makeContract({ type: "max_files_changed", params: { max: 5 } })],
			makeDiff(),
			makeSpec(),
		);
		expect(results[0].passed).toBe(true);
	});

	it("fails when over limit", () => {
		const files = Array.from({ length: 6 }, (_, i) => ({
			filename: `src/file${i}.ts`,
			status: "modified" as const,
			additions: 5,
			deletions: 2,
		}));
		const diff = makeDiff({ files });
		const results = evaluateContracts(
			[makeContract({ type: "max_files_changed", params: { max: 5 } })],
			diff,
			makeSpec(),
		);
		expect(results[0].passed).toBe(false);
	});
});

// ---------------------------------------------------------------------------
// evaluateContracts — no_pattern_in_diff
// ---------------------------------------------------------------------------

describe("evaluateContracts — no_pattern_in_diff", () => {
	it("passes when pattern not found", () => {
		const results = evaluateContracts(
			[makeContract({ type: "no_pattern_in_diff", params: { pattern: "console\\.log" } })],
			makeDiff(),
			makeSpec(),
		);
		expect(results[0].passed).toBe(true);
	});

	it("fails when pattern found in patch", () => {
		const diff = makeDiff({
			files: [
				{
					filename: "src/app.ts",
					status: "modified",
					additions: 1,
					deletions: 0,
					patch: "+console.log('debug');",
				},
			],
		});
		const results = evaluateContracts(
			[makeContract({ type: "no_pattern_in_diff", params: { pattern: "console\\.log" } })],
			diff,
			makeSpec(),
		);
		expect(results[0].passed).toBe(false);
		expect(results[0].detail).toContain("src/app.ts");
	});
});

// ---------------------------------------------------------------------------
// evaluateContracts — require_pattern_in_diff
// ---------------------------------------------------------------------------

describe("evaluateContracts — require_pattern_in_diff", () => {
	it("passes when pattern found", () => {
		const diff = makeDiff({
			files: [
				{
					filename: "src/app.ts",
					status: "modified",
					additions: 1,
					deletions: 0,
					patch: "+// @ts-check",
				},
			],
		});
		const results = evaluateContracts(
			[makeContract({ type: "require_pattern_in_diff", params: { pattern: "@ts-check" } })],
			diff,
			makeSpec(),
		);
		expect(results[0].passed).toBe(true);
	});

	it("fails when pattern not found", () => {
		const results = evaluateContracts(
			[makeContract({ type: "require_pattern_in_diff", params: { pattern: "NEVER_FOUND" } })],
			makeDiff(),
			makeSpec(),
		);
		expect(results[0].passed).toBe(false);
	});
});

// ---------------------------------------------------------------------------
// evaluateContracts — no_new_exports
// ---------------------------------------------------------------------------

describe("evaluateContracts — no_new_exports", () => {
	it("fails when new export added", () => {
		const diff = makeDiff({
			files: [
				{
					filename: "src/lib.ts",
					status: "modified",
					additions: 1,
					deletions: 0,
					patch: "+export function newThing() {}",
				},
			],
		});
		const results = evaluateContracts([makeContract({ type: "no_new_exports" })], diff, makeSpec());
		expect(results[0].passed).toBe(false);
	});

	it("passes when no new exports", () => {
		const diff = makeDiff({
			files: [
				{
					filename: "src/lib.ts",
					status: "modified",
					additions: 1,
					deletions: 0,
					patch: "+const internal = 42;",
				},
			],
		});
		const results = evaluateContracts([makeContract({ type: "no_new_exports" })], diff, makeSpec());
		expect(results[0].passed).toBe(true);
	});
});

// ---------------------------------------------------------------------------
// evaluateContracts — custom_command
// ---------------------------------------------------------------------------

describe("evaluateContracts — custom_command (deprecated)", () => {
	it("always fails with security deprecation message", () => {
		const results = evaluateContracts(
			[makeContract({ type: "custom_command", params: { cmd: "true" } })],
			makeDiff(),
			makeSpec(),
		);
		expect(results[0].passed).toBe(false);
		expect(results[0].detail).toContain("removed for security reasons");
	});

	it("fails even with no command specified", () => {
		const results = evaluateContracts(
			[makeContract({ type: "custom_command", params: {} })],
			makeDiff(),
			makeSpec(),
		);
		expect(results[0].passed).toBe(false);
		expect(results[0].detail).toContain("removed for security reasons");
	});
});

// ---------------------------------------------------------------------------
// Multiple contracts
// ---------------------------------------------------------------------------

describe("evaluateContracts — multiple", () => {
	it("evaluates all contracts and returns results", () => {
		const contracts = [
			makeContract({ id: "c1", type: "no_new_dependencies" }),
			makeContract({ id: "c2", type: "max_files_changed", params: { max: 10 } }),
		];
		const results = evaluateContracts(contracts, makeDiff(), makeSpec());
		expect(results).toHaveLength(2);
		expect(results[0].contract_id).toBe("c1");
		expect(results[1].contract_id).toBe("c2");
	});

	it("mixes pass and fail results", () => {
		const diff = makeDiff({
			files: [{ filename: "pnpm-lock.yaml", status: "modified", additions: 50, deletions: 10 }],
		});
		const contracts = [
			makeContract({ id: "c1", type: "no_new_dependencies" }),
			makeContract({ id: "c2", type: "max_files_changed", params: { max: 10 } }),
		];
		const results = evaluateContracts(contracts, diff, makeSpec());
		expect(results[0].passed).toBe(false); // lock file changed
		expect(results[1].passed).toBe(true); // 1 file < 10
	});
});

// ---------------------------------------------------------------------------
// Contract storage round-trip
// ---------------------------------------------------------------------------

describe("Contract storage round-trip", () => {
	let tmpDir: string;

	beforeEach(() => {
		tmpDir = join(tmpdir(), `pr-to-spec-contracts-test-${Date.now()}`);
		mkdirSync(tmpDir, { recursive: true });
	});

	afterEach(() => {
		rmSync(tmpDir, { recursive: true, force: true });
	});

	it("returns empty array when no contracts file exists", () => {
		expect(readContracts(tmpDir)).toEqual([]);
	});

	it("round-trips contracts", () => {
		const contracts = [
			makeContract({ id: "c1", type: "no_new_dependencies" }),
			makeContract({ id: "c2", type: "max_files_changed", params: { max: 5 } }),
		];
		writeContracts(contracts, tmpDir);
		const loaded = readContracts(tmpDir);
		expect(loaded).toHaveLength(2);
		expect(loaded[0].id).toBe("c1");
		expect(loaded[1].params).toEqual({ max: 5 });
	});

	it("getContractsPath returns correct path", () => {
		const path = getContractsPath(tmpDir);
		expect(path).toContain(".pr-to-spec");
		expect(path).toContain("contracts.yaml");
	});
});
