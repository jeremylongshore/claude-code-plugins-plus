import { createHash } from "node:crypto";
import { z } from "zod";

export const FileChangeSchema = z.object({
	filename: z.string(),
	status: z.enum(["added", "removed", "modified", "renamed", "copied"]),
	additions: z.number(),
	deletions: z.number(),
	patch: z.string().optional(),
});

export const SpecFragmentSchema = z.object({
	fragment_id: z.string(), // content hash (SHA-256 hex, first 12 chars)
	fragment_type: z.enum([
		"intent",
		"scope",
		"files",
		"constraints",
		"verification",
		"risks",
		"semantics",
	]),
	content: z.unknown(), // The actual content for this fragment
	content_hash: z.string(), // Full SHA-256 hex of JSON.stringify(content)
	parent_fragment_ids: z.array(z.string()).default([]), // DAG edges to upstream fragments
});

export type SpecFragment = z.infer<typeof SpecFragmentSchema>;

export const PromptSpecSchema = z.object({
	version: z.literal(1),
	generated_at: z.string().datetime(),
	source: z.object({
		repo: z.string(),
		pr_number: z.number().optional(),
		pr_url: z.string().url().optional(),
		base_branch: z.string(),
		head_branch: z.string(),
		author: z.string(),
	}),
	title: z.string(),
	summary: z.string(),
	intent: z.object({
		likely_goal: z.string(),
		change_type: z.enum([
			"feature",
			"bugfix",
			"refactor",
			"docs",
			"test",
			"chore",
			"config",
			"mixed",
		]),
	}),
	scope: z.object({
		include: z.array(z.string()),
		exclude: z.array(z.string()),
	}),
	affected_files: z.array(FileChangeSchema),
	constraints: z.array(z.string()),
	acceptance_criteria: z.array(z.string()),
	verification: z.object({
		tests_required: z.array(z.string()),
		manual_checks: z.array(z.string()),
	}),
	risk_flags: z.array(
		z.object({
			category: z.string(),
			description: z.string(),
			severity: z.enum(["low", "medium", "high"]),
		}),
	),
	open_questions: z.array(z.string()),
	generation_prompt: z.string(),
	decision_prompt: z.string(),
	review_summary: z
		.object({
			total_comments: z.number(),
			reviewers: z.array(z.string()),
			approval_status: z.enum(["approved", "changes_requested", "pending", "mixed"]),
			key_concerns: z.array(z.string()),
			file_discussions: z.array(
				z.object({
					file: z.string(),
					comment_count: z.number(),
					topics: z.array(z.string()),
				}),
			),
		})
		.optional(),
	semantic_changes: z
		.array(
			z.object({
				type: z.enum(["function", "class", "import", "export", "config", "type", "test", "other"]),
				name: z.string(),
				action: z.enum(["added", "removed", "modified"]),
				file: z.string(),
			}),
		)
		.optional(),
	monorepo: z
		.object({
			detected: z.boolean(),
			affected_packages: z.array(z.string()),
			workspace_root: z.string().optional(),
		})
		.optional(),
	stats: z.object({
		files_changed: z.number(),
		additions: z.number(),
		deletions: z.number(),
		commits: z.number(),
	}),
	ai_enhanced: z
		.object({
			summary: z.string(),
			goal: z.string(),
			key_changes: z.array(z.string()),
			review_hints: z.array(z.string()),
			provider: z.string(),
		})
		.optional(),
	drift_signals: z
		.array(
			z.object({
				type: z.enum([
					"scope_creep",
					"forbidden_touch",
					"risk_escalation",
					"size_overrun",
					"type_mismatch",
					"assumption_violation",
					"contract_violation",
				]),
				description: z.string(),
				severity: z.enum(["low", "medium", "high"]),
				details: z.array(z.string()).optional(),
			}),
		)
		.optional(),
	declared_intent: z
		.object({
			goal: z.string(),
			expected_scope: z.array(z.string()),
			forbidden_scope: z.array(z.string()),
			max_risk: z.enum(["low", "medium", "high"]),
			expected_type: z.string().optional(),
			size_budget: z.number().optional(),
		})
		.optional(),
	fragments: z.array(SpecFragmentSchema).optional(),
});

export type PromptSpec = z.infer<typeof PromptSpecSchema>;
export type FileChange = z.infer<typeof FileChangeSchema>;

/**
 * Recursively stringify an object with sorted keys for deterministic output.
 */
export function stableStringify(value: unknown): string {
	if (value === null || typeof value !== "object") {
		return JSON.stringify(value);
	}
	if (Array.isArray(value)) {
		return `[${value.map(stableStringify).join(",")}]`;
	}
	const obj = value as Record<string, unknown>;
	const sorted = Object.keys(obj)
		.sort()
		.map((k) => `${JSON.stringify(k)}:${stableStringify(obj[k])}`)
		.join(",");
	return `{${sorted}}`;
}

/**
 * Compute a SHA-256 content hash of any value using stable key ordering.
 * Returns the full hex digest.
 */
export function computeContentHash(content: unknown): string {
	return createHash("sha256").update(stableStringify(content)).digest("hex");
}

/**
 * Derive a short fragment ID from a full content hash.
 * Returns the first 12 hex characters.
 */
export function computeFragmentId(hash: string): string {
	return hash.slice(0, 12);
}
