---
name: speak-webhooks-events
description: |
  Implement Speak webhook signature validation and event handling for language learning.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Speak event notifications for lessons and progress.
  Trigger with phrases like "speak webhook", "speak events",
  "speak webhook signature", "handle speak events", "speak notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Speak Webhooks Events

## Overview
Securely handle Speak webhooks with signature validation for language learning event notifications.

## Prerequisites
- Speak webhook secret configured
- HTTPS endpoint accessible from internet
- Understanding of cryptographic signatures
- Redis or database for idempotency (optional)

## Instructions
1. **Speak Event Types**
2. **Webhook Endpoint Setup**
3. **Signature Verification**
4. **Event Handler Pattern**
5. **Idempotency Handling**
6. **Webhook Testing**
7. **Local Development with ngrok**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Secure webhook endpoint
- Signature validation enabled
- Event handlers implemented
- Replay attack protection active
- Idempotency for duplicate prevention

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify webhook secret |
| Timestamp rejected | Clock drift | Check server time sync |
| Duplicate events | Missing idempotency | Implement event ID tracking |
| Handler timeout | Slow processing | Use async queue |
| Event not recognized | New event type | Add handler or log |

## Resources
- [Speak Webhooks Guide](https://developer.speak.com/docs/webhooks)
- [Webhook Security Best Practices](https://developer.speak.com/docs/webhooks/security)
- [Event Reference](https://developer.speak.com/docs/events)

## Next Steps
For performance optimization, see `speak-performance-tuning`.
