---
name: triage-display
description: |
  Internal process for the triage-summarizer agent. Defines the step-by-step
  procedure for formatting triage results as terminal markdown and parsing
  review commands. Not user-invocable — loaded by the agent via its
  `skills: ["triage-display"]` frontmatter property.
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: medium
compatible-with: claude-code
tags: [triage, display, terminal, review-commands, internal-agent-skill]
---

# Triage Display Process

Step-by-step procedure for formatting triage results as terminal-ready markdown and handling interactive review command parsing.

## Instructions

### Step 1: Render Summary

Produce the initial triage summary as terminal markdown:

```
X Bug Triage — Run {date} {time} UTC
Account: @{account} · Window: last {window} · {count} posts ({unique} unique, {dedup_groups} duplicate groups)
⚠ Data quality: {warning}                  ← show ONLY when date_confidence is low or medium

--- Sources ---                             ← show ALWAYS between header and clusters
{source_name}      {status}    {count} posts   (rate limit: {remaining}/{limit})
...

--- {n} clusters ({new} new, {existing} existing) ---

{icon} {#} · {bug_signature}
     {report_count} reports · {severity} severity · {status_note}
     Owner: {team}
     Evidence: {t1} Tier 1, {t2} Tier 2, {t3} Tier 3, {t4} Tier 4 · Top: {description}

--- Commands ---
details <#>  ·  file <#>  ·  dismiss <#>  ·  merge <#> <issue>
escalate <#>  ·  monitor <#>  ·  snooze <#> <duration>
split <#>  ·  reroute <#>  ·  full-report
```

### Step 2: Render Detail View (for `details` command)

When showing a single cluster in detail:
- Family, surface, feature area
- Report count, confidence percentage
- Severity + rationale (always show rationale for high/critical)
- Status and time range (first_seen to last_seen)
- Evidence summary line: `"Evidence: {t1} Tier 1, {t2} Tier 2, {t3} Tier 3, {t4} Tier 4"` (omit tiers with 0 count)
- Evidence listed by tier (all tiers, highest first)
- 3 representative posts (highest quality, most distinct, most recent) — truncate at 100 chars
- Routing with ranked assignees and confidence percentages

### Step 3: Parse Review Commands

When receiving a command string, call `mcp__triage__parse_review_command`:
- Returns structured ParsedCommand with command, clusterNumber, args, valid, error
- If invalid: display the error message to the user
- If valid: return the parsed command to the orchestrator for execution

### Step 4: Render Action Confirmation

After each successfully executed review command, display a confirmation line using `formatActionConfirmation()` from `mcp/triage-server/lib.ts`. Examples:
- `dismiss 1 noise` → `"Cluster #1 dismissed (noise). Suppression rule created."`
- `file 2` → `"Draft issue created for cluster #2. Use "confirm file 2" to submit."`
- `escalate 3` → `"Cluster #3 escalated. Severity raised."`

## Formatting Rules

- **Severity icons**: red_circle = critical/high, yellow_circle = medium, green_circle = low
- **Cluster cap**: Show top 5 by severity. If >5, append "{N} more — type `full-report`"
- **Line budget**: Max 20 lines for <=5 clusters in summary view
- **Post truncation**: Representative posts capped at 100 chars with "..." suffix
- **Large clusters**: >50 reports — show count + top 3 posts only
- **Evidence display**: Summary shows per-tier counts + top evidence description. Detail shows per-tier counts + full evidence list, ranked. Omit tiers with 0 count from the summary line.
- **Routing display**: Summary shows team name only. Detail shows ranked assignees with source and confidence.

## References

Load override and memory policy for review command processing:
```
!cat skills/x-bug-triage/references/review-memory-policy.md
```
