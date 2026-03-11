---
name: granola-webhooks-events
description: |
  Handle Granola webhook events and build event-driven automations.
  Use when building custom integrations, processing meeting events,
  or creating real-time notification systems.
  Trigger with phrases like "granola webhooks", "granola events",
  "granola triggers", "granola real-time", "granola callbacks".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Webhooks & Events

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Build event-driven automations using Granola's Zapier webhooks and event triggers for real-time meeting note processing.

## Prerequisites
- Granola Pro or Business plan
- Zapier account
- Webhook endpoint (or Zapier as processor)

## Available Events

| Event | Description | Key Data |
|-------|-------------|----------|
| New Note Created | Notes ready after meeting | Full note, attendees, actions |
| Note Updated | Notes manually edited | Changes diff |
| Note Shared | Notes shared with others | Share details |

## Instructions

### Step 1: Set Up Zapier Integration
Configure Granola trigger in Zapier. Select events to listen for. Get webhook URL for custom endpoints.

### Step 2: Build Event Handler
Create endpoint that receives events, validates them, and routes to appropriate processors (task creation, notifications, CRM updates).

### Step 3: Implement Event Filtering
Filter by meeting type (title keywords), content (has action items), and attendees (external vs internal).

### Step 4: Choose Processing Pattern
- **Immediate**: Process each event in real-time (~2 min latency)
- **Batch**: Queue events, process every 15 min (reduce noise)
- **Conditional**: Route based on attendee type, action count, duration

### Step 5: Add Retry Logic
Implement exponential backoff with 3 retries. Send failures to dead letter queue for manual review.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for event payload schemas, Express.js/Python handlers, filtering patterns, and monitoring metrics.

## Output
- Webhook receiver processing events
- Event filtering reducing noise
- Retry logic handling transient failures
- Monitoring tracking event throughput

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missed events | Endpoint down | Use reliable hosting, add health monitoring |
| Duplicate processing | Retry delivery | Implement idempotency with event IDs |
| Slow processing | Synchronous handling | Use async queue (Bull/SQS) |
| Invalid payload | Schema changed | Validate payload before processing |

## Examples

### Quick Webhook Test
```bash
set -euo pipefail
curl -X POST https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID \
  -H "Content-Type: application/json" \
  -d '{"event_type":"note.created","data":{"meeting_title":"Test","action_items":[]}}'
```

## Resources
- [Zapier Webhooks](https://zapier.com/help/create/code-webhooks)
- [Webhook Best Practices](https://zapier.com/blog/webhook-best-practices)

## Next Steps
Proceed to `granola-performance-tuning` for optimization techniques.