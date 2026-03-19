import { analyzeAssumptions } from "../decisions/classifier.js";
import type { Intent } from "../intent/schema.js";
import type { DiffSource } from "../sources/types.js";
import type { DriftSignal, DriftSignalType } from "./signals.js";

/** Simple glob matcher — supports * and ** patterns */
export function matchesGlob(filename: string, pattern: string): boolean {
	// Convert glob to regex
	const escaped = pattern
		.replace(/[.+^${}()|[\]\\]/g, "\\$&")
		.replace(/\*\*/g, "§DOUBLE§")
		.replace(/\*/g, "[^/]*")
		.replace(/§DOUBLE§/g, ".*");
	return new RegExp(`^${escaped}$`).test(filename);
}

function matchesAnyGlob(filename: string, globs: string[]): boolean {
	return globs.some((g) => matchesGlob(filename, g));
}

const RISK_ORDER: Record<string, number> = { low: 0, medium: 1, high: 2 };

export function detectDrift(diff: DiffSource, intent: Intent): DriftSignal[] {
	const signals: DriftSignal[] = [];
	const filenames = diff.files.map((f) => f.filename);

	// 1. scope_creep — files outside expected_scope
	if (intent.expected_scope.length > 0) {
		const outsideScope = filenames.filter((f) => !matchesAnyGlob(f, intent.expected_scope));
		if (outsideScope.length > 0) {
			signals.push({
				type: "scope_creep",
				description: `${outsideScope.length} file(s) changed outside expected scope`,
				severity: "medium",
				details: outsideScope.slice(0, 10),
			});
		}
	}

	// 2. forbidden_touch — files matching forbidden_scope
	if (intent.forbidden_scope.length > 0) {
		const forbidden = filenames.filter((f) => matchesAnyGlob(f, intent.forbidden_scope));
		if (forbidden.length > 0) {
			signals.push({
				type: "forbidden_touch",
				description: `${forbidden.length} forbidden file(s) modified`,
				severity: "high",
				details: forbidden,
			});
		}
	}

	// 4. size_overrun
	if (intent.size_budget !== undefined) {
		const totalLOC = diff.files.reduce((sum, f) => sum + f.additions + f.deletions, 0);
		if (totalLOC > intent.size_budget) {
			signals.push({
				type: "size_overrun",
				description: `Total changes (${totalLOC} LOC) exceed budget of ${intent.size_budget}`,
				severity: "low",
				details: [`actual: ${totalLOC}`, `budget: ${intent.size_budget}`],
			});
		}
	}

	return signals;
}

/**
 * Detect assumption violations — decisions that were classified as must_ask
 * but no confirmation was provided.
 */
export function detectAssumptionViolations(diff: DiffSource, intent: Intent): DriftSignal[] {
	const decisions = analyzeAssumptions(diff, intent);
	const mustAsk = decisions.filter((d) => d.action === "must_ask");

	return mustAsk.map((d) => ({
		type: "assumption_violation" as DriftSignalType,
		description: d.question,
		severity: "high" as const,
		details: d.context ? [d.context, `category: ${d.category}`] : [`category: ${d.category}`],
	}));
}

/**
 * Detect drift with full spec context (risk flags, change type).
 * This is the primary entry point from the check command.
 */
export function detectDriftWithSpec(
	diff: DiffSource,
	intent: Intent,
	specChangeType: string,
	specRiskFlags: Array<{ severity: string }>,
): DriftSignal[] {
	const signals = detectDrift(diff, intent);

	// risk_escalation
	const maxRiskOrder = RISK_ORDER[intent.max_risk] ?? 2;
	const hasEscalation = specRiskFlags.some((r) => (RISK_ORDER[r.severity] ?? 0) > maxRiskOrder);
	if (hasEscalation) {
		const highFlags = specRiskFlags.filter((r) => (RISK_ORDER[r.severity] ?? 0) > maxRiskOrder);
		signals.push({
			type: "risk_escalation",
			description: `Risk level exceeds max_risk "${intent.max_risk}"`,
			severity: "high",
			details: highFlags.map((r) => JSON.stringify(r)),
		});
	}

	// type_mismatch
	if (intent.expected_type && specChangeType !== intent.expected_type) {
		signals.push({
			type: "type_mismatch",
			description: `Inferred change type "${specChangeType}" doesn't match expected "${intent.expected_type}"`,
			severity: "low",
			details: [`inferred: ${specChangeType}`, `expected: ${intent.expected_type}`],
		});
	}

	// assumption_violation — unconfirmed must_ask decisions
	const violations = detectAssumptionViolations(diff, intent);
	signals.push(...violations);

	return signals;
}
