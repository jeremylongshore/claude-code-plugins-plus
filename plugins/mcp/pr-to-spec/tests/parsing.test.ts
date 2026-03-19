import { describe, expect, it } from "vitest";
import type { PRData } from "../src/core/github/client.js";
import { compactSpec, generateSpecFromPR } from "../src/core/parsing/pr-parser.js";
import { PromptSpecSchema } from "../src/core/schema/prompt-spec.js";

function makePR(overrides: Partial<PRData> = {}): PRData {
	return {
		number: 42,
		title: "feat: add rate limiting",
		body: "Add tenant-aware rate limiting to public API routes.\n\nThis prevents abuse.",
		url: "https://github.com/owner/repo/pull/42",
		base_branch: "main",
		head_branch: "feat/rate-limiting",
		author: "contributor",
		state: "open",
		commits: 3,
		additions: 150,
		deletions: 20,
		changed_files: 3,
		labels: [],
		linked_issues: [],
		review_comments: [],
		reviews: [],
		files: [
			{
				filename: "src/middleware/rateLimit.ts",
				status: "added",
				additions: 100,
				deletions: 0,
				patch: "+export function rateLimit() {}",
			},
			{
				filename: "src/routes/api.ts",
				status: "modified",
				additions: 30,
				deletions: 10,
				patch: "+import { rateLimit } from './middleware'",
			},
			{
				filename: "tests/rateLimit.test.ts",
				status: "added",
				additions: 20,
				deletions: 10,
			},
		],
		...overrides,
	};
}

describe("generateSpecFromPR", () => {
	it("produces a valid spec", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const result = PromptSpecSchema.safeParse(spec);
		expect(result.success).toBe(true);
	});

	it("sets version to 1", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		expect(spec.version).toBe(1);
	});

	it("extracts source metadata", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		expect(spec.source.repo).toBe("owner/repo");
		expect(spec.source.pr_number).toBe(42);
		expect(spec.source.author).toBe("contributor");
	});

	it("infers feature change type from title", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		expect(spec.intent.change_type).toBe("feature");
	});

	it("infers bugfix change type", () => {
		const spec = generateSpecFromPR(
			makePR({ title: "fix: null pointer in parser", head_branch: "fix/null-pointer" }),
			"owner/repo",
		);
		expect(spec.intent.change_type).toBe("bugfix");
	});

	it("infers docs change type from file extensions", () => {
		const spec = generateSpecFromPR(
			makePR({
				title: "Update docs",
				head_branch: "docs/update",
				files: [{ filename: "README.md", status: "modified", additions: 10, deletions: 5 }],
			}),
			"owner/repo",
		);
		expect(spec.intent.change_type).toBe("docs");
	});

	it("uses PR body first paragraph as goal", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		expect(spec.intent.likely_goal).toBe("Add tenant-aware rate limiting to public API routes.");
	});

	it("falls back to title when body is empty", () => {
		const spec = generateSpecFromPR(makePR({ body: null }), "owner/repo");
		expect(spec.intent.likely_goal).toContain("add rate limiting");
	});

	it("populates stats correctly", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		expect(spec.stats.files_changed).toBe(3);
		expect(spec.stats.additions).toBe(150);
		expect(spec.stats.deletions).toBe(20);
		expect(spec.stats.commits).toBe(3);
	});

	it("generates a non-empty generation prompt", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		expect(spec.generation_prompt.length).toBeGreaterThan(50);
		expect(spec.generation_prompt).toContain("owner/repo");
	});

	it("includes affected files", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		expect(spec.affected_files).toHaveLength(3);
		expect(spec.affected_files[0].filename).toBe("src/middleware/rateLimit.ts");
	});

	it("generates a decision prompt", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		expect(spec.decision_prompt.length).toBeGreaterThan(50);
		expect(spec.decision_prompt).toContain("Decision Required");
		expect(spec.decision_prompt).toContain("APPROVE");
		expect(spec.decision_prompt).toContain("REQUEST_CHANGES");
	});
});

describe("compactSpec", () => {
	it("removes patch data from files", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const compact = compactSpec(spec);
		for (const f of compact.affected_files) {
			expect(f.patch).toBeUndefined();
		}
	});

	it("preserves all other fields", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const compact = compactSpec(spec);
		expect(compact.title).toBe(spec.title);
		expect(compact.source).toEqual(spec.source);
		expect(compact.stats).toEqual(spec.stats);
	});
});
