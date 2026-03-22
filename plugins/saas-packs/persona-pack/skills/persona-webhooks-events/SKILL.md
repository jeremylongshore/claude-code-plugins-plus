---
name: persona-webhooks-events
description: |
  Handle Persona webhook events for inquiry and verification status changes.
  Use when working with Persona identity verification.
  Trigger with phrases like "persona webhooks-events", "persona webhooks-events".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, identity, kyc, verification]
compatible-with: claude-code, codex, openclaw
---

# persona webhooks events | sed 's/\b\(.\)/\u\1/g'

## Overview
HMAC signature verification, inquiry.completed/approved/declined events, idempotent processing.

## Prerequisites
- Completed `persona-install-auth` setup
- Valid Persona API key (sandbox or production)

## Instructions

### Step 1: Configure Webhook in Dashboard
```text
1. Dashboard > Settings > Webhooks > Add Webhook
2. URL: https://your-app.com/webhooks/persona
3. Events: inquiry.completed, inquiry.approved, inquiry.declined,
           verification.passed, verification.failed
4. Copy the webhook secret for signature verification
```

### Step 2: Webhook Endpoint with HMAC Verification
```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();

app.post('/webhooks/persona',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['persona-signature'] as string;
    const secret = process.env.PERSONA_WEBHOOK_SECRET!;

    // Verify HMAC-SHA256 signature
    const expectedSig = crypto
      .createHmac('sha256', secret)
      .update(req.body)
      .digest('hex');

    if (!crypto.timingSafeEqual(Buffer.from(signature || ''), Buffer.from(expectedSig))) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    await handlePersonaEvent(event);
    res.status(200).json({ received: true });
  }
);
```

### Step 3: Event Handlers
```typescript
async function handlePersonaEvent(event: any) {
  const { type, data } = event;

  switch (type) {
    case 'inquiry.completed':
      const inquiryId = data.attributes.payload.data.id;
      const referenceId = data.attributes.payload.data.attributes['reference-id'];
      console.log(`Inquiry completed: ${inquiryId} for user ${referenceId}`);
      // Update user KYC status in your database
      await updateUserKycStatus(referenceId, 'completed');
      break;

    case 'inquiry.approved':
      await updateUserKycStatus(data.attributes.payload.data.attributes['reference-id'], 'approved');
      break;

    case 'inquiry.declined':
      await updateUserKycStatus(data.attributes.payload.data.attributes['reference-id'], 'declined');
      break;

    case 'verification.passed':
      console.log(`Verification passed: ${data.attributes.payload.data.id}`);
      break;

    case 'verification.failed':
      console.log(`Verification failed: ${data.attributes.payload.data.id}`);
      break;

    default:
      console.log(`Unhandled event: ${type}`);
  }
}
```

### Step 4: Idempotent Processing
```typescript
const processedEvents = new Set<string>();

async function idempotentHandle(event: any) {
  const eventId = event.data.id;
  if (processedEvents.has(eventId)) {
    console.log(`Skipping duplicate: ${eventId}`);
    return;
  }
  await handlePersonaEvent(event);
  processedEvents.add(eventId);
}
```

## Output
- Webhook endpoint with HMAC signature verification
- Event handlers for inquiry and verification lifecycle
- Idempotent processing preventing duplicates

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong webhook secret | Re-copy secret from Dashboard |
| Missing events | Events not selected | Check webhook configuration |
| Duplicate processing | Retry delivery | Use event ID deduplication |

## Resources
- [Webhooks Quickstart](https://docs.withpersona.com/quickstart-webhooks)
- [Create a Webhook](https://docs.withpersona.com/api-reference/webhooks/create-a-webhook)

## Next Steps
For common errors, see `persona-common-errors`.
