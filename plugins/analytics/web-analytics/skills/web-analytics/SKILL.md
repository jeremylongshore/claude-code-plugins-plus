---
name: web-analytics
description: 'Push-based web analytics intelligence for your entire site portfolio.
  Fetches data from

  Umami (primary) and GA4 (fallback), runs specialist analysis agents in parallel,
  and

  delivers actionable insights. Three tiers: mini (30s pulse), medium (2min brief),

  full (5min deep dive). Supports console, email, and Slack delivery.

  Trigger with "/analytics", "check my analytics", "how''s my traffic", "site stats",

  "traffic report", "analytics brief", "daily brief".

  '
allowed-tools: Read,Glob,Grep,Bash(date:*),Bash(node:*),Bash(curl:*),Bash(python3:*),Bash(source:*),Task,AskUserQuestion
version: 1.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
- analytics
- umami
- traffic
- reporting
- intelligence
argument-hint: '[mini|medium|full] [--site=name] [--period=7d] [--email] [--slack]'
compatibility: Designed for Claude Code
---
# Web Analytics Intelligence

Orchestrates a team of specialist agents to deliver business-grade analytics insights
across your entire site portfolio. Not a dashboard replacement — a push-based analytics
team that surfaces what matters.

## Overview

This skill routes analytics requests to the right combination of specialist agents based
on the requested tier, compiles their outputs into a cohesive narrative, and delivers
via console, email, or Slack.

**Architecture:** Orchestrator (this skill) → Data Collector → Specialist Agents (parallel) → Reporter

## Prerequisites

- Umami credentials in `~/.env` (UMAMI_PASSWORD for the admin user)
- Sites configured in `${CLAUDE_SKILL_DIR}/references/site-registry.md`
- For email delivery: `/email` skill working
- For Slack delivery: `/slack` skill working

## Data Access

The skill uses **direct Umami REST API calls** (more reliable than MCP):

```bash
# Get auth token
TOKEN=$(curl -s "https://analytics.intentsolutions.io/api/auth/login" \
  -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"'"$UMAMI_PASSWORD"'"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

# Get stats (uses epoch ms, compare=prev for prior period)
curl -s "https://analytics.intentsolutions.io/api/websites/{SITE_ID}/stats?startAt={START_MS}&endAt={END_MS}&compare=prev" \
  -H "Authorization: Bearer $TOKEN"

# Get active visitors
curl -s "https://analytics.intentsolutions.io/api/websites/{SITE_ID}/active" \
  -H "Authorization: Bearer $TOKEN"

# Get daily pageviews
curl -s "https://analytics.intentsolutions.io/api/websites/{SITE_ID}/pageviews?startAt={START_MS}&endAt={END_MS}&unit=day&timezone=America%2FNew_York" \
  -H "Authorization: Bearer $TOKEN"
```

## Instructions

### Step 1: Parse Request

Extract from `$ARGUMENTS` or conversation context:

| Parameter | Default | Options |
|-----------|---------|---------|
| Tier | mini | `mini`, `medium`, `full` |
| Site | all | Site name from registry, or `all` |
| Period | 7d | `today`, `yesterday`, `7d`, `30d`, `mtd`, `qtd` |
| Delivery | console | `--email`, `--slack`, `--all` |
| Compare | auto | Previous equivalent period |

Examples:
- `/analytics` → mini tier, all sites, 7d, console
- `/analytics medium --site=tonsofskills` → medium tier, one site, 7d, console
- `/analytics full --period=30d --email` → full tier, all sites, 30d, email delivery
- `how's my traffic today?` → mini tier, all sites, today, console

### Step 2: Load Configuration

Read these reference files for context:

1. `${CLAUDE_SKILL_DIR}/references/site-registry.md` — site config, baselines, thresholds
2. `${CLAUDE_SKILL_DIR}/references/mcp-tool-reference.md` — MCP tool signatures
3. `${CLAUDE_SKILL_DIR}/references/reporting-tiers.md` — output format specs (medium/full tiers)
4. `${CLAUDE_SKILL_DIR}/references/interpretation-guide.md` — advisory voice standards

### Step 3: Route by Tier

#### Mini Tier (inline — no subagents)

For mini tier, handle data collection inline to minimize latency:

1. Source `~/.env` to get UMAMI_PASSWORD, then get auth token via curl
2. Calculate time range as epoch milliseconds (use `date -d "2026-04-30" +%s` then append `000`)
3. For each site (or specified site):
   - Call `/api/websites/{ID}/stats?startAt=...&endAt=...&compare=prev` for aggregate metrics
   - Call `/api/websites/{ID}/active` for real-time visitor count
4. Compute deltas using the `comparison` block returned by `get_stats`
5. Format as mini pulse:

```
## Analytics Pulse — {date}

**Portfolio:** {total_visitors} visitors across {n} sites ({+/-n%} vs prior {period})

| Site | Visitors | Pageviews | Bounce | Trend |
|------|----------|-----------|--------|-------|
| {site} | {n} | {n} | {n%} | {↑↓→ n%} |

**Top Signal:** {most notable change across all sites}
**Active Now:** {n} visitors
```

Keep it under 15 lines. No analysis, just the numbers and one signal.

#### Medium Tier (4 agents)

Launch these agents using the Agent tool with subagent_type:

**Phase A — Data Collection:**
1. Spawn `data-collector` agent with instructions:
   - Sites: {sites from request}
   - Period: {calculated time range}
   - Data needed: stats, referrers, top pages, time series
   - Provide the full content of `${CLAUDE_SKILL_DIR}/references/mcp-tool-reference.md`
   - Provide the full content of `${CLAUDE_SKILL_DIR}/references/site-registry.md`

**Phase B — Parallel Analysis (after data returns):**
2. Spawn `traffic-intelligence` agent with data-collector output
3. Spawn `content-seo` agent with data-collector output (if available)
4. Spawn `anomaly-detector` agent with data-collector output (if available)

**Phase C — Compilation:**
5. Spawn `reporting-narrative` agent with all specialist outputs
   - Tier: medium
   - Delivery format: {console/email/slack}

#### Full Tier (all agents)

**Phase A — Data Collection:**
1. Spawn `data-collector` agent — request ALL data types including events, tech, geo

**Phase B — Parallel Analysis:**
2. Spawn ALL specialist agents in parallel:
   - `traffic-intelligence` — channel/source analysis
   - `content-seo` — page performance
   - `anomaly-detector` — spike/drop detection
   - `conversion-funnel` — event/goal analysis
   - `audience-segmentation` — cohort/geo analysis

**Phase C — Verification:**
3. Spawn `verification-agent` with all specialist outputs — adversarial quality check

**Phase D — Compilation:**
4. Spawn `reporting-narrative` agent with all outputs + verification notes
   - Tier: full
   - Delivery format: {console/email/slack}

### Step 4: Deliver

**Console (default):** Display the narrative report directly.

**Email (`--email`):** Invoke the `/email` skill with:
- To: jeremy@intentsolutions.io
- Subject: "Analytics {Tier} — {date} — {headline}"
- Body: Report content (formatted for email)

**Slack (`--slack`):** Invoke the `/slack` skill with:
- Channel: #operation-hired
- Message: Report content (formatted for Slack, respect 3000-char limit)

**All (`--all`):** Console + email + Slack.

### Step 5: Memory Update (Full Tier Only)

For full-tier reports, spawn the `memory-agent` to:
- Record this period's baselines for future comparison
- Note any new referral sources or traffic patterns
- Update seasonal adjustment data if applicable

## Agent Roster

| Agent | File | Tier | Purpose |
|-------|------|------|---------|
| data-collector | `${CLAUDE_SKILL_DIR}/agents/data-collector.md` | All | MCP data fetching |
| traffic-intelligence | `${CLAUDE_SKILL_DIR}/agents/traffic-intelligence.md` | Medium+ | Source attribution |
| content-seo | `${CLAUDE_SKILL_DIR}/agents/content-seo.md` | Medium+ | Page performance |
| anomaly-detector | `${CLAUDE_SKILL_DIR}/agents/anomaly-detector.md` | Medium+ | Spike/drop detection |
| conversion-funnel | `${CLAUDE_SKILL_DIR}/agents/conversion-funnel.md` | Full | Event/goal analysis |
| audience-segmentation | `${CLAUDE_SKILL_DIR}/agents/audience-segmentation.md` | Full | Cohort analysis |
| verification-agent | `${CLAUDE_SKILL_DIR}/agents/verification-agent.md` | Full | Output quality check |
| reporting-narrative | `${CLAUDE_SKILL_DIR}/agents/reporting-narrative.md` | Medium+ | Narrative compilation |
| memory-agent | `${CLAUDE_SKILL_DIR}/agents/memory-agent.md` | Full | Rolling context |

## Troubleshooting

| Issue | Resolution |
|-------|-----------|
| "Umami MCP not connected" | Run `/mcp` to check server status. Ensure `umami-analytics` is in settings.json |
| Empty data for a site | Verify site ID in site-registry.md matches Umami. Run `mcp__umami__get_websites` to list. If all sites show zero, the tracker `<script>` likely isn't installed on the site (see site-registry per-site repo paths). |
| Slow response (>5min) | Switch to lower tier. Mini tier bypasses all subagents. |
| Email/Slack delivery fails | Test `/email` and `/slack` independently first |
| Stale baselines | Run `/analytics full` to trigger memory-agent baseline update |
