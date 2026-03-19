import { matchesGlob } from "../drift/detector.js";
import type { Intent } from "../intent/schema.js";
import type { DiffSource } from "../sources/types.js";

/**
 * Decision taxonomy based on 2x2 matrix:
 *   - Predictability: how likely is the agent to guess correctly?
 *   - Reversibility: how easy is it to undo?
 */
export type DecisionAction = "must_ask" | "confirm_upfront" | "ask_adhoc" | "assume_safe";

export interface Decision {
	id: string;
	question: string;
	action: DecisionAction;
	predictability: "low" | "high";
	reversibility: "low" | "high";
	category: string;
	context?: string;
}

/**
 * Classify an assumption into the 2x2 decision matrix.
 *
 * | predictability | reversibility | action          |
 * |----------------|---------------|-----------------|
 * | low            | low           | must_ask        |
 * | high           | low           | confirm_upfront |
 * | low            | high          | ask_adhoc       |
 * | high           | high          | assume_safe     |
 *
 * @param predictability - How reliably the AI can guess the user's intent.
 * @param reversibility - How easily the decision can be undone.
 * @returns The appropriate decision action.
 */
export function classifyDecision(
	predictability: "low" | "high",
	reversibility: "low" | "high",
): DecisionAction {
	if (predictability === "low" && reversibility === "low") return "must_ask";
	if (predictability === "high" && reversibility === "low") return "confirm_upfront";
	if (predictability === "low" && reversibility === "high") return "ask_adhoc";
	return "assume_safe";
}

/**
 * Analyze a DiffSource + Intent to surface implicit assumptions
 * that should be validated before coding.
 */
export function analyzeAssumptions(diff: DiffSource, intent: Intent): Decision[] {
	const decisions: Decision[] = [];
	let idCounter = 0;
	const nextId = () => `decision-${++idCounter}`;

	// 1. Database migrations — low predictability, low reversibility → must_ask
	if (diff.files.some((f) => /\b(migration|migrate|\.sql)\b/i.test(f.filename))) {
		decisions.push({
			id: nextId(),
			question: "Is this database migration destructive? Will it cause data loss?",
			action: "must_ask",
			predictability: "low",
			reversibility: "low",
			category: "database",
			context: "Database migrations are hard to reverse in production",
		});
	}

	// 2. Auth/security changes — high predictability (we know it's risky), low reversibility → confirm_upfront
	if (
		diff.files.some((f) => /\b(auth|login|session|oauth|jwt|permission|rbac)\b/i.test(f.filename))
	) {
		decisions.push({
			id: nextId(),
			question: "Touching authentication/authorization logic. Proceeding with changes.",
			action: "confirm_upfront",
			predictability: "high",
			reversibility: "low",
			category: "authentication",
			context: "Auth changes affect all users and are hard to roll back",
		});
	}

	// 3. API contract changes — low predictability, low reversibility → must_ask
	if (diff.files.some((f) => /\b(api|route|endpoint)\b/i.test(f.filename))) {
		const hasBreaking = diff.files.some(
			(f) => f.patch !== undefined && /\b(DELETE|remove|rename|breaking)\b/i.test(f.patch),
		);
		if (hasBreaking) {
			decisions.push({
				id: nextId(),
				question: "API changes may break existing clients. Are these backwards-compatible?",
				action: "must_ask",
				predictability: "low",
				reversibility: "low",
				category: "api",
				context: "API breaking changes affect downstream consumers",
			});
		}
	}

	// 4. Infrastructure/deploy changes — high predictability, low reversibility → confirm_upfront
	if (
		diff.files.some((f) => /\b(docker|terraform|k8s|deploy|infra|workflow)\b/i.test(f.filename))
	) {
		decisions.push({
			id: nextId(),
			question: "Infrastructure changes detected. Confirming deployment configuration updates.",
			action: "confirm_upfront",
			predictability: "high",
			reversibility: "low",
			category: "infrastructure",
		});
	}

	// 5. Dependency updates — low predictability (might break), high reversibility → ask_adhoc
	if (
		diff.files.some((f) =>
			/^(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|Gemfile|requirements.*\.txt|go\.(mod|sum)|Cargo\.(toml|lock))$/.test(
				f.filename,
			),
		)
	) {
		decisions.push({
			id: nextId(),
			question: "Dependency changes detected. Any specific version constraints to follow?",
			action: "ask_adhoc",
			predictability: "low",
			reversibility: "high",
			category: "dependencies",
		});
	}

	// 6. Test file changes — high predictability, high reversibility → assume_safe
	if (diff.files.every((f) => /\b(test|spec|__tests__)\b/i.test(f.filename))) {
		decisions.push({
			id: nextId(),
			question: "Only test files changed. No review needed.",
			action: "assume_safe",
			predictability: "high",
			reversibility: "high",
			category: "testing",
		});
	}

	// 7. Large change — low predictability (might have unintended side effects), high reversibility → ask_adhoc
	const totalLoc = diff.files.reduce((sum, f) => sum + f.additions + f.deletions, 0);
	if (totalLoc > 500) {
		decisions.push({
			id: nextId(),
			question: `Large change (${totalLoc} LOC). Could this be split into smaller changes?`,
			action: "ask_adhoc",
			predictability: "low",
			reversibility: "high",
			category: "scope",
		});
	}

	// 8. File deletions — low predictability (might have dependents), low reversibility → must_ask
	const deletedFiles = diff.files.filter((f) => f.status === "removed");
	if (deletedFiles.length > 0) {
		decisions.push({
			id: nextId(),
			question: `${deletedFiles.length} file(s) being deleted. Confirm no other modules depend on them.`,
			action: "must_ask",
			predictability: "low",
			reversibility: "low",
			category: "deletion",
			context: deletedFiles.map((f) => f.filename).join(", "),
		});
	}

	// 9. Scope drift from intent — if intent has expected_scope, check if files are outside
	if (intent.expected_scope.length > 0) {
		const outOfScope = diff.files.filter(
			(f) => !intent.expected_scope.some((g) => matchesGlob(f.filename, g)),
		);
		if (outOfScope.length > 0) {
			decisions.push({
				id: nextId(),
				question: `${outOfScope.length} file(s) are outside declared scope. Is this intentional?`,
				action: "must_ask",
				predictability: "low",
				reversibility: "low",
				category: "scope_violation",
				context: outOfScope
					.map((f) => f.filename)
					.slice(0, 5)
					.join(", "),
			});
		}
	}

	// 10. Forbidden scope violation — always must_ask
	if (intent.forbidden_scope.length > 0) {
		const forbidden = diff.files.filter((f) =>
			intent.forbidden_scope.some((g) => matchesGlob(f.filename, g)),
		);
		if (forbidden.length > 0) {
			decisions.push({
				id: nextId(),
				question: `${forbidden.length} file(s) in forbidden scope were modified. This violates the declared intent.`,
				action: "must_ask",
				predictability: "low",
				reversibility: "low",
				category: "forbidden_violation",
				context: forbidden.map((f) => f.filename).join(", "),
			});
		}
	}

	return decisions;
}
