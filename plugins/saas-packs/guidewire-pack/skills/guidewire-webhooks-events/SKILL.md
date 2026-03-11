---
name: guidewire-webhooks-events
description: |
  Implement Guidewire App Events and webhook integrations for event-driven architecture.
  Use when setting up outbound events, message queuing, webhook receivers,
  or asynchronous integration patterns.
  Trigger with phrases like "guidewire webhooks", "app events",
  "event-driven", "message queue", "guidewire notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Guidewire Webhooks & Events

## Overview
Implement event-driven integrations using Guidewire App Events, webhooks, and message queuing for real-time notifications and asynchronous processing.

## Prerequisites
- Guidewire Cloud Console access
- Understanding of event-driven architecture
- HTTPS endpoint for webhook receiver
- Message queue service (optional)

## Instructions

### Step 1: App Events Architecture
+------------------+      +------------------+      +------------------+
### Step 2: Instructions
events:
### Step 3: Event Types Reference
Implement event types reference.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- App Events Architecture
- Instructions
- Event Types Reference

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify webhook secret |
| Event timeout | Slow processing | Use async queue |
| Duplicate events | Missing idempotency | Track processed event IDs |
| Delivery failure | Endpoint down | Check webhook endpoint |

## Resources
- [Guidewire App Events](https://docs.guidewire.com/education/cloud-integration-basics/latest/docs/integration_cloud_basics/appevents_overview/)
- [Integration Gateway](https://www.guidewire.com/developers/developer-tools-and-guides/integration-framework)

## Next Steps
For performance optimization, see `guidewire-performance-tuning`.
