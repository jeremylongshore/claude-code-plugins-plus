import { z } from "zod";

export const ContractTypeSchema = z.enum([
	"no_new_dependencies",
	"no_file_outside_scope",
	"max_files_changed",
	"no_pattern_in_diff",
	"require_pattern_in_diff",
	"no_new_exports",
	"custom_command",
]);

export type ContractType = z.infer<typeof ContractTypeSchema>;

export const ContractSchema = z.object({
	id: z.string(),
	description: z.string().default(""),
	type: ContractTypeSchema,
	params: z.record(z.unknown()).default({}),
	severity: z.enum(["blocking", "warning"]).default("blocking"),
});

export type Contract = z.infer<typeof ContractSchema>;

export interface ContractResult {
	contract_id: string;
	contract_type: ContractType;
	passed: boolean;
	severity: "blocking" | "warning";
	detail: string;
}
