---
name: juicebox-webhooks-events
description: |
  Implement Juicebox webhook handling.
  Use when setting up event notifications, processing webhooks,
  or integrating real-time updates from Juicebox.
  Trigger with phrases like "juicebox webhooks", "juicebox events",
  "juicebox notifications", "juicebox real-time".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox Webhooks & Events

## Overview
Implement webhook handlers for real-time Juicebox events and notifications.

## Prerequisites
- Juicebox account with webhooks enabled
- HTTPS endpoint for webhook delivery
- Request signature verification capability

## Instructions
- Step 1: Register Webhook Endpoint
- Step 2: Implement Webhook Handler
- Step 3: Process Different Event Types
- Step 4: Implement Retry Logic

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Webhook endpoint handler
- Signature verification
- Event type processors
- Retry queue with backoff

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify webhook secret |
| Duplicate events | Network retry | Implement idempotency |
| Processing timeout | Slow handler | Use async queue |

## Resources
- [Webhooks Documentation](https://juicebox.ai/docs/webhooks)
- [Event Reference](https://juicebox.ai/docs/events)

## Next Steps
After webhooks, see `juicebox-performance-tuning` for optimization.
