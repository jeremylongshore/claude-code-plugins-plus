#!/usr/bin/env node

import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { program } from "commander";
import { type AIEnhanceOptions, enhanceSpec } from "../core/ai/enhancer.js";
import { createClient, fetchPR } from "../core/github/client.js";
import { generateSpecFromPR } from "../core/parsing/pr-parser.js";
import { buildEnvelope } from "../core/protocol/envelope.js";
import { renderComment } from "../core/rendering/comment.js";
import { renderJson } from "../core/rendering/json.js";
import { renderMarkdown } from "../core/rendering/markdown.js";
import { renderYaml } from "../core/rendering/yaml.js";
import { checkCommand } from "./check.js";
import { contractCommand } from "./contract.js";
import { feedbackCommand } from "./feedback.js";
import { graphCommand } from "./graph.js";
import { intentCommand } from "./intent.js";
import { scanCommand } from "./scan.js";

program
	.name("pr-to-spec")
	.description("Convert code changes into structured, agent-consumable spec artifacts")
	.version("0.8.0")
	.requiredOption("--repo <owner/name>", "GitHub repository (owner/name)")
	.requiredOption("--pr <number>", "Pull request number", Number.parseInt)
	.option("--out <directory>", "Output directory", "./output")
	.option("--token <token>", "GitHub token (or set GITHUB_TOKEN env var)")
	.option("--comment", "Post spec summary as a PR comment", false)
	.option("--format <format>", "Output format: yaml, markdown, json, both", "both")
	.option("--stdout", "Print to stdout instead of writing files", false)
	.option("--quiet", "Suppress all logging, only output the spec (for piping)", false)
	.option("--field <path>", "Extract a single field from the spec (dot notation)")
	.option("--json", "Shorthand for --format json --stdout --quiet", false)
	.option("--ai-enhance", "Enhance spec with AI-generated insights", false)
	.option("--ai-provider <provider>", "AI provider: anthropic, openai", "anthropic")
	.option("--ai-model <model>", "AI model override")
	.option("--debug", "Log git commands, API URLs, and timing info", false)
	.action(async (opts) => {
		try {
			const exitCode = await run(opts);
			process.exit(exitCode);
		} catch (err) {
			const message = err instanceof Error ? err.message : String(err);
			if (!opts.quiet && !opts.json) {
				console.error(`Error: ${message}`);
			}
			process.exit(1);
		}
	});

interface CLIOptions {
	repo: string;
	pr: number;
	out: string;
	token?: string;
	comment: boolean;
	format: string;
	stdout: boolean;
	quiet: boolean;
	field?: string;
	json: boolean;
	aiEnhance: boolean;
	aiProvider: string;
	aiModel?: string;
	debug: boolean;
}

function log(opts: CLIOptions, ...args: unknown[]): void {
	if (!opts.quiet && !opts.json) {
		console.log(...args);
	}
}

async function run(opts: CLIOptions): Promise<number> {
	// --json is shorthand for --format json --stdout --quiet
	if (opts.json) {
		opts.format = "json";
		opts.stdout = true;
		opts.quiet = true;
	}

	const token = opts.token ?? process.env.GITHUB_TOKEN;
	if (!token) {
		throw new Error(
			"GitHub token required. Set GITHUB_TOKEN env var or pass --token flag.\nToken needs `repo` scope (or fine-grained: pull requests read access).",
		);
	}

	const [owner, repo] = opts.repo.split("/");
	if (!owner || !repo) {
		throw new Error("Repository must be in owner/name format (e.g., octocat/hello-world)");
	}

	if (Number.isNaN(opts.pr) || opts.pr < 1) {
		throw new Error("PR number must be a positive integer");
	}

	log(opts, `Fetching PR #${opts.pr} from ${opts.repo}...`);
	if (opts.debug) {
		console.error(`[debug] API: GET /repos/${owner}/${repo}/pulls/${opts.pr}`);
	}
	const startTime = opts.debug ? Date.now() : 0;
	const octokit = createClient(token);
	const prData = await fetchPR(octokit, owner, repo, opts.pr);
	if (opts.debug) {
		console.error(
			`[debug] Fetched PR in ${Date.now() - startTime}ms (${prData.files.length} files)`,
		);
	}

	log(opts, `Generating prompt-spec for: "${prData.title}"`);
	let spec = generateSpecFromPR(prData, opts.repo);

	if (opts.aiEnhance) {
		const aiKey = resolveAIKey(opts.aiProvider);
		if (!aiKey) {
			throw new Error(
				`AI enhancement requires an API key. Set ${opts.aiProvider === "openai" ? "OPENAI_API_KEY" : "ANTHROPIC_API_KEY"} env var.`,
			);
		}
		log(opts, `Enhancing with AI (${opts.aiProvider})...`);
		const aiOpts: AIEnhanceOptions = {
			provider: opts.aiProvider as "anthropic" | "openai",
			apiKey: aiKey,
			model: opts.aiModel,
		};
		spec = await enhanceSpec(spec, aiOpts);
		log(opts, "  AI enhancement complete.");
	}

	// --field: extract a single field and output it
	if (opts.field) {
		const value = extractField(spec, opts.field);
		if (value === undefined) {
			throw new Error(`Field "${opts.field}" not found in spec`);
		}
		const output = typeof value === "string" ? value : JSON.stringify(value, null, 2);
		process.stdout.write(`${output}\n`);
		return 0;
	}

	const yamlOutput = renderYaml(spec);
	const mdOutput = renderMarkdown(spec);
	const jsonOutput = opts.json
		? JSON.stringify(buildEnvelope("analyze", spec), null, 2)
		: renderJson(spec);

	if (opts.stdout) {
		if (opts.format === "json") {
			process.stdout.write(`${jsonOutput}\n`);
		} else if (opts.format === "yaml") {
			if (!opts.quiet) console.log("\n--- YAML ---\n");
			process.stdout.write(`${yamlOutput}\n`);
		} else if (opts.format === "markdown") {
			if (!opts.quiet) console.log("\n--- Markdown ---\n");
			process.stdout.write(`${mdOutput}\n`);
		} else {
			// "both" — all formats with separators
			if (!opts.quiet) console.log("\n--- YAML ---\n");
			process.stdout.write(`${yamlOutput}\n`);
			if (!opts.quiet) console.log("\n--- Markdown ---\n");
			process.stdout.write(`${mdOutput}\n`);
			if (!opts.quiet) console.log("\n--- JSON ---\n");
			process.stdout.write(`${jsonOutput}\n`);
		}
	} else {
		const outDir = resolve(opts.out);
		mkdirSync(outDir, { recursive: true });

		const yamlPath = resolve(outDir, `pr-${opts.pr}.spec.yaml`);
		const mdPath = resolve(outDir, `pr-${opts.pr}.summary.md`);
		const jsonPath = resolve(outDir, `pr-${opts.pr}.spec.json`);

		if (opts.format === "yaml" || opts.format === "both") {
			writeFileSync(yamlPath, yamlOutput, "utf-8");
			log(opts, `  Written: ${yamlPath}`);
		}
		if (opts.format === "markdown" || opts.format === "both") {
			writeFileSync(mdPath, mdOutput, "utf-8");
			log(opts, `  Written: ${mdPath}`);
		}
		if (opts.format === "json" || opts.format === "both") {
			writeFileSync(jsonPath, jsonOutput, "utf-8");
			log(opts, `  Written: ${jsonPath}`);
		}
	}

	if (opts.comment) {
		log(opts, "Posting PR comment...");
		const commentBody = renderComment(spec);
		await octokit.issues.createComment({
			owner,
			repo,
			issue_number: opts.pr,
			body: commentBody,
		});
		log(opts, `  Comment posted on PR #${opts.pr}`);
	}

	log(opts, "Done.");

	// Exit code 2 if high-risk PR detected
	const hasHighRisk = spec.risk_flags.some((r) => r.severity === "high");
	return hasHighRisk ? 2 : 0;
}

/**
 * Extract a nested field from the spec using dot notation.
 * e.g., "risk_flags" -> spec.risk_flags, "source.author" -> spec.source.author
 */
function extractField(obj: Record<string, unknown>, path: string): unknown {
	const BLOCKED_KEYS = new Set(["__proto__", "constructor", "prototype"]);
	const parts = path.split(".");
	let current: unknown = obj;
	for (const part of parts) {
		if (BLOCKED_KEYS.has(part)) return undefined;
		if (current === null || current === undefined || typeof current !== "object") {
			return undefined;
		}
		current = (current as Record<string, unknown>)[part];
	}
	return current;
}

function resolveAIKey(provider: string): string | undefined {
	if (provider === "openai") {
		return process.env.OPENAI_API_KEY;
	}
	return process.env.ANTHROPIC_API_KEY;
}

program.addCommand(scanCommand);
program.addCommand(intentCommand);
program.addCommand(checkCommand);
program.addCommand(feedbackCommand);
program.addCommand(graphCommand);
program.addCommand(contractCommand);
program.parse();
