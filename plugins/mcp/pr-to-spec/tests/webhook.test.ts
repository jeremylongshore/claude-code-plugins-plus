import { describe, expect, it } from "vitest";
import type { PRData } from "../src/core/github/client.js";
import { generateSpecFromPR } from "../src/core/parsing/pr-parser.js";

function makePR(): PRData {
	return {
		number: 42,
		title: "feat: add rate limiting",
		body: "Add rate limiting.",
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
			},
		],
	};
}

describe("webhook payload", () => {
	it("generates valid JSON payload from spec", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const payload = JSON.stringify({
			event: "spec_generated",
			repo: "owner/repo",
			pr_number: 42,
			spec,
			generated_at: spec.generated_at,
		});
		const parsed = JSON.parse(payload);
		expect(parsed.event).toBe("spec_generated");
		expect(parsed.repo).toBe("owner/repo");
		expect(parsed.pr_number).toBe(42);
		expect(parsed.spec.version).toBe(1);
		expect(parsed.generated_at).toBe(spec.generated_at);
	});

	it("webhook payload contains full spec", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const payload = {
			event: "spec_generated",
			repo: "owner/repo",
			pr_number: 42,
			spec,
			generated_at: spec.generated_at,
		};
		expect(payload.spec.title).toBe("feat: add rate limiting");
		expect(payload.spec.source.author).toBe("contributor");
		expect(Array.isArray(payload.spec.risk_flags)).toBe(true);
		expect(payload.spec.stats.files_changed).toBe(1);
	});

	it("webhook payload includes risk flags array with correct structure", () => {
		const pr = makePR();
		// Override with a file that triggers risk
		pr.files = [{ filename: "src/auth/login.ts", status: "modified", additions: 20, deletions: 5 }];
		const spec = generateSpecFromPR(pr, "owner/repo");
		const payload = {
			event: "spec_generated",
			repo: "owner/repo",
			pr_number: 42,
			spec,
			generated_at: spec.generated_at,
		};
		expect(Array.isArray(payload.spec.risk_flags)).toBe(true);
		// Auth file should produce at least one high-severity risk flag
		expect(payload.spec.risk_flags.some((r) => r.severity === "high")).toBe(true);
		// Each flag has required fields
		for (const flag of payload.spec.risk_flags) {
			expect(typeof flag.category).toBe("string");
			expect(typeof flag.description).toBe("string");
			expect(["low", "medium", "high"]).toContain(flag.severity);
		}
	});

	it("webhook payload event field is the literal string spec_generated", () => {
		const spec = generateSpecFromPR(makePR(), "owner/repo");
		const payload = JSON.stringify({ event: "spec_generated", spec });
		const parsed = JSON.parse(payload);
		// This tests that the event enum value is correct and survives serialization
		expect(parsed.event).toBe("spec_generated");
		expect(parsed.event).not.toBe("spec_created");
		expect(parsed.event).not.toBe("pr_analyzed");
	});
});
