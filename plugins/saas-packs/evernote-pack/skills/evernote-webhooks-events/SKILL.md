---
name: evernote-webhooks-events
description: |
  Implement Evernote webhook notifications and sync events.
  Use when handling note changes, implementing real-time sync,
  or processing Evernote notifications.
  Trigger with phrases like "evernote webhook", "evernote events",
  "evernote sync", "evernote notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Evernote Webhooks & Events

## Overview
Implement Evernote webhook notifications for real-time change detection. Note: Evernote webhooks notify you that changes occurred, but you must use the sync API to retrieve actual changes.

## Prerequisites
- Evernote API key with webhook permissions
- HTTPS endpoint accessible from internet
- Understanding of Evernote sync API

## Instructions

### Step 1: Webhook Endpoint

### Step 2: Webhook Reasons

### Step 3: Sync State Management

### Step 4: Webhook Event Processing

### Step 5: Event Handlers

### Step 6: Webhook Registration

### Step 7: Polling Fallback

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Webhook endpoint implementation
- Sync state management
- Event-driven change processing
- Event handlers for note lifecycle
- Polling fallback mechanism

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not received | URL not reachable | Verify HTTPS endpoint |
| Duplicate webhooks | Network retries | Implement idempotency |
| Missing changes | Race condition | Re-sync after timeout |
| Sync timeout | Large change set | Increase chunk size |

## Resources
- [Webhooks Overview](https://dev.evernote.com/doc/articles/webhooks.php)
- [Synchronization](https://dev.evernote.com/doc/articles/synchronization.php)
- [Developer Portal](https://dev.evernote.com/)

## Next Steps
For performance optimization, see `evernote-performance-tuning`.
