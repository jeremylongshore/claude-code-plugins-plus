import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse as parseYaml, stringify as stringifyYaml } from "yaml";
import { type IntentGatePolicy, IntentGatePolicySchema } from "./policy.js";

const GATE_DIR = process.env.PR_TO_SPEC_DIR ?? ".pr-to-spec";
const POLICY_FILE = "policy.yaml";

export function getPolicyPath(cwd: string = process.cwd()): string {
	return resolve(cwd, GATE_DIR, POLICY_FILE);
}

export function readPolicy(cwd: string = process.cwd()): IntentGatePolicy | null {
	const path = getPolicyPath(cwd);
	if (!existsSync(path)) return null;
	const raw = parseYaml(readFileSync(path, "utf-8"));
	return IntentGatePolicySchema.parse(raw);
}

export function writePolicy(policy: IntentGatePolicy, cwd: string = process.cwd()): void {
	const dir = resolve(cwd, GATE_DIR);
	mkdirSync(dir, { recursive: true });
	const path = getPolicyPath(cwd);
	writeFileSync(path, stringifyYaml(policy), "utf-8");
}
