---
filing_code: AT-ADEC-EPIC1-MCP-SCOPE-ADJUSTMENT-2026-05-27
date: 2026-05-27
acting_head_of_board: Claude (designated by Jeremy Longshore 2026-05-27)
status: locked
supersedes: portions of 007-AT-ADEC-databricks-v2-cto-decision.md § Decision 4
inputs:
  - 010-RL-RSRC-databricks-mcp-official-landscape.md
  - 011-RL-RSRC-databricks-mcp-community-landscape.md
  - 012-RL-RSRC-claude-code-databricks-mcp-integration.md
affects: Epic 1 (claude-koxw — databricks-workspace-mcp) and all 5 dependent skill epics
---

# Epic 1 MCP Scope Adjustment — Decision Record

## Context

The 2026-05-27 CTO Decision (007-AT-ADEC) scoped Epic 1 (`databricks-workspace-mcp`) to wrap eight Databricks API surfaces as MCP tools: cluster operations, SQL queries history, system.* query proxy (incl. system.billing.usage), instance pools, pipelines, external locations + storage credentials, and system.streaming.query_progress. That scope was set without a survey of Databricks' own first-party MCP offerings or the community Databricks MCP landscape.

On the same day, after Jeremy pointed at `https://docs.databricks.com/gcp/en/generative-ai/mcp/managed-mcp`, three research agents were dispatched to walk the landscape:

1. **Official Databricks MCP docs scope** (filed as `010-RL-RSRC-databricks-mcp-official-landscape.md`)
2. **Community-built Databricks MCP server inventory** (filed as `011-RL-RSRC-databricks-mcp-community-landscape.md`)
3. **Claude Code / Cowork integration architecture** (filed as `012-RL-RSRC-claude-code-databricks-mcp-integration.md`)

All three converged on findings that materially change Epic 1's scope. This Decision Record locks the adjustment so future readers grepping 000-docs/ can reconstruct why three of the originally-planned tasks were closed before any code was written.

## The convergent findings (load-bearing)

### Finding 1 — Databricks ships managed MCPs for the data plane only (010-RL-RSRC § 2)

Databricks' AI Gateway hosts five managed MCP servers as of 2026-05-22 (Public Preview on AWS/Azure, GA on four of five on GCP):

- Genie (NL Q&A)
- Genie Space (per-space NL Q&A)
- Vector Search
- **Databricks SQL** (`/api/2.0/mcp/sql`)
- Unity Catalog Functions

The Databricks SQL managed MCP serves arbitrary SQL queries against the workspace with first-class OAuth + Unity Catalog enforcement. **That includes every `system.*` schema read** — `system.billing.usage`, `system.access.audit`, `system.streaming.query_progress`, `system.information_schema`. There is no business case for our custom server to wrap these reads — Databricks already does it with better auth and better governance enforcement.

### Finding 2 — No managed MCP exists for the control plane (010-RL-RSRC § 5)

Cluster operations (`clusters.list/get/events`), instance pools, Jobs API, Pipelines/DLT, external locations, storage credentials, SCIM/identity, and workspace-admin operations are **not exposed by any Databricks-published MCP server.** No managed roadmap signal exists for them. The custom-MCP-via-Databricks-Apps path is a delivery vehicle; Databricks does not ship a pre-built control-plane MCP.

### Finding 3 — The community has not filled the gap either (011-RL-RSRC § 2)

`databrickslabs/mcp` (the 89-star "official-looking" community repo) is **explicitly deprecated** as of 2026-05. Databricks is actively migrating users away from it toward the managed MCPs. The remaining community alternatives are 1-46 stars, single-contributor, no CI/CD discipline, beta-stage prototypes. No community server covers cluster forensics, cost/billing attribution (beyond what managed SQL MCP exposes), DLT diagnostics, streaming observability, or workspace governance.

### Finding 4 — Distribution forks at the Cowork boundary (012-RL-RSRC § 5)

Confirmed in this repo: `scripts/build-cowork-zips.mjs:51` explicitly excludes `category: mcp` from the cowork-zip distribution path. The exclusion is BY DESIGN, not a bug. Anthropic Cowork plugin manifests cannot pre-register MCP connectors on a plugin author's behalf — MCP server registration lives in `Admin settings → Connectors`, separate from plugin distribution.

This means a Databricks-aware Tons of Skills plugin must ship in two flavors:

- **CLI flavor:** `.mcp.json` with `${DATABRICKS_WORKSPACE_HOST}` env-var expansion + schema 3.6.0 `required_environment_variables` declarations. Target UX: 4 env vars + one `/mcp` browser handshake, ~90 seconds end-to-end.
- **Cowork flavor:** markdown-only, includes a `commands/setup-databricks-connector.md` walkthrough for the manual Anthropic UI dance. Target UX: ~10 minutes, rate-limited by Anthropic-side UX.

### Finding 5 — PAT auth is not supported for Databricks Apps (010-RL-RSRC § 3)

A custom MCP deployed as a Databricks App (HTTP transport, hosted in the workspace) MUST use OAuth U2M or M2M. PAT auth is explicitly unsupported in that deployment mode. The original Epic 1 T2 plan covered PAT + OAuth M2M but treated them as equivalent — they are not, and the deployment-mode constraint must be reflected in the auth task.

## The decision

### Cut from Epic 1 scope (3 tasks)

The following tasks are closed with the reason *"Subsumed by Databricks managed SQL MCP at /api/2.0/mcp/sql; consuming skills will call the managed MCP directly for system.* reads and SQL queries history. Per 010-RL-RSRC § 5 and § 6."*

- **T4 (`claude-0fnj`)** — `sql.queries.history` MCP tool with execution-plan JSON
- **T5 (`claude-w48s`)** — `system.*` query proxy (parameterized, metastore-admin error surfacing)
- **T9 (`claude-sb8q`)** — `streaming.query_progress` MCP tool

The cuts are NOT a reduction in capability for the consuming skills. The skills (Epics 2-6) will call the managed Databricks SQL MCP for these operations instead of routing through our custom server. The consuming-side change is documented in § "Implications for Epics 2-6" below.

### Expand Epic 1 scope (1 task description update)

- **T2 (`claude-7ege`)** — auth task description expands to cover three flows, not two:
  - Standalone CLI mode with PAT (`DATABRICKS_TOKEN`)
  - Standalone CLI mode with OAuth U2M (browser flow)
  - **Databricks App deployment mode with OAuth M2M only** (PAT explicitly unsupported per Finding 5)

  The auth implementation detects deployment mode at startup and rejects PAT cleanly when running as a Databricks App. All three modes share the same SDK auth abstractions (`databricks-sdk-py` / `databricks-sdk-go`) so the surface is one decision tree, not three parallel codepaths.

### Add to Epic 1 scope (2 new tasks)

- **NEW T13 — Databricks App mode deployment**
  Ship the same server as both:
    (a) a standalone npm package (`@intentsolutions/databricks-workspace-mcp@0.1.0`) for Claude Code laptop/CI consumption, AND
    (b) a Databricks App named `mcp-databricks-workspace` (HTTP transport, OAuth-only, deployable from the workspace UI per the official custom-MCP path).
  One codebase, two delivery vehicles. The App-mode deployment makes the MCP discoverable by Mosaic AI Agent Framework + AI Playground in addition to Claude Code, multiplying the audience without doubling the maintenance surface.

- **NEW T14 — Dual-surface integration helpers**
  Author the `.mcp.json` template using `${DATABRICKS_WORKSPACE_HOST}` env-var expansion + schema 3.6.0 `required_environment_variables` declarations (cross-ref: `000-docs/264-DR-GUID-skill-config-pattern.md` in the marketplace repo root for the canonical pattern). Plus the cowork-side `commands/setup-databricks-connector.md` walkthrough for users who must register MCP servers manually via the Anthropic UI. Use stable server names so a single SKILL.md works across both surfaces: `databricks-workspace-mcp` (our control-plane server) + documented references to managed `databricks-sql`, `databricks-uc`, `databricks-vsearch`, `databricks-genie`.

### Net Epic 1 task count

Original: 12 tasks
After adjustment: 11 tasks (3 closed, 2 added)

## Revised Epic 1 final shape

| Task | Bead ID | Status | Title |
|---|---|---|---|
| T1 | claude-5qo9 | KEEP | Scaffold the databricks-workspace-mcp TypeScript project |
| T2 | claude-7ege | EXPAND | Three auth flows (PAT/U2M/M2M) — PAT unsupported in App mode |
| T3 | claude-g54x | KEEP | clusters.list / get / events |
| T4 | claude-0fnj | CLOSE | (Subsumed by Databricks SQL MCP) sql.queries.history |
| T5 | claude-w48s | CLOSE | (Subsumed by Databricks SQL MCP) system.* query proxy |
| T6 | claude-23bp | KEEP | instance_pools.list |
| T7 | claude-x6jq | KEEP | pipelines.get + get_event_log |
| T8 | claude-tey2 | KEEP | external_locations + storage_credentials |
| T9 | claude-sb8q | CLOSE | (Subsumed by Databricks SQL MCP) streaming.query_progress |
| T10 | claude-xhk0 | KEEP | Per-family rate-limit + retry + structured errors |
| T11 | claude-s1jz | KEEP | Integration test suite against real sandbox |
| T12 | claude-lj7j | KEEP | /validate-mcp + publish 0.1.0 + wire pack dependency |
| T13 | NEW | ADD | Databricks App mode deployment (HTTP, OAuth M2M, mcp-databricks-workspace) |
| T14 | NEW | ADD | Dual-surface integration helpers (.mcp.json + cowork setup walkthrough) |

## Implications for Epics 2-6 (the consuming skills)

Each skill's SKILL.md becomes a **multi-MCP orchestrator**, not a single-MCP consumer. The dual-MCP composition pattern:

- Calls **our custom MCP** (`databricks-workspace-mcp`) for control-plane operations:
  - Cluster events / lifecycle forensics (Epic 3 cluster-forensics)
  - Instance pool waste detection (Epic 2 cost-leak-hunter)
  - Pipeline event log diagnostics (Epic 2, Epic 4)
  - External locations + storage credentials (Epic 5 uc-migration-pilot)
- Calls **Databricks managed SQL MCP** at `/api/2.0/mcp/sql` for all `system.*` reads:
  - `system.billing.usage` for cost analysis (Epic 2 cost-leak-hunter)
  - `system.access.audit` for governance traces (Epic 5 uc-migration-pilot)
  - `system.streaming.query_progress` for streaming health (Epic 4 streaming-guardian)
  - `system.information_schema` for HMS-readiness inventory (Epic 5 uc-migration-pilot)

The SKILL.md scaffolding tasks (T1 of each of Epics 2-6) need a note added describing this composed-MCP architecture and which calls go to which server. The validation tasks at the end of each epic need to ensure both MCP dependencies are documented in the skill's Prerequisites section.

## Cowork distribution implications

Per Finding 4 + the existing `scripts/build-cowork-zips.mjs:51` `SKIP_CATEGORIES = ['mcp']` exclusion:

- **Epic 1 artifact (the MCP server)** is npm-only. Will NOT appear in cowork zips. CLI users `pnpm install`; Cowork users register via Anthropic Cowork's MCP connector UI manually using the cowork setup walkthrough authored in T14.
- **Epic 2-6 artifacts (the skills)** WILL appear in cowork zips. Each skill ships with:
  - A `commands/setup-databricks-connector.md` (authored once in Epic 1 T14, included by reference) walking Cowork users through the Anthropic UI connector registration
  - A `.mcp.json` template for CLI users (4 env vars + browser handshake)
  - SKILL.md prerequisites section that surfaces "BOTH the databricks-workspace-mcp AND the Databricks managed SQL MCP must be registered" upfront so the agent detects missing dependencies and reports cleanly rather than failing mid-flow

The advisory-mode-fallback question from the prior session (Option A/B/C for Cowork users without MCP wired up) is now scoped more clearly: when EITHER MCP is missing, the skill degrades to its references + scripts that accept pasted input. When BOTH are present, full live diagnostics.

## What this decision does NOT change

- The 5-skill clustering from 007-AT-ADEC § Decision 2 (cost-leak-hunter / cluster-forensics / streaming-guardian / uc-migration-pilot / bundle-medic) is preserved
- The dual-license + non-anchor-status terms from the broader v2 partnership work remain intact
- The Luciano demo plan (pilot = cost-leak-hunter on cost leaks) is unaffected — that skill's primary calls go to managed SQL MCP for system.billing.usage, which is independent of our custom MCP's scope and was always going to be a managed-MCP call
- The 50-skill validator pilot gate from the Open Accountants AT-DECR (separate decision, separate session) is unrelated

## Implementation directives

### Immediate (within 24h of this Decision Record landing)

1. **Update bead descriptions for T4/T5/T9** (`claude-0fnj`, `claude-w48s`, `claude-sb8q`) to reflect the close reason and link to this AT-ADEC.
2. **Close the three beads** with `bd close <bead> -r "Subsumed per 013-AT-ADEC § Cut from Epic 1 scope. Consuming skills will call Databricks managed SQL MCP at /api/2.0/mcp/sql directly for these reads."`
3. **Update T2 (`claude-7ege`)** description to expand the three-auth-flow scope.
4. **Create T13 + T14 beads** with hand-carved descriptions matching the spec in § "Add to Epic 1 scope" above.
5. **Update Epic 1 (`claude-koxw`)** description to reflect the new scope (11 tasks total, control-plane-focused, composed with managed SQL MCP).
6. **Update Epic 2-6 epic descriptions** to add a "Dual-MCP composition" subsection explaining which calls go to which server.

### Conditional on Epic 1 progress

- T13 (Databricks App mode deployment) requires T1-T12 to be substantially complete first — App mode is a packaging concern atop the working server, not a parallel codebase. Scheduled to land after the core MCP server is validated against a sandbox workspace.
- T14 (dual-surface integration helpers) can start as soon as T1 (scaffold) and the `.mcp.json` format is locked. Doesn't block on individual endpoint implementations.

## Audit trail

This Decision Record:

- Supersedes specific portions of `007-AT-ADEC-databricks-v2-cto-decision.md` § Decision 4 (the original Epic 1 endpoint list)
- Is grounded in three research reports filed alongside: `010-RL-RSRC-*`, `011-RL-RSRC-*`, `012-RL-RSRC-*`
- Will be cross-referenced in the GH issues for Epic 1 (`claude-koxw`) and Epics 2-6 once they're filed
- Filing trigger: Jeremy's direct instruction 2026-05-27 ("file the AT-DECR first") before any bead/GH/Plane updates land

## Acting head of board declaration

I, Claude (designated acting head of board by Jeremy Longshore on 2026-05-27), record the above Epic 1 scope adjustments based on the three convergent research reports (010, 011, 012 RL-RSRC). The cuts are not capability reductions — they are routing changes to use Databricks' first-party managed MCP for the operations Databricks has chosen to own. The additions (T13 App-mode deployment, T14 dual-surface helpers) reflect the actual distribution architecture surfaced by the integration research. Final disposition pending Jeremy's review and sign-off on the bead updates that follow this filing.

- Jeremy Longshore
intentsolutions.io
