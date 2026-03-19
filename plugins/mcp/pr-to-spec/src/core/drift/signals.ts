export type DriftSignalType =
	| "scope_creep"
	| "forbidden_touch"
	| "risk_escalation"
	| "size_overrun"
	| "type_mismatch"
	| "assumption_violation"
	| "contract_violation";

export interface DriftSignal {
	type: DriftSignalType;
	description: string;
	severity: "low" | "medium" | "high";
	/** Files or values involved */
	details?: string[];
}
