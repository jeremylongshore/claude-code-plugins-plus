---
name: lokalise-webhooks-events
description: |
  Implement Lokalise webhook handling and event processing.
  Use when setting up webhook endpoints, handling translation events,
  or building automation based on Lokalise notifications.
  Trigger with phrases like "lokalise webhook", "lokalise events",
  "lokalise notifications", "handle lokalise events", "lokalise automation".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Webhooks Events

## Overview
Handle Lokalise webhooks for real-time translation updates and automation.

## Prerequisites
- Lokalise project with webhook access
- HTTPS endpoint accessible from internet
- Understanding of webhook security
- Queue system for reliable processing (optional)

## Instructions
1. **Webhook Event Types**
2. **Instructions**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Webhook endpoint receiving events
- Secret verification enabled
- Event handlers for key scenarios
- Async processing with error handling

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify webhook secret in Lokalise |
| Timeout (8 seconds) | Slow processing | Process async, respond immediately |
| Duplicate events | Retry after failure | Implement idempotency |
| Missing events | Handler not registered | Subscribe to event in Lokalise |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [Lokalise Webhooks Guide](https://developers.lokalise.com/docs/webhooks-guide)
- [Webhook Events Reference](https://developers.lokalise.com/docs/webhook-events)
- [Webhooks API](https://developers.lokalise.com/reference/list-project-webhooks)

## Next Steps
For performance optimization, see `lokalise-performance-tuning`.