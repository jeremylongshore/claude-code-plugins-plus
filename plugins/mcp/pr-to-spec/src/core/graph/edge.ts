import { z } from "zod";
import { IntentNodeSchema } from "./node.js";

export const EdgeTypeSchema = z.enum([
	"derives_from",
	"constrains",
	"invalidates",
	"satisfies",
	"conflicts_with",
]);

export type EdgeType = z.infer<typeof EdgeTypeSchema>;

export const IntentEdgeSchema = z.object({
	source_id: z.string(),
	target_id: z.string(),
	edge_type: EdgeTypeSchema,
	created_at: z.string().datetime().optional(),
});

export type IntentEdge = z.infer<typeof IntentEdgeSchema>;

export const IntentGraphSchema = z.object({
	version: z.literal(1),
	nodes: z.array(IntentNodeSchema),
	edges: z.array(IntentEdgeSchema),
	updated_at: z.string().datetime(),
});

export type IntentGraph = z.infer<typeof IntentGraphSchema>;
