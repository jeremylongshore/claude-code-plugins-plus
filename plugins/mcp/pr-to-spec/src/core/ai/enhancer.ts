import type { PromptSpec } from "../schema/prompt-spec.js";

export interface AIEnhanceOptions {
	provider: "anthropic" | "openai";
	apiKey: string;
	model?: string;
}

interface AIResponse {
	summary: string;
	goal: string;
	key_changes: string[];
	review_hints: string[];
}

/**
 * Enhance a deterministic spec with AI-generated insights.
 * Opt-in feature — deterministic spec is always preserved.
 */
export async function enhanceSpec(
	spec: PromptSpec,
	options: AIEnhanceOptions,
): Promise<PromptSpec> {
	const prompt = buildPrompt(spec);
	const raw = await callProvider(prompt, options);
	const parsed = parseResponse(raw);

	return {
		...spec,
		ai_enhanced: {
			...parsed,
			provider: `${options.provider}/${options.model ?? defaultModel(options.provider)}`,
		},
	};
}

function defaultModel(provider: "anthropic" | "openai"): string {
	return provider === "anthropic" ? "claude-sonnet-4-20250514" : "gpt-4o-mini";
}

function buildPrompt(spec: PromptSpec): string {
	const files = spec.affected_files
		.slice(0, 20)
		.map((f) => `  ${f.status} ${f.filename} (+${f.additions}/-${f.deletions})`)
		.join("\n");

	const risks = spec.risk_flags
		.map((r) => `  [${r.severity}] ${r.category}: ${r.description}`)
		.join("\n");

	return `Analyze this pull request and provide structured insights.

## PR: ${spec.title}
Author: @${spec.source.author}
Branch: ${spec.source.head_branch} → ${spec.source.base_branch}
Stats: ${spec.stats.files_changed} files, +${spec.stats.additions}/-${spec.stats.deletions}

## Deterministic Summary
${spec.summary}

## Inferred Goal
${spec.intent.likely_goal}

## Change Type
${spec.intent.change_type}

## Files Changed
${files}

## Risk Flags
${risks || "  None identified"}

## Constraints
${spec.constraints.map((c) => `  - ${c}`).join("\n")}

Respond with ONLY valid JSON (no markdown fences):
{
  "summary": "A concise 1-2 sentence summary focusing on WHY this change matters, not just what it does",
  "goal": "The core objective of this PR in one clear sentence",
  "key_changes": ["Up to 5 bullet points describing the most important changes"],
  "review_hints": ["Up to 3 specific things a reviewer should pay attention to"]
}`;
}

async function callProvider(prompt: string, options: AIEnhanceOptions): Promise<string> {
	if (options.provider === "anthropic") {
		return callAnthropic(prompt, options);
	}
	return callOpenAI(prompt, options);
}

async function callAnthropic(prompt: string, options: AIEnhanceOptions): Promise<string> {
	const model = options.model ?? defaultModel("anthropic");
	const res = await fetch("https://api.anthropic.com/v1/messages", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"x-api-key": options.apiKey,
			"anthropic-version": "2023-06-01",
		},
		body: JSON.stringify({
			model,
			max_tokens: 1024,
			messages: [{ role: "user", content: prompt }],
		}),
	});

	if (!res.ok) {
		const body = await res.text();
		throw new Error(`Anthropic API error (${res.status}): ${body}`);
	}

	const data = (await res.json()) as { content: Array<{ text: string }> };
	return data.content[0].text;
}

async function callOpenAI(prompt: string, options: AIEnhanceOptions): Promise<string> {
	const model = options.model ?? defaultModel("openai");
	const res = await fetch("https://api.openai.com/v1/chat/completions", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${options.apiKey}`,
		},
		body: JSON.stringify({
			model,
			max_tokens: 1024,
			messages: [{ role: "user", content: prompt }],
		}),
	});

	if (!res.ok) {
		const body = await res.text();
		throw new Error(`OpenAI API error (${res.status}): ${body}`);
	}

	const data = (await res.json()) as { choices: Array<{ message: { content: string } }> };
	return data.choices[0].message.content;
}

function parseResponse(raw: string): AIResponse {
	// Strip markdown code fences if present
	const cleaned = raw.replace(/^```(?:json)?\s*\n?/m, "").replace(/\n?```\s*$/m, "");

	try {
		const parsed = JSON.parse(cleaned) as AIResponse;
		return {
			summary: String(parsed.summary ?? ""),
			goal: String(parsed.goal ?? ""),
			key_changes: Array.isArray(parsed.key_changes)
				? parsed.key_changes.map(String).slice(0, 5)
				: [],
			review_hints: Array.isArray(parsed.review_hints)
				? parsed.review_hints.map(String).slice(0, 3)
				: [],
		};
	} catch {
		throw new Error(`Failed to parse AI response as JSON: ${cleaned.slice(0, 200)}`);
	}
}
