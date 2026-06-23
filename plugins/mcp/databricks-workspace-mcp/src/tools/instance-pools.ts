/**
 * Instance pool tools (013-AT-ADEC T6 — KEEP). Idle-pool waste is one of the cost-leak-hunter
 * pillars (D09): pools hold warm VMs at `min_idle_instances` you pay the cloud provider for even
 * when nothing schedules onto them. Managed MCP does not expose pool config.
 */

import { z } from "zod";
import { defineTool } from "./types.js";

const FAMILY = "instance_pools";

export const instancePoolsList = defineTool({
  name: "instance_pools_list",
  description:
    "List all instance pools with their config and live stats — min_idle_instances, max_capacity, node_type_id, idle_instance_autotermination_minutes, and stats (used/idle/pending counts). Use to find pools holding warm idle VMs (min_idle_instances > 0 with low utilization) that bill the underlying cloud compute. Read-only. GET /api/2.0/instance-pools/list.",
  schema: z.object({}).strict(),
  family: FAMILY,
  handler: (client) => client.get("/api/2.0/instance-pools/list", FAMILY),
});

export const instancePoolTools = [instancePoolsList];
