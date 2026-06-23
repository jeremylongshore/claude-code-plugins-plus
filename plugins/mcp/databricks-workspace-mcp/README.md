<h1 align="center">databricks-workspace-mcp</h1>

<p align="center">
  An MCP server for the Databricks <strong>control plane</strong> — cluster forensics, instance-pool
  waste, DLT pipeline event logs, and Unity Catalog storage governance.<br>
  The 8 read-only tools no managed Databricks MCP exposes. Pairs with the managed SQL MCP for
  <code>system.*</code> reads.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-10b981?style=flat-square" alt="License: MIT">
  <img src="https://img.shields.io/badge/MCP-stdio%20%2B%20HTTP-8b5cf6?style=flat-square" alt="MCP stdio + HTTP">
  <img src="https://img.shields.io/badge/access-read--only-0ea5e9?style=flat-square" alt="read-only">
</p>

---

## Why this server exists

Databricks ships five managed MCP servers (Genie, Genie Space, Vector Search, Databricks SQL, Unity
Catalog Functions) — **all data plane**. None of them expose live control-plane state: cluster event
timelines, instance-pool idle stats, DLT pipeline event logs, or the Unity Catalog external-location /
storage-credential wiring. That's the gap this server fills.

The split is deliberate. A consuming skill calls **this** server for typed control-plane state, and the
**managed Databricks SQL MCP** (`/api/2.0/mcp/sql`) for everything in `system.*` (billing, audit,
information_schema) — OAuth- and UC-governed on Databricks' side. Two MCPs, one diagnostic picture; no
skill should ever have to shell out to the `databricks` CLI to fill a gap.

Everything here is **read-only** — no create/edit/terminate. It inventories and diagnoses; it does not
mutate your workspace.

## Tool surface (8)

| Tool | Endpoint | What it does |
|---|---|---|
| `clusters_list` | `GET /api/2.0/clusters/list` | Inventory all clusters — state, autotermination, autoscale, node types, creator. Find never-auto-terminating clusters. |
| `clusters_get` | `GET /api/2.0/clusters/get` | Full config + state of one cluster — DBR version, Photon vs standard, autoscale bounds, `state_message`. |
| `clusters_events` | `POST /api/2.0/clusters/events` | The event timeline (CREATING → STARTING → RUNNING → RESIZING → TERMINATING, init-script events). THE source for cold-start / launch-failure forensics. |
| `instance_pools_list` | `GET /api/2.0/instance-pools/list` | All instance pools with live used/idle/pending stats — find pools holding warm idle VMs that bill cloud compute. |
| `pipelines_get` | `GET /api/2.0/pipelines/{id}` | A DLT pipeline's definition + latest state — edition, channel, serverless flag, continuous vs triggered, `latest_updates`. |
| `pipelines_get_event_log` | `GET /api/2.0/pipelines/{id}/events` | Page the structured event log (flow/update/maintenance progress, data-quality expectations, backpressure). Supports a filter expression. |
| `external_locations_list` | `GET /api/2.1/unity-catalog/external-locations` | UC external locations — each binds a storage URL (s3/abfss/gs) to a credential, with owner + read-only + binding mode. |
| `storage_credentials_list` | `GET /api/2.1/unity-catalog/storage-credentials` | UC storage credentials — the cloud-IAM principals UC assumes for storage access. Trace the IAM wiring behind external locations. |

## Auth — three flows

Resolution is lazy: the server starts and `tools/list` succeeds even with no credentials, so a consuming
skill can detect "MCP present but unauthenticated" and degrade cleanly. Set `DATABRICKS_HOST` plus **one**
credential:

| Flow | Env | Mode |
|---|---|---|
| **PAT** | `DATABRICKS_TOKEN` | CLI only (not supported in App mode) |
| **OAuth U2M** | `DATABRICKS_OAUTH_TOKEN` (from `databricks auth login`) | CLI |
| **OAuth M2M** | `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET` | CLI **and** the only flow accepted in Databricks App mode |

See [`.env.example`](./.env.example) for the full template.

## Install

### A) Claude Code / any `.mcp.json` consumer (stdio)

```jsonc
{
  "mcpServers": {
    "databricks-workspace": {
      "command": "npx",
      "args": ["-y", "@intentsolutions/databricks-workspace-mcp"],
      "env": {
        "DATABRICKS_HOST": "https://dbc-xxxx.cloud.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

### B) Databricks App (HTTP, OAuth M2M)

The same codebase serves over Streamable HTTP for deployment as a custom Databricks App, which makes the
control-plane tools discoverable by the Mosaic AI Agent Framework and the AI Playground in addition to
Claude Code. PAT is unsupported in this mode — use a service principal (`DATABRICKS_CLIENT_ID` /
`DATABRICKS_CLIENT_SECRET`).

## Develop

```bash
pnpm install
pnpm build        # tsc → dist/, chmods dist/index.js executable
pnpm check        # typecheck + vitest (run against recorded fixtures, no live workspace)
pnpm dev          # tsc --watch
```

Tests run entirely against recorded JSON fixtures in `tests/fixtures/` — no Databricks workspace or
credentials required to run the suite.

## License

MIT © [Jeremy Longshore](https://intentsolutions.io) / Intent Solutions
