import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse as parseYaml, stringify as stringifyYaml } from "yaml";
import { z } from "zod";
import { type Contract, ContractSchema } from "./schema.js";

const CONTRACTS_DIR = process.env.PR_TO_SPEC_DIR ?? ".pr-to-spec";
const CONTRACTS_FILE = "contracts.yaml";

export function getContractsPath(cwd: string = process.cwd()): string {
	return resolve(cwd, CONTRACTS_DIR, CONTRACTS_FILE);
}

export function readContracts(cwd: string = process.cwd()): Contract[] {
	const path = getContractsPath(cwd);
	if (!existsSync(path)) return [];
	const raw = parseYaml(readFileSync(path, "utf-8"));
	return z.array(ContractSchema).parse(raw ?? []);
}

export function writeContracts(contracts: Contract[], cwd: string = process.cwd()): void {
	const dir = resolve(cwd, CONTRACTS_DIR);
	mkdirSync(dir, { recursive: true });
	const path = getContractsPath(cwd);
	writeFileSync(path, stringifyYaml(contracts), "utf-8");
}
