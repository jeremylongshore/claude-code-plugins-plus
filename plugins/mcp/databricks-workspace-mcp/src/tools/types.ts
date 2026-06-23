/**
 * Shared tool-definition contract. Each control-plane tool is a self-describing record:
 * a name, an agent-facing description, a zod input schema (also used to generate the MCP
 * JSON Schema), the rate-limit family it belongs to, and a handler that takes the REST client
 * plus validated args and returns plain data.
 */

import type { z } from "zod";
import type { DatabricksClient } from "../client.js";

export interface ToolDef<S extends z.ZodTypeAny = z.ZodTypeAny> {
  name: string;
  description: string;
  schema: S;
  family: string;
  handler: (client: DatabricksClient, args: z.infer<S>) => Promise<unknown>;
}

/** Helper that preserves the zod inference while typing the def. */
export function defineTool<S extends z.ZodTypeAny>(def: ToolDef<S>): ToolDef<S> {
  return def;
}
