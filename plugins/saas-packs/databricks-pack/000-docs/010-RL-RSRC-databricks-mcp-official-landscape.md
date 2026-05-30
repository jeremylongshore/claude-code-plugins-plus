# Databricks MCP Landscape — Engineering Decision Input

**Date:** 2026-05-27
**Author:** Research agent (Claude Code)
**Purpose:** Ground the build-vs-consume decision on `databricks-workspace-mcp@0.1.0` against what Databricks officially ships today.

---

## 1. Executive Summary

Databricks ships a three-path MCP architecture — **managed**, **custom**, and **external** — all in Public Preview as of 2026-05-22 (GCP shows GA on four of five managed servers; AWS and Azure are still Preview). The five **managed** servers cover the *data plane* exclusively: Genie (NL Q&A), Genie Space (per-space NL Q&A), Vector Search, **Databricks SQL**, and **Unity Catalog Functions**. There is **no managed MCP for the control plane** — clusters, jobs, pipelines/DLT, instance pools, external locations, storage credentials, SCIM/identity, streaming progress, or cluster events are not surfaced as MCP tools by any Databricks-published server. The **custom path** ships your MCP as a **Databricks App** (HTTP transport, name-prefixed `mcp-`, Python via `@mcp.tool()`); Databricks hosts it inside the workspace and brokers OAuth via the `databricks-mcp` PyPI helper, but **does not ship a pre-built control-plane MCP** — that work is left to the developer. The **external path** is a UC-Connection-backed proxy for *third-party* services (GitHub, Atlassian, Glean) and does **not** apply to Databricks-API workloads. Net: the proposed `databricks-workspace-mcp@0.1.0` fills a real, currently-unfilled gap; it is not duplicating an existing Databricks offering.

---

## 2. Managed MCP Server Catalog

All five servers ship from Databricks. Endpoints are workspace-scoped (`https://<workspace-hostname>/api/2.0/mcp/...`). Unity Catalog permissions are always enforced.

| Server | Endpoint Pattern | OAuth Scope | AWS Status | GCP Status | Azure Status | Tools Exposed | Use Case |
|---|---|---|---|---|---|---|---|
| **Genie** | `/api/2.0/mcp/genie` | `genie` | Beta | Beta | Beta | `genie_ask`, `genie_poll_response` | Async NL Q&A across all Genie Spaces + UC data, returns grounded answer with deep link. Read-only. |
| **Genie Space** | `/api/2.0/mcp/genie/{genie_space_id}` | `genie` | Public Preview | **GA** | Public Preview | (per-space tool surface; poll-based) | NL Q&A scoped to a single Genie Space. Read-only. No history. |
| **Vector Search** | `/api/2.0/mcp/vector-search/{catalog}/{schema}/{index_name}` | `vector-search` | Public Preview | **GA** | Public Preview | (index-scoped query tool) | Semantic search over Databricks-managed embedding indexes. |
| **Databricks SQL** | `/api/2.0/mcp/sql` | `sql` | Public Preview | **GA** | Public Preview | (SQL execution tool — poll-based for long queries) | AI-generated SQL execution. **Read AND write.** This is the workhorse that can hit any UC-permitted table including `system.*`. |
| **Unity Catalog Functions** | `/api/2.0/mcp/functions/{catalog}/{schema}/{function_name}` | `unity-catalog` | Public Preview | **GA** | Public Preview | (one tool per UC function in the namespace) | Run pre-defined UC functions. `system/ai` namespace exposes `python_exec` (built-in code interpreter). |

**Auth:** OAuth U2M (interactive, Claude Code), OAuth M2M (service principal), or PAT (managed + external only — **PAT not supported for custom MCPs on Databricks Apps**). Dynamic Client Registration is explicitly **not** supported.

**Discovery surface:** Workspace UI → **AI Gateway** → **MCPs** tab.

**Per-cloud parity:** AWS, GCP, Azure all expose the same five servers with identical endpoint shapes. GCP is furthest along (GA on four; Beta on Genie). AWS/Azure are still labeled Public Preview overall.

---

## 3. Custom MCP Architecture

**Hosting model:** Databricks hosts the custom MCP **inside the workspace as a Databricks App**. The MCP server is a Python HTTP service deployed via `databricks apps create mcp-<name>`. Endpoint becomes `https://<app-url>/mcp`.

**Constraints:**

- App name **must start with `mcp-`** to be recognized by AI Playground and Mosaic AI Agent Framework.
- HTTP-compatible transport required (streamable HTTP — not WebSocket, not SSE).
- Default port 8000, overridable via `app.yaml` env vars.
- PAT auth is **not supported** for custom MCPs (OAuth only).

**Framework:** Python with the `@mcp.tool()` decorator pattern (from the standard `mcp` PyPI package — Anthropic's reference MCP SDK). Databricks does **not** ship a proprietary MCP server SDK. The `databricks-mcp` PyPI package (from [databricks/databricks-ai-bridge](https://github.com/databricks/databricks-ai-bridge)) is a **client-side helper** for OAuth and resource discovery, *not* a server framework.

**Template:** [github.com/databricks/app-templates/tree/main/mcp-server-hello-world](https://github.com/databricks/app-templates/tree/main/mcp-server-hello-world) — `MCP Server - Hello World` under Compute → Apps → Create app → Agents category.

**Auth model for tools running inside the custom MCP:**

- **On-behalf-of-user:** `WorkspaceClient(credentials_strategy=ModelServingUserCredentials())` — agent passes the calling user's identity. UC permissions enforced as that user.
- **Service principal:** `WorkspaceClient(client_id=..., client_secret=...)` — runs as the app's SP.

**Discovery:** No registry API. Naming convention (`mcp-` prefix) + workspace visibility + Databricks Apps permissions.

**Secrets:** No first-class secrets management. Env vars in `app.yaml` or rely on workspace identity / OAuth tokens.

---

## 4. External MCP Architecture

**Definition:** Third-party MCP servers hosted **outside** Databricks (GitHub, Atlassian, Glean, or self-hosted), reached **through** a Databricks-managed proxy backed by a Unity Catalog HTTP connection.

**Endpoint pattern:** `https://<workspace-hostname>/api/2.0/mcp/external/{connection_name}`
Also: `https://<workspace-hostname>/api/2.0/unity-catalog/connections/{connection_name}/proxy[/<sub-path>]`

**Auth brokerage:** **Databricks brokers everything.** The client passes a `WorkspaceClient` to `databricks-mcp` / `databricks-langchain` / `databricks-openai`; the proxy handles OAuth token exchange and refresh to the third-party service. Tokens never leave the backend.

**Auth modes supported on the UC connection:**

- Shared principal: Bearer, OAuth M2M, OAuth U2M Shared
- Per-user: OAuth U2M Per User (individual identity, audit-friendly)

**Registration paths (four):**

1. **Managed OAuth** (recommended; Glean, GitHub, Atlassian today)
2. **Databricks Marketplace** (pre-curated integrations)
3. **Custom HTTP Connection** (manual; "Is mcp connection" checkbox)
4. **Dynamic Client Registration** (RFC 7591)

**Required privilege:** `CREATE CONNECTION` on the metastore. Region must support Model Serving.

**Status:** Public Preview as of 2026-05-15.

**Critically:** External MCP cannot directly modify Databricks workspace resources — it is read-only / service-specific by design. It is **not** a path for exposing Databricks APIs to agents.

---

## 5. Coverage Gap Analysis

The proposed `databricks-workspace-mcp@0.1.0` aims at control-plane and admin surfaces. Mapping requested coverage against what Databricks ships:

| Required Operation | Covered by Managed MCP? | Reachable via Databricks SQL MCP? | Reachable via UC Functions MCP? | Real Gap? |
|---|---|---|---|---|
| `clusters.list` | **No** | No (REST API, not SQL) | Only if wrapped in a UC function | **Yes — gap** |
| `clusters.get` | **No** | No | UC function wrapping REST possible | **Yes — gap** |
| `clusters.events` | **No** | No | Same as above | **Yes — gap** |
| `instance_pools.list` | **No** | No | UC function wrap possible | **Yes — gap** |
| `jobs.list` | **No** | No | Same | **Yes — gap** |
| `jobs.runs.list` | **No** | No | Same | **Yes — gap** |
| `pipelines.get` (DLT) | **No** | No | Same | **Yes — gap** |
| `pipelines.get_event_log` | **No** | Partial — event log is queryable via `event_log()` SQL TVF, so SQL MCP **can** reach it | Yes via UC function | **Partial** — SQL path works for event log, not for pipeline metadata |
| `system.billing.usage` SQL | **No (no dedicated billing MCP)** | **Yes** — SQL MCP can `SELECT * FROM system.billing.usage` if caller has UC SELECT | UC function wrap also viable | **No — covered by SQL MCP** |
| `system.streaming.query_progress` | **No** | **Yes — if** the table exists and is UC-readable (system table since Jan 2026 lakeflow GA) | UC function wrap | **No — covered by SQL MCP** |
| `external_locations.list` | **No** | No (REST API) | UC function wrap possible | **Yes — gap** |
| `storage_credentials.list` | **No** | No (REST API) | UC function wrap possible | **Yes — gap** |
| Cluster pool / workspace admin ops | **No** | No | UC function wrap possible but admin scope | **Yes — gap** |
| SCIM / identity / group sync | **No** | No | No (control-plane only) | **Yes — gap** |

**Pattern:** Databricks managed MCPs cover the **data plane** (read/write rows + run UC functions + semantic search + NL Q&A). They do **not** cover the **control plane** (clusters, jobs, pipelines, identity, infra config). The only workaround inside the managed surface is "wrap every REST call in a UC function" — which is feasible but inverts the architecture (every API call becomes a Python UC function the user has to author and maintain).

**`system.*` table reads are NOT a gap** — Databricks SQL MCP handles them. Anything that boils down to "SELECT FROM system.billing.usage" should consume the managed SQL MCP, not be re-implemented.

---

## 6. Architectural Recommendation

**Ship `databricks-workspace-mcp@0.1.0` as planned, with one scope adjustment.**

**Real gap confirmed:** The Databricks-published managed MCPs cover Genie, Vector Search, SQL, and UC Functions only. Control-plane operations (clusters, jobs, pipelines, instance pools, external locations, storage credentials, SCIM) are **not surfaced as MCP tools by any Databricks-published server today** and the docs give no roadmap signal that they will be. A third-party MCP that exposes the Databricks REST control plane is the only practical path.

**The "custom MCP via Databricks Apps" path is not a substitute** — it is the *delivery mechanism* a third party would use to ship such an MCP inside a customer's workspace. It does not pre-solve the problem; it just gives us a hosting target. (Bonus: shipping as a Databricks App means OAuth + UC perms enforcement come for free via `databricks-mcp` client helpers.)

**Recommended scope adjustments to the original `databricks-workspace-mcp@0.1.0` plan:**

1. **Drop `system.billing.usage` SQL proxy and `system.streaming.query_progress` from the MCP's tool surface.** These are pure SELECTs against `system.*` tables and the managed Databricks SQL MCP already does this with first-class OAuth + UC enforcement. Document the recommendation: "use Databricks SQL MCP for any `system.*` query." Re-implementing wastes effort and creates two ways to do the same thing.

2. **Keep clusters / jobs / pipelines / instance pools / external locations / storage credentials.** These are the actual gap. Use the Databricks Python SDK (`databricks-sdk`) inside the MCP server, expose one MCP tool per REST endpoint family.

3. **Ship two deployment modes from day one:**

- **Standalone:** runs anywhere (local dev box, CI, Claude Code on a laptop) authenticating via PAT or local OAuth profile. Maximum portability, minimum integration.
- **Databricks App:** ships as an `mcp-databricks-workspace` app. Picks up the workspace's OAuth identity, gets discovered by AI Playground and the Mosaic AI Agent Framework, leverages `databricks-mcp` for resource declaration when logged with an agent. This is the path for customers who want Anthropic-side Claude Code agents AND Databricks-side Mosaic agents to share one tool surface.

1. **Auth boundary:** for Claude Code as the calling client, the cleanest pattern is **Claude Code → MCP server (standalone or App) → Databricks workspace** using OAuth U2M with scoped tokens (`all-apis` for full control plane access; reduce to `unity-catalog` + custom scope if Databricks adds one later). Avoid passing user OAuth through to the workspace from Claude Code directly — every documented auth path goes through the MCP server's `WorkspaceClient`.

2. **Use `databricks-mcp` PyPI for client-side helpers only; build the server with the standard `mcp` reference SDK (Python).** Databricks does not ship a server-side framework; the standard MCP Python SDK + `@mcp.tool()` decorators + `databricks-sdk` for REST calls is the canonical stack and matches every official template.

**Net:** Epic 1 (`databricks-workspace-mcp@0.1.0` foundation) should ship — with `system.*` table queries dropped from scope and a note in the README pointing those use cases at the managed SQL MCP. Everything else in the original Epic 1 plan is a real, currently-unfilled gap.

---

## 7. Sources

### Databricks official docs (walked)

- [MCP on Databricks (AWS overview)](https://docs.databricks.com/aws/en/generative-ai/mcp/)
- [Managed MCP servers (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp)
- [Custom MCP servers (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/custom-mcp)
- [External MCP servers (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/external-mcp)
- [Connect clients to Databricks MCPs (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/connect-clients)
- [Use custom MCPs in agents (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/custom-mcp-usage)
- [Use external MCPs in agents (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/external-mcp-usage)
- [Managed MCP servers (GCP)](https://docs.databricks.com/gcp/en/generative-ai/mcp/managed-mcp)
- [Managed MCP servers (Azure)](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/mcp/managed-mcp)
- [Unity AI Gateway (AWS)](https://docs.databricks.com/aws/en/ai-gateway/)

### Supporting

- [databricks-mcp on PyPI](https://pypi.org/project/databricks-mcp/)
- [databricks/databricks-ai-bridge (GitHub)](https://github.com/databricks/databricks-ai-bridge)
- [databricks/app-templates — mcp-server-hello-world](https://github.com/databricks/app-templates/tree/main/mcp-server-hello-world)
- [Databricks January 2026 release notes (AWS)](https://docs.databricks.com/aws/en/release-notes/product/2026/january) — lakeflow system tables GA
- [Databricks April 2026 release notes (AWS)](https://docs.databricks.com/aws/en/release-notes/product/2026/april) — AI Gateway governance over MCP
- [Atlan: MCP Server for Databricks deployment types (2026)](https://atlan.com/know/mcp/mcp-server-for-databricks/) — third-party landscape view
- [Truto: Best MCP Server for Databricks 2026](https://truto.one/blog/best-mcp-server-for-databricks-in-2026-give-ai-agents-secure-access-to-lakehouse-data/) — third-party landscape view
- [JustTryAI/databricks-mcp-server (GitHub)](https://github.com/JustTryAI/databricks-mcp-server) — existing community MCP for REST APIs
- [RafaelCartenet/mcp-databricks-server (GitHub)](https://github.com/RafaelCartenet/mcp-databricks-server) — existing community MCP for UC metadata
