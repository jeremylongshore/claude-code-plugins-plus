---
name: granola-observability
description: |
  Monitor Granola adoption, meeting analytics, and build custom dashboards.
  Use when tracking team meeting patterns, measuring adoption,
  building analytics pipelines, or creating executive reports.
  Trigger: "granola analytics", "granola metrics", "granola monitoring",
  "granola adoption", "meeting insights".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, monitoring, analytics, observability]

---
# Granola Observability

## Overview
Monitor Granola usage, track meeting patterns, and build analytics dashboards. Granola Enterprise includes a usage analytics dashboard. For deeper insights, build custom pipelines using Zapier to stream meeting metadata to BigQuery, Metabase, or other analytics platforms.

## Prerequisites
- Granola Business or Enterprise plan
- Admin access for organization-level analytics
- Optional: BigQuery/Metabase for custom dashboards, Zapier for data pipeline

## Instructions

### Step 1 — Built-in Analytics (Enterprise)

Access the analytics dashboard at Settings > **Analytics** (Enterprise plan):

| Metric | What It Shows |
|--------|--------------|
| Total meetings captured | Meeting volume over time |
| Active users | Users who recorded meetings this period |
| Hours captured | Total meeting hours transcribed |
| Notes shared | How often notes are distributed |
| Action items created | Extracted action items across org |
| Adoption rate | Active users / total licensed seats |

### Step 2 — Define Key Metrics

Track these metrics to measure Granola's impact:

| Category | Metric | Target | Formula |
|----------|--------|--------|---------|
| Adoption | Activation rate | >80% | Users with 1+ meeting / total seats |
| Adoption | Weekly active users | >70% | Users recording this week / total seats |
| Quality | Capture rate | >70% | Meetings captured / total calendar meetings |
| Quality | Share rate | >50% | Notes shared / notes created |
| Efficiency | Time saved | >10 min/meeting | Survey: manual notes time - Granola time |
| Efficiency | Action completion | >80% | Actions completed / actions created |
| Health | Processing success | >99% | Successful enhancements / total attempts |
| Health | Integration uptime | >99% | Successful syncs / total sync attempts |

### Step 3 — Build a Custom Analytics Pipeline

Stream meeting metadata from Granola to a data warehouse via Zapier:

```yaml
# Zapier: Granola → BigQuery pipeline
Trigger: Granola — Note Added to Folder ("All Meetings")

Step 1 — Code by Zapier (extract metadata):
  const data = {
    meeting_id: inputData.title + '_' + inputData.calendar_event_datetime,
    title: inputData.title,
    date: inputData.calendar_event_datetime,
    creator: inputData.creator_email,
    attendee_count: JSON.parse(inputData.attendees || '[]').length,
    has_action_items: inputData.note_content.includes('- [ ]'),
    action_item_count: (inputData.note_content.match(/- \[ \]/g) || []).length,
    has_decisions: inputData.note_content.includes('## Decision') ||
                   inputData.note_content.includes('## Key Decision'),
    word_count: inputData.note_content.split(/\s+/).length,
    is_external: JSON.parse(inputData.attendees || '[]')
      .some(a => !a.email?.endsWith('@company.com')),
    workspace: inputData.folder || 'unknown',
    captured_at: new Date().toISOString(),
  };
  output = [data];

Step 2 — BigQuery: Insert Row
  Dataset: meeting_analytics
  Table: granola_meetings
  Row: {{metadata from step 1}}
```

**BigQuery schema:**
```sql
CREATE TABLE meeting_analytics.granola_meetings (
  meeting_id STRING NOT NULL,
  title STRING,
  date TIMESTAMP,
  creator STRING,
  attendee_count INT64,
  has_action_items BOOL,
  action_item_count INT64,
  has_decisions BOOL,
  word_count INT64,
  is_external BOOL,
  workspace STRING,
  captured_at TIMESTAMP
);
```

### Step 4 — Analytics Queries

```sql
-- Weekly meeting volume by workspace
SELECT
  workspace,
  DATE_TRUNC(date, WEEK) AS week,
  COUNT(*) AS meeting_count,
  SUM(action_item_count) AS total_actions,
  AVG(attendee_count) AS avg_attendees
FROM meeting_analytics.granola_meetings
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 WEEK)
GROUP BY workspace, week
ORDER BY week DESC, workspace;

-- Adoption: active users per week
SELECT
  DATE_TRUNC(date, WEEK) AS week,
  COUNT(DISTINCT creator) AS active_users
FROM meeting_analytics.granola_meetings
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 WEEK)
GROUP BY week
ORDER BY week DESC;

-- Meeting efficiency score (has action items + decisions + < 8 attendees)
SELECT
  title,
  date,
  CASE
    WHEN has_action_items AND has_decisions AND attendee_count <= 8 THEN 'Efficient'
    WHEN has_action_items OR has_decisions THEN 'Partially Efficient'
    ELSE 'Low Efficiency'
  END AS efficiency_rating
FROM meeting_analytics.granola_meetings
ORDER BY date DESC
LIMIT 50;

-- External vs internal meeting ratio
SELECT
  DATE_TRUNC(date, MONTH) AS month,
  COUNTIF(is_external) AS external_meetings,
  COUNTIF(NOT is_external) AS internal_meetings,
  ROUND(COUNTIF(is_external) * 100.0 / COUNT(*), 1) AS external_pct
FROM meeting_analytics.granola_meetings
GROUP BY month
ORDER BY month DESC;
```

### Step 5 — Automated Reporting

**Weekly Slack digest (via Zapier Schedule):**
```yaml
Trigger: Schedule by Zapier — Every Friday at 5 PM

Step 1 — BigQuery: Run Query
  Query: "SELECT COUNT(*) as meetings, SUM(action_item_count) as actions,
          COUNT(DISTINCT creator) as active_users
          FROM meeting_analytics.granola_meetings
          WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"

Step 2 — Slack: Send Message to #leadership
  Message: |
    :bar_chart: *Weekly Granola Report*

    *This Week:*
    - Meetings captured: {{meetings}}
    - Action items created: {{actions}}
    - Active users: {{active_users}}

    [View full dashboard →]
```

### Step 6 — Health Monitoring and Alerts

Set up alerts for operational issues:

| Alert | Condition | Channel |
|-------|-----------|---------|
| Low adoption | Active users <50% of seats (weekly) | Slack #it-alerts |
| Processing failures | >5% enhancement failures (daily) | PagerDuty |
| Integration outage | Slack/Notion/CRM sync failures >3 (hourly) | Slack #it-alerts |
| Zero meetings captured | No meetings for any workspace (daily) | Email to workspace admin |

**Status monitoring:**
```bash
# Check Granola service status
curl -s https://status.granola.ai/api/v2/status.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
status = data.get('status', {}).get('description', 'Unknown')
print(f'Granola Status: {status}')
"
```

## Output
- Built-in analytics reviewed and baselines established
- Custom analytics pipeline streaming to data warehouse
- Dashboard visualizing adoption, efficiency, and meeting patterns
- Automated weekly/monthly reports delivered to stakeholders
- Health monitoring alerts configured for operational issues

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Missing data in pipeline | Zapier trigger failed | Check Zap history, reconnect if needed |
| Duplicate entries in BigQuery | Zapier retry on timeout | Add deduplication (MERGE or INSERT IGNORE) |
| Dashboard shows stale data | Pipeline paused | Monitor Zapier health, restart paused Zaps |
| Low adoption alert false positive | New seats just added | Adjust alert threshold, use percentage not absolute |

## Resources
- [Granola Updates](https://www.granola.ai/updates)
- [Enterprise API](https://docs.granola.ai/help-center/sharing/integrations/enterprise-api)
- [Status Page](https://status.granola.ai)

## Next Steps
Proceed to `granola-incident-runbook` for incident response procedures.
