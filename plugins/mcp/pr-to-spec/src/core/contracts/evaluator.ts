import type { PromptSpec } from "../schema/prompt-spec.js";
import type { DiffSource } from "../sources/types.js";
import type { Contract, ContractResult, ContractType } from "./schema.js";

type Checker = (
	params: Record<string, unknown>,
	diff: DiffSource,
	spec: PromptSpec,
) => { passed: boolean; detail: string };

const DEPENDENCY_LOCK_FILES = new Set([
	"package-lock.json",
	"pnpm-lock.yaml",
	"yarn.lock",
	"Gemfile.lock",
	"Pipfile.lock",
	"poetry.lock",
	"Cargo.lock",
	"go.sum",
	"composer.lock",
]);

const DEPENDENCY_MANIFEST_FILES = new Set([
	"package.json",
	"Gemfile",
	"requirements.txt",
	"Pipfile",
	"Cargo.toml",
	"go.mod",
	"composer.json",
]);

const checkers: Record<ContractType, Checker> = {
	no_new_dependencies: (_params, diff) => {
		// Lock files changing always signals dependency changes
		const lockFiles = diff.files.filter(
			(f) =>
				DEPENDENCY_LOCK_FILES.has(f.filename.split("/").pop() ?? "") &&
				(f.status === "added" || f.status === "modified"),
		);
		if (lockFiles.length > 0) {
			return {
				passed: false,
				detail: `Dependency lock files changed: ${lockFiles.map((f) => f.filename).join(", ")}`,
			};
		}
		// For manifest files, check if the patch contains dependency-section additions
		const manifestFiles = diff.files.filter(
			(f) =>
				DEPENDENCY_MANIFEST_FILES.has(f.filename.split("/").pop() ?? "") &&
				(f.status === "added" || f.status === "modified") &&
				f.patch &&
				/^\+.*"(dependencies|devDependencies|peerDependencies|optionalDependencies)"/m.test(
					f.patch,
				),
		);
		if (manifestFiles.length > 0) {
			return {
				passed: false,
				detail: `Dependency sections modified: ${manifestFiles.map((f) => f.filename).join(", ")}`,
			};
		}
		return { passed: true, detail: "No dependency changes detected" };
	},

	no_file_outside_scope: (params, diff) => {
		const scope = (params.scope as string[]) ?? [];
		if (scope.length === 0) {
			return { passed: true, detail: "No scope defined" };
		}
		const outside = diff.files.filter((f) => !scope.some((s) => matchGlob(f.filename, s)));
		if (outside.length === 0) {
			return { passed: true, detail: "All files within scope" };
		}
		return {
			passed: false,
			detail: `Files outside scope: ${outside.map((f) => f.filename).join(", ")}`,
		};
	},

	max_files_changed: (params, diff) => {
		const max = (params.max as number) ?? 10;
		if (diff.files.length <= max) {
			return {
				passed: true,
				detail: `${diff.files.length} file(s) changed (<= ${max})`,
			};
		}
		return {
			passed: false,
			detail: `${diff.files.length} file(s) changed (> ${max})`,
		};
	},

	no_pattern_in_diff: (params, diff) => {
		const pattern = params.pattern as string;
		if (!pattern) {
			return { passed: true, detail: "No pattern specified" };
		}
		const regex = new RegExp(pattern);
		const matches: string[] = [];
		for (const file of diff.files) {
			if (file.patch && regex.test(file.patch)) {
				matches.push(file.filename);
			}
		}
		if (matches.length === 0) {
			return { passed: true, detail: `Pattern "${pattern}" not found in diff` };
		}
		return {
			passed: false,
			detail: `Pattern "${pattern}" found in: ${matches.join(", ")}`,
		};
	},

	require_pattern_in_diff: (params, diff) => {
		const pattern = params.pattern as string;
		if (!pattern) {
			return { passed: false, detail: "No pattern specified" };
		}
		const regex = new RegExp(pattern);
		for (const file of diff.files) {
			if (file.patch && regex.test(file.patch)) {
				return {
					passed: true,
					detail: `Pattern "${pattern}" found in ${file.filename}`,
				};
			}
		}
		return {
			passed: false,
			detail: `Required pattern "${pattern}" not found in any diff`,
		};
	},

	no_new_exports: (params, diff) => {
		const exportPattern =
			/^\+.*export\s+(default\s+)?(function|class|const|let|var|type|interface|enum)/;
		const matches: string[] = [];
		for (const file of diff.files) {
			if (file.patch) {
				const lines = file.patch.split("\n");
				for (const line of lines) {
					if (exportPattern.test(line)) {
						matches.push(file.filename);
						break;
					}
				}
			}
		}
		if (matches.length === 0) {
			return { passed: true, detail: "No new exports detected" };
		}
		return {
			passed: false,
			detail: `New exports in: ${matches.join(", ")}`,
		};
	},

	custom_command: () => {
		return {
			passed: false,
			detail:
				"custom_command contract type has been removed for security reasons (arbitrary command execution). Use a CI step or pre-commit hook instead.",
		};
	},
};

/**
 * Simple glob matcher supporting * and ** patterns.
 */
function matchGlob(filename: string, pattern: string): boolean {
	const regexStr = pattern
		.replace(/\./g, "\\.")
		.replace(/\*\*/g, "{{GLOBSTAR}}")
		.replace(/\*/g, "[^/]*")
		.replace(/\{\{GLOBSTAR\}\}/g, ".*");
	return new RegExp(`^${regexStr}$`).test(filename);
}

/**
 * Evaluate all contracts against the current diff and spec.
 */
export function evaluateContracts(
	contracts: Contract[],
	diff: DiffSource,
	spec: PromptSpec,
): ContractResult[] {
	return contracts.map((contract) => {
		const checker = checkers[contract.type];
		const { passed, detail } = checker(contract.params, diff, spec);
		return {
			contract_id: contract.id,
			contract_type: contract.type,
			passed,
			severity: contract.severity,
			detail,
		};
	});
}
