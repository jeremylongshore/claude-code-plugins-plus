import { z } from "zod";

export const IntentNodeTypeSchema = z.enum([
	"project_intent",
	"prd",
	"architecture",
	"task_plan",
	"change_intent",
	"spec_fragment",
	"decision",
	"drift_signal",
	"risk_flag",
	"feedback",
	"gate_check",
	"contract_check",
]);

export type IntentNodeType = z.infer<typeof IntentNodeTypeSchema>;

export const IntentNodeSourceSchema = z.enum([
	"interview",
	"heuristic",
	"declared",
	"inferred",
	"feedback",
]);

export type IntentNodeSource = z.infer<typeof IntentNodeSourceSchema>;

export const IntentNodeSchema = z.object({
	node_id: z.string(), // content hash
	node_type: IntentNodeTypeSchema,
	content: z.unknown(), // type-specific payload
	parent_ids: z.array(z.string()).default([]), // upstream DAG edges (derives_from)
	confidence: z.number().min(0).max(1).default(1),
	source: IntentNodeSourceSchema,
	invalidated_at: z.string().datetime().nullable().default(null),
	version: z.number().int().min(1).default(1),
	created_at: z.string().datetime().optional(),
	updated_at: z.string().datetime().optional(),
});

export type IntentNode = z.infer<typeof IntentNodeSchema>;
