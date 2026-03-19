import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { Command } from "commander";
import { generateSpec } from "../core/parsing/pr-parser.js";
import { buildEnvelope } from "../core/protocol/envelope.js";
import { renderJson } from "../core/rendering/json.js";
import { renderMarkdown } from "../core/rendering/markdown.js";
import { renderYaml } from "../core/rendering/yaml.js";
import { buildLocalDiffSource } from "../core/sources/local.js";

export const scanCommand = new Command("scan")
	.description("Analyze local git changes and generate a spec")
	.option("--branch <ref>", "Base branch to diff against (default: main)")
	.option("--diff <n>", "Diff last N commits (e.g. HEAD~3)", (v) => Number.parseInt(v))
	.option("--staged", "Analyze staged changes only", false)
	.option("--out <directory>", "Output directory", "./output")
	.option("--format <format>", "Output format: yaml, markdown, json, both", "both")
	.option("--stdout", "Print to stdout instead of writing files", false)
	.option("--quiet", "Suppress all logging", false)
	.option("--field <path>", "Extract a single field (dot notation)")
	.option("--json", "Shorthand for --format json --stdout --quiet", false)
	.action(async (opts) => {
		try {
			const exitCode = await runScan(opts);
			process.exit(exitCode);
		} catch (err) {
			const message = err instanceof Error ? err.message : String(err);
			if (!opts.quiet && !opts.json) {
				console.error(`Error: ${message}`);
			}
			process.exit(1);
		}
	});

interface ScanOptions {
	branch?: string;
	diff?: number;
	staged: boolean;
	out: string;
	format: string;
	stdout: boolean;
	quiet: boolean;
	field?: string;
	json: boolean;
}

function log(opts: ScanOptions, ...args: unknown[]): void {
	if (!opts.quiet && !opts.json) {
		console.log(...args);
	}
}

async function runScan(opts: ScanOptions): Promise<number> {
	if (opts.json) {
		opts.format = "json";
		opts.stdout = true;
		opts.quiet = true;
	}

	log(opts, "Scanning local git changes...");

	const source = buildLocalDiffSource({
		base: opts.branch,
		commits: opts.diff,
		staged: opts.staged,
	});

	if (source.files.length === 0) {
		if (!opts.quiet) console.log("No changes detected.");
		process.exit(0);
	}

	log(opts, `Generating spec for: "${source.title}"`);
	const spec = generateSpec(source);

	if (opts.field) {
		const value = extractField(spec as Record<string, unknown>, opts.field);
		if (value === undefined) throw new Error(`Field "${opts.field}" not found in spec`);
		const output = typeof value === "string" ? value : JSON.stringify(value, null, 2);
		process.stdout.write(`${output}\n`);
		return 0;
	}

	const jsonOutput = opts.json
		? JSON.stringify(buildEnvelope("scan", spec), null, 2)
		: renderJson(spec);
	const yamlOutput = renderYaml(spec);
	const mdOutput = renderMarkdown(spec);

	if (opts.stdout) {
		if (opts.format === "json") process.stdout.write(`${jsonOutput}\n`);
		else if (opts.format === "yaml") process.stdout.write(`${yamlOutput}\n`);
		else if (opts.format === "markdown") process.stdout.write(`${mdOutput}\n`);
		else {
			process.stdout.write(`${yamlOutput}\n${mdOutput}\n${jsonOutput}\n`);
		}
	} else {
		const outDir = resolve(opts.out);
		mkdirSync(outDir, { recursive: true });
		const base = `scan-${Date.now()}`;
		if (opts.format === "yaml" || opts.format === "both") {
			writeFileSync(resolve(outDir, `${base}.spec.yaml`), yamlOutput, "utf-8");
			log(opts, `  Written: ${base}.spec.yaml`);
		}
		if (opts.format === "markdown" || opts.format === "both") {
			writeFileSync(resolve(outDir, `${base}.summary.md`), mdOutput, "utf-8");
			log(opts, `  Written: ${base}.summary.md`);
		}
		if (opts.format === "json" || opts.format === "both") {
			writeFileSync(resolve(outDir, `${base}.spec.json`), jsonOutput, "utf-8");
			log(opts, `  Written: ${base}.spec.json`);
		}
	}

	log(opts, "Done.");
	const hasHighRisk = spec.risk_flags.some((r) => r.severity === "high");
	return hasHighRisk ? 2 : 0;
}

function extractField(obj: Record<string, unknown>, path: string): unknown {
	const BLOCKED_KEYS = new Set(["__proto__", "constructor", "prototype"]);
	const parts = path.split(".");
	let current: unknown = obj;
	for (const part of parts) {
		if (BLOCKED_KEYS.has(part)) return undefined;
		if (current === null || current === undefined || typeof current !== "object") return undefined;
		current = (current as Record<string, unknown>)[part];
	}
	return current;
}
