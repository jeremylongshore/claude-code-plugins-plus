---
name: apollo-webhooks-events
description: |
  Implement Apollo.io webhook handling.
  Use when receiving Apollo webhooks, processing event notifications,
  or building event-driven integrations.
  Trigger with phrases like "apollo webhooks", "apollo events",
  "apollo notifications", "apollo webhook handler", "apollo triggers".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Webhooks Events

## Overview
Implement webhook handlers for Apollo.io to receive real-time notifications about contact updates, sequence events, and engagement activities.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-webhooks-events:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-webhooks-events/references/implementation-guide.md)`

## Output
- Webhook endpoint with signature verification
- Event handlers for all Apollo event types
- Database sync for contact and engagement data
- Webhook registration instructions
- Test suite for webhook validation

## Error Handling
| Issue | Resolution |
|-------|------------|
| Invalid signature | Check webhook secret |
| Unknown event | Log and acknowledge (200) |
| Processing error | Log error, return 500 |
| Duplicate events | Implement idempotency |

## Resources
- [Apollo Webhooks Documentation](https://knowledge.apollo.io/hc/en-us/articles/4415154183053)
- [Webhook Security Best Practices](https://hookdeck.com/webhooks/guides/webhook-security-best-practices)
- [ngrok for Local Testing](https://ngrok.com/)

## Next Steps
Proceed to `apollo-performance-tuning` for optimization.

## Examples

**Basic usage**: Apply apollo webhooks events to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo webhooks events for production environments with multiple constraints and team-specific requirements.