---
name: lindy-webhooks-events
description: |
  Configure Lindy AI webhooks and event handling.
  Use when setting up webhooks, handling events,
  or building event-driven integrations.
  Trigger with phrases like "lindy webhook", "lindy events",
  "lindy event handler", "lindy callbacks".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Webhooks & Events

## Overview
Configure webhooks and event-driven integrations with Lindy AI.

## Prerequisites
- Lindy account with webhook access
- HTTPS endpoint for receiving webhooks
- Understanding of event types

## Instructions

### Step 1: Register Webhook
### Step 2: Create Webhook Handler
### Step 3: Implement Event Handlers
### Step 4: Test Webhooks

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Event Types

| Event | Description | Payload |
|-------|-------------|---------|
| `agent.run.started` | Agent run began | runId, agentId, input |
| `agent.run.completed` | Agent run finished | runId, output, duration |
| `agent.run.failed` | Agent run failed | runId, error, errorCode |
| `automation.triggered` | Automation fired | automationId, input |
| `agent.created` | New agent created | agentId, name |
| `agent.deleted` | Agent deleted | agentId |

## Output
- Registered webhooks
- Event handler implementation
- Signature verification
- Event logging

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Check WEBHOOK_SECRET |
| Timeout | Handler slow | Respond quickly, process async |
| Duplicate events | Retry delivery | Implement idempotency |

## Examples

### Async Processing Pattern
## Resources
- [Lindy Webhooks](https://docs.lindy.ai/webhooks)
- [Event Reference](https://docs.lindy.ai/webhooks/events)
- [Security Best Practices](https://docs.lindy.ai/webhooks/security)

## Next Steps
Proceed to `lindy-performance-tuning` for optimization.