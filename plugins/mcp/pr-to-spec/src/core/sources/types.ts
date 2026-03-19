/** A single changed file from any diff source */
export interface DiffFile {
	filename: string;
	status: "added" | "removed" | "modified" | "renamed" | "copied";
	additions: number;
	deletions: number;
	patch?: string;
	previous_filename?: string;
}

/** A diff from any source (GitHub PR, local git, staged changes) */
export interface DiffSource {
	/** Human-readable title, e.g. PR title or branch name */
	title: string;
	/** Description or PR body */
	body?: string;
	/** The base ref (branch or commit SHA) */
	base_ref: string;
	/** The head ref (branch or commit SHA) */
	head_ref: string;
	/** Author login or git user */
	author: string;
	/** Files changed */
	files: DiffFile[];
	/** Labels (GitHub PRs) */
	labels?: string[];
	/** Total commits in the diff */
	commits?: number;
	/** Source type */
	source_type: "github_pr" | "local_branch" | "local_staged" | "local_commits";
	/** GitHub PR number (if source_type is github_pr) */
	pr_number?: number;
	/** GitHub repo (if source_type is github_pr) */
	repo?: string;
	/** GitHub PR URL (if source_type is github_pr) */
	pr_url?: string;
}
