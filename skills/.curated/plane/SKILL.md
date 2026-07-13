---
name: plane
description: |
  Plane is a team behavior observatory — synthesize Plane API data into observations
  about how teams actually behave under pressure, not just ticket state. Five compound
  commands surface cycle velocity vs. plan, stale-ticket ownership churn, reviewer gate
  strength, stated-vs-actual priority drift, and cross-project workload concentration.
  Reads from the live mcp__plane MCP server when present; documentation-only otherwise.
  Use when investigating "why is this team's plan diverging from reality", auditing cycle
  health, finding orphan tickets, identifying review bottlenecks, or onboarding to a
  new project. Trigger with "/plane-cycle-velocity", "/plane-stale-tickets",
  "/plane-reviewer-gate-strength", "/plane-priority-drift", "/plane-cross-project-load",
  "audit Plane cycle", "team behavior plane", "how is my team behaving".
allowed-tools: "Read,Bash(jq:*),Bash(date:*),AskUserQuestion"
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; requires mcp__plane MCP server configured (PLANE_API_KEY, PLANE_WORKSPACE_SLUG, PLANE_API_HOST_URL env vars)
tags: [plane, project-management, team-behavior, observability, productivity]
model: inherit
---

# Plane — Team Behavior Observatory

A behavioral observation layer on top of Plane's project-tracking API. This skill **does not** wrap Plane CRUD — `mcp__plane` already does that and you should call it directly for ticket entry, status changes, etc.

Instead, this skill answers behavioral questions about how a team is actually performing under pressure: cycle velocity vs. plan, ownership churn, reviewer gate strength, priority drift, and cross-project load. Each question is answered by a compound command that synthesizes data across multiple Plane endpoints — observations no single endpoint exposes.

## Overview

The NOI (`references/noi.md`) is the design anchor: **Plane is a team behavior observatory**. Five compound commands derive from that framing:

1. `/plane-cycle-velocity` — does cycle close-out match cycle planning?
2. `/plane-stale-tickets` — which `In Progress` tickets are quietly failing under shared ownership?
3. `/plane-reviewer-gate-strength` — which reviewers gate-keep harder than the spec demands?
4. `/plane-priority-drift` — does the team plan high-priority work but ship low-priority work?
5. `/plane-cross-project-load` — which engineers are spread across too many active projects?

None of these are answerable from any single Plane API call. Each requires cross-endpoint synthesis. That synthesis is the value.

## Prerequisites

- `mcp__plane` MCP server installed and configured (env vars `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG`, `PLANE_API_HOST_URL`)
- A Plane workspace with at least one project, cycle, and active issues (otherwise the commands return informative empty states)

## Authentication

This skill does not handle credentials directly. Auth is delegated to the MCP server. See `references/api-surface.md` for the env-var setup; if `mcp__plane` returns an auth error, the skill surfaces the error verbatim and instructs the user to verify their token.

## Instructions

### Mode detection

Determine user intent from their prompt:

- **Compound query mode** (default): user asks about cycle health, team behavior, stale tickets, reviewer patterns, priority drift, or workload distribution → route to `plane-analyst` agent (see `agents/plane-analyst.md`) which orchestrates the compound commands.
- **API help mode**: user asks "how do I query X in Plane" or "what endpoint does Y" → route to `plane-expert` agent (see `agents/plane-expert.md`) which answers from `references/api-surface.md` without firing live API calls.
- **Skill metadata**: user asks "what does this skill do" / "explain plane skill" → return the Overview above + the 5 commands.

If unclear, use `AskUserQuestion`:

> Are you asking about (a) team behavior / cycle health / patterns, or (b) how to use a specific Plane API endpoint?

### Step 1: Resolve target project

Most compound commands operate on a specific project. Extract the project slug or readable identifier (e.g., `BRAVES`, `OPS`) from the user's prompt.

If absent, list available projects via `mcp__plane__get_projects` and ask which one. Cache the chosen project for the rest of the conversation.

### Step 2: Route to compound command

Match user intent to one of the five commands:

| User asks about... | Command |
|---|---|
| cycle velocity, sprint completion, overrun | `/plane-cycle-velocity` |
| stale tickets, orphan work, ownership churn | `/plane-stale-tickets` |
| reviewer bottlenecks, blocked PRs, gate-keeping | `/plane-reviewer-gate-strength` |
| priority drift, planning vs. reality, P1 vs. P3 | `/plane-priority-drift` |
| workload distribution, project sprawl, focus | `/plane-cross-project-load` |

Read `references/compound-commands.md` for the exact endpoint sequence and output format per command.

### Step 3: Execute via `plane-analyst` agent

Invoke the analyst agent (`agents/plane-analyst.md`) with the chosen command + project. The agent:

1. Calls the relevant `mcp__plane__*` tools in sequence
2. Performs the JOIN logic
3. Computes the behavioral score per the command's formula
4. Renders the output table per the format in `compound-commands.md`
5. Adds a "Behavioral signal" interpretation paragraph

If `mcp__plane` is unavailable, the agent emits a documentation-only response: shows what the command WOULD return, plus the install hint.

### Step 4: Interpret the signal

The output is observations, not prescriptions. The skill says "this team plans P1s and ships P3s — the planning conversation is theater." It does NOT say "fire the planner." Interpretation belongs to the human reading the report.

## Output

Each compound command produces:

- A table of metrics specific to that observation
- A "Behavioral signal" paragraph that names the pattern in plain language
- Optionally, a follow-up suggestion (e.g., "consolidate projects" / "split this queue") — framed as a question the team can take to its retro

## Error Handling

| Error | Recovery |
|---|---|
| `mcp__plane` unavailable | Emit documentation-only output + install hint pointing at `~/.claude.json` MCP config |
| API rate limit (429) | Back off + retry with exponential delay; if persistent, advise user to wait and re-run |
| Empty project (no cycles / issues) | Return informative empty state explaining why the command can't compute |
| Auth error (401/403) | Surface verbatim + instruct user to verify env vars or re-issue token |
| Workspace member lookup fails | Fall back to assignee UUIDs in output (less readable but functional) |

## Examples

**"How is my team performing on cycle velocity?"**

```
/plane-cycle-velocity BRAVES
```

→ Renders the cycle-velocity table from `references/compound-commands.md` § Command 1.

**"Are we shipping what we plan?"**

```
/plane-priority-drift BRAVES
```

→ Renders the priority-drift table; surfaces the gap between planned and shipped priorities.

**"Which engineers are stretched too thin?"**

```
/plane-cross-project-load
```

→ Walks the entire workspace; lists engineers with their active-project / active-cycle / open-issue counts; flags crisis-level stretch.

## Resources

- [NOI](references/noi.md) — the secret-identity statement that anchors every command
- [API surface](references/api-surface.md) — endpoints consumed + auth + pagination
- [Compound commands](references/compound-commands.md) — exact endpoint sequence + output format per command
- [Plane docs](https://docs.plane.so/) — upstream API reference
- `mcp__plane` MCP server — direct CRUD wrapper this skill builds on top of
