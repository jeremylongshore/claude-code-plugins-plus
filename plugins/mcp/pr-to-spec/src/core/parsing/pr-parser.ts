import type { PRData } from "../github/client.js";
import { classifyRisks } from "../risk/classifier.js";
import {
	type FileChange,
	type PromptSpec,
	type SpecFragment,
	computeContentHash,
	computeFragmentId,
} from "../schema/prompt-spec.js";
import { githubPRtoDiffSource } from "../sources/github.js";
import type { DiffSource } from "../sources/types.js";
import { detectMonorepo } from "./monorepo-detector.js";
import { parseReviews } from "./review-parser.js";
import { analyzeSemanticDiff } from "./semantic-diff.js";

/**
 * Deterministic spec generation from any DiffSource.
 * No LLM required — uses heuristics and templates.
 */
export function generateSpec(source: DiffSource, repo?: string): PromptSpec {
	const changeType = inferChangeType(source);
	const likelyGoal = inferGoal(source);
	const scope = inferScope(source);
	const constraints = inferConstraints(source);
	const acceptanceCriteria = inferAcceptanceCriteria(source);
	const verification = inferVerification(source);
	const risks = classifyRisks(source.files);
	const semanticChanges = analyzeSemanticDiff(source.files);
	const monorepo = detectMonorepo(source.files);
	const openQuestions = inferOpenQuestions(source, risks);

	const effectiveRepo = repo ?? source.repo ?? "local";
	const prompt = buildGenerationPrompt(source, effectiveRepo, likelyGoal, scope, constraints);
	const decisionPrompt = buildDecisionPrompt(source, effectiveRepo, risks, constraints, changeType);

	const totalAdditions = source.files.reduce((sum, f) => sum + f.additions, 0);
	const totalDeletions = source.files.reduce((sum, f) => sum + f.deletions, 0);

	const spec: PromptSpec = {
		version: 1,
		generated_at: new Date().toISOString(),
		source: {
			repo: effectiveRepo,
			pr_number: source.pr_number,
			pr_url: source.pr_url,
			base_branch: source.base_ref,
			head_branch: source.head_ref,
			author: source.author,
		},
		title: source.title,
		summary: buildSummary(source, changeType, totalAdditions, totalDeletions),
		intent: {
			likely_goal: likelyGoal,
			change_type: changeType,
		},
		scope,
		affected_files: source.files.map(
			(f): FileChange => ({
				filename: f.filename,
				status: f.status,
				additions: f.additions,
				deletions: f.deletions,
				patch: f.patch,
			}),
		),
		constraints,
		acceptance_criteria: acceptanceCriteria,
		verification,
		risk_flags: risks,
		semantic_changes: semanticChanges.length > 0 ? semanticChanges : undefined,
		review_summary: undefined,
		monorepo,
		open_questions: openQuestions,
		generation_prompt: prompt,
		decision_prompt: decisionPrompt,
		stats: {
			files_changed: source.files.length,
			additions: totalAdditions,
			deletions: totalDeletions,
			commits: source.commits ?? 0,
		},
	};

	return { ...spec, fragments: decomposeIntoFragments(spec) };
}

/**
 * Backwards-compatible wrapper: generate spec from GitHub PRData.
 */
export function generateSpecFromPR(pr: PRData, repo: string): PromptSpec {
	const source = githubPRtoDiffSource(pr, repo);
	const spec = generateSpec(source, repo);
	// Attach review summary (GitHub-specific)
	const reviewSummary = parseReviews(pr);
	return { ...spec, review_summary: reviewSummary };
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

// Keep normalizeStatus exported for tests that may import it
export { normalizeStatus };

function inferChangeType(
	source: DiffSource,
): "feature" | "bugfix" | "refactor" | "docs" | "test" | "chore" | "config" | "mixed" {
	const title = source.title.toLowerCase();
	const branch = source.head_ref.toLowerCase();

	if (/\b(fix|bug|patch|hotfix|issue)\b/.test(title) || branch.startsWith("fix/")) return "bugfix";
	if (/\b(feat|feature|add|implement)\b/.test(title) || branch.startsWith("feat/"))
		return "feature";
	if (/\b(refactor|cleanup|clean up|reorganize)\b/.test(title) || branch.startsWith("refactor/"))
		return "refactor";
	if (/\b(doc|docs|readme|documentation)\b/.test(title) || branch.startsWith("docs/"))
		return "docs";
	if (/\b(test|spec|coverage)\b/.test(title) || branch.startsWith("test/")) return "test";
	if (/\b(chore|ci|build|deps|bump)\b/.test(title) || branch.startsWith("chore/")) return "chore";
	if (/\b(config|setup|configure)\b/.test(title)) return "config";

	// Check file patterns
	const exts = source.files.map((f) => f.filename.split(".").pop() ?? "");
	const allDocs = exts.every((e) => ["md", "txt", "rst", "adoc"].includes(e));
	if (allDocs) return "docs";

	const allTests = source.files.every((f) => /\b(test|spec|__tests__)\b/i.test(f.filename));
	if (allTests) return "test";

	return "mixed";
}

function inferGoal(source: DiffSource): string {
	// Use body first line or title as the goal basis
	if (source.body) {
		const firstParagraph = source.body.split("\n\n")[0].trim();
		if (firstParagraph.length > 10 && firstParagraph.length < 500) {
			return firstParagraph;
		}
	}
	return `${source.title} (inferred from title)`;
}

function inferScope(source: DiffSource): { include: string[]; exclude: string[] } {
	// Group files by top-level directory paths
	const dirs = new Set<string>();
	for (const f of source.files) {
		const parts = f.filename.split("/");
		if (parts.length > 2) {
			// Deep path: use top two directory segments as glob
			dirs.add(`${parts[0]}/${parts[1]}/**`);
		} else if (parts.length === 2) {
			// Single directory + file: use the exact path
			dirs.add(f.filename);
		} else {
			// Root-level file
			dirs.add(f.filename);
		}
	}

	return {
		include: [...dirs].slice(0, 15),
		exclude: ["Unrelated modules not touched by this change"],
	};
}

function inferConstraints(source: DiffSource): string[] {
	const constraints: string[] = [];

	if (source.files.some((f) => /test/i.test(f.filename))) {
		constraints.push("Existing tests must continue to pass");
	}

	if (
		source.files.some(
			(f) =>
				/\b(migration|migrate)\b/i.test(f.filename) ||
				/\.sql$/.test(f.filename) ||
				(/\bschema\b/i.test(f.filename) &&
					/\b(db|database|prisma|drizzle|knex|sequelize|typeorm|sql|alembic)\b/i.test(f.filename)),
		)
	) {
		constraints.push("Database migrations must be backwards-compatible");
	}

	if (source.files.some((f) => /api|route|endpoint/i.test(f.filename))) {
		constraints.push("API contracts must remain stable for existing clients");
	}

	if (source.labels?.includes("breaking-change")) {
		constraints.push("This is a breaking change — requires version bump and migration guide");
	}

	constraints.push("Preserve existing behavior for untouched code paths");
	return constraints;
}

function inferAcceptanceCriteria(source: DiffSource): string[] {
	const criteria: string[] = [];

	criteria.push(`Changes apply cleanly to ${source.base_ref}`);
	criteria.push("All existing tests pass");

	if (source.files.some((f) => f.status === "added")) {
		criteria.push("New files are properly integrated with existing module structure");
	}

	if (source.files.some((f) => /test/i.test(f.filename))) {
		criteria.push("New/modified tests cover the changed functionality");
	}

	criteria.push("No regressions in affected modules");
	return criteria;
}

function inferVerification(source: DiffSource): {
	tests_required: string[];
	manual_checks: string[];
} {
	const tests: string[] = [];
	const manual: string[] = [];

	if (source.files.some((f) => /test/i.test(f.filename))) {
		tests.push("unit");
	}

	if (source.files.some((f) => /integration|e2e/i.test(f.filename))) {
		tests.push("integration");
	}

	if (tests.length === 0) {
		tests.push("unit");
		manual.push("Verify no test coverage gaps introduced");
	}

	if (source.files.some((f) => /api|route/i.test(f.filename))) {
		manual.push("Verify API endpoint behavior manually");
	}

	if (source.files.some((f) => /ui|component|page/i.test(f.filename))) {
		manual.push("Visual check of affected UI components");
	}

	return { tests_required: tests, manual_checks: manual };
}

function inferOpenQuestions(
	source: DiffSource,
	risks: Array<{ category: string; severity: string }>,
): string[] {
	const questions: string[] = [];

	if (!source.body || source.body.trim().length < 20) {
		questions.push("Description is sparse — clarify the motivation for this change");
	}

	if (source.files.length > 20) {
		questions.push("Large changeset — could this be split into smaller changes?");
	}

	if (risks.some((r) => r.severity === "high")) {
		questions.push("High-risk changes detected — has this been reviewed by a domain expert?");
	}

	if (source.files.some((f) => f.status === "removed")) {
		questions.push("Files were deleted — confirm no other modules depend on them");
	}

	return questions;
}

function buildSummary(
	source: DiffSource,
	changeType: string,
	additions: number,
	deletions: number,
): string {
	const fileWord = source.files.length === 1 ? "file" : "files";
	return `${capitalize(changeType)} by ${source.author}: "${source.title}" — ${source.files.length} ${fileWord} changed (+${additions}/-${deletions})`;
}

function buildGenerationPrompt(
	source: DiffSource,
	repo: string,
	goal: string,
	scope: { include: string[] },
	constraints: string[],
): string {
	const files = source.files.map((f) => `  - ${f.filename} (${f.status})`).join("\n");
	const ref = source.pr_url ? `Original PR: ${source.pr_url}` : `Branch: ${source.head_ref}`;

	return `Re-implement the following change for the ${repo} repository.

## Goal
${goal}

## Branch
Apply changes to: ${source.base_ref}
Original branch: ${source.head_ref}

## Affected Files
${files}

## Scope
Focus on: ${scope.include.join(", ")}

## Constraints
${constraints.map((c) => `- ${c}`).join("\n")}

## Reference
${ref}
Author: ${source.author}

Implement this change following the repository's existing patterns and conventions.
Ensure all tests pass after making the changes.`;
}

function buildDecisionPrompt(
	source: DiffSource,
	repo: string,
	risks: Array<{ category: string; severity: string; description: string }>,
	constraints: string[],
	changeType: string,
): string {
	const riskSection =
		risks.length > 0
			? risks
					.map((r) => `- [${r.severity.toUpperCase()}] ${r.category}: ${r.description}`)
					.join("\n")
			: "No risk flags detected.";

	const constraintSection = constraints.map((c) => `- ${c}`).join("\n");
	const totalAdditions = source.files.reduce((sum, f) => sum + f.additions, 0);
	const totalDeletions = source.files.reduce((sum, f) => sum + f.deletions, 0);
	const prRef = source.pr_number ? `PR #${source.pr_number} in ` : "Change in ";

	return `You are reviewing ${prRef}${repo}.

## Decision Required
Should this change be approved, request changes, or need more information?

## Context
- **Title:** ${source.title}
- **Author:** ${source.author}
- **Type:** ${changeType}
- **Files changed:** ${source.files.length} (+${totalAdditions}/-${totalDeletions})
- **Branch:** ${source.head_ref} → ${source.base_ref}

## Risk Assessment
${riskSection}

## Constraints to Verify
${constraintSection}

## Questions to Answer
1. Does this change align with the repository's architecture and conventions?
2. Are there any security implications not covered by the risk flags?
3. Is the scope appropriate, or should this be split into smaller changes?
4. Are edge cases and error handling adequately addressed?
5. Will this change be maintainable long-term?

## Response Format
Respond with one of:
- **APPROVE** — Change is safe and well-implemented
- **REQUEST_CHANGES** — Specific issues must be addressed (list them)
- **NEEDS_INFO** — Cannot decide without additional context (list questions)

Include a brief rationale (2-3 sentences) for your decision.`;
}

function capitalize(s: string): string {
	return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Decompose a PromptSpec into independently hashable SpecFragments.
 * Each fragment captures a logical section of the spec, with DAG edges
 * (parent_fragment_ids) expressing upstream dependencies.
 */
export function decomposeIntoFragments(spec: PromptSpec): SpecFragment[] {
	const fragments: SpecFragment[] = [];

	function makeFragment(
		fragment_type: SpecFragment["fragment_type"],
		content: unknown,
		parent_fragment_ids: string[],
	): SpecFragment {
		const content_hash = computeContentHash(content);
		return {
			fragment_id: computeFragmentId(content_hash),
			fragment_type,
			content,
			content_hash,
			parent_fragment_ids,
		};
	}

	// intent — no parents (root fragment)
	const intentFragment = makeFragment(
		"intent",
		{ likely_goal: spec.intent.likely_goal, change_type: spec.intent.change_type },
		[],
	);
	fragments.push(intentFragment);

	// scope — parent: intent
	const scopeFragment = makeFragment("scope", spec.scope, [intentFragment.fragment_id]);
	fragments.push(scopeFragment);

	// files — parent: scope
	const filesContent = spec.affected_files.map((f) => ({ filename: f.filename, status: f.status }));
	const filesFragment = makeFragment("files", filesContent, [scopeFragment.fragment_id]);
	fragments.push(filesFragment);

	// constraints — parent: intent
	const constraintsFragment = makeFragment("constraints", spec.constraints, [
		intentFragment.fragment_id,
	]);
	fragments.push(constraintsFragment);

	// verification — parent: intent
	const verificationFragment = makeFragment("verification", spec.verification, [
		intentFragment.fragment_id,
	]);
	fragments.push(verificationFragment);

	// risks — parent: files
	const risksFragment = makeFragment("risks", spec.risk_flags, [filesFragment.fragment_id]);
	fragments.push(risksFragment);

	// semantics — only if spec.semantic_changes exists, parent: files
	if (spec.semantic_changes !== undefined) {
		const semanticsFragment = makeFragment("semantics", spec.semantic_changes, [
			filesFragment.fragment_id,
		]);
		fragments.push(semanticsFragment);
	}

	return fragments;
}

/**
 * Build a compact spec without patch data (for YAML output).
 */
export function compactSpec(spec: PromptSpec): PromptSpec {
	return {
		...spec,
		affected_files: spec.affected_files.map(({ patch: _patch, ...rest }) => rest as FileChange),
	};
}
