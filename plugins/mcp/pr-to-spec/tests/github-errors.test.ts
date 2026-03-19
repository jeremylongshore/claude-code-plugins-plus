import { describe, expect, it, vi } from "vitest";
import { type createClient, fetchPR } from "../src/core/github/client.js";

// ---------------------------------------------------------------------------
// Mock Octokit to simulate API error responses
// ---------------------------------------------------------------------------

function makeOctokitError(status: number, headers: Record<string, string> = {}): never {
	const err = new Error("HttpError") as Error & {
		status: number;
		response: { headers: Record<string, string> };
	};
	err.status = status;
	err.response = { headers };
	throw err;
}

function mockOctokit(status: number, headers: Record<string, string> = {}) {
	return {
		pulls: {
			get: () => makeOctokitError(status, headers),
			listFiles: () => makeOctokitError(status, headers),
			listReviewComments: () => makeOctokitError(status, headers),
			listReviews: () => makeOctokitError(status, headers),
		},
	} as unknown as ReturnType<typeof createClient>;
}

// ---------------------------------------------------------------------------
// API error mapping
// ---------------------------------------------------------------------------

describe("GitHub API error handling", () => {
	it("maps 401 to invalid token message", async () => {
		const octokit = mockOctokit(401);
		await expect(fetchPR(octokit, "owner", "repo", 42)).rejects.toThrow(/invalid or expired/i);
	});

	it("maps 403 to access denied message", async () => {
		const octokit = mockOctokit(403);
		await expect(fetchPR(octokit, "owner", "repo", 42)).rejects.toThrow(/access denied/i);
	});

	it("maps 403 with exhausted rate limit to rate limit message", async () => {
		const resetTime = String(Math.floor(Date.now() / 1000) + 3600);
		const octokit = mockOctokit(403, {
			"x-ratelimit-remaining": "0",
			"x-ratelimit-reset": resetTime,
		});
		await expect(fetchPR(octokit, "owner", "repo", 42)).rejects.toThrow(/rate limit exceeded/i);
	});

	it("maps 404 to PR not found message with context", async () => {
		const octokit = mockOctokit(404);
		await expect(fetchPR(octokit, "owner", "repo", 42)).rejects.toThrow(
			/PR #42 not found in owner\/repo/,
		);
	});

	it("maps 422 to invalid request message", async () => {
		const octokit = mockOctokit(422);
		await expect(fetchPR(octokit, "owner", "repo", 42)).rejects.toThrow(/invalid request/i);
	});

	it("passes through generic errors", async () => {
		const octokit = {
			pulls: {
				get: () => {
					throw new Error("Network failure");
				},
				listFiles: () => {
					throw new Error("Network failure");
				},
				listReviewComments: () => {
					throw new Error("Network failure");
				},
				listReviews: () => {
					throw new Error("Network failure");
				},
			},
		} as unknown as ReturnType<typeof createClient>;
		await expect(fetchPR(octokit, "owner", "repo", 42)).rejects.toThrow("Network failure");
	});
});

// ---------------------------------------------------------------------------
// Large PR file truncation warning
// ---------------------------------------------------------------------------

describe("Large PR file truncation", () => {
	it("warns when file list reaches 300", async () => {
		const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

		const files300 = Array.from({ length: 300 }, (_, i) => ({
			filename: `src/file${i}.ts`,
			status: "modified",
			additions: 1,
			deletions: 0,
			patch: "+// change",
		}));

		const octokit = {
			pulls: {
				get: () =>
					Promise.resolve({
						data: {
							number: 1,
							title: "big PR",
							body: "",
							html_url: "https://github.com/o/r/pull/1",
							base: { ref: "main" },
							head: { ref: "feat" },
							user: { login: "dev" },
							state: "open",
							commits: 1,
							additions: 300,
							deletions: 0,
							changed_files: 300,
							labels: [],
						},
					}),
				listFiles: () => Promise.resolve({ data: files300 }),
				listReviewComments: () => Promise.resolve({ data: [] }),
				listReviews: () => Promise.resolve({ data: [] }),
			},
		} as unknown as ReturnType<typeof createClient>;

		await fetchPR(octokit, "owner", "repo", 1);

		expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining("300+ files"));
		warnSpy.mockRestore();
	});

	it("does not warn for small PRs", async () => {
		const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

		const octokit = {
			pulls: {
				get: () =>
					Promise.resolve({
						data: {
							number: 1,
							title: "small PR",
							body: "",
							html_url: "https://github.com/o/r/pull/1",
							base: { ref: "main" },
							head: { ref: "feat" },
							user: { login: "dev" },
							state: "open",
							commits: 1,
							additions: 10,
							deletions: 0,
							changed_files: 2,
							labels: [],
						},
					}),
				listFiles: () =>
					Promise.resolve({
						data: [
							{ filename: "a.ts", status: "modified", additions: 5, deletions: 0 },
							{ filename: "b.ts", status: "modified", additions: 5, deletions: 0 },
						],
					}),
				listReviewComments: () => Promise.resolve({ data: [] }),
				listReviews: () => Promise.resolve({ data: [] }),
			},
		} as unknown as ReturnType<typeof createClient>;

		await fetchPR(octokit, "owner", "repo", 1);

		expect(warnSpy).not.toHaveBeenCalled();
		warnSpy.mockRestore();
	});
});
