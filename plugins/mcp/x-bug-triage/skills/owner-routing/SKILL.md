---
name: owner-routing
description: |
  Internal procedure for the owner-router agent. Determines the most likely
  owner/team for each bug cluster using strict 6-level precedence with
  staleness detection and override memory. Loaded by the parent agent via its
  skills frontmatter property; not user-invocable. Use when the owner-router
  agent processes a clustered batch.
allowed-tools: Read, Bash(node:*)
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: medium
compatibility: Designed for claude-code
tags: [triage, routing, ownership, precedence, internal-agent-skill]
---

# Owner Routing Process

## Overview

Determines the most likely owner/team for each bug cluster using strict 6-level
precedence with staleness detection and override memory. Run by the
owner-router agent inside the x-bug-triage plugin once clustering completes.

The 6-level precedence is intentionally explicit: service ownership beats
oncall, oncall beats CODEOWNERS, and so on. Each lower-confidence source
contributes only when every source above it is silent — this prevents stale or
generic data from outranking authoritative routing signals.

## Prerequisites

- Input: clustered bugs (output of the bug-clustering skill).
- MCP tools registered by the triage server: `mcp__triage__lookup_service_owner`,
  `mcp__triage__lookup_oncall`, `mcp__triage__parse_codeowners`,
  `mcp__triage__lookup_recent_assignees`,
  `mcp__triage__lookup_recent_committers`.
- Config: `routing_config` (precedence modifiers, staleness threshold,
  fallback mappings).
- Routing override memory loaded from prior runs.

## Instructions

### Step 1: Check Overrides First

For each cluster, check if a routing_override exists from a prior run:
- If found: use the override (confidence 1.0, source "routing_override"), skip
  precedence lookup
- Log the override application to audit

### Step 2: Query Sources in Precedence Order

For each cluster without an override, query sources strictly in order:

| Level | Source                  | Tool                                       | Base Confidence |
|-------|-------------------------|--------------------------------------------|-----------------|
| 1     | Service owner           | `mcp__triage__lookup_service_owner`        | 1.0             |
| 2     | Oncall                  | `mcp__triage__lookup_oncall`               | 0.9             |
| 3     | CODEOWNERS              | `mcp__triage__parse_codeowners`            | 0.8             |
| 4     | Recent assignees (30d)  | `mcp__triage__lookup_recent_assignees`     | 0.6             |
| 5     | Recent committers (14d) | `mcp__triage__lookup_recent_committers`    | 0.5             |
| 6     | Fallback mapping        | Config lookup                              | 0.3             |

Stop at the first level that returns a valid team or assignee.

### Step 3: Apply Confidence Modifiers

Multiply each result's confidence by the precedence modifier from
routing_config.

### Step 4: Detect Staleness

Flag any routing signal older than the staleness threshold (default 30 days):
- Mark the result as stale with the number of days
- Reduce confidence accordingly
- Stale signals are still usable but should be noted in output

### Step 5: Build Recommendation

Using `lib.buildRoutingRecommendation()`:
- Rank valid results by level (lowest level = highest priority)
- Set top_recommendation to the best result
- If no valid results: set uncertainty=true with reason "Routing: uncertain —
  no routing signals available. Manual assignment required."

## Output

For each cluster, a `RoutingRecommendation` containing:
- `top_recommendation`: { team, assignees, source, level, confidence,
  is_stale, staleness_days }
- `ranked_results`: full list of all valid results from levels 1–6, sorted by
  level (lowest = highest priority).
- `uncertainty`: boolean with `uncertainty_reason` string (set when no signals
  yielded a valid owner).
- An audit event when an override was applied — `routing.override_applied` —
  so prior-run memory is auditable.

## Error Handling

- **No override + no level 1–6 signal**: set `uncertainty=true` with reason
  "Routing: uncertain — no routing signals available. Manual assignment
  required." Do not invent an owner.
- **MCP tool failure on a single level**: skip the level, log a degraded
  signal warning, continue to the next level. A failing oncall lookup never
  blocks CODEOWNERS from running.
- **Stale signal beyond threshold (default 30d)**: still surface the result,
  flagged `is_stale=true`. Downstream display shows the staleness so the human
  reviewer can decide whether to trust it.
- **Override targeting a now-resolved cluster**: keep the override but emit
  `routing.override_skipped` audit event — the override remains in memory for
  any reopen.

## Examples

### Example 1: Service-owner hit

Cluster signature touches `service=checkout`. Level 1 lookup returns
`team=checkout-platform`. Stop at level 1. Confidence 1.0, no staleness.

### Example 2: Fallback to recent committers

Cluster touches a tiny utility library with no service owner, no oncall, no
CODEOWNERS entry, no recent assignees in 30 days. Level 5 returns 2 recent
committers (8 days old). Confidence becomes
`0.5 × precedence_modifier=0.5 → 0.25`. `is_stale=false` (within threshold).

### Example 3: Override beats everything

Cluster has `routing_override.team=billing-eng` from a prior run. Step 1 sets
`top_recommendation.team=billing-eng`, confidence 1.0, source
`routing_override`. Steps 2–5 are skipped. Audit event
`routing.override_applied` written.

## Resources

The parent x-bug-triage skill ships these references at
`plugins/mcp/x-bug-triage/skills/x-bug-triage/references/` and the agent loads
them on demand:

- `routing-rules.md` — precedence rules and confidence modifiers.
- `escalation-rules.md` — escalation trigger definitions.

Trigger phrase: this skill is loaded by the owner-router agent and has no
direct user-facing trigger. Trigger with the parent plugin's `/x-bug-triage`
command.
