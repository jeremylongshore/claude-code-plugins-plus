---
name: twinmind-webhooks-events
description: |
  Handle TwinMind webhooks and events for real-time meeting notifications.
  Use when implementing webhook handlers, processing meeting events,
  or building real-time integrations.
  Trigger with phrases like "twinmind webhooks", "twinmind events",
  "twinmind notifications", "meeting webhook handler".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Webhooks & Events

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement webhook handlers for real-time TwinMind meeting events including transcription completion, meeting lifecycle, summary generation, action item extraction, and usage alerts. Includes signature verification, event routing, and retry logic.

## Prerequisites
- TwinMind Pro/Enterprise account
- Public HTTPS endpoint for webhooks
- Webhook secret configured
- Understanding of event-driven architecture

## Instructions

### Step 1: Define Event Types
Create `TwinMindEventType` enum for transcription (started/completed/failed), meeting (started/ended/participant join/leave), summary (generated), action items (extracted), calendar (synced/reminder), and usage (limit warning/exceeded).

### Step 2: Implement Webhook Handler
Build signature verification middleware using HMAC-SHA256 with timestamp validation (5-minute replay window) and `crypto.timingSafeEqual`. Create event handler registry with `registerHandler()` and async `handleWebhook()` that acknowledges immediately then processes.

### Step 3: Register Event Handlers
Wire up handlers: transcription.completed triggers summary generation, meeting.ended notifies Slack and sends summary email, summary.generated stores in database, action_items.extracted creates Linear tasks, usage.limit.warning alerts ops channel.

### Step 4: Set Up Webhook Endpoint
Create Express route with raw body parser for signature verification, connect to handler.

### Step 5: Register Webhooks with TwinMind
Script to register webhook URL with desired event types via TwinMind API.

### Step 6: Implement Retry Logic
Build `WebhookRetryQueue` with exponential backoff (base 60s), max 5 retries, and dead letter queue for failed events with ops team alerting.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete event types, webhook handler, event processors, registration script, and retry queue.

## Output
- Event type definitions
- Webhook handler with signature verification
- Event processing logic
- Webhook registration script
- Retry queue for failed events

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify webhook secret matches |
| Event missed | Endpoint down | Implement retry queue |
| Processing slow | Heavy handler | Use async background queue |
| Duplicate events | Retries from TwinMind | Implement idempotency by event ID |

## Examples


**Basic usage**: Apply twinmind webhooks events to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind webhooks events for production environments with multiple constraints and team-specific requirements.

## Webhook Events Reference

| Event | Description |
|-------|-------------|
| `transcription.completed` | Transcription finished |
| `meeting.ended` | Meeting finished |
| `summary.generated` | AI summary ready |
| `action_items.extracted` | Action items available |
| `usage.limit.warning` | Usage approaching limit |

## Resources
- [TwinMind Webhooks API](https://twinmind.com/docs/webhooks)
- [Webhook Best Practices](https://twinmind.com/docs/webhook-best-practices)
- [Event Reference](https://twinmind.com/docs/events)

## Next Steps
For performance optimization, see `twinmind-performance-tuning`.