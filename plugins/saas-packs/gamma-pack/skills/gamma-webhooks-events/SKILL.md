---
name: gamma-webhooks-events
description: |
  Handle Gamma webhooks and events for real-time updates.
  Use when implementing webhook receivers, processing events,
  or building real-time Gamma integrations.
  Trigger with phrases like "gamma webhooks", "gamma events",
  "gamma notifications", "gamma real-time", "gamma callbacks".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Gamma Webhooks & Events

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement webhook handlers and event processing for real-time Gamma updates with signature verification and reliable queue processing.

## Prerequisites
- Public endpoint for webhook delivery
- Webhook secret from Gamma dashboard
- Understanding of event-driven architecture

## Event Types

| Event | Description | Key Data |
|-------|-------------|----------|
| `presentation.created` | New presentation | id, title, userId |
| `presentation.updated` | Slides modified | id, changes[] |
| `presentation.exported` | Export completed | id, format, url |
| `presentation.deleted` | Removed | id |
| `presentation.shared` | Sharing updated | id, shareSettings |

## Instructions

### Step 1: Register Webhook
Register endpoint URL with Gamma API specifying events to receive and webhook secret.

### Step 2: Create Handler with Signature Verification
Verify `x-gamma-signature` header using HMAC-SHA256. Acknowledge receipt immediately (200), then process asynchronously.

### Step 3: Implement Event Processing
Route events to type-specific handlers: notify team on create, update database on changes, send export links, cleanup on delete.

### Step 4: Add Reliable Queue
Use Bull/Redis queue with 3 retry attempts and exponential backoff. Failed events go to dead letter queue for manual review.

### Step 5: Manage Webhooks
List, update (change events), delete, and test webhooks via API.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for webhook registration, signature verification, event handlers, Bull queue setup, and webhook management code.

## Output
- Webhook endpoint with signature verification
- Event handlers for all presentation events
- Reliable queue with retry logic
- Webhook lifecycle management

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Secret mismatch | Verify GAMMA_WEBHOOK_SECRET matches |
| Timeout | Slow processing | Use async queue, acknowledge immediately |
| Duplicate events | Retry delivery | Implement idempotency with event IDs |
| Missing events | Endpoint down | Use reliable hosting with health monitoring |

## Examples

### Test Webhook Delivery
```typescript
await gamma.webhooks.test(webhookId);
// Sends test event to registered endpoint
```

## Resources
- [Gamma Webhooks Guide](https://gamma.app/docs/webhooks)
- [Webhook Best Practices](https://gamma.app/docs/webhooks-best-practices)

## Next Steps
Proceed to `gamma-performance-tuning` for optimization.
