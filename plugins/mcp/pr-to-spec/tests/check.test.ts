import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DriftSignal } from "../src/core/drift/signals.js";
import type { Intent } from "../src/core/intent/schema.js";
import type { PromptSpec } from "../src/core/schema/prompt-spec.js";
import type { DiffSource } from "../src/core/sources/types.js";

// ---------------------------------------------------------------------------
// Module-level mocks — must come before any import of the module under test
// ---------------------------------------------------------------------------

vi.mock("../src/core/sources/local.js", () => ({
	buildLocalDiffSource: vi.fn(),
}));

vi.mock("../src/core/intent/storage.js", () => ({
	readIntent: vi.fn(),
	writeIntent: vi.fn(),
}));

vi.mock("../src/core/parsing/pr-parser.js", () => ({
	generateSpec: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Lazy imports (after mocks are registered)
// ---------------------------------------------------------------------------

import { checkCommand } from "../src/cli/check.js";
import { readIntent } from "../src/core/intent/storage.js";
import { generateSpec } from "../src/core/parsing/pr-parser.js";
import { buildLocalDiffSource } from "../src/core/sources/local.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeDiffSource(overrides: Partial<DiffSource> = {}): DiffSource {
	return {
		title: "Branch feat/test vs main",
		body: "Test change",
		base_ref: "main",
		head_ref: "feat/test",
		author: "dev",
		files: [
			{
				filename: "src/feature.ts",
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

function makeSpec(overrides: Partial<PromptSpec> = {}): PromptSpec {
	return {
		version: 1,
		generated_at: "2026-03-17T00:00:00.000Z",
		source: {
			repo: "local",
			base_branch: "main",
			head_branch: "feat/test",
			author: "dev",
		},
		title: "Branch feat/test vs main",
		summary: "Feature by dev",
		intent: { likely_goal: "Add feature", change_type: "feature" },
		scope: { include: ["src/**"], exclude: [] },
		affected_files: [{ filename: "src/feature.ts", status: "added", additions: 20, deletions: 0 }],
		constraints: [],
		acceptance_criteria: [],
		verification: { tests_required: ["unit"], manual_checks: [] },
		risk_flags: [],
		monorepo: { detected: false },
		open_questions: [],
		generation_prompt: "Re-implement the following change...",
		decision_prompt: "You are reviewing...",
		stats: { files_changed: 1, additions: 20, deletions: 0, commits: 1 },
		...overrides,
	} as PromptSpec;
}

function makeIntent(overrides: Partial<Intent> = {}): Intent {
	return {
		goal: "Add a feature",
		expected_scope: [],
		forbidden_scope: [],
		max_risk: "high",
		...overrides,
	};
}

// ---------------------------------------------------------------------------
// Test suite
// ---------------------------------------------------------------------------

describe("checkCommand — runCheck behavior", () => {
	let stdoutSpy: ReturnType<typeof vi.spyOn>;
	let consoleLogSpy: ReturnType<typeof vi.spyOn>;

	beforeEach(() => {
		// Default: no intent, default diff source, no risk flags
		vi.mocked(buildLocalDiffSource).mockReturnValue(makeDiffSource());
		vi.mocked(readIntent).mockReturnValue(null);
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));

		stdoutSpy = vi.spyOn(process.stdout, "write").mockReturnValue(true);
		consoleLogSpy = vi.spyOn(console, "log").mockReturnValue(undefined);
		vi.spyOn(console, "error").mockReturnValue(undefined);
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	// Helper to invoke the check command action and capture the exit code.
	// Mocks must be configured BEFORE calling runAction.
	//
	// Implementation note: the check command action wraps runCheck in a try/catch
	// and calls process.exit() in both branches. To capture the *first* exit code
	// (the meaningful one from runCheck), we track whether exit was already called
	// and only capture the first invocation, then suppress subsequent ones so the
	// action's catch block doesn't re-throw with exit code 1.
	async function runAction(args: string[] = []): Promise<number> {
		let capturedExitCode = -1;
		vi.spyOn(process, "exit").mockImplementation((code?: number | string) => {
			const numeric = typeof code === "number" ? code : Number(code ?? 0);
			if (capturedExitCode === -1) {
				// First call: record the code and throw to unwind the call stack
				capturedExitCode = numeric;
				throw new Error(`exit:${numeric}`);
			}
			// Subsequent calls (from the action's catch block): do NOT overwrite — discard
			return undefined as never;
		});
		try {
			await checkCommand.parseAsync(["node", "check", ...args]);
		} catch (err) {
			// Expected — process.exit throws in tests
		}
		return capturedExitCode;
	}

	// -------------------------------------------------------------------------
	// 1. No intent set — falls back to scan behavior
	// -------------------------------------------------------------------------

	it("exits 0 when no intent set and no high-risk files", async () => {
		vi.mocked(readIntent).mockReturnValue(null);
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		const code = await runAction();
		expect(code).toBe(0);
	});

	it("exits 2 when no intent set but high-risk file present", async () => {
		vi.mocked(readIntent).mockReturnValue(null);
		vi.mocked(generateSpec).mockReturnValue(
			makeSpec({
				risk_flags: [{ category: "auth", severity: "high", description: "auth change" }],
			}),
		);
		const code = await runAction();
		expect(code).toBe(2);
	});

	it("outputs spec JSON envelope when --json and no intent set", async () => {
		vi.mocked(readIntent).mockReturnValue(null);
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		await runAction(["--json"]);
		expect(stdoutSpy).toHaveBeenCalledOnce();
		const written = stdoutSpy.mock.calls[0][0] as string;
		const envelope = JSON.parse(written);
		expect(envelope.version).toBe(1);
		expect(envelope.command).toBe("check");
		expect(envelope.spec).toBeDefined();
	});

	// -------------------------------------------------------------------------
	// 2. Intent set, no drift — exits 0 with status "clean"
	// -------------------------------------------------------------------------

	it("exits 0 when intent set and no drift signals", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent());
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		const code = await runAction();
		expect(code).toBe(0);
	});

	it("prints 'No drift detected.' when intent set and no drift (non-json)", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent());
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		await runAction();
		expect(consoleLogSpy).toHaveBeenCalledWith("No drift detected.");
	});

	// -------------------------------------------------------------------------
	// 3. Intent set, scope_creep — exits 3
	// -------------------------------------------------------------------------

	it("exits 3 when scope_creep detected", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent({ expected_scope: ["src/middleware/**"] }));
		// File outside expected_scope triggers scope_creep
		vi.mocked(buildLocalDiffSource).mockReturnValue(
			makeDiffSource({
				files: [
					{
						filename: "src/unrelated/other.ts",
						status: "modified",
						additions: 10,
						deletions: 0,
					},
				],
			}),
		);
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		const code = await runAction();
		expect(code).toBe(3);
	});

	it("signals array includes scope_creep type when scope violated", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent({ expected_scope: ["src/middleware/**"] }));
		vi.mocked(buildLocalDiffSource).mockReturnValue(
			makeDiffSource({
				files: [
					{
						filename: "src/unrelated/other.ts",
						status: "modified",
						additions: 5,
						deletions: 0,
					},
				],
			}),
		);
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		await runAction(["--json"]);
		const written = stdoutSpy.mock.calls[0][0] as string;
		const envelope = JSON.parse(written);
		const types = (envelope.signals as DriftSignal[]).map((s) => s.type);
		expect(types).toContain("scope_creep");
	});

	// -------------------------------------------------------------------------
	// 4. Intent set, forbidden_touch — exits 3
	// -------------------------------------------------------------------------

	it("exits 3 when forbidden_touch detected", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent({ forbidden_scope: ["src/db/**"] }));
		vi.mocked(buildLocalDiffSource).mockReturnValue(
			makeDiffSource({
				files: [
					{
						filename: "src/db/migration.ts",
						status: "modified",
						additions: 5,
						deletions: 0,
					},
				],
			}),
		);
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		const code = await runAction();
		expect(code).toBe(3);
	});

	it("signals array includes forbidden_touch type when forbidden file modified", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent({ forbidden_scope: ["src/db/**"] }));
		vi.mocked(buildLocalDiffSource).mockReturnValue(
			makeDiffSource({
				files: [
					{
						filename: "src/db/migration.ts",
						status: "modified",
						additions: 5,
						deletions: 0,
					},
				],
			}),
		);
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		await runAction(["--json"]);
		const written = stdoutSpy.mock.calls[0][0] as string;
		const envelope = JSON.parse(written);
		const types = (envelope.signals as DriftSignal[]).map((s) => s.type);
		expect(types).toContain("forbidden_touch");
	});

	// -------------------------------------------------------------------------
	// 5. Intent set, high-risk file but no drift — exits 2
	// -------------------------------------------------------------------------

	it("exits 2 when intent set, no drift signals, but high-risk file present", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent());
		vi.mocked(generateSpec).mockReturnValue(
			makeSpec({
				risk_flags: [{ category: "auth", severity: "high", description: "auth code change" }],
			}),
		);
		const code = await runAction();
		expect(code).toBe(2);
	});

	// -------------------------------------------------------------------------
	// 6. --json flag — outputs valid protocol envelope
	// -------------------------------------------------------------------------

	it("--json with intent outputs envelope with version, command, status, exit_code, signals, spec, intent", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent());
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		await runAction(["--json"]);
		expect(stdoutSpy).toHaveBeenCalledOnce();
		const written = stdoutSpy.mock.calls[0][0] as string;
		const envelope = JSON.parse(written);
		expect(envelope.version).toBe(1);
		expect(envelope.command).toBe("check");
		expect(typeof envelope.status).toBe("string");
		expect(typeof envelope.exit_code).toBe("number");
		expect(envelope.spec).toBeDefined();
		expect(envelope.intent).toBeDefined();
	});

	it("--json envelope status is 'clean' when no drift and no high-risk", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent());
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		await runAction(["--json"]);
		const written = stdoutSpy.mock.calls[0][0] as string;
		const envelope = JSON.parse(written);
		expect(envelope.status).toBe("clean");
		expect(envelope.exit_code).toBe(0);
	});

	it("--json envelope status is 'drift_detected' when drift signals present", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent({ forbidden_scope: ["src/db/**"] }));
		vi.mocked(buildLocalDiffSource).mockReturnValue(
			makeDiffSource({
				files: [
					{
						filename: "src/db/schema.ts",
						status: "modified",
						additions: 5,
						deletions: 0,
					},
				],
			}),
		);
		vi.mocked(generateSpec).mockReturnValue(makeSpec({ risk_flags: [] }));
		await runAction(["--json"]);
		const written = stdoutSpy.mock.calls[0][0] as string;
		const envelope = JSON.parse(written);
		expect(envelope.status).toBe("drift_detected");
		expect(envelope.exit_code).toBe(3);
	});

	// -------------------------------------------------------------------------
	// 7. No files changed — exits 0 cleanly
	// -------------------------------------------------------------------------

	it("exits 0 when no files changed and no intent set", async () => {
		vi.mocked(readIntent).mockReturnValue(null);
		vi.mocked(buildLocalDiffSource).mockReturnValue(makeDiffSource({ files: [] }));
		vi.mocked(generateSpec).mockReturnValue(
			makeSpec({
				risk_flags: [],
				affected_files: [],
				stats: { files_changed: 0, additions: 0, deletions: 0, commits: 0 },
			}),
		);
		const code = await runAction();
		expect(code).toBe(0);
	});

	it("exits 0 when no files changed and intent set (no drift possible)", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent({ expected_scope: ["src/**"] }));
		vi.mocked(buildLocalDiffSource).mockReturnValue(makeDiffSource({ files: [] }));
		vi.mocked(generateSpec).mockReturnValue(
			makeSpec({
				risk_flags: [],
				affected_files: [],
				stats: { files_changed: 0, additions: 0, deletions: 0, commits: 0 },
			}),
		);
		const code = await runAction();
		expect(code).toBe(0);
	});
});
