/**
 * GitHub Action entrypoint for pr-to-prompt.
 * Reads PR context from environment and GitHub event payload.
 */

import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { type AIEnhanceOptions, enhanceSpec } from "../core/ai/enhancer.js";
import { createClient, fetchPR } from "../core/github/client.js";
import { generateSpecFromPR } from "../core/parsing/pr-parser.js";
import { renderComment } from "../core/rendering/comment.js";
import { renderJson } from "../core/rendering/json.js";
import { renderMarkdown } from "../core/rendering/markdown.js";
import { renderYaml } from "../core/rendering/yaml.js";
import type { PromptSpec } from "../core/schema/prompt-spec.js";

interface ActionInputs {
	token: string;
	comment: boolean;
	outputDir: string;
	format: string;
	aiEnhance: boolean;
	aiProvider: "anthropic" | "openai";
	aiApiKey: string;
	aiModel?: string;
	webhookUrl: string;
}

function getInputs(): ActionInputs {
	const aiProvider = (process.env.INPUT_AI_PROVIDER ?? "anthropic") as "anthropic" | "openai";
	return {
		token: process.env.GITHUB_TOKEN ?? process.env.INPUT_GITHUB_TOKEN ?? "",
		comment: (process.env.INPUT_COMMENT ?? "true") === "true",
		outputDir: process.env.INPUT_OUTPUT_DIR ?? ".pr-to-spec/specs",
		format: process.env.INPUT_FORMAT ?? "both",
		aiEnhance: (process.env.INPUT_AI_ENHANCE ?? "false") === "true",
		aiProvider,
		aiApiKey:
			process.env.INPUT_AI_API_KEY ??
			(aiProvider === "openai" ? process.env.OPENAI_API_KEY : process.env.ANTHROPIC_API_KEY) ??
			"",
		aiModel: process.env.INPUT_AI_MODEL || undefined,
		webhookUrl: process.env.INPUT_WEBHOOK_URL ?? "",
	};
}

function getEventPayload(): { owner: string; repo: string; prNumber: number } {
	const eventPath = process.env.GITHUB_EVENT_PATH;
	if (!eventPath) {
		throw new Error("GITHUB_EVENT_PATH not set — are you running inside a GitHub Action?");
	}

	const event = JSON.parse(readFileSync(eventPath, "utf-8"));
	const prNumber = event.pull_request?.number ?? event.number;
	const repoFullName = process.env.GITHUB_REPOSITORY ?? "";
	const [owner, repo] = repoFullName.split("/");

	if (!owner || !repo || !prNumber) {
		throw new Error("Could not determine PR context from GitHub event payload");
	}

	return { owner, repo, prNumber };
}

function validateWebhookUrl(url: string): void {
	let parsed: URL;
	try {
		parsed = new URL(url);
	} catch {
		throw new Error("Webhook URL is not a valid URL");
	}

	if (parsed.protocol !== "https:") {
		throw new Error("Webhook URL must use HTTPS");
	}

	const hostname = parsed.hostname.toLowerCase();
	const blocked = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"];
	if (blocked.includes(hostname)) {
		throw new Error("Webhook URL must not point to localhost");
	}

	// Block private/link-local IP ranges
	const privatePatterns = [
		/^10\./,
		/^172\.(1[6-9]|2\d|3[01])\./,
		/^192\.168\./,
		/^169\.254\./,
		/^fc00:/i,
		/^fd/i,
		/^fe80:/i,
	];
	for (const pattern of privatePatterns) {
		if (pattern.test(hostname)) {
			throw new Error("Webhook URL must not point to a private or link-local address");
		}
	}
}

async function sendWebhook(
	url: string,
	spec: PromptSpec,
	repo: string,
	prNumber: number,
): Promise<void> {
	validateWebhookUrl(url);

	const payload = JSON.stringify({
		event: "spec_generated",
		repo,
		pr_number: prNumber,
		spec,
		generated_at: spec.generated_at,
	});

	const response = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"User-Agent": "pr-to-spec/0.8.0",
		},
		body: payload,
	});

	const maskedUrl = maskUrl(url);
	if (!response.ok) {
		console.warn(`::warning::Webhook POST to ${maskedUrl} failed with status ${response.status}`);
	} else {
		console.log(`Webhook delivered to ${maskedUrl} (${response.status})`);
	}
}

async function main(): Promise<void> {
	const inputs = getInputs();
	const { owner, repo, prNumber } = getEventPayload();

	if (!inputs.token) {
		throw new Error("GitHub token is required. Set GITHUB_TOKEN or pass github_token input.");
	}

	const repoFull = `${owner}/${repo}`;
	console.log(`::group::Fetching PR #${prNumber} from ${repoFull}`);
	const octokit = createClient(inputs.token);
	const prData = await fetchPR(octokit, owner, repo, prNumber);
	console.log(`PR: "${prData.title}" by @${prData.author}`);
	console.log("::endgroup::");

	console.log("::group::Generating prompt-spec");
	let spec = generateSpecFromPR(prData, repoFull);

	if (inputs.aiEnhance && inputs.aiApiKey) {
		console.log(`Enhancing with AI (${inputs.aiProvider})...`);
		const aiOpts: AIEnhanceOptions = {
			provider: inputs.aiProvider,
			apiKey: inputs.aiApiKey,
			model: inputs.aiModel,
		};
		spec = await enhanceSpec(spec, aiOpts);
		console.log("AI enhancement complete.");
	}

	const yamlOutput = renderYaml(spec);
	const mdOutput = renderMarkdown(spec);
	const jsonOutput = renderJson(spec);
	console.log("::endgroup::");

	// Write output files
	console.log("::group::Writing output files");
	const outDir = resolve(inputs.outputDir);
	mkdirSync(outDir, { recursive: true });

	const yamlPath = resolve(outDir, `pr-${prNumber}.spec.yaml`);
	const mdPath = resolve(outDir, `pr-${prNumber}.summary.md`);
	const jsonPath = resolve(outDir, `pr-${prNumber}.spec.json`);

	if (inputs.format === "yaml" || inputs.format === "both") {
		writeFileSync(yamlPath, yamlOutput, "utf-8");
		console.log(`Written: ${yamlPath}`);
	}
	if (inputs.format === "markdown" || inputs.format === "both") {
		writeFileSync(mdPath, mdOutput, "utf-8");
		console.log(`Written: ${mdPath}`);
	}
	if (inputs.format === "json" || inputs.format === "both") {
		writeFileSync(jsonPath, jsonOutput, "utf-8");
		console.log(`Written: ${jsonPath}`);
	}
	console.log("::endgroup::");

	// Set action outputs
	setOutput("spec_yaml_path", yamlPath);
	setOutput("spec_md_path", mdPath);
	setOutput("spec_json_path", jsonPath);
	setOutput("pr_number", String(prNumber));
	setOutput("files_changed", String(spec.stats.files_changed));
	setOutput("risk_count", String(spec.risk_flags.length));

	// Send webhook
	if (inputs.webhookUrl) {
		console.log("::group::Sending webhook notification");
		await sendWebhook(inputs.webhookUrl, spec, repoFull, prNumber);
		console.log("::endgroup::");
	}

	// Post comment
	if (inputs.comment) {
		console.log("::group::Posting PR comment");
		const commentBody = renderComment(spec);
		await octokit.issues.createComment({
			owner,
			repo,
			issue_number: prNumber,
			body: commentBody,
		});
		console.log(`Comment posted on PR #${prNumber}`);
		console.log("::endgroup::");
	}
}

function maskUrl(url: string): string {
	try {
		const parsed = new URL(url);
		return `${parsed.protocol}//${parsed.hostname}/***`;
	} catch {
		return "***";
	}
}

function setOutput(name: string, value: string): void {
	const outputFile = process.env.GITHUB_OUTPUT;
	if (outputFile) {
		appendFileSync(outputFile, `${name}=${value}\n`);
	}
}

main().catch((err) => {
	console.error(`::error::${err instanceof Error ? err.message : String(err)}`);
	process.exit(1);
});
