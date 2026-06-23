/**
 * Cluster lifecycle tools (013-AT-ADEC T3 — KEEP). Powers cluster-forensics + the idle-cluster
 * line of cost-leak-hunter. The managed SQL MCP cannot reach `clusters.events`; this is exactly
 * the control-plane gap this server exists to fill.
 */

import { z } from "zod";
import { defineTool } from "./types.js";

const FAMILY = "clusters";

export const clustersList = defineTool({
  name: "clusters_list",
  description:
    "List all clusters in the workspace with their config and current state (RUNNING/TERMINATED/PENDING), autotermination, autoscale, node types, and creator. Use to inventory compute, find never-auto-terminating clusters, or pick All-Purpose clusters running scheduled jobs. Read-only. GET /api/2.0/clusters/list.",
  schema: z.object({}).strict(),
  family: FAMILY,
  handler: (client) => client.get("/api/2.0/clusters/list", FAMILY),
});

export const clustersGet = defineTool({
  name: "clusters_get",
  description:
    "Get the full configuration and current state of one cluster by id — autotermination_minutes, autoscale bounds, spark_version (DBR), node_type_id, runtime_engine (Photon vs standard), and state_message. Use for single-cluster forensics. Read-only. GET /api/2.0/clusters/get.",
  schema: z.object({ cluster_id: z.string().min(1).describe("The cluster id, e.g. 0123-456789-abcde123") }).strict(),
  family: FAMILY,
  handler: (client, args) => client.get("/api/2.0/clusters/get", FAMILY, { cluster_id: args.cluster_id }),
});

export const clustersEvents = defineTool({
  name: "clusters_events",
  description:
    "Retrieve the event timeline for a cluster (CREATING, STARTING, RUNNING, RESIZING, UPSCALE_COMPLETED, DRIVER_HEALTHY, TERMINATING, INIT_SCRIPTS_*, etc.) with timestamps and details. This is THE source for cold-start / launch-failure / resize forensics — managed MCP has no equivalent. Read-only. POST /api/2.0/clusters/events.",
  schema: z
    .object({
      cluster_id: z.string().min(1).describe("The cluster id to fetch events for"),
      start_time: z.number().int().optional().describe("Epoch millis lower bound (inclusive)"),
      end_time: z.number().int().optional().describe("Epoch millis upper bound (inclusive)"),
      event_types: z
        .array(z.string())
        .optional()
        .describe("Filter to specific event types, e.g. ['STARTING','TERMINATING','INIT_SCRIPTS_FINISHED']"),
      order: z.enum(["ASC", "DESC"]).optional().describe("Sort order by timestamp (default DESC)"),
      limit: z.number().int().min(1).max(500).optional().describe("Max events per page (default 50)"),
      offset: z.number().int().min(0).optional().describe("Page offset"),
    })
    .strict(),
  family: FAMILY,
  handler: (client, args) =>
    client.post("/api/2.0/clusters/events", FAMILY, {
      cluster_id: args.cluster_id,
      start_time: args.start_time,
      end_time: args.end_time,
      event_types: args.event_types,
      order: args.order,
      limit: args.limit,
      offset: args.offset,
    }),
});

export const clusterTools = [clustersList, clustersGet, clustersEvents];
