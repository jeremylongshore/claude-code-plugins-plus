import type { PRData, PRReviewComment } from "../github/client.js";

export interface ReviewSummary {
	total_comments: number;
	reviewers: string[];
	approval_status: "approved" | "changes_requested" | "pending" | "mixed";
	key_concerns: string[];
	file_discussions: Array<{
		file: string;
		comment_count: number;
		topics: string[];
	}>;
}

/**
 * Parse PR reviews and comments into a structured summary.
 * Returns undefined if there are no reviews or comments.
 */
export function parseReviews(pr: PRData): ReviewSummary | undefined {
	if (pr.reviews.length === 0 && pr.review_comments.length === 0) {
		return undefined;
	}

	const reviewers = [...new Set(pr.reviews.map((r) => r.author))];
	const approvalStatus = inferApprovalStatus(pr);
	const keyConcerns = extractKeyConcerns(pr);
	const fileDiscussions = groupByFile(pr.review_comments);

	return {
		total_comments: pr.review_comments.length,
		reviewers,
		approval_status: approvalStatus,
		key_concerns: keyConcerns.slice(0, 10),
		file_discussions: fileDiscussions.slice(0, 15),
	};
}

function inferApprovalStatus(pr: PRData): "approved" | "changes_requested" | "pending" | "mixed" {
	if (pr.reviews.length === 0) return "pending";

	// Get the latest review state per reviewer
	const latestByReviewer = new Map<string, string>();
	for (const review of pr.reviews) {
		if (review.state === "APPROVED" || review.state === "CHANGES_REQUESTED") {
			latestByReviewer.set(review.author, review.state);
		}
	}

	if (latestByReviewer.size === 0) return "pending";

	const states = [...latestByReviewer.values()];
	const hasApproval = states.includes("APPROVED");
	const hasChangesRequested = states.includes("CHANGES_REQUESTED");

	if (hasApproval && hasChangesRequested) return "mixed";
	if (hasChangesRequested) return "changes_requested";
	if (hasApproval) return "approved";
	return "pending";
}

function extractKeyConcerns(pr: PRData): string[] {
	const concerns: string[] = [];

	// Extract concerns from reviews with body text
	for (const review of pr.reviews) {
		if (review.body && review.body.trim().length > 10) {
			const firstLine = review.body.split("\n")[0].trim();
			if (firstLine.length > 5 && firstLine.length < 300) {
				const prefix = review.state === "CHANGES_REQUESTED" ? "[blocking] " : "";
				concerns.push(`${prefix}@${review.author}: ${firstLine}`);
			}
		}
	}

	// Extract concerns from inline comments (non-trivial ones)
	for (const comment of pr.review_comments) {
		if (comment.body.trim().length > 20) {
			const firstLine = comment.body.split("\n")[0].trim();
			if (firstLine.length > 10 && firstLine.length < 300) {
				concerns.push(`@${comment.author} on ${comment.path}: ${firstLine}`);
			}
		}
	}

	return concerns;
}

function groupByFile(
	comments: PRReviewComment[],
): Array<{ file: string; comment_count: number; topics: string[] }> {
	const groups = new Map<string, PRReviewComment[]>();

	for (const comment of comments) {
		const existing = groups.get(comment.path) ?? [];
		existing.push(comment);
		groups.set(comment.path, existing);
	}

	return [...groups.entries()]
		.map(([file, fileComments]) => ({
			file,
			comment_count: fileComments.length,
			topics: fileComments
				.map((c) => c.body.split("\n")[0].trim())
				.filter((t) => t.length > 5 && t.length < 200)
				.slice(0, 5),
		}))
		.sort((a, b) => b.comment_count - a.comment_count);
}
