---
name: openevidence-webhooks-events
description: |
  Configure OpenEvidence webhooks for async DeepConsult completion and events.
  Use when implementing webhook handlers, configuring async notifications,
  or setting up event-driven clinical AI workflows.
  Trigger with phrases like "openevidence webhook", "openevidence events",
  "deepconsult callback", "openevidence notifications".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Webhooks & Events

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure webhooks for asynchronous OpenEvidence operations. Covers DeepConsult lifecycle events, signature verification, event handlers, idempotency, and webhook testing.

## Prerequisites
- OpenEvidence Enterprise account with webhook access
- HTTPS endpoint for receiving webhooks
- Webhook secret for signature verification

## Webhook Events

| Event Type | Description | Key Payload |
|------------|-------------|-------------|
| `deepconsult.started` | Processing began | consultId, estimatedTime |
| `deepconsult.progress` | Progress update | consultId, progress (0-100) |
| `deepconsult.completed` | Finished successfully | consultId, report |
| `deepconsult.failed` | Processing failed | consultId, error, retryable |
| `rate_limit.warning` | Approaching rate limit | remaining, limit, resetAt |
| `api_key.expiring` | Key expiration warning | keyId, expiresAt |

## Instructions

### Step 1: Create Webhook Endpoint
Set up Express route at `/webhooks/openevidence` with signature verification middleware. Parse `t=timestamp,v1=signature` format from `x-openevidence-signature` header.

### Step 2: Implement Signature Verification
Compute HMAC-SHA256 of `${timestamp}.${payload}` with webhook secret. Use timing-safe comparison. Reject timestamps older than 5 minutes (replay protection).

### Step 3: Build Event Handlers
Create handlers for each event type: update database status for DeepConsult lifecycle, send push/email notifications on completion, alert ops on failures and rate limit warnings.

### Step 4: Add Idempotency
Track processed webhook IDs in database with 24-hour TTL. Skip already-processed events to handle retries safely.

### Step 5: Register Webhooks
Call `client.webhooks.register()` on app startup with endpoint URL, event list, and secret.

## Output
- Secure webhook endpoint with HMAC-SHA256 verification
- Event handlers for all OpenEvidence webhook events
- Notification integration (push + email)
- Idempotency protection against duplicate processing
- Webhook registration on startup

## Error Handling
| Webhook Issue | Detection | Resolution |
|---------------|-----------|------------|
| Invalid signature | 401 response | Check webhook secret configuration |
| Missing events | No handler called | Verify webhook registration |
| Duplicate processing | Multiple notifications | Enable idempotency tracking |
| Timeout | Webhook fails | Process async, return 200 immediately |

## Examples

### Signature Format
```
x-openevidence-signature: t=1234567890,v1=abc123def456...  # 1234567890 = configured value
```

### Quick Test
```bash
set -euo pipefail
# Generate test signature and POST to local endpoint
curl -X POST http://localhost:3000/webhooks/openevidence \  # 3000: 3 seconds in ms
  -H "Content-Type: application/json" \
  -H "x-openevidence-signature: t=$(date +%s),v1=TEST" \
  -d '{"event":"deepconsult.completed","data":{"consultId":"test"}}'
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [OpenEvidence API Docs](https://docs.openevidence.com/)
- [Webhook Security Best Practices](https://webhooks.fyi/)