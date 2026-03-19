import { z } from "zod";

export const IntentSchema = z.object({
	goal: z.string().min(1, "Goal is required"),
	expected_scope: z.array(z.string()).default([]),
	forbidden_scope: z.array(z.string()).default([]),
	max_risk: z.enum(["low", "medium", "high"]).default("high"),
	expected_type: z
		.enum(["feature", "bugfix", "refactor", "docs", "test", "chore", "config", "mixed"])
		.optional(),
	size_budget: z.number().int().positive().optional(),
	status: z.enum(["draft", "approved", "locked"]).default("draft"),
	approved_by: z.string().optional(),
	approved_at: z.string().datetime().optional(),
	created_at: z.string().datetime().optional(),
	updated_at: z.string().datetime().optional(),
});

export type Intent = z.infer<typeof IntentSchema>;

export const IntentLayerSchema = z.object({
	name: z.string().min(1),
	priority: z.number().int().min(0).default(0),
	intent: IntentSchema,
});

export type IntentLayer = z.infer<typeof IntentLayerSchema>;

export const LayeredIntentSchema = z.object({
	layers: z.array(IntentLayerSchema).min(1),
	merged_at: z.string().datetime().optional(),
});

export type LayeredIntent = z.infer<typeof LayeredIntentSchema>;
