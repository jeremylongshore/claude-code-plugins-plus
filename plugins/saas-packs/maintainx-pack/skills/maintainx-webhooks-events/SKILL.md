---
name: maintainx-webhooks-events
description: |
  Implement MaintainX webhook handling and event-driven integrations.
  Use when setting up webhooks, handling MaintainX events,
  or building real-time integrations with MaintainX.
  Trigger with phrases like "maintainx webhook", "maintainx events",
  "maintainx notifications", "maintainx real-time", "maintainx triggers".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Webhooks & Events

## Overview
Build real-time integrations with MaintainX using webhooks and event-driven patterns for work order updates, asset changes, and maintenance notifications.

## Prerequisites
- MaintainX account with webhook access
- HTTPS endpoint accessible from internet
- Understanding of webhook security patterns

## Instructions
Follow these high-level steps to implement maintainx-webhooks-events:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-webhooks-events/references/implementation-guide.md)`

## Output
- Webhook endpoint with signature verification
- Event handler pattern implemented
- Idempotency handling
- Testing tools configured
- Retry queue for reliability
- Admin dashboard for monitoring

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [Webhook Security Best Practices](https://hookdeck.com/webhooks/guides/webhook-security-vulnerabilities-guide)
- [Bull Queue Documentation](https://github.com/OptimalBits/bull)

## Next Steps
For performance optimization, see `maintainx-performance-tuning`.
