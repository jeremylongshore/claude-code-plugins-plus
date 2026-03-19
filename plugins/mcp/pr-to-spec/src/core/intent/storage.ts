import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse as parseYaml, stringify as stringifyYaml } from "yaml";
import { type Intent, IntentSchema } from "./schema.js";

const INTENT_DIR = process.env.PR_TO_SPEC_DIR ?? ".pr-to-spec";
const INTENT_FILE = "intent.yaml";

export function getIntentPath(cwd: string = process.cwd()): string {
	return resolve(cwd, INTENT_DIR, INTENT_FILE);
}

export function readIntent(cwd: string = process.cwd()): Intent | null {
	const path = getIntentPath(cwd);
	if (!existsSync(path)) return null;
	const raw = parseYaml(readFileSync(path, "utf-8"));
	return IntentSchema.parse(raw);
}

export function writeIntent(intent: Intent, cwd: string = process.cwd()): void {
	const dir = resolve(cwd, INTENT_DIR);
	mkdirSync(dir, { recursive: true });
	const path = getIntentPath(cwd);
	writeFileSync(path, stringifyYaml(intent), "utf-8");
}
