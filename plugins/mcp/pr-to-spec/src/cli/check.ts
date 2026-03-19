import { Command } from "commander";
import { evaluateContracts } from "../core/contracts/evaluator.js";
import type { ContractResult } from "../core/contracts/schema.js";
import { readContracts } from "../core/contracts/storage.js";
import { detectDriftWithSpec } from "../core/drift/detector.js";
import type { DriftSignal } from "../core/drift/signals.js";
import { type GateResult, IntentGatePolicySchema, evaluateGate } from "../core/gate/policy.js";
import { readPolicy } from "../core/gate/storage.js";
import { materializeContractResult, materializeGateResult } from "../core/graph/materialize.js";
import { readGraph, writeGraph } from "../core/graph/storage.js";
import { readIntent } from "../core/intent/storage.js";
import { generateSpec } from "../core/parsing/pr-parser.js";
import { buildEnvelope } from "../core/protocol/envelope.js";
import { renderJson } from "../core/rendering/json.js";
import { buildLocalDiffSource } from "../core/sources/local.js";

export const checkCommand = new Command("check")
	.description("Scan local changes and check for drift against declared intent")
	.option("--branch <ref>", "Base branch to diff against (default: main)")
	.option("--diff <n>", "Diff last N commits", (v) => Number.parseInt(v))
	.option("--staged", "Analyze staged changes only", false)
	.option("--quiet", "Suppress all logging", false)
	.option("--json", "Output as JSON (default for agent use)", false)
	.action(async (opts) => {
		try {
			const exitCode = await runCheck(opts);
			process.exit(exitCode);
		} catch (err) {
			const message = err instanceof Error ? err.message : String(err);
			if (!opts.quiet && !opts.json) console.error(`Error: ${message}`);
			process.exit(1);
		}
	});

function log(opts: { quiet: boolean; json: boolean }, ...args: unknown[]): void {
	if (!opts.quiet && !opts.json) console.log(...args);
}

async function runCheck(opts: {
	branch?: string;
	diff?: number;
	staged: boolean;
	quiet: boolean;
	json: boolean;
}): Promise<number> {
	const source = buildLocalDiffSource({
		base: opts.branch,
		commits: opts.diff,
		staged: opts.staged,
	});

	log(opts, `Scanning: "${source.title}" (${source.files.length} files)`);
	const spec = generateSpec(source);

	const intent = readIntent();

	if (!intent) {
		log(opts, 'No intent declared. Run: pr-to-spec intent set --goal "..."');
		// Fall back to scan behavior — use envelope if --json
		if (opts.json) {
			const envelope = buildEnvelope("check", spec);
			process.stdout.write(`${JSON.stringify(envelope, null, 2)}\n`);
		}
		const hasHighRisk = spec.risk_flags.some((r) => r.severity === "high");
		return hasHighRisk ? 2 : 0;
	}

	log(opts, "Checking drift against intent...");
	const signals: DriftSignal[] = detectDriftWithSpec(
		source,
		intent,
		spec.intent.change_type,
		spec.risk_flags,
	);

	// Contract evaluation
	let contractResults: ContractResult[] | undefined;
	const contracts = readContracts();
	if (contracts.length > 0) {
		log(opts, `Evaluating ${contracts.length} contract(s)...`);
		contractResults = evaluateContracts(contracts, source, spec);
		// Append violations as drift signals
		for (const cr of contractResults) {
			if (!cr.passed) {
				signals.push({
					type: "contract_violation",
					description: cr.detail,
					severity: cr.severity === "blocking" ? "high" : "medium",
					details: [cr.contract_id, cr.contract_type],
				});
			}
		}
	}

	// Gate evaluation (when policy exists)
	let gateResult: GateResult | undefined;
	const policy = readPolicy();
	if (policy) {
		log(opts, "Evaluating gate policy...");
		const graph = readGraph();
		gateResult = evaluateGate(graph, intent, source, policy);
	}

	// Materialize results into graph (audit trail)
	if (gateResult || contractResults) {
		const graph = readGraph();
		if (gateResult) materializeGateResult(graph, gateResult);
		if (contractResults) materializeContractResult(graph, contractResults);
		writeGraph(graph);
	}

	if (opts.json) {
		const envelope = buildEnvelope("check", spec, {
			signals,
			intent,
			gate_result: gateResult,
			contracts: contractResults,
		});
		process.stdout.write(`${JSON.stringify(envelope, null, 2)}\n`);
	} else {
		if (signals.length === 0) {
			console.log("No drift detected.");
		} else {
			console.log(`${signals.length} drift signal(s) detected:`);
			for (const s of signals) {
				console.log(`  [${s.severity.toUpperCase()}] ${s.type}: ${s.description}`);
				if (s.details?.length) {
					for (const d of s.details.slice(0, 5)) console.log(`    - ${d}`);
				}
			}
		}
		if (gateResult) {
			console.log(gateResult.passed ? "Gate: PASSED" : "Gate: FAILED");
			for (const c of gateResult.blocking_checks) {
				console.log(`  [FAIL] ${c.name}: ${c.detail}`);
			}
		}
	}

	if (gateResult && !gateResult.passed) return 4;
	if (signals.length > 0) return 3;
	const hasHighRisk = spec.risk_flags.some((r) => r.severity === "high");
	return hasHighRisk ? 2 : 0;
}
