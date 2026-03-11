---
name: documenso-webhooks-events
description: |
  Implement Documenso webhook configuration and event handling.
  Use when setting up webhook endpoints, handling document events,
  or implementing real-time notifications for document signing.
  Trigger with phrases like "documenso webhook", "documenso events",
  "document completed webhook", "signing notification".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(ngrok:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Webhooks & Events

## Overview
Configure and handle Documenso webhooks for real-time document signing notifications.

## Prerequisites
- Documenso team account (webhooks require teams)
- HTTPS endpoint for webhook reception
- Understanding of webhook security

## Instructions

### Step 1: Supported Events
Implement supported events.
### Step 2: Webhook Setup
1. Log into Documenso dashboard
### Step 3: Local Development
ngrok http 3000
### Step 4: Testing Webhooks
curl -X POST http://localhost:3000/webhooks/documenso \

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Supported Events
- Webhook Setup
- Local Development
- Testing Webhooks

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Wrong secret | Check webhook secret |
| Webhook not received | URL not HTTPS | Use HTTPS endpoint |
| Duplicate processing | No idempotency | Add deduplication |
| Timeout | Slow handler | Use async queue |

## Resources
- [Documenso Webhooks](https://docs.documenso.com/developers/webhooks)
- [ngrok Documentation](https://ngrok.com/docs)
- [Webhook Best Practices](https://webhooks.fyi/)

## Next Steps
For performance optimization, see `documenso-performance-tuning`.

## Examples

**Basic usage**: Apply documenso webhooks events to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso webhooks events for production environments with multiple constraints and team-specific requirements.