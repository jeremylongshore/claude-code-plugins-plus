---
name: triage-display
description: |
  Internal procedure for the triage-summarizer agent. Formats triage results
  as terminal-ready markdown and parses interactive review commands. Loaded
  by the parent agent via its skills frontmatter property; not user-invocable.
  Use when the triage-summarizer agent renders a finalized triage run.
allowed-tools: Read, Bash(node:*)
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: medium
compatibility: Designed for claude-code
tags: [triage, display, terminal, review-commands, internal-agent-skill]
---

# Triage Display Process

## Overview

Formats triage results as terminal-ready markdown and parses interactive
review commands. Run by the triage-summarizer agent inside the x-bug-triage
plugin, after clustering, owner routing, and repo scanning have all completed.

The output is shaped for a CLI reviewer working in their terminal — line
budgets are tight, severity icons are stable, evidence summaries collapse
empty tiers, and review commands round-trip through a deterministic parser
so the agent never re-interprets ambiguous user input.

## Prerequisites

- Input: fully populated triage run record with clusters, owners, evidence,
  and source/rate-limit metadata.
- MCP tool `mcp__triage__parse_review_command` registered by the triage server
  (deterministic parser used by Step 3).
- `formatActionConfirmation()` exported from
  `plugins/mcp/x-bug-triage/mcp/triage-server/lib.ts`.

## Instructions

### Step 1: Render Summary

Produce the initial triage summary as terminal markdown:

```
X Bug Triage — Run YYYY-MM-DD HH:MM UTC
Account: @account · Window: last 24h · 42 posts (37 unique, 2 duplicate groups)
WARN  Data quality: date_confidence=low                ← show ONLY when date_confidence is low or medium

--- Sources ---                             ← show ALWAYS between header and clusters
search           ok          18 posts   (rate limit: 4500/5000)
mentions         ok          24 posts   (rate limit: 950/1000)

--- 5 clusters (2 new, 3 existing) ---

[red]   1 · checkout-500-on-mobile-safari
       12 reports · high severity · existing
       Owner: checkout-platform
       Evidence: 1 Tier 1, 2 Tier 2 · Top: GH#4421 exact error match

--- Commands ---
details N  ·  file N  ·  dismiss N  ·  merge N <issue>
escalate N  ·  monitor N  ·  snooze N <duration>
split N  ·  reroute N  ·  full-report
```

### Step 2: Render Detail View (for `details` command)

When showing a single cluster in detail:
- Family, surface, feature area
- Report count, confidence percentage
- Severity + rationale (always show rationale for high/critical)
- Status and time range (first_seen to last_seen)
- Evidence summary line: "Evidence: A Tier 1, B Tier 2, C Tier 3, D Tier 4"
  (omit tiers with 0 count)
- Evidence listed by tier (all tiers, highest first)
- 3 representative posts (highest quality, most distinct, most recent) —
  truncate at 100 chars
- Routing with ranked assignees and confidence percentages

### Step 3: Parse Review Commands

When receiving a command string, call `mcp__triage__parse_review_command`:
- Returns structured ParsedCommand with command, clusterNumber, args, valid,
  error
- If invalid: display the error message to the user
- If valid: return the parsed command to the orchestrator for execution

### Step 4: Render Action Confirmation

After each successfully executed review command, display a confirmation line
using `formatActionConfirmation()` from
`plugins/mcp/x-bug-triage/mcp/triage-server/lib.ts`. Examples:
- `dismiss 1 noise` → "Cluster #1 dismissed (noise). Suppression rule created."
- `file 2` → "Draft issue created for cluster #2. Use 'confirm file 2' to
  submit."
- `escalate 3` → "Cluster #3 escalated. Severity raised."

## Formatting Rules

- **Severity icons**: red = critical/high, yellow = medium, green = low
- **Cluster cap**: Show top 5 by severity. If >5, append "N more — type
  `full-report`"
- **Line budget**: Max 20 lines for <=5 clusters in summary view
- **Post truncation**: Representative posts capped at 100 chars with "..."
  suffix
- **Large clusters**: >50 reports — show count + top 3 posts only
- **Evidence display**: Summary shows per-tier counts + top evidence
  description. Detail shows per-tier counts + full evidence list, ranked. Omit
  tiers with 0 count from the summary line.
- **Routing display**: Summary shows team name only. Detail shows ranked
  assignees with source and confidence.

## Output

- Terminal-rendered markdown for the summary view (Step 1).
- Terminal-rendered markdown for the detail view (Step 2), invoked by a
  `details N` command.
- A `ParsedCommand` struct returned to the orchestrator for review-command
  execution (Step 3).
- A confirmation line emitted after each executed command (Step 4).

## Error Handling

- **Invalid review command**: parser returns `valid=false` with `error`
  populated. Display the error string to the reviewer; do not pass the
  command to the orchestrator.
- **Cluster number out of range**: parser returns `error="cluster #N not in
  this run"`. Display, do not execute.
- **`details N` for a cluster with zero evidence**: render an explicit "No
  evidence collected for this cluster" line in the detail view. Do not
  fabricate evidence rows.
- **Line budget exceeded** (>20 lines for <=5 clusters): truncate
  representative posts further before truncating cluster rows. The summary
  must always fit even if posts collapse to 60 chars.
- **Missing `formatActionConfirmation()` export**: surface a clear "display
  layer broken — confirmation suppressed" warning rather than silently
  dropping the action confirmation.

## Examples

### Example 1: Summary with low data quality

42 posts in the window, but `date_confidence=low` (search API returned 18
posts without timestamps). Output includes the `WARN Data quality` line
between the header and the `--- Sources ---` block; the `--- Sources ---`
block is always shown.

### Example 2: Detail view for a high-severity cluster

`details 1` invoked. Detail view renders rationale ("3 distinct internal
reporters in 90 minutes"), evidence summary ("Evidence: 1 Tier 1, 2 Tier 2"),
3 representative posts (each <100 chars), and the ranked routing block
(top: checkout-platform 1.0; second: oncall@platform 0.9).

### Example 3: Invalid review command

User types `delete 3`. `parse_review_command` returns `valid=false`,
`error="unknown command: delete (try: dismiss, file, merge, escalate,
monitor, snooze, split, reroute, details, full-report)"`. Display sends the
error string back to the reviewer; orchestrator does nothing.

## Resources

The parent x-bug-triage skill ships its review/memory policy at
`plugins/mcp/x-bug-triage/skills/x-bug-triage/references/review-memory-policy.md`
— load on demand when implementing override and memory handling for review
commands.

Trigger phrase: this skill is loaded by the triage-summarizer agent and has no
direct user-facing trigger. Trigger with the parent plugin's `/x-bug-triage`
command.
