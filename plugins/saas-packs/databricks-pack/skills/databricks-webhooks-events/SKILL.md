---
name: databricks-webhooks-events
description: |
  Configure Databricks job notifications, webhooks, and event handling.
  Use when setting up Slack/Teams notifications, configuring alerts,
  or integrating Databricks events with external systems.
  Trigger with phrases like "databricks webhook", "databricks notifications",
  "databricks alerts", "job failure notification", "databricks slack".
allowed-tools: Read, Write, Edit, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Webhooks & Events

## Overview
Configure notifications and event-driven workflows for Databricks jobs and pipelines. Databricks supports notification destinations (Slack, Teams, PagerDuty, email, generic webhooks) and system tables for event monitoring.

## Prerequisites
- Databricks workspace admin access (for notification destinations)
- Webhook endpoint URL (Slack incoming webhook, Teams connector, etc.)
- Job permissions for notification configuration

## Instructions

### Step 1: Create Notification Destinations
Register webhook endpoints that jobs and alerts can send to.

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.settings import (
    CreateNotificationDestinationRequest,
    SlackConfig,
    EmailConfig,
    GenericWebhookConfig,
)

w = WorkspaceClient()

# Slack destination
slack_dest = w.notification_destinations.create(
    display_name="Engineering Slack",
    config=SlackConfig(url="https://hooks.slack.com/services/T00/B00/xxxx"),
)

# Email destination
email_dest = w.notification_destinations.create(
    display_name="Oncall Email",
    config=EmailConfig(addresses=["oncall@company.com", "data-team@company.com"]),
)

# Generic webhook (PagerDuty, custom endpoint, etc.)
pagerduty_dest = w.notification_destinations.create(
    display_name="PagerDuty",
    config=GenericWebhookConfig(
        url="https://events.pagerduty.com/integration/YOUR_KEY/enqueue",
        username=None,
        password=None,
    ),
)

print(f"Slack: {slack_dest.id}, Email: {email_dest.id}, PD: {pagerduty_dest.id}")
```

### Step 2: Configure Job Notifications
Attach notification destinations to jobs for lifecycle events.

```python
from databricks.sdk.service.jobs import (
    JobEmailNotifications,
    WebhookNotifications,
    Webhook,
)

# Update an existing job with notifications
w.jobs.update(
    job_id=123,
    new_settings={
        "email_notifications": JobEmailNotifications(
            on_start=["team@company.com"],
            on_success=["team@company.com"],
            on_failure=["oncall@company.com", "team@company.com"],
            no_alert_for_skipped_runs=True,
        ),
        "webhook_notifications": WebhookNotifications(
            on_start=[Webhook(id=slack_dest.id)],
            on_success=[Webhook(id=slack_dest.id)],
            on_failure=[Webhook(id=slack_dest.id), Webhook(id=pagerduty_dest.id)],
        ),
    },
)
```

Or in `databricks.yml` Asset Bundle config:
```yaml
resources:
  jobs:
    daily_etl:
      name: daily-etl
      email_notifications:
        on_failure:
          - oncall@company.com
      webhook_notifications:
        on_failure:
          - id: "<notification-destination-id>"
```

### Step 3: Build a Custom Webhook Handler
Receive Databricks job events at your own endpoint. Databricks sends a JSON payload with run details.

```python
# webhook_handler.py — deploy as a Flask/FastAPI endpoint
from fastapi import FastAPI, Request
import json

app = FastAPI()

@app.post("/databricks/webhook")
async def handle_databricks_event(request: Request):
    payload = await request.json()

    # Databricks webhook payload structure
    event_type = payload.get("event_type")  # "jobs.on_failure", "jobs.on_success", etc.
    run_id = payload.get("run", {}).get("run_id")
    job_name = payload.get("job", {}).get("name")
    result_state = payload.get("run", {}).get("result_state")  # SUCCESS, FAILED, TIMED_OUT

    if result_state == "FAILED":
        error_msg = payload.get("run", {}).get("state_message", "Unknown error")
        # Route to PagerDuty, create Jira ticket, etc.
        await create_incident(job_name=job_name, run_id=run_id, error=error_msg)

    return {"status": "ok"}
```

### Step 4: Monitor Events via System Tables
Query the `system.access.audit` table for real-time event monitoring without webhooks.

```sql
-- Recent job events (last 6 hours)
SELECT event_time, user_identity.email AS actor,
       action_name, request_params.job_id, request_params.run_id,
       response.status_code, response.error_message
FROM system.access.audit
WHERE service_name = 'jobs'
  AND action_name IN ('runNow', 'submitRun', 'cancelRun', 'repairRun')
  AND event_date >= current_date()
  AND event_time > current_timestamp() - INTERVAL 6 HOURS
ORDER BY event_time DESC;

-- Permission changes (security audit)
SELECT event_time, user_identity.email, action_name,
       request_params
FROM system.access.audit
WHERE action_name IN ('changeJobPermissions', 'changeClusterPermissions',
                       'updatePermissions', 'grantPermission')
  AND event_date >= current_date() - 7
ORDER BY event_time DESC;
```

### Step 5: Set Up SQL Alerts
Create automated alerts that fire when query conditions are met.

```sql
-- Alert query: detect job failures exceeding threshold
-- Create this as a Databricks SQL Alert (SQL Editor > Alerts > New Alert)
-- Trigger condition: failure_count > 3
-- Schedule: every 15 minutes
-- Destination: Slack notification destination

SELECT COUNT(*) AS failure_count,
       COLLECT_LIST(DISTINCT job_name) AS failed_jobs
FROM (
    SELECT j.name AS job_name
    FROM system.lakeflow.job_run_timeline r
    JOIN system.lakeflow.jobs j ON r.job_id = j.job_id
    WHERE r.result_state = 'FAILED'
      AND r.start_time > current_timestamp() - INTERVAL 1 HOUR
);
```

```python
# Programmatically create an alert via SDK
alert = w.alerts.create(
    name="High Job Failure Rate",
    query_id="<sql-query-id>",
    options={
        "column": "failure_count",
        "op": ">",
        "value": "3",
    },
    rearm=900,  # Re-alert after 15 minutes if still triggered
)

# Attach notification destination
w.alerts.create_schedule(
    alert_id=alert.id,
    cron="*/15 * * * *",
    notification_destinations=[slack_dest.id],
)
```

## Output
- Notification destinations registered (Slack, email, PagerDuty, custom webhook)
- Job lifecycle notifications configured (on_start, on_success, on_failure)
- Custom webhook handler ready for deployment
- System table queries for event auditing
- SQL alerts with automated triggers and destinations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RESOURCE_DOES_NOT_EXIST` for destination ID | Destination deleted or wrong workspace | List destinations: `w.notification_destinations.list()` |
| Webhook not triggered | Destination URL unreachable from Databricks | Test URL accessibility from workspace network; check firewall/VPN rules |
| Duplicate notifications | Same destination on both job and task level | Configure notifications at job level only, remove task-level duplicates |
| Alert never fires | Query returns no rows or wrong column name | Test alert query manually in SQL Editor first |
| System tables empty | Unity Catalog not enabled or audit logs disabled | Enable system tables in account admin settings |

## Examples

### Slack Message Formatter
```python
def format_slack_message(payload: dict) -> dict:
    """Format Databricks job event as a rich Slack message."""
    run = payload.get("run", {})
    job = payload.get("job", {})
    status = run.get("result_state", "UNKNOWN")
    emoji = {"SUCCESS": ":white_check_mark:", "FAILED": ":x:", "TIMED_OUT": ":hourglass:"}.get(status, ":question:")

    return {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {job.get('name', 'Unknown Job')}"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Status:* {status}"},
                {"type": "mrkdwn", "text": f"*Run ID:* {run.get('run_id')}"},
                {"type": "mrkdwn", "text": f"*Duration:* {run.get('execution_duration', 0) // 1000}s"},
            ]},
        ]
    }
```

### List All Notification Destinations
```bash
databricks notification-destinations list --output json | \
  jq '.[] | {name: .display_name, type: .destination_type, id: .id}'
```

## Resources
- [Job Notifications](https://docs.databricks.com/workflows/jobs/job-notifications.html)
- [Notification Destinations](https://docs.databricks.com/administration-guide/workspace/notification-destinations.html)
- [System Tables Reference](https://docs.databricks.com/administration-guide/system-tables/index.html)
- [SQL Alerts](https://docs.databricks.com/sql/admin/alerts.html)

## Next Steps
For performance tuning, see `databricks-performance-tuning`.
