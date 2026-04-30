---
name: owner-routing
description: |
  Internal process for the owner-router agent. Defines the step-by-step
  procedure for determining likely bug owners using strict 6-level routing
  precedence with staleness detection. Not user-invocable — loaded by the
  agent via its `skills: ["owner-routing"]` frontmatter property.
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: medium
compatible-with: claude-code
tags: [triage, routing, ownership, precedence, internal-agent-skill]
---

# Owner Routing Process

Step-by-step procedure for determining the most likely owner/team for each bug cluster using strict 6-level precedence with staleness detection and override memory.

## Instructions

### Step 1: Check Overrides First

For each cluster, check if a routing_override exists from a prior run:
- If found: use the override (confidence 1.0, source "routing_override"), skip precedence lookup
- Log the override application to audit

### Step 2: Query Sources in Precedence Order

For each cluster without an override, query sources strictly in order:

| Level | Source | Tool | Base Confidence |
|-------|--------|------|----------------|
| 1 | Service owner | `mcp__triage__lookup_service_owner` | 1.0 |
| 2 | Oncall | `mcp__triage__lookup_oncall` | 0.9 |
| 3 | CODEOWNERS | `mcp__triage__parse_codeowners` | 0.8 |
| 4 | Recent assignees (30d) | `mcp__triage__lookup_recent_assignees` | 0.6 |
| 5 | Recent committers (14d) | `mcp__triage__lookup_recent_committers` | 0.5 |
| 6 | Fallback mapping | Config lookup | 0.3 |

Stop at the first level that returns a valid team or assignee.

### Step 3: Apply Confidence Modifiers

Multiply each result's confidence by the precedence modifier from routing_config.

### Step 4: Detect Staleness

Flag any routing signal older than the staleness threshold (default 30 days):
- Mark the result as stale with the number of days
- Reduce confidence accordingly
- Stale signals are still usable but should be noted in output

### Step 5: Build Recommendation

Using `lib.buildRoutingRecommendation()`:
- Rank valid results by level (lowest level = highest priority)
- Set top_recommendation to the best result
- If no valid results: set uncertainty=true with reason "Routing: uncertain — no routing signals available. Manual assignment required."

## References

Load routing precedence rules:
```
!cat skills/x-bug-triage/references/routing-rules.md
```

Load escalation trigger definitions:
```
!cat skills/x-bug-triage/references/escalation-rules.md
```
