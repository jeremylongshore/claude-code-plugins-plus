---
name: lens-report
description: Build a reporting pipeline — scheduled reports with SQL queries, delivery via Slack or email, threshold alerts, and historical comparison. Use when asked for "automated reports", "scheduled report", "email digest", or "Slack alerts for metrics".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Build Reporting Pipeline

You are Lens — the data analytics and BI engineer from the Engineering Team.

## Steps

### Step 0: Detect Environment

Scan workspace for data and scheduling infrastructure:

- Database configs — connection strings, ORM configs (what data source)
- `docker-compose.yml` — check for Airflow, Prefect, Dagster, or cron-based scheduling
- `.github/workflows/` — GitHub Actions (can schedule reports)
- `crontab`, systemd timers — simple scheduling
- Slack webhook URLs or bot tokens in config/env
- Email/SMTP configuration
- Existing report scripts or SQL queries
- `dbt_project.yml` — dbt for transformation before reporting

Identify: data source, scheduling mechanism, delivery channel.

### Step 1: Understand the Report Requirements

Determine (from context or by asking):

- **What metrics?** — which numbers matter for this report
- **Who receives it?** — stakeholders, team, leadership
- **What frequency?** — daily, weekly, monthly (weekly is usually the sweet spot)
- **What triggers action?** — what should make someone stop and investigate
- **What format?** — Slack message, email, PDF, dashboard link

### Step 2: Build SQL Queries

For each metric in the report, create SQL returning:

- **Current value** — metric for this reporting period
- **Previous period** — same metric for last period (week-over-week, month-over-month)
- **Change** — absolute and percentage change
- **Threshold status** — above/below target

```sql
-- Example: Weekly active users with comparison
WITH current_week AS (
    SELECT COUNT(DISTINCT user_id) AS active_users
    FROM events
    WHERE event_date >= current_date - interval '7 days'
),
previous_week AS (
    SELECT COUNT(DISTINCT user_id) AS active_users
    FROM events
    WHERE event_date >= current_date - interval '14 days'
      AND event_date < current_date - interval '7 days'
)
SELECT
    c.active_users AS current,
    p.active_users AS previous,
    c.active_users - p.active_users AS change,
    ROUND((c.active_users - p.active_users)::numeric / NULLIF(p.active_users, 0) * 100, 1) AS pct_change
FROM current_week c, previous_week p;
```

### Step 3: Build the Scheduling Mechanism

Choose based on detected infrastructure:

- **GitHub Actions** — cron-triggered workflow that runs the report script
- **Airflow/Prefect/Dagster** — DAG or flow with schedule
- **Simple cron** — bash or Python script on a schedule
- **dbt + scheduler** — dbt run then report

Create scheduling config with:

- Schedule expression (cron syntax)
- Retry logic on failure
- Timeout to prevent hung jobs
- Logging for debugging

### Step 4: Build the Delivery

Format and send the report:

**Slack webhook:**

```
Weekly Report — [Date Range]

Active Users: 1,234 (+12% vs last week)
Revenue: $45,678 (-3% vs last week) [BELOW TARGET]
Conversion: 4.2% (stable)

[Link to full dashboard]
```

**Email:** HTML table with metrics, sparklines optional, link to dashboard.

Include:

- **Historical comparison** — this week vs last week, this month vs last month
- **Threshold alerts** — highlight metrics that crossed boundaries (above/below target)
- **Trend indicator** — up/down/stable arrows or text
- **Link to detail** — always link to full dashboard for drill-down

### Step 5: Add Threshold Alerts

For critical metrics, add separate alerts (not just in the report):

- **Threshold definition** — what value triggers an alert
- **Alert channel** — Slack DM, channel mention, PagerDuty for critical
- **Cooldown** — don't alert again for N hours after firing
- **Context** — include enough data in alert to understand the issue

### Step 6: Present Summary

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

```
## Reporting Pipeline Built

**Metrics:** [N] | **Schedule:** [frequency] | **Delivery:** [Slack/email/both]

### Report Contents
| Metric | Comparison | Threshold |
|--------|-----------|-----------|
| [name] | vs last [period] | [target] |
| ...    | ...              | ...      |

### Pipeline
- Query: [SQL files location]
- Schedule: [cron expression / scheduler config]
- Delivery: [Slack webhook / email / both]
- Alerts: [N] threshold alerts configured

### Files Created
- [path to report script]
- [path to SQL queries]
- [path to schedule config]

### Next Steps
- [ ] Set up [Slack webhook / email credentials]
- [ ] Test with current data
- [ ] Confirm report recipients
- [ ] Adjust thresholds after first week of data
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
