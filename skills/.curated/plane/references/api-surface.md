# Plane API Surface

**Captured**: 2026-05-07
**Source of truth**: `mcp__plane` MCP server tool list + Plane open-source repo (`makeplane/plane`)
**Plane version targeted**: API v1, current production at `projects.intentsolutions.io`

This skill operates against Plane's public REST API. It does NOT implement the API client itself — instead it delegates to `mcp__plane` MCP tools (already wired in the user's environment). When `mcp__plane` is unavailable, the skill degrades to a documentation-only mode and instructs the user how to install it.

## Authentication

Three environment variables, all required:

```bash
PLANE_API_KEY="<your_personal_access_token>"
PLANE_WORKSPACE_SLUG="<workspace_slug>"
PLANE_API_HOST_URL="https://projects.intentsolutions.io"
```

Mirror these into the MCP server config (already done in user's `~/.claude.json` per `reference_plane_setup.md` memory).

**Rate limits**: 60 requests/minute on the standard tier. Compound commands batch where possible and back off on 429.

## Endpoint groups consumed

### Issues

| Tool | Purpose | Used by compound command |
|---|---|---|
| `mcp__plane__list_project_issues` | Enumerate issues per project | All — base query |
| `mcp__plane__get_issue_using_readable_identifier` | Full issue detail by `PROJECT-N` ID | priority-drift, stale-tickets |
| `mcp__plane__list_states` | Project state enum (Backlog / In Progress / Done / etc.) | stale-tickets, cycle-velocity |
| `mcp__plane__update_issue` | Mutation — used only when explicitly requested by user | (none — this skill is read-mostly) |

### Cycles

| Tool | Purpose | Used by compound command |
|---|---|---|
| `mcp__plane__list_cycles` | Cycle list per project | cycle-velocity, priority-drift |
| `mcp__plane__get_cycle` | Cycle details (start/end dates, completion stats) | cycle-velocity |
| `mcp__plane__list_cycle_issues` | Issues planned in a specific cycle | cycle-velocity, priority-drift |
| `mcp__plane__transfer_cycle_issues` | Track issues moved between cycles (re-planning signal) | priority-drift (read-side via list_cycle_issues + diff over time) |

### Modules

| Tool | Purpose | Used by compound command |
|---|---|---|
| `mcp__plane__list_modules` | Module enumeration | cross-project-load |
| `mcp__plane__list_module_issues` | Issues per module | cross-project-load |

### Comments / Activity

| Tool | Purpose | Used by compound command |
|---|---|---|
| `mcp__plane__get_issue_comments` | Comment thread on an issue | reviewer-gate-strength |

### Workspace + Worklogs

| Tool | Purpose | Used by compound command |
|---|---|---|
| `mcp__plane__get_workspace_members` | Engineer roster | engineer-velocity, cross-project-load |
| `mcp__plane__get_total_worklogs` | Time tracked per assignee | engineer-velocity |
| `mcp__plane__get_issue_worklogs` | Time tracked per issue | cycle-velocity (estimate-vs-actual) |

## Response shapes (excerpts)

Full schemas live at `mcp__plane`'s tool-detail descriptions; these are the shapes the compound commands JOIN against.

### Issue (excerpt)

```jsonc
{
  "id": "uuid",
  "name": "Issue title",
  "state": "uuid",                  // → joined against list_states
  "priority": "urgent|high|medium|low|none",
  "assignees": ["uuid", ...],       // → joined against get_workspace_members
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "completed_at": "ISO-8601 | null",
  "estimate_point": 5,              // → estimate-vs-actual signal
  "cycle_id": "uuid | null",
  "module_ids": ["uuid", ...],
  "labels": ["uuid", ...]
}
```

### Cycle (excerpt)

```jsonc
{
  "id": "uuid",
  "name": "Sprint 14",
  "start_date": "ISO-8601",
  "end_date": "ISO-8601",
  "total_issues": 23,
  "completed_issues": 18,
  "cancelled_issues": 1,
  "started_issues": 4,              // still open at close — overrun signal
  "unstarted_issues": 0
}
```

## Pagination

All `list_*` endpoints return cursor-based pagination:

```jsonc
{
  "results": [...],
  "next_cursor": "<opaque-token>",
  "prev_cursor": "<opaque-token>"
}
```

Compound commands paginate to completion when scoring requires the full set; sample-mode (first page only) is supported via the `--sample` flag for fast iteration.

## When the API surface drifts

Re-run via `/skill-creator --reforge plane` (see `/skill-creator` SKILL.md § Reforge Mode Workflow). Auto-bumps version per detected change scope.

Future enhancement (Phase 5C cron): scheduled daily diff against the live API surface, opens a GitHub issue tagged `forge-drift` when an endpoint adds / removes / changes shape.
