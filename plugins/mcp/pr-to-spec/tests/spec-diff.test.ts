import { describe, expect, it } from "vitest";
import { diffSpecs } from "../src/core/diff/spec-diff.js";
import type { PromptSpec } from "../src/core/schema/prompt-spec.js";

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
		title: "feat: add feature",
		summary: "Summary",
		intent: { likely_goal: "Add feature", change_type: "feature" },
		scope: { include: ["src/"], exclude: [] },
		affected_files: [{ filename: "src/main.ts", status: "modified", additions: 10, deletions: 5 }],
		constraints: ["Tests must pass"],
		acceptance_criteria: ["Changes apply cleanly"],
		verification: { tests_required: ["unit"], manual_checks: [] },
		risk_flags: [],
		open_questions: [],
		generation_prompt: "Re-implement",
		stats: { files_changed: 1, additions: 10, deletions: 5, commits: 1 },
		...overrides,
	};
}

describe("diffSpecs", () => {
	it("reports no changes for identical specs", () => {
		const spec = makeSpec();
		const diff = diffSpecs(spec, spec);
		expect(diff.changed).toBe(false);
		expect(diff.sections).toHaveLength(0);
	});

	it("detects title changes", () => {
		const prev = makeSpec({ title: "feat: old title" });
		const curr = makeSpec({ title: "feat: new title" });
		const diff = diffSpecs(prev, curr);
		expect(diff.changed).toBe(true);
		expect(diff.sections.some((s) => s.section === "title" && s.type === "changed")).toBe(true);
	});

	it("detects change type changes", () => {
		const prev = makeSpec({ intent: { likely_goal: "Goal", change_type: "feature" } });
		const curr = makeSpec({ intent: { likely_goal: "Goal", change_type: "bugfix" } });
		const diff = diffSpecs(prev, curr);
		expect(diff.sections.some((s) => s.section === "change_type")).toBe(true);
	});

	it("detects added files", () => {
		const prev = makeSpec();
		const curr = makeSpec({
			affected_files: [
				{ filename: "src/main.ts", status: "modified", additions: 10, deletions: 5 },
				{ filename: "src/new.ts", status: "added", additions: 20, deletions: 0 },
			],
		});
		const diff = diffSpecs(prev, curr);
		const fileSection = diff.sections.find(
			(s) => s.section === "affected_files" && s.type === "added",
		);
		expect(fileSection?.details).toContain("src/new.ts");
	});

	it("detects removed files", () => {
		const prev = makeSpec({
			affected_files: [
				{ filename: "src/main.ts", status: "modified", additions: 10, deletions: 5 },
				{ filename: "src/old.ts", status: "removed", additions: 0, deletions: 30 },
			],
		});
		const curr = makeSpec();
		const diff = diffSpecs(prev, curr);
		const fileSection = diff.sections.find(
			(s) => s.section === "affected_files" && s.type === "removed",
		);
		expect(fileSection?.details).toContain("src/old.ts");
	});

	it("detects stats changes", () => {
		const prev = makeSpec({ stats: { files_changed: 1, additions: 10, deletions: 5, commits: 1 } });
		const curr = makeSpec({
			stats: { files_changed: 3, additions: 50, deletions: 20, commits: 2 },
		});
		const diff = diffSpecs(prev, curr);
		expect(diff.sections.some((s) => s.section === "stats")).toBe(true);
	});

	it("detects new risk flags", () => {
		const prev = makeSpec();
		const curr = makeSpec({
			risk_flags: [{ category: "authentication", description: "Auth changes", severity: "high" }],
		});
		const diff = diffSpecs(prev, curr);
		const riskSection = diff.sections.find((s) => s.section === "risk_flags" && s.type === "added");
		expect(riskSection?.details).toContain("authentication:high");
	});

	it("detects resolved risk flags", () => {
		const prev = makeSpec({
			risk_flags: [{ category: "database", description: "DB migration", severity: "high" }],
		});
		const curr = makeSpec();
		const diff = diffSpecs(prev, curr);
		const riskSection = diff.sections.find(
			(s) => s.section === "risk_flags" && s.type === "removed",
		);
		expect(riskSection?.details).toContain("database:high");
	});

	it("detects review status changes", () => {
		const prev = makeSpec({
			review_summary: {
				total_comments: 2,
				reviewers: ["alice"],
				approval_status: "changes_requested",
				key_concerns: [],
				file_discussions: [],
			},
		});
		const curr = makeSpec({
			review_summary: {
				total_comments: 3,
				reviewers: ["alice"],
				approval_status: "approved",
				key_concerns: [],
				file_discussions: [],
			},
		});
		const diff = diffSpecs(prev, curr);
		expect(diff.sections.some((s) => s.section === "review_status" && s.type === "changed")).toBe(
			true,
		);
	});
});
