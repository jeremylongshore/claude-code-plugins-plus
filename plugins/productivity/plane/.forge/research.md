# Forge Research — Plane Plugin

**Forge run**: 2026-05-07
**Forge version**: /skill-creator v8.1.0
**Plugin slug**: `plane`
**Category**: productivity
**Author type**: forge

## Gate 1 — NOI accepted

**NOI**: *Plane is a team behavior observatory.*

Reasoning: project trackers expose how teams behave under pressure. Plane's API surface (cycles, modules, issues, comments, worklogs, states) carries the substrate; what nobody surfaces is the behavioral signal that emerges from JOINing that data.

Examples that crystallize the framing (in NOI files, also captured here for build-time audit):

- Cycle close-out velocity vs. cycle planning dates
- Stale-ticket drift (`In Progress` ownership churn during the open window)
- Reviewer gate strength (time-to-blocker-cleared by reviewer)
- Stated-vs-actual priority drift
- Cross-project workload concentration

This NOI rejects the "Plane CRUD wrapper" framing — `mcp__plane` already exposes that surface.

## Gate 2 — Ecosystem absorb

WebSearch + direct knowledge:

| Tool | What it does | What it doesn't do |
|---|---|---|
| Plane web UI | Ticket entry, cycle planning, dashboards | No cross-project synthesis; behavioral patterns invisible |
| `mcp__plane` MCP | Direct CRUD against the Plane API | No compound queries — calls return one resource type at a time; no JOIN layer |
| Linear (competitor) | Similar tracker with similar dashboards | Same limit — single-team-view, no behavioral synthesis |
| Notion + Plane embeds | Cross-tool aggregation via embed walls | Display-only; no scoring, no observation engine |
| Plane CLI (community) | Terminal access to ticket CRUD | Same as MCP — exposes the API, doesn't synthesize |

**Gap this forge fills**: behavioral synthesis layer on top of Plane's API. None of the existing tools surface "your team plans P1s but ships P3s — the planning conversation is theater" from raw API data. That requires multi-endpoint JOIN logic, which is the compound-command discipline.

**How this differs**: existing tools are display layers (web UI, MCP, CLI, embeds). This skill is an observation layer — it asks behavioral questions, not data-retrieval questions.

## Gate 3 — API surface research

Source of truth: `mcp__plane` MCP (live) + agentskills.io examples + the Plane open-source repo.

Endpoints used (subset of full surface — covers what compound commands need):

- `list_project_issues` — issue enumeration per project
- `list_cycles` — cycle list per project
- `get_cycle` — cycle details (start/end dates, planned vs. completed)
- `list_cycle_issues` — issues in a specific cycle
- `transfer_cycle_issues` — track which issues moved cycles (signal for re-planning)
- `list_modules` — module enumeration
- `list_module_issues` — issues per module
- `get_issue_using_readable_identifier` — full issue detail by `PROJECT-N` ID
- `get_issue_comments` — comment thread (used to detect blocker patterns)
- `list_states` — state enum per project (e.g., Backlog/Todo/In Progress/Done/Cancelled)
- `get_workspace_members` — engineer roster
- `get_total_worklogs` — time-tracking data per assignee
- `get_issue_worklogs` — time spent per issue

**Auth**: API key via env vars `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG`, `PLANE_API_HOST_URL`. Documented in references/api-surface.md.

**Rate limits**: per Plane docs, 60 req/min on free tier. Compound commands are pagination-aware and back off appropriately.

**Pagination**: Plane uses `cursor`-based pagination on list endpoints (returns `next_cursor`).

## Gate 4 — Domain archetype

**Archetype**: Project / Workflow tracker (per /skill-creator's archetype table).

**Default compound command set per archetype**:
- `<api>-velocity` → adapted as `/plane-cycle-velocity` and `/plane-engineer-velocity`
- `<api>-stale` → adapted as `/plane-stale-tickets` (with ownership-churn scoring)
- `<api>-bottleneck` → adapted as `/plane-reviewer-gate-strength` and `/plane-cross-project-load`

Plus a NOI-specific addition not in the default set:
- `/plane-priority-drift` — stated vs. actual priority labels; unique to behavioral-observatory framing

## Gate 5 — Compound command design

Documented separately in `references/compound-commands.md`. Each command lists endpoints called, output format, caching strategy.

## Gate 6 — Generation

This forge run produces:
- `plugin.json` (with `"generated": true`, `"author_type": "forge"`)
- `README.md` (NOI framing in opening paragraph)
- `skills/plane/SKILL.md` (orchestrator)
- `skills/plane/agents/plane-expert.md` (deep API-surface specialist)
- `skills/plane/agents/plane-analyst.md` (compound-command synthesis)
- `skills/plane/references/noi.md` (already written above)
- `skills/plane/references/api-surface.md` (endpoint enumeration)
- `skills/plane/references/compound-commands.md` (5 command designs)
- `.forge/research.md` (this file)
- `.forge/ecosystem.md` (competitor analysis)
- `.forge/proofs.md` (validation evidence)

MCP server scaffolding **deferred** — `mcp__plane` already exists in the user's MCP-server stack. No need to ship a duplicate.

## Gate 7 — Validation

See `.forge/proofs.md`. Must pass:
- Tier 1: Grade A on /validate-skillmd
- Tier 2: GREEN on all 5 production-gate checks
- Tier 3: VERIFIED when JRig CLI is run (manual; not a hard block today since JRig integration is in flight per cross-PR coordination)

## Gate 8 — Output

This forge run lands as a feature branch (`feat/forge-plane-plugin`) with:
- The plugin scaffold (this file's siblings)
- Catalog entry added to `marketplace.extended.json`
- `pnpm run sync-marketplace` regeneration
- PR description includes NOI verbatim, compound commands list, validation results, link to this `.forge/research.md`

Provenance flags in `plugin.json`:
- `"generated": true`
- `"author_type": "forge"`

These flag the plugin in the marketplace anti-spam moat per Phase 5A — visible as "Forge-generated" pill on detail page.
