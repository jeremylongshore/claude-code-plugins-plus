---
name: "cloud-tasks-queue-setup"
description: |
  Configure cloud tasks queue setup operations. Auto-activating skill for GCP Skills.
  Triggers on: cloud tasks queue setup, cloud tasks queue setup
  Part of the GCP Skills skill category. Use when working with cloud tasks queue setup functionality. Trigger with phrases like "cloud tasks queue setup", "cloud setup", "cloud".
allowed-tools: "Read, Write, Edit, Bash(gcloud:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
---

# Cloud Tasks Queue Setup

## Overview

Create and configure Google Cloud Tasks queues for reliable asynchronous task execution. Covers queue creation with rate limiting and retry policies, HTTP and App Engine task targets, task dispatching with scheduling delays, and queue management operations (pause, resume, purge).

## Prerequisites

- Google Cloud project with Cloud Tasks API enabled (`gcloud services enable cloudtasks.googleapis.com`)
- `gcloud` CLI authenticated with `roles/cloudtasks.admin` or `roles/cloudtasks.enqueuer` IAM role
- Target HTTP endpoint or App Engine service to receive dispatched tasks
- Service account with appropriate permissions for task execution

## Instructions

1. Create a Cloud Tasks queue with rate limiting: `gcloud tasks queues create <queue-name> --location=<region> --max-dispatches-per-second=10 --max-concurrent-dispatches=5`
2. Configure retry policy for failed tasks: `gcloud tasks queues update <queue-name> --max-attempts=5 --min-backoff=1s --max-backoff=300s --max-doublings=4`
3. Create an HTTP task targeting your endpoint: `gcloud tasks create-http-task --queue=<queue-name> --url=https://your-service.run.app/process --method=POST --body-content='<json-payload>'`
4. Schedule a delayed task by adding `--schedule-time` with an ISO 8601 timestamp up to 30 days in the future
5. Verify queue status and task counts: `gcloud tasks queues describe <queue-name>` to check dispatch rate, retry config, and queue state
6. Manage queue operations: pause (`gcloud tasks queues pause`), resume (`gcloud tasks queues resume`), or purge all tasks (`gcloud tasks queues purge`)

## Examples

**Setting up an email processing queue**: Create a queue with 5 dispatches per second rate limit and 3 max concurrent tasks to avoid overwhelming the email service. Configure retry with exponential backoff (1s min, 60s max, 3 doublings) and 10 max attempts for transient failures.

**Scheduling delayed webhook callbacks**: Create HTTP tasks with a 15-minute schedule delay to implement webhook retries. Each task POSTs to the callback URL with the original event payload and includes an OIDC token for authentication.

## Output

- Cloud Tasks queue created with rate limiting and retry configuration
- Task creation commands for HTTP and App Engine targets
- Queue management commands for operational control

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Queue already exists | Queue name taken in the specified region | Use `gcloud tasks queues describe` to check existing config; update if needed |
| PERMISSION_DENIED on task creation | Service account lacks `cloudtasks.tasks.create` permission | Grant `roles/cloudtasks.enqueuer` to the service account |
| Task handler returns 5xx | Target endpoint failed to process the task | Tasks auto-retry per queue retry policy; check handler logs for root cause |
| Rate limit exceeded | Dispatch rate exceeds queue configuration | Increase `max-dispatches-per-second` or reduce task creation rate |

## Resources

- Cloud Tasks documentation: https://cloud.google.com/tasks/docs
- Queue configuration reference: https://cloud.google.com/tasks/docs/configuring-queues
- Creating HTTP tasks: https://cloud.google.com/tasks/docs/creating-http-target-tasks
- IAM permissions: https://cloud.google.com/tasks/docs/access-control

## Related Skills

Part of the **GCP Skills** skill category.
Tags: gcp, bigquery, vertex-ai, cloud-run, firebase
