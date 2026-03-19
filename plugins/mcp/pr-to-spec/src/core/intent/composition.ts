import type { Intent, IntentLayer, LayeredIntent } from "./schema.js";

/**
 * Risk level ordering used for MIN selection.
 * Lower numeric value = more conservative (takes precedence in merge).
 */
const RISK_ORDER: Record<"low" | "medium" | "high", number> = {
	low: 0,
	medium: 1,
	high: 2,
};

const RISK_BY_ORDER: Record<number, "low" | "medium" | "high"> = {
	0: "low",
	1: "medium",
	2: "high",
};

/**
 * Merge multiple intent layers into a single resolved Intent.
 *
 * Composition algebra:
 *   - `goal`           — unique goals joined with "; ", highest-priority first
 *   - `expected_scope` — union of all arrays (deduplicated)
 *   - `forbidden_scope`— union of all arrays (deduplicated)
 *   - `max_risk`       — MIN(all max_risk): most conservative wins
 *   - `expected_type`  — highest-priority layer's type that has one set
 *   - `size_budget`    — SUM of all budgets; undefined if none are set
 *   - `created_at`     — earliest timestamp across all layers
 *   - `updated_at`     — current ISO timestamp
 *
 * @param layers - One or more intent layers to merge. Must be non-empty.
 * @returns A single flattened Intent reflecting the merged state.
 */
export function mergeIntents(layers: IntentLayer[]): Intent {
	if (layers.length === 0) {
		throw new Error("mergeIntents requires at least one layer");
	}

	// Sort descending by priority so highest-priority comes first
	const sorted = [...layers].sort((a, b) => b.priority - a.priority);

	// goal: unique goals in priority order, joined with "; "
	const seenGoals = new Set<string>();
	const goals: string[] = [];
	for (const layer of sorted) {
		const g = layer.intent.goal.trim();
		if (!seenGoals.has(g)) {
			seenGoals.add(g);
			goals.push(g);
		}
	}
	const goal = goals.join("; ");

	// expected_scope: union, deduplicated
	const expectedScopeSet = new Set<string>();
	for (const layer of sorted) {
		for (const s of layer.intent.expected_scope) {
			expectedScopeSet.add(s);
		}
	}

	// forbidden_scope: union, deduplicated
	const forbiddenScopeSet = new Set<string>();
	for (const layer of sorted) {
		for (const s of layer.intent.forbidden_scope) {
			forbiddenScopeSet.add(s);
		}
	}

	// max_risk: pick the minimum (most conservative) risk level
	let minRiskOrder = RISK_ORDER[sorted[0].intent.max_risk];
	for (const layer of sorted) {
		const order = RISK_ORDER[layer.intent.max_risk];
		if (order < minRiskOrder) {
			minRiskOrder = order;
		}
	}
	const max_risk = RISK_BY_ORDER[minRiskOrder];

	// expected_type: first set value in priority order
	let expected_type: Intent["expected_type"];
	for (const layer of sorted) {
		if (layer.intent.expected_type !== undefined) {
			expected_type = layer.intent.expected_type;
			break;
		}
	}

	// size_budget: sum of all set values; undefined if none are set
	let size_budget: number | undefined;
	for (const layer of sorted) {
		if (layer.intent.size_budget !== undefined) {
			size_budget = (size_budget ?? 0) + layer.intent.size_budget;
		}
	}

	// created_at: earliest timestamp
	let created_at: string | undefined;
	for (const layer of sorted) {
		if (layer.intent.created_at !== undefined) {
			if (created_at === undefined || layer.intent.created_at < created_at) {
				created_at = layer.intent.created_at;
			}
		}
	}

	// updated_at: current timestamp
	const updated_at = new Date().toISOString();

	return {
		goal,
		expected_scope: Array.from(expectedScopeSet),
		forbidden_scope: Array.from(forbiddenScopeSet),
		max_risk,
		expected_type,
		size_budget,
		status: "draft" as const,
		created_at,
		updated_at,
	};
}

/**
 * Flatten a LayeredIntent into a single resolved Intent by merging all layers.
 *
 * @param layered - A LayeredIntent with one or more layers.
 * @returns A single merged Intent.
 */
export function flattenToIntent(layered: LayeredIntent): Intent {
	return mergeIntents(layered.layers);
}

/**
 * Wrap a plain Intent into a single-layer LayeredIntent.
 * Allows existing code to opt into the layered system with no behavioural change.
 *
 * @param intent - The intent to wrap.
 * @param name   - Optional layer name. Defaults to "default".
 * @returns A LayeredIntent with a single layer at priority 0.
 */
export function singleLayerIntent(intent: Intent, name = "default"): LayeredIntent {
	return {
		layers: [
			{
				name,
				priority: 0,
				intent,
			},
		],
	};
}
