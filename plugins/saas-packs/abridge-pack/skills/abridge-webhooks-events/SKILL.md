---
name: abridge-webhooks-events
description: |
  Implement Abridge webhook handling for clinical documentation events.
  Use when receiving note completion notifications, encounter status changes,
  provider enrollment events, or quality alert callbacks from Abridge.
  Trigger: "abridge webhook", "abridge events", "abridge notifications",
  "abridge note completed event", "abridge encounter event".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, webhooks]
compatible-with: claude-code
---

# Abridge Webhooks & Events

## Overview

Handle Abridge webhook events for clinical documentation lifecycle: note completion, encounter status changes, quality alerts, and provider enrollment notifications. All webhook payloads are HIPAA-scoped (contain session IDs but no PHI).

## Abridge Event Types

| Event | Trigger | Use Case |
|-------|---------|----------|
| `encounter.session.completed` | Note generation finished | Push note to EHR |
| `encounter.session.failed` | Note generation failed | Alert clinical team |
| `encounter.note.reviewed` | Clinician reviewed/edited note | Update EHR with final version |
| `encounter.note.signed` | Clinician signed the note | Lock note in EHR |
| `patient.summary.ready` | Patient summary generated | Push to patient portal |
| `provider.enrolled` | Provider onboarded | Update provider roster |
| `quality.alert` | Low confidence or missing content | Flag for clinical review |

## Instructions

### Step 1: Webhook Endpoint with Signature Verification

```typescript
// src/webhooks/abridge-webhook-handler.ts
import express from 'express';
import crypto from 'crypto';

const router = express.Router();

// CRITICAL: Use raw body for signature verification
router.post('/webhooks/abridge',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-abridge-signature'] as string;
    const timestamp = req.headers['x-abridge-timestamp'] as string;

    if (!verifySignature(req.body, signature, timestamp)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());

    // Idempotency check
    if (await isProcessed(event.event_id)) {
      return res.status(200).json({ status: 'already_processed' });
    }

    // Process asynchronously — respond immediately
    processEvent(event).catch(err =>
      console.error(`Event processing failed: ${event.event_id}`, err)
    );

    res.status(200).json({ received: true });
  }
);

function verifySignature(payload: Buffer, signature: string, timestamp: string): boolean {
  const secret = process.env.ABRIDGE_WEBHOOK_SECRET!;
  const maxAge = 300000; // 5 minutes

  if (Date.now() - parseInt(timestamp) * 1000 > maxAge) {
    console.error('Webhook timestamp expired');
    return false;
  }

  const expected = crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${payload.toString()}`)
    .digest('hex');

  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}
```

### Step 2: Event Router

```typescript
// src/webhooks/event-router.ts
interface AbridgeEvent {
  event_id: string;
  type: string;
  timestamp: string;
  data: {
    session_id?: string;
    note_id?: string;
    provider_id?: string;
    status?: string;
    quality_score?: number;
  };
}

type EventHandler = (data: AbridgeEvent['data']) => Promise<void>;

const handlers: Record<string, EventHandler> = {
  'encounter.session.completed': async (data) => {
    console.log(`Note ready for session ${data.session_id}`);
    // Fetch note and push to EHR
    await fetchAndPushNote(data.session_id!);
  },

  'encounter.session.failed': async (data) => {
    console.error(`Note generation failed: ${data.session_id} — ${data.status}`);
    // Alert clinical operations team
    await sendClinicalAlert(data.session_id!, 'Note generation failed');
  },

  'encounter.note.signed': async (data) => {
    console.log(`Note signed: ${data.note_id}`);
    // Lock note in EHR — no further edits
    await lockNoteInEhr(data.note_id!);
  },

  'patient.summary.ready': async (data) => {
    console.log(`Patient summary ready: ${data.session_id}`);
    // Push to patient portal
    await pushSummaryToPortal(data.session_id!);
  },

  'quality.alert': async (data) => {
    console.warn(`Quality alert: session ${data.session_id}, score ${data.quality_score}`);
    // Flag for clinical review if score < 0.7
    if ((data.quality_score || 0) < 0.7) {
      await flagForReview(data.session_id!);
    }
  },
};

async function processEvent(event: AbridgeEvent): Promise<void> {
  const handler = handlers[event.type];
  if (!handler) {
    console.log(`Unhandled event: ${event.type}`);
    return;
  }
  await handler(event.data);
  await markProcessed(event.event_id);
}
```

### Step 3: Idempotency Store

```typescript
// src/webhooks/idempotency.ts
// Use Redis or database for production — in-memory for dev

const processedEvents = new Map<string, number>();

async function isProcessed(eventId: string): Promise<boolean> {
  return processedEvents.has(eventId);
}

async function markProcessed(eventId: string): Promise<void> {
  processedEvents.set(eventId, Date.now());
  // Clean up events older than 7 days
  const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000;
  for (const [id, ts] of processedEvents) {
    if (ts < cutoff) processedEvents.delete(id);
  }
}
```

### Step 4: Webhook Registration

```bash
# Register webhook endpoint with Abridge
curl -X POST "${ABRIDGE_BASE_URL}/webhooks" \
  -H "Authorization: Bearer ${ABRIDGE_CLIENT_SECRET}" \
  -H "X-Org-Id: ${ABRIDGE_ORG_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-service.run.app/webhooks/abridge",
    "events": [
      "encounter.session.completed",
      "encounter.session.failed",
      "encounter.note.signed",
      "patient.summary.ready",
      "quality.alert"
    ],
    "secret": "your-webhook-secret"
  }'
```

## Output

- Secure webhook endpoint with HMAC signature verification
- Event router with handlers for all clinical documentation events
- Idempotency store preventing duplicate processing
- Webhook registration via Abridge API

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong webhook secret | Verify secret matches Abridge config |
| Timestamp expired | Clock drift > 5 min | Sync server clock via NTP |
| Duplicate processing | Missing idempotency | Implement event ID tracking |
| Handler timeout | Slow EHR push | Process async; respond 200 immediately |

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [HMAC Signature Verification](https://nodejs.org/api/crypto.html#cryptocreatehmacsignedalgorithm-key-options)

## Next Steps

For performance optimization, see `abridge-performance-tuning`.
