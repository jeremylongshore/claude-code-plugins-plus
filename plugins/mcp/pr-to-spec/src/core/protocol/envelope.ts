import type { DriftSignal } from "../drift/signals.js";
import type { GateResult } from "../gate/policy.js";
import type { Intent } from "../intent/schema.js";
import type { PromptSpec } from "../schema/prompt-spec.js";

export type ProtocolStatus = "clean" | "high_risk" | "drift_detected" | "gate_failed" | "error";

export interface AgentProtocolEnvelope {
	version: 1;
	command: string;
	status: ProtocolStatus;
	exit_code: 0 | 1 | 2 | 3 | 4;
	signals?: DriftSignal[];
	spec?: PromptSpec;
	intent?: Intent;
	gate_result?: GateResult;
	contracts?: unknown[];
}

export function buildEnvelope(
	command: string,
	spec: PromptSpec,
	opts: {
		signals?: DriftSignal[];
		intent?: Intent;
		gate_result?: GateResult;
		contracts?: unknown[];
	} = {},
): AgentProtocolEnvelope {
	const hasHighRisk = spec.risk_flags.some((r) => r.severity === "high");
	const hasDrift = (opts.signals?.length ?? 0) > 0;
	const gateFailed = opts.gate_result && !opts.gate_result.passed;

	let status: ProtocolStatus;
	let exit_code: 0 | 1 | 2 | 3 | 4;

	if (gateFailed) {
		status = "gate_failed";
		exit_code = 4;
	} else if (hasDrift) {
		status = "drift_detected";
		exit_code = 3;
	} else if (hasHighRisk) {
		status = "high_risk";
		exit_code = 2;
	} else {
		status = "clean";
		exit_code = 0;
	}

	return {
		version: 1,
		command,
		status,
		exit_code,
		signals: opts.signals,
		spec,
		intent: opts.intent,
		gate_result: opts.gate_result,
		contracts: opts.contracts,
	};
}
