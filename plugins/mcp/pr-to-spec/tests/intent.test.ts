import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { IntentSchema } from "../src/core/intent/schema.js";
import { getIntentPath, readIntent, writeIntent } from "../src/core/intent/storage.js";

describe("IntentSchema", () => {
	it("validates a minimal intent", () => {
		const result = IntentSchema.safeParse({ goal: "Add rate limiting" });
		expect(result.success).toBe(true);
		if (result.success) {
			expect(result.data.goal).toBe("Add rate limiting");
			expect(result.data.expected_scope).toEqual([]);
			expect(result.data.forbidden_scope).toEqual([]);
			expect(result.data.max_risk).toBe("high");
		}
	});

	it("validates a full intent", () => {
		const result = IntentSchema.safeParse({
			goal: "Add rate limiting to API",
			expected_scope: ["src/middleware/**"],
			forbidden_scope: ["src/db/**"],
			max_risk: "medium",
			expected_type: "feature",
			size_budget: 200,
			created_at: "2026-03-17T00:00:00.000Z",
			updated_at: "2026-03-17T00:00:00.000Z",
		});
		expect(result.success).toBe(true);
		if (result.success) {
			expect(result.data.max_risk).toBe("medium");
			expect(result.data.expected_type).toBe("feature");
			expect(result.data.size_budget).toBe(200);
		}
	});

	it("rejects empty goal", () => {
		const result = IntentSchema.safeParse({ goal: "" });
		expect(result.success).toBe(false);
	});

	it("rejects invalid max_risk", () => {
		const result = IntentSchema.safeParse({ goal: "Test", max_risk: "critical" });
		expect(result.success).toBe(false);
	});

	it("rejects invalid expected_type", () => {
		const result = IntentSchema.safeParse({ goal: "Test", expected_type: "hotfix" });
		expect(result.success).toBe(false);
	});

	it("rejects negative size_budget", () => {
		const result = IntentSchema.safeParse({ goal: "Test", size_budget: -10 });
		expect(result.success).toBe(false);
	});

	it("allows optional fields to be absent", () => {
		const result = IntentSchema.safeParse({ goal: "Test change" });
		expect(result.success).toBe(true);
		if (result.success) {
			expect(result.data.expected_type).toBeUndefined();
			expect(result.data.size_budget).toBeUndefined();
		}
	});
});

describe("Intent storage round-trip", () => {
	let tmpDir: string;

	beforeEach(() => {
		tmpDir = join(tmpdir(), `pr-to-spec-test-${Date.now()}`);
		mkdirSync(tmpDir, { recursive: true });
	});

	afterEach(() => {
		rmSync(tmpDir, { recursive: true, force: true });
	});

	it("returns null when no intent file exists", () => {
		const result = readIntent(tmpDir);
		expect(result).toBeNull();
	});

	it("round-trips a minimal intent", () => {
		const intent = IntentSchema.parse({ goal: "Add pagination" });
		writeIntent(intent, tmpDir);
		const loaded = readIntent(tmpDir);
		expect(loaded).not.toBeNull();
		expect(loaded?.goal).toBe("Add pagination");
	});

	it("round-trips a full intent", () => {
		const intent = IntentSchema.parse({
			goal: "Add rate limiting to API",
			expected_scope: ["src/middleware/**", "src/routes/**"],
			forbidden_scope: ["src/db/**"],
			max_risk: "medium",
			expected_type: "feature",
			size_budget: 300,
		});
		writeIntent(intent, tmpDir);
		const loaded = readIntent(tmpDir);
		expect(loaded?.goal).toBe("Add rate limiting to API");
		expect(loaded?.expected_scope).toEqual(["src/middleware/**", "src/routes/**"]);
		expect(loaded?.forbidden_scope).toEqual(["src/db/**"]);
		expect(loaded?.max_risk).toBe("medium");
		expect(loaded?.expected_type).toBe("feature");
		expect(loaded?.size_budget).toBe(300);
	});

	it("getIntentPath returns correct path", () => {
		const path = getIntentPath(tmpDir);
		expect(path).toContain(".pr-to-spec");
		expect(path).toContain("intent.yaml");
	});

	it("overwrites an existing intent on write", () => {
		const intent1 = IntentSchema.parse({ goal: "First goal" });
		writeIntent(intent1, tmpDir);
		const intent2 = IntentSchema.parse({ goal: "Second goal" });
		writeIntent(intent2, tmpDir);
		const loaded = readIntent(tmpDir);
		expect(loaded?.goal).toBe("Second goal");
	});

	it("writeIntent creates the .pr-to-spec directory if it does not exist", () => {
		const nestedDir = join(tmpDir, "new-project");
		// nestedDir does not exist yet
		const intent = IntentSchema.parse({ goal: "Create dir test" });
		// Should not throw
		expect(() => writeIntent(intent, nestedDir)).not.toThrow();
		const loaded = readIntent(nestedDir);
		expect(loaded?.goal).toBe("Create dir test");
	});

	it("readIntent throws on corrupt YAML that fails schema validation", () => {
		// Write a YAML file with an invalid intent (empty goal violates min(1))
		const intentDir = join(tmpDir, "corrupt-test", ".pr-to-spec");
		mkdirSync(intentDir, { recursive: true });
		writeFileSync(join(intentDir, "intent.yaml"), 'goal: ""\n', "utf-8");
		// readIntent should throw because goal is empty (fails schema validation)
		expect(() => readIntent(join(tmpDir, "corrupt-test"))).toThrow();
	});

	it("written YAML file contains the goal field", () => {
		const intent = IntentSchema.parse({ goal: "Inspect file contents" });
		writeIntent(intent, tmpDir);
		const raw = readFileSync(getIntentPath(tmpDir), "utf-8");
		expect(raw).toContain("Inspect file contents");
	});
});

describe("IntentSchema — default values", () => {
	it("defaults expected_scope to empty array", () => {
		const result = IntentSchema.parse({ goal: "Test" });
		expect(result.expected_scope).toEqual([]);
	});

	it("defaults forbidden_scope to empty array", () => {
		const result = IntentSchema.parse({ goal: "Test" });
		expect(result.forbidden_scope).toEqual([]);
	});

	it("defaults max_risk to high", () => {
		const result = IntentSchema.parse({ goal: "Test" });
		expect(result.max_risk).toBe("high");
	});

	it("accepts all valid expected_type values", () => {
		const types = ["feature", "bugfix", "refactor", "docs", "test", "chore", "config", "mixed"];
		for (const t of types) {
			const result = IntentSchema.safeParse({ goal: "Test", expected_type: t });
			expect(result.success).toBe(true);
		}
	});

	it("rejects zero size_budget (must be positive integer)", () => {
		const result = IntentSchema.safeParse({ goal: "Test", size_budget: 0 });
		expect(result.success).toBe(false);
	});
});
