---
name: granola-observability
description: |
  Monitor Granola usage, analytics, and meeting insights.
  Use when tracking meeting patterns, analyzing team productivity,
  or building meeting analytics dashboards.
  Trigger with phrases like "granola analytics", "granola metrics",
  "granola monitoring", "meeting insights", "granola observability".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Granola Observability

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Monitor Granola usage, track meeting metrics, and gain insights into team productivity using built-in analytics and custom data pipelines.

## Prerequisites
- Granola Business or Enterprise plan
- Admin access for organization metrics
- Analytics destination (optional: BigQuery, Metabase)

## Key Metrics

| Category | Metric | Target |
|----------|--------|--------|
| Usage | Adoption Rate | > 80% |
| Usage | Capture Rate | > 70% |
| Quality | Action Item Detection | > 90% |
| Quality | Transcription Accuracy | > 95% |
| Efficiency | Time Saved | ~20 min/meeting |
| Efficiency | Action Completion | > 80% |

## Instructions

### Step 1: Enable Built-in Analytics
Access at Settings > Analytics. Track total meetings, hours per week, active users, notes shared, action items created.

### Step 2: Build Custom Analytics Pipeline
Route Granola note data via Zapier to BigQuery for deep analysis (meeting frequency, trends, peak times, efficiency scores).

### Step 3: Create Dashboards
Build Metabase/Looker dashboard with meeting volume, active users, time breakdown by workspace, action item trends.

### Step 4: Automate Reporting
Weekly Slack digest to leadership with meeting stats and insights. Monthly executive PDF report.

### Step 5: Configure Health Monitoring
Set up alerts for processing failures (>5%), integration outages, and low adoption.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for BigQuery schema, analytics queries, dashboard config, Slack digest template, and alerting rules.

## Output
- Built-in analytics reviewed regularly
- Custom pipeline streaming to data warehouse
- Dashboards visualizing meeting patterns
- Automated weekly/monthly reports

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missing data in pipeline | Zapier trigger failed | Check Zapier task history |
| Inaccurate metrics | Duplicate entries | Add deduplication to pipeline |
| Dashboard stale | Pipeline stopped | Monitor Zapier health |
| Low adoption signal | Users not recording | Investigate and provide training |

## Examples

### Meeting Efficiency Check
Track three indicators per meeting: had action items (yes/no), under 30 min (yes/no), right-sized (<=5 attendees). Average score reveals organizational meeting health.

## Resources
- [Granola Analytics Guide](https://granola.ai/help/analytics)
- [Admin Dashboard](https://app.granola.ai/admin)
- [Status Page](https://status.granola.ai)

## Next Steps
Proceed to `granola-incident-runbook` for incident response procedures.
