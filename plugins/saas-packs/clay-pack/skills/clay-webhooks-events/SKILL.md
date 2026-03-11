---
name: clay-webhooks-events
description: |
  Implement Clay webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Clay event notifications securely.
  Trigger with phrases like "clay webhook", "clay events",
  "clay webhook signature", "handle clay events", "clay notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Webhooks & Events

## Overview

Handle Clay webhooks for real-time notifications when data enrichment completes, tables update, or workflows finish. Respond 200 immediately and process events asynchronously.

## Prerequisites

- Clay account with API access and webhook configuration enabled
- HTTPS endpoint accessible from the internet
- Clay API key stored in `CLAY_API_KEY` environment variable
- Familiarity with Clay table and enrichment concepts

## Webhook Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `enrichment.completed` | Column enrichment finishes | Row data, enrichment results |
| `enrichment.failed` | Enrichment errors out | Row ID, error details |
| `table.row.created` | New row added to table | Full row data |
| `table.row.updated` | Row data changes | Changed fields, row ID |
| `table.export.completed` | Table export finishes | Export URL, row count |
| `workflow.completed` | Automated workflow ends | Workflow ID, results summary |

## Instructions

### Step 1: Configure Webhook Endpoint

Create an Express endpoint that validates the `x-clay-signature` header using HMAC-SHA256 with `crypto.timingSafeEqual`. Respond 200 before processing.

### Step 2: Route Events by Type

Switch on `payload.event` to dispatch to specific handlers for enrichment completion, failures, new rows, and exports.

### Step 3: Handle Enrichment Results

On `enrichment.completed`, push enriched data (company info, LinkedIn data) to your CRM. On `enrichment.failed`, queue for retry with the error details.

### Step 4: Register Webhook via Clay API

POST to `https://api.clay.com/v1/webhooks` with your endpoint URL, desired event types, and table ID.

For complete TypeScript implementations and curl examples, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong webhook secret | Verify secret in Clay dashboard settings |
| Missing enrichment data | Column not configured | Check enrichment column setup in table |
| Duplicate events | Retry delivery | Track `row_id + timestamp` for idempotency |
| Webhook timeout | Slow handler | Respond 200 immediately, process async |

## Resources

- [Clay API Documentation](https://docs.clay.com/api)
- [Clay Webhooks Guide](https://docs.clay.com/webhooks)

## Next Steps

For performance optimization, see `clay-performance-tuning`.
