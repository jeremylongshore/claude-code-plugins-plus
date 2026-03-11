# Databricks Webhooks & Events - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Configure Job Notifications

```yaml
resources:
  jobs:
    etl_pipeline:
      name: etl-pipeline

      # Email notifications
      email_notifications:
        on_start:
          - team@company.com
        on_success:
          - success-alerts@company.com
        on_failure:
          - oncall@company.com
          - pagerduty@company.pagerduty.com
        on_duration_warning_threshold_exceeded:
          - oncall@company.com
        no_alert_for_skipped_runs: true
        no_alert_for_canceled_runs: false

      # Webhook notifications
      webhook_notifications:
        on_start:
          - id: ${var.slack_webhook_id}
        on_success:
          - id: ${var.slack_webhook_id}
        on_failure:
          - id: ${var.pagerduty_webhook_id}
          - id: ${var.slack_webhook_id}

      # System notification destinations
      notification_settings:
        no_alert_for_skipped_runs: true
        no_alert_for_canceled_runs: false
```

### Step 2: Create Webhook Destinations

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.settings import (
    CreateNotificationDestinationRequest,
    SlackConfig,
    MicrosoftTeamsConfig,
    PagerdutyConfig,
    GenericWebhookConfig,
)

def setup_slack_webhook(
    w: WorkspaceClient,
    name: str,
    webhook_url: str,
) -> str:
    """Create Slack notification destination."""
    destination = w.notification_destinations.create(
        display_name=name,
        config=SlackConfig(url=webhook_url),
    )
    return destination.id

def setup_teams_webhook(
    w: WorkspaceClient,
    name: str,
    webhook_url: str,
) -> str:
    """Create Microsoft Teams notification destination."""
    destination = w.notification_destinations.create(
        display_name=name,
        config=MicrosoftTeamsConfig(url=webhook_url),
    )
    return destination.id

def setup_pagerduty_webhook(
    w: WorkspaceClient,
    name: str,
    integration_key: str,
) -> str:
    """Create PagerDuty notification destination."""
    destination = w.notification_destinations.create(
        display_name=name,
        config=PagerdutyConfig(
            integration_key=integration_key,
        ),
    )
    return destination.id

def setup_generic_webhook(
    w: WorkspaceClient,
    name: str,
    webhook_url: str,
    username: str = None,
    password: str = None,
) -> str:
    """Create generic webhook destination."""
    config = GenericWebhookConfig(
        url=webhook_url,
        username=username,
        password=password,
    )
    destination = w.notification_destinations.create(
        display_name=name,
        config=config,
    )
    return destination.id

w = WorkspaceClient()

slack_id = setup_slack_webhook(
    w,
    "Data Team Slack",
    "https://hooks.slack.com/services/T00/B00/XXX"
)
print(f"Slack webhook ID: {slack_id}")
```

### Step 3: Custom Webhook Handler

```python
from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

@app.route("/databricks/webhook", methods=["POST"])
def handle_databricks_webhook():
    """Handle incoming Databricks job notifications."""
    payload = request.json

    # Parse Databricks webhook payload
    event_type = payload.get("event_type")
    job_id = payload.get("job_id")
    run_id = payload.get("run_id")
    run_page_url = payload.get("run_page_url")

    # Job run state info
    state = payload.get("state", {})
    life_cycle_state = state.get("life_cycle_state")
    result_state = state.get("result_state")
    state_message = state.get("state_message")

    # Process based on event type
    if event_type == "jobs.on_failure":
        handle_job_failure(payload)
    elif event_type == "jobs.on_success":
        handle_job_success(payload)
    elif event_type == "jobs.on_start":
        handle_job_start(payload)

    return jsonify({"status": "received"})

def handle_job_failure(payload: dict):
    """Process job failure notification."""
    job_name = payload.get("job_name", "Unknown Job")
    run_id = payload.get("run_id")
    error_message = payload.get("state", {}).get("state_message", "")

    # Send to Slack
    slack_message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Job Failed: {job_name}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Run ID:* {run_id}"},
                    {"type": "mrkdwn", "text": f"*Time:* {datetime.now().isoformat()}"},
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:* {error_message[:500]}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Run"},
                        "url": payload.get("run_page_url"),
                    }
                ]
            }
        ]
    }

    # Send to Slack (implement your Slack client)
    # slack_client.send_message(slack_message)

    # Create PagerDuty incident
    # pagerduty_client.create_incident(...)

def handle_job_success(payload: dict):
    """Process job success notification."""
    # Log metrics, update dashboards, etc.
    pass

def handle_job_start(payload: dict):
    """Process job start notification."""
    # Update job tracking, send start notification, etc.
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Step 4: System Tables for Event Monitoring

```sql
-- Query job run events from system tables
SELECT
    job_id,
    job_name,
    run_id,
    result_state,
    error_message,
    start_time,
    end_time,
    (end_time - start_time) / 1000 / 60 as duration_minutes
FROM system.lakeflow.job_run_timeline
WHERE start_time > current_timestamp() - INTERVAL 24 HOURS
ORDER BY start_time DESC;

-- Alert on failures
SELECT *
FROM system.lakeflow.job_run_timeline
WHERE result_state = 'FAILED'
  AND start_time > current_timestamp() - INTERVAL 1 HOUR;

-- Calculate failure rate by job
SELECT
    job_name,
    COUNT(*) as total_runs,
    SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) as failures,
    ROUND(SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate
FROM system.lakeflow.job_run_timeline
WHERE start_time > current_timestamp() - INTERVAL 7 DAYS
GROUP BY job_name
HAVING failure_rate > 5
ORDER BY failure_rate DESC;
```

### Step 5: SQL Alert Integration

```sql
-- Create SQL alert for job failures
CREATE ALERT job_failure_alert
AS SELECT
    COUNT(*) as failure_count,
    COLLECT_LIST(job_name) as failed_jobs
FROM system.lakeflow.job_run_timeline
WHERE result_state = 'FAILED'
  AND start_time > current_timestamp() - INTERVAL 15 MINUTES
HAVING failure_count > 0
SCHEDULE CRON '0/15 * * * *'
NOTIFICATIONS (
    email_addresses = ['oncall@company.com'],
    webhook_destinations = ['slack-alerts']
);
```


## Complete Examples

### Slack Block Kit Message
```python
def format_slack_notification(run_info: dict) -> dict:
    """Format rich Slack notification."""
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{run_info['status_emoji']} Job: {run_info['job_name']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Status:* {run_info['status']}"},
                    {"type": "mrkdwn", "text": f"*Duration:* {run_info['duration']}"},
                    {"type": "mrkdwn", "text": f"*Run ID:* {run_info['run_id']}"},
                    {"type": "mrkdwn", "text": f"*Cluster:* {run_info['cluster']}"},
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Run"},
                        "url": run_info['run_url'],
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Logs"},
                        "url": run_info['logs_url']
                    }
                ]
            }
        ]
    }
```
