---
name: deepgram-webhooks-events
description: |
  Implement Deepgram callback and webhook handling for async transcription.
  Use when implementing callback URLs, processing async transcription results,
  or handling Deepgram event notifications.
  Trigger with phrases like "deepgram callback", "deepgram webhook",
  "async transcription deepgram", "deepgram events", "deepgram notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Webhooks Events

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement callback URL handling for asynchronous Deepgram transcription workflows. Covers callback server setup, signature verification, result processing, retry mechanisms, and client SDK for async operations.

## Prerequisites
- Publicly accessible HTTPS endpoint
- Deepgram API key with transcription permissions
- Request validation capabilities
- Secure storage for transcription results

## Deepgram Callback Flow
1. Client sends transcription request with `callback` URL parameter
2. Deepgram processes audio asynchronously
3. Deepgram POSTs results to callback URL
4. Your server processes, stores results, and notifies clients

## Instructions

### Step 1: Create Callback Endpoint
Set up an Express endpoint at `/webhooks/deepgram` using raw body parsing for signature verification.

### Step 2: Implement Signature Verification
Verify callbacks using HMAC-SHA256 with timing-safe comparison against `x-deepgram-signature` header.

### Step 3: Process Results
Extract transcript, confidence, words, and metadata from the callback payload. Store in database and Redis.

### Step 4: Notify Clients
Push results via WebSocket to connected clients and/or send email notifications.

### Step 5: Add Retry Handling
Implement `CallbackRetryHandler` with exponential backoff (max 3 retries, 5s-60s delay).

## Output
- Callback server with signature verification
- Async transcription service with job tracking (Redis)
- Store and notify services
- Retry mechanism for failed processing
- Client SDK with submit/poll/wait pattern

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Invalid signature | Wrong webhook secret | Verify `DEEPGRAM_WEBHOOK_SECRET` matches |
| Callback not received | Endpoint not reachable | Check HTTPS, firewall rules, use ngrok for local |
| Processing timeout | Slow downstream services | Increase timeout, add async processing queue |
| Duplicate callbacks | Network retry | Implement idempotency using `request_id` |

## Examples

### Test Callback Locally
```bash
# Expose local server
ngrok http 3000

# Submit async transcription
curl -X POST 'https://api.deepgram.com/v1/listen?callback=https://your-ngrok.ngrok.io/webhooks/deepgram&model=nova-2' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://static.deepgram.com/examples/nasa-podcast.wav"}'
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Deepgram Callback Documentation](https://developers.deepgram.com/docs/callback)
- [Webhook Best Practices](https://developers.deepgram.com/docs/webhook-best-practices)
- [ngrok Documentation](https://ngrok.com/docs)
