---
name: linear-webhooks-events
description: |
  Configure and handle Linear webhooks for real-time event processing.
  Use when setting up webhooks, handling Linear events,
  or building real-time integrations.
  Trigger with phrases like "linear webhooks", "linear events",
  "linear real-time", "handle linear webhook", "linear webhook setup".
allowed-tools: Read, Write, Edit, Bash(ngrok:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear Webhooks & Events

## Overview
Set up and handle Linear webhooks for real-time event notifications.

## Prerequisites
- Linear workspace admin access
- Public endpoint for webhook delivery
- Webhook signing secret configured

## Instructions
- Step 1: Create Webhook Endpoint
- Step 2: Event Processing Router
- Step 3: Business Logic Handlers
- Step 4: Register Webhook in Linear
- Step 5: Local Development with ngrok
- Step 6: Idempotent Event Processing

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid signature` | Wrong secret or tampering | Verify webhook secret |
| `Timeout` | Processing too slow | Use async queue |
| `Duplicate events` | Webhook retry | Implement idempotency |
| `Missing data` | Partial event | Handle gracefully |

## Resources
- [Linear Webhooks Documentation](https://developers.linear.app/docs/graphql/webhooks)
- [Webhook Events Reference](https://developers.linear.app/docs/graphql/webhooks#webhook-events)
- [ngrok Documentation](https://ngrok.com/docs)

## Next Steps
Optimize performance with `linear-performance-tuning`.
