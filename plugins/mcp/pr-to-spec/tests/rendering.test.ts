import { describe, expect, it } from "vitest";
import type { PRData } from "../src/core/github/client.js";
import { generateSpecFromPR } from "../src/core/parsing/pr-parser.js";
import { renderComment } from "../src/core/rendering/comment.js";
import { renderJson } from "../src/core/rendering/json.js";
import { renderMarkdown } from "../src/core/rendering/markdown.js";
import { renderYaml } from "../src/core/rendering/yaml.js";
import { PromptSpecSchema } from "../src/core/schema/prompt-spec.js";

function makePR(): PRData {
	return {
		number: 17,
		title: "feat: add webhook handler",
		body: "Implement webhook handler for Stripe events.\n\nHandles payment_intent.succeeded and invoice.paid.",
		url: "https://github.com/owner/repo/pull/17",
		base_branch: "main",
		head_branch: "feat/webhooks",
		author: "dev",
		state: "open",
		commits: 2,
		additions: 80,
		deletions: 5,
		changed_files: 2,
		labels: [],
		linked_issues: [],
		review_comments: [],
		reviews: [],
		files: [
			{
				filename: "src/webhooks/stripe.ts",
				status: "added",
				additions: 60,
				deletions: 0,
				patch: "+export function handleWebhook() {}",
			},
			{
				filename: "src/routes/webhooks.ts",
				status: "modified",
				additions: 20,
				deletions: 5,
			},
		],
	};
}

describe("renderYaml", () => {
	it("produces valid YAML string", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const yaml = renderYaml(spec);
		expect(typeof yaml).toBe("string");
		expect(yaml.length).toBeGreaterThan(100);
	});

	it("contains key fields", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const yaml = renderYaml(spec);
		expect(yaml).toContain("version: 1");
		expect(yaml).toContain("owner/repo");
		expect(yaml).toContain("pr_number: 17");
		expect(yaml).toContain("feat: add webhook handler");
	});

	it("does not contain patch data in affected_files", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const yaml = renderYaml(spec);
		// YAML renderer strips patch field from affected_files
		expect(yaml).not.toContain("export function handleWebhook");
	});
});

describe("renderMarkdown", () => {
	it("produces Markdown with headers", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const md = renderMarkdown(spec);
		expect(md).toContain("# Prompt Spec:");
		expect(md).toContain("## Summary");
		expect(md).toContain("## Affected Files");
	});

	it("includes file status badges", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const md = renderMarkdown(spec);
		expect(md).toContain("[A]");
		expect(md).toContain("[M]");
	});

	it("includes generation prompt in code block", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const md = renderMarkdown(spec);
		expect(md).toContain("## Generation Prompt");
		expect(md).toContain("```");
	});

	it("includes stats table", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const md = renderMarkdown(spec);
		expect(md).toContain("Files changed");
		expect(md).toContain("+80");
	});

	it("includes decision prompt section", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const md = renderMarkdown(spec);
		expect(md).toContain("## Decision Prompt");
	});
});

describe("renderComment", () => {
	it("produces a compact PR comment", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const comment = renderComment(spec);
		expect(comment).toContain("## PR Spec Analysis");
		expect(comment).toContain("pr-to-spec");
	});

	it("includes acceptance criteria as checkboxes", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const comment = renderComment(spec);
		expect(comment).toContain("- [ ]");
	});

	it("includes copy-ready prompt in details block", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const comment = renderComment(spec);
		expect(comment).toContain("<details>");
		expect(comment).toContain("Copy-ready prompt spec");
	});

	it("lists affected files", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const comment = renderComment(spec);
		expect(comment).toContain("stripe.ts");
		expect(comment).toContain("webhooks.ts");
	});
});

describe("renderJson", () => {
	it("produces valid JSON string", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		expect(parsed.version).toBe(1);
	});

	it("contains key fields", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		expect(parsed.source.repo).toBe("owner/repo");
		expect(parsed.source.pr_number).toBe(17);
		expect(parsed.title).toBe("feat: add webhook handler");
	});

	it("does not contain patch data", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		expect(json).not.toContain("export function handleWebhook");
	});

	it("round-trips through PromptSpecSchema validation", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		// Use PromptSpecSchema to validate the round-tripped object
		const result = PromptSpecSchema.safeParse(parsed);
		expect(result.success).toBe(true);
		if (result.success) {
			expect(result.data.version).toBe(1);
			expect(result.data.stats.files_changed).toBe(2);
		}
	});
});

describe("renderMarkdown — risk flags section", () => {
	it("renders Risk Flags section when spec has risk flags", () => {
		const pr = makePR();
		// Add a file that triggers auth risk
		pr.files = [{ filename: "src/auth/login.ts", status: "added", additions: 60, deletions: 0 }];
		const spec = generateSpecFromPR(pr, "owner/repo");
		const md = renderMarkdown(spec);
		expect(md).toContain("## Risk Flags");
		expect(md).toContain("[HIGH]");
		expect(md).toContain("authentication");
	});

	it("does not render Risk Flags section when no risk flags", () => {
		const spec = generateSpecFromPR(
			{
				...makePR(),
				files: [{ filename: "README.md", status: "modified", additions: 5, deletions: 2 }],
			},
			"owner/repo",
		);
		const md = renderMarkdown(spec);
		expect(md).not.toContain("## Risk Flags");
	});

	it("renders status badge [D] for removed files", () => {
		const spec = generateSpecFromPR(
			{
				...makePR(),
				files: [{ filename: "src/old-module.ts", status: "removed", additions: 0, deletions: 50 }],
			},
			"owner/repo",
		);
		const md = renderMarkdown(spec);
		expect(md).toContain("[D]");
		expect(md).not.toContain("[A]");
	});

	it("renders renamed file with [R] badge", () => {
		const spec = generateSpecFromPR(
			{
				...makePR(),
				files: [
					{
						filename: "src/new-name.ts",
						status: "renamed",
						additions: 0,
						deletions: 0,
						previous_filename: "src/old-name.ts",
					},
				],
			},
			"owner/repo",
		);
		const md = renderMarkdown(spec);
		expect(md).toContain("[R]");
	});
});
