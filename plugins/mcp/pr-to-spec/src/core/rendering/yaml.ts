import { stringify } from "yaml";
import { compactSpec } from "../parsing/pr-parser.js";
import type { PromptSpec } from "../schema/prompt-spec.js";

/**
 * Render a PromptSpec as a clean YAML string.
 * Strips patch data to keep output compact.
 */
export function renderYaml(spec: PromptSpec): string {
	const compact = compactSpec(spec);
	return stringify(compact, {
		lineWidth: 120,
		defaultStringType: "PLAIN",
		defaultKeyType: "PLAIN",
	});
}
