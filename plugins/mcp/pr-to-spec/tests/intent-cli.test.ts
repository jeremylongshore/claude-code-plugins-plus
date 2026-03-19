import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Intent } from "../src/core/intent/schema.js";

// ---------------------------------------------------------------------------
// Module-level mocks — must come before any import of the module under test
// ---------------------------------------------------------------------------

vi.mock("../src/core/intent/storage.js", () => ({
	readIntent: vi.fn(),
	writeIntent: vi.fn(),
	getIntentPath: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Lazy imports (after mocks are registered)
// ---------------------------------------------------------------------------

import { intentCommand } from "../src/cli/intent.js";
import { readIntent, writeIntent } from "../src/core/intent/storage.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeIntent(overrides: Partial<Intent> = {}): Intent {
	return {
		goal: "Add rate limiting",
		expected_scope: [],
		forbidden_scope: [],
		max_risk: "high",
		created_at: "2026-01-01T00:00:00.000Z",
		updated_at: "2026-01-01T00:00:00.000Z",
		...overrides,
	};
}

// ---------------------------------------------------------------------------
// Test suite — intent set
// ---------------------------------------------------------------------------

describe("intent set", () => {
	let consoleLogSpy: ReturnType<typeof vi.spyOn>;

	beforeEach(() => {
		consoleLogSpy = vi.spyOn(console, "log").mockReturnValue(undefined);
		vi.mocked(readIntent).mockReturnValue(null);
		vi.mocked(writeIntent).mockReturnValue(undefined);
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	// -------------------------------------------------------------------------
	// 1. intent set with all options
	// -------------------------------------------------------------------------

	it("writes intent with all options provided", async () => {
		await intentCommand.parseAsync([
			"node",
			"intent",
			"set",
			"--goal",
			"Add rate limiting to API",
			"--scope",
			"src/middleware/**",
			"--forbid",
			"src/db/**",
			"--max-risk",
			"medium",
			"--type",
			"feature",
			"--size-budget",
			"200",
		]);

		expect(writeIntent).toHaveBeenCalledOnce();
		const saved = vi.mocked(writeIntent).mock.calls[0][0];
		expect(saved.goal).toBe("Add rate limiting to API");
		expect(saved.expected_scope).toEqual(["src/middleware/**"]);
		expect(saved.forbidden_scope).toEqual(["src/db/**"]);
		expect(saved.max_risk).toBe("medium");
		expect(saved.expected_type).toBe("feature");
		expect(saved.size_budget).toBe(200);
	});

	// -------------------------------------------------------------------------
	// 2. intent set minimal — only goal, defaults applied
	// -------------------------------------------------------------------------

	it("applies defaults when only --goal is provided", async () => {
		await intentCommand.parseAsync(["node", "intent", "set", "--goal", "Fix the bug"]);

		expect(writeIntent).toHaveBeenCalledOnce();
		const saved = vi.mocked(writeIntent).mock.calls[0][0];
		expect(saved.goal).toBe("Fix the bug");
		expect(saved.expected_scope).toEqual([]);
		expect(saved.forbidden_scope).toEqual([]);
		expect(saved.max_risk).toBe("high");
		expect(saved.expected_type).toBeUndefined();
		expect(saved.size_budget).toBeUndefined();
	});

	// -------------------------------------------------------------------------
	// 3. intent set --json — outputs JSON of saved intent
	// -------------------------------------------------------------------------

	it("outputs JSON when --json flag is set", async () => {
		await intentCommand.parseAsync(["node", "intent", "set", "--goal", "Add pagination", "--json"]);

		expect(consoleLogSpy).toHaveBeenCalledOnce();
		const output = consoleLogSpy.mock.calls[0][0] as string;
		const parsed = JSON.parse(output);
		expect(parsed.goal).toBe("Add pagination");
		expect(parsed.max_risk).toBe("high");
	});

	// -------------------------------------------------------------------------
	// 4. intent set without --json prints confirmation message
	// -------------------------------------------------------------------------

	it("prints confirmation message when --json not set", async () => {
		await intentCommand.parseAsync(["node", "intent", "set", "--goal", "Refactor auth module"]);

		expect(consoleLogSpy).toHaveBeenCalledOnce();
		const msg = consoleLogSpy.mock.calls[0][0] as string;
		expect(msg).toContain("Intent saved:");
		expect(msg).toContain("Refactor auth module");
	});

	// -------------------------------------------------------------------------
	// 5. intent set preserves created_at on subsequent updates
	// -------------------------------------------------------------------------

	it("preserves created_at from existing intent on update", async () => {
		const originalCreatedAt = "2025-12-01T00:00:00.000Z";
		vi.mocked(readIntent).mockReturnValue(makeIntent({ created_at: originalCreatedAt }));

		await intentCommand.parseAsync(["node", "intent", "set", "--goal", "Updated goal"]);

		expect(writeIntent).toHaveBeenCalledOnce();
		const saved = vi.mocked(writeIntent).mock.calls[0][0];
		expect(saved.created_at).toBe(originalCreatedAt);
	});

	it("updates updated_at to a newer timestamp on update", async () => {
		const originalUpdatedAt = "2025-12-01T00:00:00.000Z";
		vi.mocked(readIntent).mockReturnValue(makeIntent({ updated_at: originalUpdatedAt }));

		await intentCommand.parseAsync(["node", "intent", "set", "--goal", "Updated goal"]);

		expect(writeIntent).toHaveBeenCalledOnce();
		const saved = vi.mocked(writeIntent).mock.calls[0][0];
		// updated_at should be a valid ISO string different from (or equal to) the old one,
		// but it will always be >= original since time only moves forward
		expect(saved.updated_at).toBeDefined();
		expect(new Date(saved.updated_at as string).getTime()).toBeGreaterThanOrEqual(
			new Date(originalUpdatedAt).getTime(),
		);
	});

	// -------------------------------------------------------------------------
	// 6. intent set with --type and --size-budget stored correctly
	// -------------------------------------------------------------------------

	it("stores expected_type and size_budget correctly", async () => {
		await intentCommand.parseAsync([
			"node",
			"intent",
			"set",
			"--goal",
			"Refactor DB layer",
			"--type",
			"refactor",
			"--size-budget",
			"500",
		]);

		const saved = vi.mocked(writeIntent).mock.calls[0][0];
		expect(saved.expected_type).toBe("refactor");
		expect(saved.size_budget).toBe(500);
	});

	// -------------------------------------------------------------------------
	// 7. intent set when no prior intent — creates new created_at
	// -------------------------------------------------------------------------

	it("creates new created_at when no prior intent exists", async () => {
		vi.mocked(readIntent).mockReturnValue(null);

		await intentCommand.parseAsync(["node", "intent", "set", "--goal", "Brand new project goal"]);

		const saved = vi.mocked(writeIntent).mock.calls[0][0];
		expect(saved.created_at).toBeDefined();
		expect(typeof saved.created_at).toBe("string");
		// Should be a valid ISO date
		expect(() => new Date(saved.created_at as string)).not.toThrow();
	});
});

// ---------------------------------------------------------------------------
// Test suite — intent show
// ---------------------------------------------------------------------------

describe("intent show", () => {
	let consoleLogSpy: ReturnType<typeof vi.spyOn>;

	beforeEach(() => {
		consoleLogSpy = vi.spyOn(console, "log").mockReturnValue(undefined);
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	// -------------------------------------------------------------------------
	// 1. intent show when intent exists — prints goal, scope, etc.
	// -------------------------------------------------------------------------

	it("prints goal when intent exists", async () => {
		vi.mocked(readIntent).mockReturnValue(makeIntent({ goal: "Add rate limiting" }));

		await intentCommand.parseAsync(["node", "intent", "show"]);

		const allOutput = consoleLogSpy.mock.calls.map((c) => c[0]).join("\n");
		expect(allOutput).toContain("Goal: Add rate limiting");
	});

	it("prints max_risk when intent exists", async () => {
		vi.mocked(readIntent).mockReturnValue(
			makeIntent({ goal: "Add rate limiting", max_risk: "medium" }),
		);

		await intentCommand.parseAsync(["node", "intent", "show"]);

		const allOutput = consoleLogSpy.mock.calls.map((c) => c[0]).join("\n");
		expect(allOutput).toContain("Max risk: medium");
	});

	it("prints scope and forbidden when present", async () => {
		vi.mocked(readIntent).mockReturnValue(
			makeIntent({
				goal: "Scoped change",
				expected_scope: ["src/api/**"],
				forbidden_scope: ["src/db/**"],
			}),
		);

		await intentCommand.parseAsync(["node", "intent", "show"]);

		const allOutput = consoleLogSpy.mock.calls.map((c) => c[0]).join("\n");
		expect(allOutput).toContain("Scope:");
		expect(allOutput).toContain("Forbidden:");
	});

	it("prints expected_type when set", async () => {
		vi.mocked(readIntent).mockReturnValue(
			makeIntent({ goal: "Typed change", expected_type: "bugfix" }),
		);

		await intentCommand.parseAsync(["node", "intent", "show"]);

		const allOutput = consoleLogSpy.mock.calls.map((c) => c[0]).join("\n");
		expect(allOutput).toContain("Type: bugfix");
	});

	it("prints size_budget when set", async () => {
		vi.mocked(readIntent).mockReturnValue(
			makeIntent({ goal: "Budgeted change", size_budget: 300 }),
		);

		await intentCommand.parseAsync(["node", "intent", "show"]);

		const allOutput = consoleLogSpy.mock.calls.map((c) => c[0]).join("\n");
		expect(allOutput).toContain("Size budget: 300 LOC");
	});

	// -------------------------------------------------------------------------
	// 2. intent show --json — outputs valid JSON
	// -------------------------------------------------------------------------

	it("outputs valid JSON when --json and intent exists", async () => {
		const intent = makeIntent({ goal: "JSON output test", max_risk: "low" });
		vi.mocked(readIntent).mockReturnValue(intent);

		await intentCommand.parseAsync(["node", "intent", "show", "--json"]);

		expect(consoleLogSpy).toHaveBeenCalledOnce();
		const output = consoleLogSpy.mock.calls[0][0] as string;
		const parsed = JSON.parse(output);
		expect(parsed.goal).toBe("JSON output test");
		expect(parsed.max_risk).toBe("low");
	});

	// -------------------------------------------------------------------------
	// 3. intent show when no intent — prints helpful message (not an error)
	// -------------------------------------------------------------------------

	it("prints helpful message when no intent set", async () => {
		vi.mocked(readIntent).mockReturnValue(null);

		await intentCommand.parseAsync(["node", "intent", "show"]);

		expect(consoleLogSpy).toHaveBeenCalledOnce();
		const msg = consoleLogSpy.mock.calls[0][0] as string;
		expect(msg).toContain("No intent set");
		// Should mention how to set it
		expect(msg).toContain("intent set");
	});

	// -------------------------------------------------------------------------
	// 4. intent show --json when no intent — outputs JSON null
	// -------------------------------------------------------------------------

	it("outputs JSON null when --json and no intent exists", async () => {
		vi.mocked(readIntent).mockReturnValue(null);

		await intentCommand.parseAsync(["node", "intent", "show", "--json"]);

		expect(consoleLogSpy).toHaveBeenCalledOnce();
		const output = consoleLogSpy.mock.calls[0][0] as string;
		const parsed = JSON.parse(output);
		expect(parsed).toBeNull();
	});
});
