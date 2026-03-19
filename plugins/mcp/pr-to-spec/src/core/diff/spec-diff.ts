import type { PromptSpec, SpecFragment } from "../schema/prompt-spec.js";

export interface FragmentDiff {
	fragment_type: string;
	status: "unchanged" | "changed" | "added" | "removed";
	previous_hash?: string;
	current_hash?: string;
}

export interface SpecDiff {
	changed: boolean;
	sections: SectionDiff[];
}

export interface SectionDiff {
	section: string;
	type: "added" | "removed" | "changed" | "unchanged";
	details?: string;
}

/**
 * Compare two prompt specs and produce a structured diff.
 * Useful for tracking how a PR spec evolves across revisions.
 */
export function diffSpecs(previous: PromptSpec, current: PromptSpec): SpecDiff {
	const sections: SectionDiff[] = [];

	// Title
	if (previous.title !== current.title) {
		sections.push({
			section: "title",
			type: "changed",
			details: `"${previous.title}" → "${current.title}"`,
		});
	}

	// Intent
	if (previous.intent.change_type !== current.intent.change_type) {
		sections.push({
			section: "change_type",
			type: "changed",
			details: `${previous.intent.change_type} → ${current.intent.change_type}`,
		});
	}

	// Files
	const prevFiles = new Set(previous.affected_files.map((f) => f.filename));
	const currFiles = new Set(current.affected_files.map((f) => f.filename));
	const addedFiles = [...currFiles].filter((f) => !prevFiles.has(f));
	const removedFiles = [...prevFiles].filter((f) => !currFiles.has(f));

	if (addedFiles.length > 0) {
		sections.push({
			section: "affected_files",
			type: "added",
			details: `+${addedFiles.length} files: ${addedFiles.join(", ")}`,
		});
	}
	if (removedFiles.length > 0) {
		sections.push({
			section: "affected_files",
			type: "removed",
			details: `-${removedFiles.length} files: ${removedFiles.join(", ")}`,
		});
	}

	// Stats
	if (
		previous.stats.files_changed !== current.stats.files_changed ||
		previous.stats.additions !== current.stats.additions ||
		previous.stats.deletions !== current.stats.deletions
	) {
		sections.push({
			section: "stats",
			type: "changed",
			details: `${previous.stats.files_changed}→${current.stats.files_changed} files, +${previous.stats.additions}→+${current.stats.additions}, -${previous.stats.deletions}→-${current.stats.deletions}`,
		});
	}

	// Risk flags
	const prevRisks = new Set(previous.risk_flags.map((r) => `${r.category}:${r.severity}`));
	const currRisks = new Set(current.risk_flags.map((r) => `${r.category}:${r.severity}`));
	const newRisks = [...currRisks].filter((r) => !prevRisks.has(r));
	const resolvedRisks = [...prevRisks].filter((r) => !currRisks.has(r));

	if (newRisks.length > 0) {
		sections.push({
			section: "risk_flags",
			type: "added",
			details: `New risks: ${newRisks.join(", ")}`,
		});
	}
	if (resolvedRisks.length > 0) {
		sections.push({
			section: "risk_flags",
			type: "removed",
			details: `Resolved: ${resolvedRisks.join(", ")}`,
		});
	}

	// Constraints
	const prevConstraints = new Set(previous.constraints);
	const currConstraints = new Set(current.constraints);
	const newConstraints = [...currConstraints].filter((c) => !prevConstraints.has(c));
	if (newConstraints.length > 0) {
		sections.push({
			section: "constraints",
			type: "added",
			details: `+${newConstraints.length} constraints`,
		});
	}

	// Review status
	if (previous.review_summary?.approval_status !== current.review_summary?.approval_status) {
		const prev = previous.review_summary?.approval_status ?? "none";
		const curr = current.review_summary?.approval_status ?? "none";
		sections.push({ section: "review_status", type: "changed", details: `${prev} → ${curr}` });
	}

	// Fragment-level diff — only when both specs carry fragments
	if (previous.fragments !== undefined && current.fragments !== undefined) {
		const fragmentDiffs = diffFragments(previous.fragments, current.fragments);
		const changed = fragmentDiffs.filter((d) => d.status !== "unchanged");
		if (changed.length > 0) {
			const summary = changed.map((d) => `${d.fragment_type}:${d.status}`).join(", ");
			sections.push({
				section: "fragments",
				type: "changed",
				details: summary,
			});
		}
	}

	return {
		changed: sections.length > 0,
		sections,
	};
}

/**
 * Compare two arrays of SpecFragments by fragment_type, returning a diff entry
 * per type that appears in either array.
 */
export function diffFragments(previous: SpecFragment[], current: SpecFragment[]): FragmentDiff[] {
	const prevByType = new Map(previous.map((f) => [f.fragment_type, f]));
	const currByType = new Map(current.map((f) => [f.fragment_type, f]));

	const allTypes = new Set([...prevByType.keys(), ...currByType.keys()]);
	const diffs: FragmentDiff[] = [];

	for (const type of allTypes) {
		const prev = prevByType.get(type);
		const curr = currByType.get(type);

		if (prev === undefined) {
			diffs.push({
				fragment_type: type,
				status: "added",
				current_hash: curr?.content_hash,
			});
		} else if (curr === undefined) {
			diffs.push({
				fragment_type: type,
				status: "removed",
				previous_hash: prev.content_hash,
			});
		} else if (prev.content_hash === curr.content_hash) {
			diffs.push({
				fragment_type: type,
				status: "unchanged",
				previous_hash: prev.content_hash,
				current_hash: curr.content_hash,
			});
		} else {
			diffs.push({
				fragment_type: type,
				status: "changed",
				previous_hash: prev.content_hash,
				current_hash: curr.content_hash,
			});
		}
	}

	return diffs;
}
