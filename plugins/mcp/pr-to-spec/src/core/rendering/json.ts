import { compactSpec } from "../parsing/pr-parser.js";
import type { PromptSpec } from "../schema/prompt-spec.js";

/**
 * Render a PromptSpec as a JSON string.
 * Strips patch data to keep output compact.
 */
export function renderJson(spec: PromptSpec): string {
	return JSON.stringify(compactSpec(spec), null, 2);
}
