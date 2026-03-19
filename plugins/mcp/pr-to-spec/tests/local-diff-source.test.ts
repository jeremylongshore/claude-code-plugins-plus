import { describe, expect, it, vi } from "vitest";
import type { PRData } from "../src/core/github/client.js";
import { githubPRtoDiffSource } from "../src/core/sources/github.js";
import { buildLocalDiffSource, parseDiffStat, parseNameStatus } from "../src/core/sources/local.js";
import type { DiffSource } from "../src/core/sources/types.js";

function makePR(): PRData {
	return {
		number: 42,
		title: "feat: add rate limiting",
		body: "Add tenant-aware rate limiting to public API routes.",
		url: "https://github.com/owner/repo/pull/42",
		base_branch: "main",
		head_branch: "feat/rate-limiting",
		author: "contributor",
		state: "open",
		commits: 3,
		additions: 150,
		deletions: 20,
		changed_files: 3,
		labels: ["enhancement"],
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
				filename: "src/old.ts",
				status: "removed",
				additions: 0,
				deletions: 20,
				previous_filename: undefined,
			},
		],
	};
}

describe("githubPRtoDiffSource", () => {
	it("produces a valid DiffSource from PRData", () => {
		const source: DiffSource = githubPRtoDiffSource(makePR(), "owner/repo");
		expect(source.source_type).toBe("github_pr");
		expect(source.title).toBe("feat: add rate limiting");
		expect(source.author).toBe("contributor");
		expect(source.base_ref).toBe("main");
		expect(source.head_ref).toBe("feat/rate-limiting");
		expect(source.repo).toBe("owner/repo");
		expect(source.pr_number).toBe(42);
		expect(source.pr_url).toBe("https://github.com/owner/repo/pull/42");
	});

	it("maps files correctly", () => {
		const source = githubPRtoDiffSource(makePR(), "owner/repo");
		expect(source.files).toHaveLength(3);
		expect(source.files[0].filename).toBe("src/middleware/rateLimit.ts");
		expect(source.files[0].status).toBe("added");
		expect(source.files[0].additions).toBe(100);
		expect(source.files[0].patch).toBe("+export function rateLimit() {}");
		expect(source.files[2].status).toBe("removed");
	});

	it("copies labels", () => {
		const source = githubPRtoDiffSource(makePR(), "owner/repo");
		expect(source.labels).toEqual(["enhancement"]);
	});

	it("copies commits", () => {
		const source = githubPRtoDiffSource(makePR(), "owner/repo");
		expect(source.commits).toBe(3);
	});

	it("maps body to undefined when null", () => {
		const pr = makePR();
		pr.body = null;
		const source = githubPRtoDiffSource(pr, "owner/repo");
		expect(source.body).toBeUndefined();
	});

	it("normalizes unknown status to modified", () => {
		const pr = makePR();
		pr.files[1].status = "changed"; // non-standard
		const source = githubPRtoDiffSource(pr, "owner/repo");
		expect(source.files[1].status).toBe("modified");
	});
});

describe("parseDiffStat", () => {
	it("parses a standard diff stat line", () => {
		const input = " src/middleware/rateLimit.ts | 10 ++++++----\n";
		const result = parseDiffStat(input);
		expect(result).toHaveLength(1);
		expect(result[0].filename).toBe("src/middleware/rateLimit.ts");
		expect(result[0].additions + result[0].deletions).toBe(10);
	});

	it("returns empty array for empty output", () => {
		const result = parseDiffStat("");
		expect(result).toHaveLength(0);
	});

	it("handles multiple lines", () => {
		const input = [
			" src/a.ts | 5 +++++",
			" src/b.ts | 3 +--",
			" 2 files changed, 6 insertions(+), 2 deletions(-)",
		].join("\n");
		const result = parseDiffStat(input);
		expect(result).toHaveLength(2);
		expect(result.map((r) => r.filename)).toContain("src/a.ts");
		expect(result.map((r) => r.filename)).toContain("src/b.ts");
	});
});

describe("parseNameStatus", () => {
	it("parses added files", () => {
		const result = parseNameStatus("A\tsrc/new.ts\n");
		expect(result).toHaveLength(1);
		expect(result[0].status).toBe("added");
		expect(result[0].filename).toBe("src/new.ts");
	});

	it("parses deleted files", () => {
		const result = parseNameStatus("D\tsrc/old.ts\n");
		expect(result[0].status).toBe("removed");
		expect(result[0].filename).toBe("src/old.ts");
	});

	it("parses modified files", () => {
		const result = parseNameStatus("M\tsrc/changed.ts\n");
		expect(result[0].status).toBe("modified");
		expect(result[0].filename).toBe("src/changed.ts");
	});

	it("parses renamed files", () => {
		const result = parseNameStatus("R100\tsrc/old.ts\tsrc/new.ts\n");
		expect(result[0].status).toBe("renamed");
		expect(result[0].filename).toBe("src/new.ts");
		expect(result[0].previous_filename).toBe("src/old.ts");
	});

	it("parses copied files", () => {
		const result = parseNameStatus("C100\tsrc/original.ts\tsrc/copy.ts\n");
		expect(result[0].status).toBe("copied");
		expect(result[0].filename).toBe("src/copy.ts");
		expect(result[0].previous_filename).toBe("src/original.ts");
	});

	it("handles empty lines gracefully", () => {
		const result = parseNameStatus("\n\n");
		expect(result).toHaveLength(0);
	});

	it("handles multiple files", () => {
		const input = "A\tsrc/a.ts\nM\tsrc/b.ts\nD\tsrc/c.ts\n";
		const result = parseNameStatus(input);
		expect(result).toHaveLength(3);
		expect(result.map((r) => r.status)).toEqual(["added", "modified", "removed"]);
	});

	it("treats unknown status codes as modified", () => {
		const result = parseNameStatus("X\tsrc/weird.ts\n");
		expect(result[0].status).toBe("modified");
		expect(result[0].filename).toBe("src/weird.ts");
	});
});

describe("parseDiffStat — edge cases", () => {
	it("handles a line with only deletions (all minuses)", () => {
		const input = " src/removed.ts | 8 --------\n";
		const result = parseDiffStat(input);
		expect(result).toHaveLength(1);
		expect(result[0].filename).toBe("src/removed.ts");
		expect(result[0].deletions).toBe(8);
		expect(result[0].additions).toBe(0);
	});

	it("handles a line with only additions (all plusses)", () => {
		const input = " src/added.ts | 15 +++++++++++++++\n";
		const result = parseDiffStat(input);
		expect(result).toHaveLength(1);
		expect(result[0].additions).toBe(15);
		expect(result[0].deletions).toBe(0);
	});

	it("ignores the summary line at the bottom of diff --stat", () => {
		const input = [" src/a.ts | 5 +++++", " 1 file changed, 5 insertions(+)"].join("\n");
		const result = parseDiffStat(input);
		expect(result).toHaveLength(1);
		expect(result[0].filename).toBe("src/a.ts");
	});

	it("returns correct addition+deletion totals summing to the stat count", () => {
		const input = " src/mixed.ts | 10 ++++------\n";
		const result = parseDiffStat(input);
		expect(result[0].additions + result[0].deletions).toBe(10);
	});
});
