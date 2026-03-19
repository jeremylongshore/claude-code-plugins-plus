import { execSync } from "node:child_process";
import type { DiffFile, DiffSource } from "./types.js";

export interface LocalDiffOptions {
	/** Base branch/ref to diff against. Defaults to "main" */
	base?: string;
	/** Number of recent commits to include (e.g. HEAD~3) */
	commits?: number;
	/** Only include staged changes */
	staged?: boolean;
	/** Working directory */
	cwd?: string;
}

/** Parse git diff --stat output into file list */
export function parseDiffStat(
	output: string,
): Pick<DiffFile, "filename" | "additions" | "deletions">[] {
	const files: Pick<DiffFile, "filename" | "additions" | "deletions">[] = [];
	for (const line of output.split("\n")) {
		const match = line.match(/^\s*(.+?)\s+\|\s+(\d+)\s+([\+\-]+)/);
		if (match) {
			const plusses = (match[3].match(/\+/g) ?? []).length;
			const minuses = (match[3].match(/-/g) ?? []).length;
			// Scale by the number: e.g. "| 5 +++++" means 5 changes
			const total = Number.parseInt(match[2]);
			const adds = Math.round((plusses / (plusses + minuses || 1)) * total);
			const dels = total - adds;
			files.push({ filename: match[1].trim(), additions: adds, deletions: dels });
		}
	}
	return files;
}

/** Parse git diff --name-status into file status entries */
export function parseNameStatus(
	output: string,
): Pick<DiffFile, "filename" | "status" | "previous_filename">[] {
	const files: Pick<DiffFile, "filename" | "status" | "previous_filename">[] = [];
	for (const line of output.split("\n")) {
		if (!line.trim()) continue;
		const parts = line.split("\t");
		const statusChar = parts[0]?.[0] ?? "M";
		const statusMap: Record<string, DiffFile["status"]> = {
			A: "added",
			D: "removed",
			M: "modified",
			R: "renamed",
			C: "copied",
		};
		const status = statusMap[statusChar] ?? "modified";
		if ((statusChar === "R" || statusChar === "C") && parts[2]) {
			files.push({ filename: parts[2], status, previous_filename: parts[1] });
		} else {
			files.push({ filename: parts[1] ?? parts[0], status });
		}
	}
	return files;
}

/** Get the current branch name */
function getCurrentBranch(cwd: string): string {
	try {
		return execSync("git rev-parse --abbrev-ref HEAD", { cwd, encoding: "utf8" }).trim();
	} catch {
		return "HEAD";
	}
}

/** Get current git user */
function getGitUser(cwd: string): string {
	try {
		return execSync("git config user.name", { cwd, encoding: "utf8" }).trim();
	} catch {
		return "local";
	}
}

/** Get number of commits between base and HEAD */
function countCommits(base: string, cwd: string): number {
	try {
		const out = execSync(`git rev-list --count ${base}..HEAD`, { cwd, encoding: "utf8" }).trim();
		return Number.parseInt(out) || 0;
	} catch {
		return 0;
	}
}

/** Get patch for a file */
function getPatch(diffArgs: string, filename: string, cwd: string): string | undefined {
	try {
		const patch = execSync(`git diff ${diffArgs} -- "${filename}"`, { cwd, encoding: "utf8" });
		return patch.trim() || undefined;
	} catch {
		return undefined;
	}
}

export function buildLocalDiffSource(opts: LocalDiffOptions = {}): DiffSource {
	const cwd = opts.cwd ?? process.cwd();
	const author = getGitUser(cwd);
	const currentBranch = getCurrentBranch(cwd);

	let diffArgs: string;
	let baseRef: string;
	let sourceType: DiffSource["source_type"];
	let title: string;

	if (opts.staged) {
		diffArgs = "--cached";
		baseRef = "HEAD";
		sourceType = "local_staged";
		title = "Staged changes";
	} else if (opts.commits) {
		diffArgs = `HEAD~${opts.commits}`;
		baseRef = `HEAD~${opts.commits}`;
		sourceType = "local_commits";
		title = `Last ${opts.commits} commit(s) on ${currentBranch}`;
	} else {
		baseRef = opts.base ?? "main";
		diffArgs = `${baseRef}...HEAD`;
		sourceType = "local_branch";
		title = `Branch ${currentBranch} vs ${baseRef}`;
	}

	// Get name-status for file statuses
	let nameStatus: string;
	let diffStat: string;
	try {
		nameStatus = execSync(`git diff --name-status ${diffArgs}`, { cwd, encoding: "utf8" });
	} catch (err) {
		throw mapGitError(err, `git diff --name-status ${diffArgs}`, cwd);
	}
	const statuses = parseNameStatus(nameStatus);

	// Get diff --stat for additions/deletions counts
	try {
		diffStat = execSync(`git diff --stat ${diffArgs}`, { cwd, encoding: "utf8" });
	} catch (err) {
		throw mapGitError(err, `git diff --stat ${diffArgs}`, cwd);
	}
	const stats = parseDiffStat(diffStat);

	// Merge the two
	const files: DiffFile[] = statuses.map((s) => {
		const stat = stats.find((st) => st.filename === s.filename) ?? {
			additions: 0,
			deletions: 0,
		};
		const patch = getPatch(diffArgs, s.filename, cwd);
		return {
			filename: s.filename,
			status: s.status,
			additions: stat.additions,
			deletions: stat.deletions,
			patch,
			previous_filename: s.previous_filename,
		};
	});

	const commits = opts.staged ? undefined : countCommits(baseRef, cwd);

	return {
		title,
		base_ref: baseRef,
		head_ref: currentBranch,
		author,
		files,
		commits,
		source_type: sourceType,
	};
}

function mapGitError(err: unknown, command: string, cwd: string): Error {
	const stderr =
		err && typeof err === "object" && "stderr" in err
			? String((err as { stderr: unknown }).stderr)
			: "";
	const message = err instanceof Error ? err.message : String(err);

	if (/not a git repository/i.test(stderr) || /not a git repository/i.test(message)) {
		return new Error(
			`Not a git repository: ${cwd}\nRun this command from inside a git repo, or use --repo to analyze a GitHub PR instead.`,
		);
	}

	if (/unknown revision/i.test(stderr) || /unknown revision/i.test(message)) {
		const refMatch =
			stderr.match(/unknown revision.*?'([^']+)'/i) ??
			message.match(/unknown revision.*?'([^']+)'/i);
		const ref = refMatch?.[1] ?? "the specified ref";
		return new Error(`Branch or ref '${ref}' not found. Check that it exists with: git branch -a`);
	}

	return new Error(`Git command failed: ${command}\n${stderr || message}`);
}
