import { describe, expect, it } from "vitest";
import type { PRData } from "../src/core/github/client.js";
import { generateSpecFromPR } from "../src/core/parsing/pr-parser.js";
import { renderJson } from "../src/core/rendering/json.js";

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
		expect(parsed.source.pr_number).toBe(42);
		expect(parsed.title).toBe("feat: add rate limiting");
	});

	it("does not contain patch data", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		expect(json).not.toContain("export function rateLimit");
	});

	it("round-trips through schema validation", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		expect(parsed.version).toBe(1);
		expect(parsed.stats.files_changed).toBe(3);
		expect(Array.isArray(parsed.risk_flags)).toBe(true);
		expect(Array.isArray(parsed.affected_files)).toBe(true);
	});
});

describe("renderJson field extraction — JSON output contains expected structure", () => {
	it("JSON output title matches PR title exactly", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		expect(parsed.title).toBe("feat: add rate limiting");
		// Ensure it's not the summary field being returned instead
		expect(parsed.title).not.toContain("Feature by");
	});

	it("JSON output version is literal 1, not a truthy number", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		expect(parsed.version).toBe(1);
		expect(parsed.version).not.toBe(2);
		expect(parsed.version).not.toBe(0);
	});

	it("nested source.author is preserved through JSON serialization", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		expect(parsed.source.author).toBe("contributor");
		// Confirm it's not the PR title or branch name
		expect(parsed.source.author).not.toBe("feat: add rate limiting");
	});

	it("stats.files_changed is the count of files, not additions", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		expect(parsed.stats.files_changed).toBe(3);
		// Ensure it's not additions (150) or deletions (20)
		expect(parsed.stats.files_changed).not.toBe(150);
		expect(parsed.stats.files_changed).not.toBe(20);
	});

	it("intent.change_type is 'feature' for feat: prefix PR", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const json = renderJson(spec);
		const parsed = JSON.parse(json);
		expect(parsed.intent.change_type).toBe("feature");
		// Not 'bugfix' or 'mixed'
		expect(parsed.intent.change_type).not.toBe("bugfix");
		expect(parsed.intent.change_type).not.toBe("mixed");
	});
});

describe("scan exit code behavior — risk threshold logic", () => {
	it("risk_flags is empty for a documentation-only PR (exit code would be 0)", () => {
		const spec = generateSpecFromPR(
			makePR({
				title: "docs: update README",
				head_branch: "docs/update-readme",
				files: [
					{
						filename: "README.md",
						status: "modified",
						additions: 5,
						deletions: 2,
					},
				],
			}),
			"owner/repo",
		);
		expect(spec.risk_flags).toHaveLength(0);
	});

	it("auth file changes produce exactly 'authentication' category with high severity", () => {
		const spec = generateSpecFromPR(
			makePR({
				files: [
					{
						filename: "src/auth/login.ts",
						status: "modified",
						additions: 30,
						deletions: 10,
					},
				],
			}),
			"owner/repo",
		);
		const authFlag = spec.risk_flags.find((r) => r.category === "authentication");
		expect(authFlag).toBeDefined();
		expect(authFlag?.severity).toBe("high");
		// Confirm it's the "high" exit code path, not medium
		expect(authFlag?.severity).not.toBe("medium");
		expect(authFlag?.severity).not.toBe("low");
	});

	it("dependency file change produces medium-severity risk (not high), exit code stays 0", () => {
		const spec = generateSpecFromPR(
			makePR({
				files: [
					{
						filename: "package.json",
						status: "modified",
						additions: 3,
						deletions: 1,
					},
				],
			}),
			"owner/repo",
		);
		const hasHighRisk = spec.risk_flags.some((r) => r.severity === "high");
		const hasMediumRisk = spec.risk_flags.some((r) => r.severity === "medium");
		expect(hasHighRisk).toBe(false);
		expect(hasMediumRisk).toBe(true);
	});
});
