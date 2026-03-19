import type { PRData } from "../github/client.js";
import type { DiffSource } from "./types.js";

/** Adapt GitHub PRData to the DiffSource interface */
export function githubPRtoDiffSource(pr: PRData, repo: string): DiffSource {
	return {
		title: pr.title,
		body: pr.body ?? undefined,
		base_ref: pr.base_branch,
		head_ref: pr.head_branch,
		author: pr.author,
		files: pr.files.map((f) => ({
			filename: f.filename,
			status: normalizeStatus(f.status),
			additions: f.additions,
			deletions: f.deletions,
			patch: f.patch,
			previous_filename: f.previous_filename,
		})),
		labels: pr.labels,
		commits: pr.commits,
		source_type: "github_pr",
		pr_number: pr.number,
		repo,
		pr_url: pr.url,
	};
}

function normalizeStatus(status: string): "added" | "removed" | "modified" | "renamed" | "copied" {
	const map: Record<string, "added" | "removed" | "modified" | "renamed" | "copied"> = {
		added: "added",
		removed: "removed",
		modified: "modified",
		renamed: "renamed",
		copied: "copied",
		changed: "modified",
	};
	return map[status] ?? "modified";
}
