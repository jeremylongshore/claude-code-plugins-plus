# Databricks Skill Pack

**v2.0.0** — 5 live-detection skills for the Databricks Lakehouse Platform, backed by the `databricks-workspace-mcp` server. The rebuild is live: where v1 shipped 24 documentation-style skills, v2 ships 5 skills that **run** against your own workspace — real `system.*` reads, real cluster events, real Delta/streaming/bundle diagnostics.

> [!NOTE]
> **This is the v2 rebuild.** The 24 v1 documentation skills have been removed. If you had
> any `databricks-*` v1 skill in your `CLAUDE.md`, see **[Migration: v1 → v2](#migration-v1--v2)**
> for where each one went. Same install slug — no rename.

## Installation

```bash
/plugin install databricks-pack@claude-code-plugins-plus
```

The pack ships a `.mcp.json` that auto-launches the control-plane MCP server via
`npx -y @intentsolutions/databricks-workspace-mcp` ([npm](https://www.npmjs.com/package/@intentsolutions/databricks-workspace-mcp))
— no separate install step. It composes with the Databricks managed SQL MCP for `system.*`
reads; each skill degrades to **advisory mode** (works on pasted input) when an MCP is
unavailable. Each skill's `## Prerequisites` lists exactly what it needs.

## The 5 skills

| Skill | What it does (live) |
|-------|---------------------|
| `databricks-cost-leak-hunter` | `$X/month wasted` audit from your own `system.billing.usage` — idle clusters, All-Purpose-vs-Jobs, instance-pool waste, DLT tier, tag-based chargeback |
| `databricks-cluster-forensics` | Cold-start / launch-failure / Photon-fallback / DBR-upgrade triage from live cluster events |
| `databricks-uc-migration-pilot` | Hive-Metastore → Unity Catalog readiness + IAM/SCIM + access tracing (HMS delist deadline) |
| `databricks-streaming-guardian` | Delta + Liquid Clustering + Structured Streaming + Auto Loader + DLT health, with a PreToolUse guard on destructive ops against streamed-from tables |
| `databricks-bundle-medic` | Asset Bundles deploy diagnostics (tfstate EOF, GRANT-ordering) + CMK rotation + PrivateLink cost audit, with two deploy hooks |

## Key APIs Covered

| API | Endpoints |
|-----|-----------|
| Jobs API 2.1 | `POST /api/2.1/jobs/create`, `runs/submit`, `run-now` |
| Clusters API 2.0 | `create`, `list`, `start`, `delete`, `events` |
| SQL Statement API | `execute-statement` |
| Unity Catalog | `catalogs`, `schemas`, `tables`, `grants` |
| DBFS / Files API | `put`, `get`, `list` |
| Secrets API | `create-scope`, `put-secret`, `list-acls` |
| SCIM API | `groups`, `users`, `service-principals` |
| Model Serving | `serving-endpoints/create`, `query` |

## Usage

Skills trigger automatically on Databricks topics:

- "Why is my Databricks bill so high?" -- `databricks-cost-leak-hunter`
- "My cluster won't start / NPIP_TUNNEL_SETUP_FAILURE" -- `databricks-cluster-forensics`
- "Migrate Hive Metastore to Unity Catalog" -- `databricks-uc-migration-pilot`
- "ConcurrentAppendException / my stream broke after VACUUM" -- `databricks-streaming-guardian`
- "unexpected EOF reading terraform.tfstate / rotate our CMK" -- `databricks-bundle-medic`

## Architecture

### Why two MCP servers, not one

The v2 rebuild ships with a deliberate split across **two** MCP servers, not a single shared one. Common question on contributor PRs — answering it once at the top so future readers don't have to re-derive it.

- **Databricks managed SQL MCP** — serves `system.*` reads (cost data, query history, streaming progress). Operated by Databricks; we consume it.
- **Custom workspace MCP** — serves cluster events, instance pools, pipeline event logs, external locations, storage credentials. Operated by this pack.

The two authenticate independently. Losing access to one does not disable the other; `cost-leak-hunter` (SQL MCP) and `cluster-forensics` (workspace MCP) fail independently when their respective MCP is unavailable. Single skills can be installed without pulling in the other MCP's dependency surface.

Full scope-boundary rationale — including the 8 → 6 endpoint cut and the auth-flow decisions — is in [`000-docs/013-AT-ADEC-epic1-mcp-scope-adjustment.md`](000-docs/013-AT-ADEC-epic1-mcp-scope-adjustment.md). Reference document for any "why is this skill not pulling X?" question.

Thanks to [@Gingiris-1031](https://github.com/Gingiris-1031) ([#795](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/795)) for surfacing the isolation-story framing that made this section necessary.

## Migration: v1 → v2

`databricks-pack@2.0.0` is a ground-up rebuild. The 24 v1 skills described Databricks ops;
the 5 v2 skills **run** them — live detection against your own workspace via a shared
`databricks-workspace-mcp` server (control plane) composed with the Databricks managed SQL
MCP (`system.*` reads). Rationale: [`000-docs/007-AT-ADEC-databricks-v2-cto-decision.md`](000-docs/007-AT-ADEC-databricks-v2-cto-decision.md)
and [`000-docs/013-AT-ADEC-epic1-mcp-scope-adjustment.md`](000-docs/013-AT-ADEC-epic1-mcp-scope-adjustment.md).

**Status:** `2.0.0` is **live** — the 5 skills + the `databricks-workspace-mcp` server
([npm](https://www.npmjs.com/package/@intentsolutions/databricks-workspace-mcp)) ship now,
and the 24 v1 skills have been removed. The map below records where each v1 skill's coverage
landed.

### Where each v1 skill goes

| v1 skill | v2 destination |
|----------|----------------|
| `databricks-cost-tuning` | `databricks-cost-leak-hunter` |
| `databricks-performance-tuning` | `databricks-cost-leak-hunter` + `databricks-cluster-forensics` |
| `databricks-incident-runbook` | `databricks-cluster-forensics` + `databricks-streaming-guardian` |
| `databricks-observability` | `databricks-streaming-guardian` |
| `databricks-upgrade-migration` | `databricks-cluster-forensics` (DBR-upgrade triage) |
| `databricks-debug-bundle` · `databricks-deploy-integration` · `databricks-local-dev-loop` · `databricks-ci-integration` | `databricks-bundle-medic` |
| `databricks-migration-deep-dive` · `databricks-multi-env-setup` · `databricks-enterprise-rbac` | `databricks-uc-migration-pilot` |
| `databricks-security-basics` | `databricks-uc-migration-pilot` + `databricks-bundle-medic` (identity/secrets) |
| `databricks-hello-world` · `databricks-install-auth` · `databricks-sdk-patterns` · `databricks-core-workflow-a` · `databricks-core-workflow-b` · `databricks-common-errors` · `databricks-prod-checklist` · `databricks-rate-limits` · `databricks-webhooks-events` · `databricks-reference-architecture` · `databricks-data-handling` | **Cut** — no direct replacement (setup folds into the MCP `.env.sops` + each skill's `## Prerequisites`; checklists/architecture move into v2 `references/`; error catalogs ship per-skill) |

(The 5 v2 skills and what each does live are listed in **[The 5 skills](#the-5-skills)** above.)

## Design Records

All architecture decisions, pain research, and pressure tests for this pack live in [`000-docs/`](000-docs/). Index: [`000-INDEX.md`](000-docs/000-INDEX.md).

## License

MIT
