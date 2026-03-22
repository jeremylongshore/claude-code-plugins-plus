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
tags: [saas, databricks, webhooks]

---
# Databricks Webhooks & Events

## Overview
Configure notifications and event-driven workflows for Databricks jobs. Covers notification destinations (Slack, Teams, PagerDuty, email, generic webhooks), job lifecycle events, SQL alerts with automated triggers, and system table queries for event auditing.

## Prerequisites
- Databricks workspace admin access (for notification destinations)
- Webhook endpoint URL (Slack incoming webhook, Teams connector, etc.)
- Job permissions for notification configuration

## Instructions

### Step 1: Create Notification Destinations
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.settings import (
    CreateNotificationDestinationRequest,
    SlackConfig, EmailConfig, GenericWebhookConfig,
)

w = WorkspaceClient()

# Slack destination
slack = w.notification_destinations.create(
    display_name="Engineering Slack",
    config=SlackConfig(url="https://hooks.slack.com/services/T00/B00/xxxx"),
)

# Email destination
email = w.notification_destinations.create(
    display_name="Oncall Email",
    config=EmailConfig(addresses=["oncall@company.com", "data-team@company.com"]),
)

# Generic webhook (PagerDuty, custom endpoint)
pagerduty = w.notification_destinations.create(
    display_name="PagerDuty",
    config=GenericWebhookConfig(
        url="https://events.pagerduty.com/integration/YOUR_KEY/enqueue",
    ),
)

print(f"Slack: {slack.id}, Email: {email.id}, PD: {pagerduty.id}")
```

### Step 2: Attach Notifications to Jobs
```python
from databricks.sdk.service.jobs import (
    JobEmailNotifications, WebhookNotifications, Webhook,
)

# Update existing job with notifications
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
            on_start=[Webhook(id=slack.id)],
            on_success=[Webhook(id=slack.id)],
            on_failure=[Webhook(id=slack.id), Webhook(id=pagerduty.id)],
        ),
    },
)
```

Or declaratively in Asset Bundles:
```yaml
# resources/jobs.yml
resources:
  jobs:
    daily_etl:
      email_notifications:
        on_failure: ["oncall@company.com"]
      webhook_notifications:
        on_failure:
          - id: "<notification-destination-id>"
```

### Step 3: Build Custom Webhook Handler
Receive Databricks job events at your own endpoint.

```python
# webhook_handler.py — FastAPI endpoint
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.post("/databricks/webhook")
async def handle_event(request: Request):
    payload = await request.json()

    event_type = payload.get("event_type")        # "jobs.on_failure", "jobs.on_success"
    run_id = payload.get("run", {}).get("run_id")
    job_name = payload.get("job", {}).get("name")
    result = payload.get("run", {}).get("result_state")  # SUCCESS, FAILED, TIMED_OUT
    error_msg = payload.get("run", {}).get("state_message", "")

    if result == "FAILED":
        # Route to PagerDuty
        await httpx.AsyncClient().post(
            "https://events.pagerduty.com/v2/enqueue",
            json={
                "routing_key": "YOUR_INTEGRATION_KEY",
                "event_action": "trigger",
                "payload": {
                    "summary": f"Databricks job failed: {job_name}",
                    "severity": "critical",
                    "source": f"databricks-run-{run_id}",
                    "custom_details": {"error": error_msg, "run_id": run_id},
                },
            },
        )

    return {"status": "ok"}
```

### Step 4: Monitor Events via System Tables
Query `system.access.audit` for event monitoring without webhooks.

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
SELECT event_time, user_identity.email, action_name, request_params
FROM system.access.audit
WHERE action_name IN ('changeJobPermissions', 'changeClusterPermissions',
                       'updatePermissions', 'grantPermission')
  AND event_date >= current_date() - 7
ORDER BY event_time DESC;
```

### Step 5: SQL Alerts with Automated Triggers
Create alerts that fire when query conditions are met.

```sql
-- Alert query: detect excessive failures
-- Create in SQL Editor > Alerts > New Alert
-- Trigger: failure_count > 3
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
# Create alert programmatically
alert = w.alerts.create(
    name="High Job Failure Rate",
    query_id="<saved-query-id>",
    options={"column": "failure_count", "op": ">", "value": "3"},
    rearm=900,  # Re-alert after 15 min if still triggered
)
```

### Step 6: Slack Message Formatter
```python
def format_slack_message(payload: dict) -> dict:
    """Format Databricks job event as a rich Slack Block Kit message."""
    run = payload.get("run", {})
    job = payload.get("job", {})
    status = run.get("result_state", "UNKNOWN")
    emoji = {"SUCCESS": ":white_check_mark:", "FAILED": ":x:", "TIMED_OUT": ":hourglass:"}.get(status, ":question:")
    duration_sec = run.get("execution_duration", 0) // 1000

    return {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {job.get('name', 'Unknown')}"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Status:* {status}"},
                {"type": "mrkdwn", "text": f"*Run ID:* {run.get('run_id')}"},
                {"type": "mrkdwn", "text": f"*Duration:* {duration_sec}s"},
                {"type": "mrkdwn", "text": f"*Error:* {run.get('state_message', 'none')[:200]}"},
            ]},
        ]
    }
```

## Output
- Notification destinations registered (Slack, email, PagerDuty)
- Job lifecycle notifications (on_start, on_success, on_failure)
- Custom webhook handler for advanced routing
- System table queries for event auditing
- SQL alerts with automated triggers and destinations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RESOURCE_DOES_NOT_EXIST` for destination | Destination deleted or wrong workspace | `w.notification_destinations.list()` to verify |
| Webhook not triggered | URL unreachable from Databricks network | Check firewall; Databricks needs outbound access to webhook URL |
| Duplicate notifications | Same destination on job AND task level | Configure at job level only |
| Alert never fires | Query returns 0 rows or wrong column | Test query in SQL Editor first |
| System tables empty | Unity Catalog not enabled | Enable system tables in Account Console |

## Examples

### List All Notification Destinations
```bash
databricks notification-destinations list --output json | \
  jq '.[] | {name: .display_name, type: .destination_type, id: .id}'
```

## Resources
- [Job Notifications](https://docs.databricks.com/aws/en/jobs/monitor)
- [Notification Destinations](https://docs.databricks.com/aws/en/admin/notification-destinations)
- [System Tables](https://docs.databricks.com/aws/en/admin/system-tables/)
- [SQL Alerts](https://docs.databricks.com/aws/en/sql/user/alerts/)

## Next Steps
For performance tuning, see `databricks-performance-tuning`.
