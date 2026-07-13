---
name: portaljs-architect
description: Recommend a data-portal architecture (storage, compute, catalog, access, hosting, metadata) from stated needs, then hand off to the build skills. The advisory entry point. Use when starting a new data-portal project and the underlying architecture has not yet been decided.
allowed-tools: Read, Write, Bash(du:*), Bash(wc:*), Bash(ls:*), Bash(head:*)
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - architecture
  - advisory
  - ckan
  - nextjs
---

# PortalJS — Architect

## Overview
The advisory entry point for a PortalJS project. Before anything gets scaffolded, this
skill works out what to build: given the kind of portal, the shape of the data, and its
purpose, it fills six architecture slots (storage, catalog, compute, access, hosting,
metadata), resolves two build-time knobs (per-dataset data tier and the portal-wide
`DATA_QUERY` mode), and hands off to the concrete build skills. It decides; it does not
build. When the brief is thin it interviews in short rounds and never dead-ends — every
question has a sensible default, reachable by replying "use defaults."

## Prerequisites
- A rough idea of the portal's purpose and data (exact numbers are not required — the
  interview supplies defaults for anything missing).
- Optional: local files or a directory of sample data to inspect for size and shape.
- No PortalJS project needs to exist yet; this skill runs before scaffolding.

## Instructions
The canonical, full step-by-step workflow lives in
[`.claude/commands/portaljs-architect.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-architect.md) —
that file is the single source of truth. Follow it when executing this skill:

1. Parse `$ARGUMENTS` for anything already specified, then interview for what's
   missing, one round at a time: (1) what's being built, (2) what the data is,
   (3) what it's for, (4) constraints. Accept "use defaults" at any point. Inspect
   named files/directories with `du -sh` and line counts to ground size guesses.
2. Derive the recommendation by matching the answers against the decision tables —
   Storage/Catalog/Compute by data volume and query needs, Access/Hosting by public
   vs. private, Metadata by standards-compliance needs — then resolve the two
   build-time knobs: per-dataset **data tier** (`inline | LFS | external`) and the
   portal-wide **`DATA_QUERY`** mode (`flat | duckdb`).
3. Echo the architecture brief (stack, reasoning per slot, deviations from default,
   deferred items) and wait for confirmation ("go") or corrections.
4. On confirmation, persist the brief to `./ARCHITECTURE.md` in the working directory.
5. Hand off to the build skills — `/portaljs-new-portal`, `/portaljs-add-dataset`,
   `/portaljs-connect-ckan`, `/portaljs-define-schema`, `/portaljs-deploy` — mapped
   from the brief, and offer to run the first one.

## Output
- **Created:** `./ARCHITECTURE.md` documenting the six slots, the two build-time
  knobs, the reasoning, and anything deferred to a later build step.
- **Modified:** nothing else — this skill is advisory only.
- **Verified:** the brief was echoed back and confirmed before being persisted.
- **Result:** a concrete, named sequence of follow-up skill invocations
  (e.g. `/portaljs-new-portal` → `/portaljs-add-dataset` → `/portaljs-deploy`).

## Error Handling
| Symptom | Cause | Fix |
| --- | --- | --- |
| Skill keeps asking rounds of questions | Brief was thin or `$ARGUMENTS` omitted | Answer inline, or reply "use defaults" to accept the opinionated default stack |
| Recommendation looks generic | Rounds were skipped without real data details | Give actual size/shape/cadence, or point at files for `du -sh` inspection |
| `ARCHITECTURE.md` never appears | Confirmation step was skipped | Reply "go" once the echoed brief looks right |
| Scaffolded portal has the wrong `DATA_QUERY` | Flat downgrade wasn't applied | Run the `perl -pi -e` one-liner from the command file against `lib/datasets.ts` |
| Hand-off names a skill that doesn't exist | Decision maps to a *(planned)* skill (e.g. `/connect-openmetadata`) | Treat it as designed-in/built-later; proceed with the closest available skill |

## Examples
### Example 1 — National statistics office, DCAT-AP harvesting
```
/portaljs-architect We're a national statistics office. ~200 datasets, mostly large
CSVs (some GBs), updated quarterly, all public, and we must publish DCAT-AP for the
EU data portal.
```
Infers a multi-publisher, analytics-grade portal. Recommends Parquet on R2 + DuckLake +
DuckDB, static Cloudflare Pages, Frictionless + DCAT-AP metadata, `owner` namespace,
data tier `external` for the Parquet, `DATA_QUERY=duckdb`. Writes `ARCHITECTURE.md` and
hands off to `/portaljs-new-portal` then `/portaljs-add-dataset`.

### Example 2 — Small nonprofit, no arguments given
```
/portaljs-architect
```
Runs the full four-round interview since nothing was pre-filled. Accepting defaults at
each round lands on the opinionated default stack: repo files or Git-LFS + R2 storage,
`datasets.json` catalog, DuckDB compute, static access on Cloudflare Pages, Frictionless
metadata, `theme` namespace, data tier LFS, `DATA_QUERY=duckdb`.

### Example 3 — Internal catalog with restricted datasets
```
/portaljs-architect Internal engineering data catalog, single team, dozens of CSVs,
some of it access-controlled to specific roles.
```
The private-data answer in Round 2 flips Access/Hosting to runtime + backend RBAC on
Cloudflare Workers — flagged as the larger, opt-in build — while Storage/Catalog/Compute
still follow the volume-based defaults.

## Resources
- Full workflow: [`.claude/commands/portaljs-architect.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-architect.md)
- Reference: [`references/reference.md`](references/reference.md)
- Decision framework: [`site/content/docs/architecture/decision-framework.md`](https://github.com/datopian/portaljs/blob/main/site/content/docs/architecture/decision-framework.md)
- Related skills: `/portaljs-new-portal`, `/portaljs-add-dataset`, `/portaljs-connect-ckan`, `/portaljs-define-schema`, `/portaljs-deploy`
