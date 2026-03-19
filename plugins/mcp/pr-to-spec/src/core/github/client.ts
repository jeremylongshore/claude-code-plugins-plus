import { Octokit } from "@octokit/rest";

export interface PRReviewComment {
	author: string;
	body: string;
	path: string;
	line: number | null;
	created_at: string;
}

export interface PRReview {
	author: string;
	state: string;
	body: string;
}

export interface PRData {
	number: number;
	title: string;
	body: string | null;
	url: string;
	base_branch: string;
	head_branch: string;
	author: string;
	state: string;
	commits: number;
	additions: number;
	deletions: number;
	changed_files: number;
	files: PRFile[];
	labels: string[];
	linked_issues: string[];
	review_comments: PRReviewComment[];
	reviews: PRReview[];
}

export interface PRFile {
	filename: string;
	status: string;
	additions: number;
	deletions: number;
	patch?: string;
	previous_filename?: string;
}

export function createClient(token: string): Octokit {
	return new Octokit({ auth: token });
}

export async function fetchPR(
	octokit: Octokit,
	owner: string,
	repo: string,
	prNumber: number,
): Promise<PRData> {
	let prResponse: Awaited<ReturnType<typeof octokit.pulls.get>>;
	let filesResponse: Awaited<ReturnType<typeof octokit.pulls.listFiles>>;
	let commentsResponse: Awaited<ReturnType<typeof octokit.pulls.listReviewComments>>;
	let reviewsResponse: Awaited<ReturnType<typeof octokit.pulls.listReviews>>;

	try {
		[prResponse, filesResponse, commentsResponse, reviewsResponse] = await Promise.all([
			octokit.pulls.get({ owner, repo, pull_number: prNumber }),
			octokit.pulls.listFiles({ owner, repo, pull_number: prNumber, per_page: 300 }),
			octokit.pulls.listReviewComments({ owner, repo, pull_number: prNumber, per_page: 100 }),
			octokit.pulls.listReviews({ owner, repo, pull_number: prNumber, per_page: 50 }),
		]);
	} catch (err: unknown) {
		throw mapGitHubError(err, owner, repo, prNumber);
	}

	const pr = prResponse.data;

	// Warn if file list may be truncated
	if (filesResponse.data.length >= 300) {
		console.warn(
			`Warning: PR #${prNumber} has 300+ files; results may be incomplete. GitHub API returns at most 300 files per page.`,
		);
	}

	// Extract linked issues from PR body
	const linkedIssues = extractLinkedIssues(pr.body ?? "", owner, repo);

	return {
		number: pr.number,
		title: pr.title,
		body: pr.body,
		url: pr.html_url,
		base_branch: pr.base.ref,
		head_branch: pr.head.ref,
		author: pr.user?.login ?? "unknown",
		state: pr.state,
		commits: pr.commits,
		additions: pr.additions,
		deletions: pr.deletions,
		changed_files: pr.changed_files,
		labels: pr.labels.map((l) => l.name),
		linked_issues: linkedIssues,
		files: filesResponse.data.map((f) => ({
			filename: f.filename,
			status: f.status,
			additions: f.additions,
			deletions: f.deletions,
			patch: f.patch,
			previous_filename: f.previous_filename,
		})),
		review_comments: commentsResponse.data.map((c) => ({
			author: c.user?.login ?? "unknown",
			body: c.body,
			path: c.path,
			line: c.line ?? null,
			created_at: c.created_at,
		})),
		reviews: reviewsResponse.data
			.filter((r) => r.state !== "PENDING")
			.map((r) => ({
				author: r.user?.login ?? "unknown",
				state: r.state,
				body: r.body ?? "",
			})),
	};
}

function mapGitHubError(err: unknown, owner: string, repo: string, prNumber: number): Error {
	if (err && typeof err === "object" && "status" in err) {
		const status = (err as { status: number }).status;
		const headers = (err as { response?: { headers?: Record<string, string> } }).response?.headers;

		switch (status) {
			case 401:
				return new Error(
					"GitHub token is invalid or expired. Check your GITHUB_TOKEN or --token value.",
				);
			case 403: {
				const remaining = headers?.["x-ratelimit-remaining"];
				if (remaining === "0") {
					const resetAt = headers?.["x-ratelimit-reset"];
					const resetTime = resetAt ? new Date(Number(resetAt) * 1000).toISOString() : "soon";
					return new Error(
						`GitHub API rate limit exceeded. Resets at ${resetTime}. Use a token with higher limits.`,
					);
				}
				return new Error(
					`Access denied to ${owner}/${repo}. Check that your token has the required permissions.`,
				);
			}
			case 404:
				return new Error(
					`PR #${prNumber} not found in ${owner}/${repo}. Check the repo name and PR number, or verify you have access.`,
				);
			case 422:
				return new Error(
					`Invalid request for PR #${prNumber} in ${owner}/${repo}. Check that the repo format is correct (owner/name) and the PR number is valid.`,
				);
		}
	}
	if (err instanceof Error) return err;
	return new Error(String(err));
}

function extractLinkedIssues(body: string, owner: string, repo: string): string[] {
	const issues: string[] = [];
	// Match "Fixes #123", "Closes #456", "Resolves #789"
	const patterns = [
		/(?:fix(?:es)?|close(?:s)?|resolve(?:s)?)\s+#(\d+)/gi,
		/(?:fix(?:es)?|close(?:s)?|resolve(?:s)?)\s+https:\/\/github\.com\/[\w-]+\/[\w-]+\/issues\/(\d+)/gi,
	];
	for (const pattern of patterns) {
		for (const match of body.matchAll(pattern)) {
			const num = match[1];
			issues.push(`https://github.com/${owner}/${repo}/issues/${num}`);
		}
	}
	return [...new Set(issues)];
}
