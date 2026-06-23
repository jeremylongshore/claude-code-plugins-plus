/**
 * DLT pipeline tools (013-AT-ADEC T7 — KEEP). The pipeline event log is the diagnostic spine for
 * streaming-guardian (DLT health) and the DLT-tier line of cost-leak-hunter. Managed MCP exposes
 * `system.*` reads but not the pipeline definition or its structured event log.
 */

import { z } from "zod";
import { defineTool } from "./types.js";

const FAMILY = "pipelines";

export const pipelinesGet = defineTool({
  name: "pipelines_get",
  description:
    "Get a DLT pipeline's definition and latest state — name, edition (CORE/PRO/ADVANCED), channel, photon flag, serverless flag, clusters/autoscale config, continuous vs triggered, and latest_updates. Use to read the cost-relevant tier (edition + serverless) and the configured compute. Read-only. GET /api/2.0/pipelines/{pipeline_id}.",
  schema: z
    .object({ pipeline_id: z.string().min(1).describe("The DLT pipeline id (UUID)") })
    .strict(),
  family: FAMILY,
  handler: (client, args) => client.get(`/api/2.0/pipelines/${encodeURIComponent(args.pipeline_id)}`, FAMILY),
});

export const pipelinesGetEventLog = defineTool({
  name: "pipelines_get_event_log",
  description:
    "Page through a DLT pipeline's structured event log (flow_progress, update_progress, maintenance_progress, user_action, cluster events) with timestamps, levels, and details — including data-quality expectation metrics and backpressure signals. Use for streaming/DLT health forensics. Read-only. GET /api/2.0/pipelines/{pipeline_id}/events.",
  schema: z
    .object({
      pipeline_id: z.string().min(1).describe("The DLT pipeline id (UUID)"),
      max_results: z.number().int().min(1).max(250).optional().describe("Page size (default 25)"),
      order: z.enum(["ASC", "DESC"]).optional().describe("Sort by timestamp (default DESC)"),
      filter: z
        .string()
        .optional()
        .describe(
          "Optional event-log filter expression, e.g. \"level = 'ERROR'\" or \"timestamp > '2026-06-01T00:00:00Z'\"",
        ),
      page_token: z.string().optional().describe("Opaque token from a prior response's next_page_token"),
    })
    .strict(),
  family: FAMILY,
  handler: (client, args) =>
    client.get(`/api/2.0/pipelines/${encodeURIComponent(args.pipeline_id)}/events`, FAMILY, {
      max_results: args.max_results,
      order_by: args.order ? `timestamp ${args.order.toLowerCase()}` : undefined,
      filter: args.filter,
      page_token: args.page_token,
    }),
});

export const pipelineTools = [pipelinesGet, pipelinesGetEventLog];
