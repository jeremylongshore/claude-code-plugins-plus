import { describe, expect, it, vi } from "vitest";
import type { PromptSpec } from "../src/core/schema/prompt-spec.js";

// Mock fetch globally before importing enhancer
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

const { enhanceSpec } = await import("../src/core/ai/enhancer.js");

function makeSpec(overrides: Partial<PromptSpec> = {}): PromptSpec {
	return {
		version: 1,
		generated_at: new Date().toISOString(),
		source: {
			repo: "owner/repo",
			pr_number: 1,
			pr_url: "https://github.com/owner/repo/pull/1",
			base_branch: "main",
			head_branch: "feat/test",
			author: "dev",
		},
		title: "feat: add test feature",
		summary: "Feature PR by @dev: add test feature — 2 files changed (+50/-10)",
		intent: { likely_goal: "Add a test feature", change_type: "feature" },
		scope: { include: ["src/test.ts"], exclude: [] },
		affected_files: [
			{ filename: "src/test.ts", status: "added", additions: 50, deletions: 0 },
			{ filename: "src/index.ts", status: "modified", additions: 5, deletions: 10 },
		],
		constraints: ["Existing tests must continue to pass"],
		acceptance_criteria: ["Changes apply cleanly to main"],
		verification: { tests_required: ["unit"], manual_checks: [] },
		risk_flags: [],
		open_questions: [],
		generation_prompt: "Re-implement this change",
		stats: { files_changed: 2, additions: 50, deletions: 10, commits: 1 },
		...overrides,
	};
}

const MOCK_AI_RESPONSE = JSON.stringify({
	summary: "Adds a new test feature with clean integration",
	goal: "Enable test feature for end users",
	key_changes: ["New test module added", "Index updated with export"],
	review_hints: ["Check export compatibility"],
});

describe("enhanceSpec", () => {
	it("calls Anthropic API and merges ai_enhanced into spec", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: async () => ({ content: [{ text: MOCK_AI_RESPONSE }] }),
		});

		const spec = makeSpec();
		const enhanced = await enhanceSpec(spec, {
			provider: "anthropic",
			apiKey: "test-key",
		});

		expect(enhanced.ai_enhanced).toBeDefined();
		expect(enhanced.ai_enhanced?.summary).toBe("Adds a new test feature with clean integration");
		expect(enhanced.ai_enhanced?.goal).toBe("Enable test feature for end users");
		expect(enhanced.ai_enhanced?.key_changes).toHaveLength(2);
		expect(enhanced.ai_enhanced?.review_hints).toHaveLength(1);
		expect(enhanced.ai_enhanced?.provider).toContain("anthropic/");

		// Verify API call
		expect(mockFetch).toHaveBeenCalledWith(
			"https://api.anthropic.com/v1/messages",
			expect.objectContaining({
				method: "POST",
				headers: expect.objectContaining({ "x-api-key": "test-key" }),
			}),
		);
	});

	it("calls OpenAI API when provider is openai", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: async () => ({
				choices: [{ message: { content: MOCK_AI_RESPONSE } }],
			}),
		});

		const spec = makeSpec();
		const enhanced = await enhanceSpec(spec, {
			provider: "openai",
			apiKey: "sk-test",
		});

		expect(enhanced.ai_enhanced?.provider).toContain("openai/");
		expect(mockFetch).toHaveBeenCalledWith(
			"https://api.openai.com/v1/chat/completions",
			expect.objectContaining({ method: "POST" }),
		);
	});

	it("preserves original spec fields", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: async () => ({ content: [{ text: MOCK_AI_RESPONSE }] }),
		});

		const spec = makeSpec();
		const enhanced = await enhanceSpec(spec, {
			provider: "anthropic",
			apiKey: "test-key",
		});

		expect(enhanced.title).toBe(spec.title);
		expect(enhanced.summary).toBe(spec.summary);
		expect(enhanced.intent).toEqual(spec.intent);
		expect(enhanced.risk_flags).toEqual(spec.risk_flags);
	});

	it("throws on API error", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 401,
			text: async () => "Unauthorized",
		});

		await expect(
			enhanceSpec(makeSpec(), { provider: "anthropic", apiKey: "bad-key" }),
		).rejects.toThrow("Anthropic API error (401)");
	});

	it("throws on malformed JSON response", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: async () => ({ content: [{ text: "not json at all" }] }),
		});

		await expect(
			enhanceSpec(makeSpec(), { provider: "anthropic", apiKey: "test-key" }),
		).rejects.toThrow("Failed to parse AI response");
	});

	it("handles markdown-fenced JSON response", async () => {
		const fenced = `\`\`\`json\n${MOCK_AI_RESPONSE}\n\`\`\``;
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: async () => ({ content: [{ text: fenced }] }),
		});

		const enhanced = await enhanceSpec(makeSpec(), {
			provider: "anthropic",
			apiKey: "test-key",
		});

		expect(enhanced.ai_enhanced?.summary).toBe("Adds a new test feature with clean integration");
	});

	it("uses custom model when specified", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: async () => ({ content: [{ text: MOCK_AI_RESPONSE }] }),
		});

		const enhanced = await enhanceSpec(makeSpec(), {
			provider: "anthropic",
			apiKey: "test-key",
			model: "claude-opus-4-20250514",
		});

		expect(enhanced.ai_enhanced?.provider).toBe("anthropic/claude-opus-4-20250514");
	});
});
