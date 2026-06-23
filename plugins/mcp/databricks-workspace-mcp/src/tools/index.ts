/**
 * The full control-plane tool set this server exposes — 8 tools across the 6 endpoint families
 * (clusters · instance pools · pipelines · UC external-locations · UC storage-credentials) that
 * no managed Databricks MCP serves (013-AT-ADEC). Everything is read-only.
 */

import { clusterTools } from "./clusters.js";
import { instancePoolTools } from "./instance-pools.js";
import { pipelineTools } from "./pipelines.js";
import { unityCatalogTools } from "./unity-catalog.js";
import type { ToolDef } from "./types.js";

export const allTools: ToolDef[] = [
  ...clusterTools,
  ...instancePoolTools,
  ...pipelineTools,
  ...unityCatalogTools,
];

export const toolsByName: ReadonlyMap<string, ToolDef> = new Map(
  allTools.map((t) => [t.name, t]),
);

export type { ToolDef } from "./types.js";
