import { describe, expect, it } from "vitest";
import type { PRData } from "../src/core/github/client.js";
import { parseReviews } from "../src/core/parsing/review-parser.js";

function makePR(overrides: Partial<PRData> = {}): PRData {
	return {
		number: 1,
		title: "feat: test",
		body: "Test body",
		url: "https://github.com/owner/repo/pull/1",
		base_branch: "main",
		head_branch: "feat/test",
		author: "dev",
		state: "open",
		commits: 1,
		additions: 10,
		deletions: 5,
		changed_files: 1,
		labels: [],
		linked_issues: [],
		review_comments: [],
		reviews: [],
		files: [{ filename: "src/test.ts", status: "modified", additions: 10, deletions: 5 }],
		...overrides,
	};
}

describe("parseReviews", () => {
	it("returns undefined when no reviews or comments", () => {
		expect(parseReviews(makePR())).toBeUndefined();
	});

	it("detects approved status", () => {
		const result = parseReviews(
			makePR({
				reviews: [{ author: "reviewer1", state: "APPROVED", body: "LGTM" }],
			}),
		);
		expect(result?.approval_status).toBe("approved");
		expect(result?.reviewers).toEqual(["reviewer1"]);
	});

	it("detects changes_requested status", () => {
		const result = parseReviews(
			makePR({
				reviews: [
					{ author: "reviewer1", state: "CHANGES_REQUESTED", body: "Please fix the naming" },
				],
			}),
		);
		expect(result?.approval_status).toBe("changes_requested");
	});

	it("detects mixed status", () => {
		const result = parseReviews(
			makePR({
				reviews: [
					{ author: "reviewer1", state: "APPROVED", body: "" },
					{ author: "reviewer2", state: "CHANGES_REQUESTED", body: "Needs work" },
				],
			}),
		);
		expect(result?.approval_status).toBe("mixed");
	});

	it("extracts key concerns from review bodies", () => {
		const result = parseReviews(
			makePR({
				reviews: [
					{
						author: "reviewer1",
						state: "CHANGES_REQUESTED",
						body: "The error handling needs improvement in the retry logic",
					},
				],
			}),
		);
		expect(result?.key_concerns).toHaveLength(1);
		expect(result?.key_concerns[0]).toContain("error handling");
	});

	it("groups comments by file", () => {
		const result = parseReviews(
			makePR({
				review_comments: [
					{
						author: "reviewer1",
						body: "This function should be extracted",
						path: "src/main.ts",
						line: 10,
						created_at: "2025-01-01T00:00:00Z",
					},
					{
						author: "reviewer2",
						body: "Consider using a constant here",
						path: "src/main.ts",
						line: 25,
						created_at: "2025-01-01T00:00:00Z",
					},
					{
						author: "reviewer1",
						body: "Missing null check on this path",
						path: "src/utils.ts",
						line: 5,
						created_at: "2025-01-01T00:00:00Z",
					},
				],
			}),
		);
		expect(result?.total_comments).toBe(3);
		expect(result?.file_discussions).toHaveLength(2);
		expect(result?.file_discussions[0].file).toBe("src/main.ts");
		expect(result?.file_discussions[0].comment_count).toBe(2);
	});

	it("counts total comments correctly", () => {
		const result = parseReviews(
			makePR({
				review_comments: [
					{
						author: "a",
						body: "Comment one about something",
						path: "a.ts",
						line: 1,
						created_at: "2025-01-01T00:00:00Z",
					},
				],
			}),
		);
		expect(result?.total_comments).toBe(1);
	});
});
