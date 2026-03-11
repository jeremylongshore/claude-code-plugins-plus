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
Configure notifications and event handling for Databricks jobs and pipelines.

## Prerequisites
- Databricks workspace access
- Webhook endpoint (Slack, Teams, PagerDuty, etc.)
- Job permissions for notification configuration

## Instructions

### Step 1: Configure Job Notifications

### Step 2: Create Webhook Destinations

### Step 3: Custom Webhook Handler

### Step 4: System Tables for Event Monitoring

### Step 5: SQL Alert Integration

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Configured notification destinations
- Job notifications active
- Custom webhook handler deployed
- Monitoring queries ready

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not triggered | Invalid destination ID | Verify destination exists |
| Email not received | Invalid email | Check email addresses |
| Duplicate notifications | Multiple configs | Deduplicate notification settings |
| Webhook timeout | Slow handler | Optimize webhook endpoint |

## Resources
- [Job Notifications](https://docs.databricks.com/workflows/jobs/job-notifications.html)
- [Notification Destinations](https://docs.databricks.com/administration-guide/workspace/notification-destinations.html)
- [System Tables](https://docs.databricks.com/administration-guide/system-tables/index.html)

## Next Steps
For performance tuning, see `databricks-performance-tuning`.
