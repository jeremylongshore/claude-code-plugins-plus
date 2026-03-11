---
name: clerk-webhooks-events
description: |
  Configure Clerk webhooks and handle authentication events.
  Use when setting up user sync, handling auth events,
  or integrating Clerk with external systems.
  Trigger with phrases like "clerk webhooks", "clerk events",
  "clerk user sync", "clerk notifications", "clerk event handling".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Webhooks & Events

## Overview
Configure and handle Clerk webhooks for user lifecycle events and data synchronization.

## Prerequisites
- Clerk account with webhook access
- HTTPS endpoint for webhooks
- svix package for verification

## Instructions
- Step 1: Install Dependencies
- Step 2: Create Webhook Endpoint
- Step 3: Implement Event Handlers
- Step 4: Idempotency and Error Handling
- Step 5: Configure Webhook in Clerk Dashboard

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Webhook endpoint configured
- Event handlers implemented
- Idempotency protection
- User data sync working

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify CLERK_WEBHOOK_SECRET |
| Missing headers | Request not from Clerk | Check sender is Clerk |
| Duplicate processing | Event sent twice | Implement idempotency |
| Timeout | Handler too slow | Use background jobs |

## Resources
- [Clerk Webhooks](https://clerk.com/docs/integrations/webhooks/overview)
- [Svix Verification](https://docs.svix.com/receiving/verifying-payloads)
- [Event Types](https://clerk.com/docs/integrations/webhooks/sync-data)

## Next Steps
Proceed to `clerk-performance-tuning` for optimization strategies.
