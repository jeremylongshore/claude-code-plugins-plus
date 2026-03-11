# Granola Observability - Implementation Details

## Custom Analytics Pipeline (Zapier -> BigQuery)

```yaml
Trigger: New Granola Note
Transform:
  meeting_id: "{{note_id}}"
  meeting_date: "{{date}}"
  duration_minutes: "{{duration}}"
  attendee_count: "{{attendees.count}}"
  action_item_count: "{{action_items.count}}"
Load:
  Destination: BigQuery
  Dataset: meetings
  Table: granola_notes
```

### BigQuery Schema
```sql
CREATE TABLE meetings.granola_notes (
  meeting_id STRING NOT NULL,
  meeting_title STRING,
  meeting_date DATE,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  duration_minutes INT64,
  attendee_count INT64,
  action_item_count INT64,
  workspace STRING,
  shared BOOLEAN,
  created_at TIMESTAMP
);

CREATE VIEW meetings.daily_summary AS
SELECT meeting_date, COUNT(*) as total_meetings,
  SUM(duration_minutes) as total_minutes,
  AVG(attendee_count) as avg_attendees,
  SUM(action_item_count) as total_actions
FROM meetings.granola_notes GROUP BY meeting_date;
```

### Analytics Queries
```sql
-- Meeting frequency by user
SELECT user_email, COUNT(*) as meeting_count,
  SUM(duration_minutes) / 60 as hours_in_meetings
FROM meetings.granola_notes
WHERE meeting_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY user_email ORDER BY meeting_count DESC;

-- Action item trends
SELECT DATE_TRUNC(meeting_date, WEEK) as week,
  SUM(action_item_count) as actions_created, COUNT(*) as meetings
FROM meetings.granola_notes GROUP BY week ORDER BY week;

-- Peak meeting times
SELECT EXTRACT(HOUR FROM start_time) as hour, COUNT(*) as meeting_count
FROM meetings.granola_notes GROUP BY hour ORDER BY hour;

-- Meeting efficiency score
WITH meeting_scores AS (
  SELECT meeting_id,
    CASE WHEN action_item_count > 0 THEN 1 ELSE 0 END as had_actions,
    CASE WHEN duration_minutes <= 30 THEN 1 ELSE 0 END as efficient_length,
    CASE WHEN attendee_count <= 5 THEN 1 ELSE 0 END as right_sized
  FROM meetings.granola_notes
)
SELECT AVG(had_actions + efficient_length + right_sized) / 3 as efficiency_score
FROM meeting_scores;
```

## Dashboard Configuration

```yaml
Dashboard: Granola Analytics
Cards:
  1. Meeting Volume: { type: "time series", metric: "daily meeting count", timeframe: "30 days" }
  2. Active Users: { type: "number", metric: "unique users (7 days)" }
  3. Time in Meetings: { type: "bar chart", metric: "hours per team", breakdown: "workspace" }
  4. Action Items: { type: "line chart", metric: "created vs completed", timeframe: "90 days" }
  5. Top Meeting Types: { type: "pie chart", breakdown: "template" }
  6. Adoption Trend: { type: "area chart", metric: "active users over time", timeframe: "6 months" }
```

## Slack Weekly Digest

```yaml
Schedule: Every Monday 9 AM
Channel: "#leadership"
Message: |
  *Last Week Summary*
  - Meetings: {{total_meetings}}
  - Hours: {{total_hours}}
  - Action Items: {{total_actions}}
  - Completion Rate: {{completion_rate}}%

  *Top Insights*
  - Busiest day: {{busiest_day}}
  - Most meetings: {{top_user}}
```

## Alerting Rules

```yaml
Alerts:
  - name: Processing Failure Spike
    condition: error_rate > 5%
    window: 15 minutes
    severity: warning
    notify: "#ops-alerts"

  - name: Integration Down
    condition: integration_health != "healthy"
    window: 5 minutes
    severity: critical
    notify: pagerduty

  - name: Low Adoption
    condition: weekly_active_users < 50%
    window: 7 days
    severity: info
    notify: "#product-team"
```

## Scheduled Executive Report
```yaml
Schedule: 1st of month
Content: Total meetings YTD, meeting time per employee, action item velocity, top participants, cost savings estimate
Format: PDF
Recipients: leadership@company.com
```
