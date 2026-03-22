---
name: elevenlabs-webhooks-events
description: |
  Implement ElevenLabs webhook HMAC signature verification and event handling.
  Use when setting up webhook endpoints for transcription completion,
  call recording, or agent conversation events from ElevenLabs.
  Trigger: "elevenlabs webhook", "elevenlabs events",
  "elevenlabs webhook signature", "handle elevenlabs notifications",
  "elevenlabs post-call webhook", "elevenlabs transcription webhook".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, webhooks, events]
compatible-with: claude-code
---

# ElevenLabs Webhooks & Events

## Overview

ElevenLabs webhooks send HTTP POST notifications when async operations complete. Supported event types include transcription completion, post-call data from Conversational AI agents, and call initiation failures. Webhooks use HMAC-SHA256 signatures for verification.

## Prerequisites

- ElevenLabs account (webhooks configured in Settings > Webhooks)
- HTTPS endpoint accessible from the internet
- Webhook secret (generated during webhook creation in dashboard)

## Instructions

### Step 1: Webhook Event Types

| Event Type | Payload | When Triggered |
|------------|---------|----------------|
| `post_call_transcription` | Full conversation transcript, analysis, metadata | After Conversational AI call ends |
| `post_call_audio` | Base64-encoded call audio, minimal metadata | After call ends (if audio recording enabled) |
| `call_initiation_failure` | Failure reason, metadata | When an outbound call fails to connect |
| `speech_to_text.completed` | Transcription result, word timestamps | Async STT job completes |

### Step 2: Webhook Setup

```bash
# Create webhook in ElevenLabs dashboard:
# Settings > Webhooks > Create Webhook
# - URL: https://your-app.com/webhooks/elevenlabs
# - Select event types to subscribe to
# - Copy the generated HMAC secret
```

### Step 3: HMAC Signature Verification

```typescript
// src/elevenlabs/webhook-verify.ts
import crypto from "crypto";

/**
 * Verify the ElevenLabs-Signature header using HMAC-SHA256.
 *
 * Header format: t=<unix_timestamp>,v1=<hex_signature>
 * Signed payload: "<timestamp>.<raw_body>"
 */
export function verifyWebhookSignature(
  rawBody: string | Buffer,
  signatureHeader: string,
  secret: string
): { valid: boolean; reason?: string } {
  if (!signatureHeader || !secret) {
    return { valid: false, reason: "Missing signature header or secret" };
  }

  // Parse header: t=1234567890,v1=abcdef...
  const parts = new Map(
    signatureHeader.split(",").map(p => {
      const [key, ...val] = p.split("=");
      return [key, val.join("=")] as [string, string];
    })
  );

  const timestamp = parts.get("t");
  const signature = parts.get("v1");

  if (!timestamp || !signature) {
    return { valid: false, reason: "Malformed signature header" };
  }

  // Replay protection: reject if older than 5 minutes
  const age = Math.floor(Date.now() / 1000) - parseInt(timestamp);
  if (age > 300) {
    return { valid: false, reason: `Timestamp too old: ${age}s` };
  }

  // Compute expected HMAC
  const signedPayload = `${timestamp}.${rawBody.toString()}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(signedPayload)
    .digest("hex");

  // Timing-safe comparison
  try {
    const isValid = crypto.timingSafeEqual(
      Buffer.from(signature, "hex"),
      Buffer.from(expected, "hex")
    );
    return { valid: isValid };
  } catch {
    return { valid: false, reason: "Signature length mismatch" };
  }
}
```

### Step 4: Express Webhook Handler

```typescript
// src/api/webhooks/elevenlabs.ts
import express from "express";
import { verifyWebhookSignature } from "../../elevenlabs/webhook-verify";

const router = express.Router();

// CRITICAL: Use raw body parser for signature verification
router.post("/webhooks/elevenlabs",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["elevenlabs-signature"] as string;
    const secret = process.env.ELEVENLABS_WEBHOOK_SECRET!;

    const { valid, reason } = verifyWebhookSignature(req.body, signature, secret);

    if (!valid) {
      console.error("Webhook verification failed:", reason);
      return res.status(401).json({ error: "Invalid signature" });
    }

    // Return 200 immediately to prevent webhook auto-disable
    res.status(200).json({ received: true });

    // Process asynchronously
    const event = JSON.parse(req.body.toString());
    processEvent(event).catch(err =>
      console.error("Webhook processing failed:", err)
    );
  }
);

// Event routing
async function processEvent(event: any) {
  const eventType = event.type || event.event_type;

  switch (eventType) {
    case "post_call_transcription":
      await handleTranscription(event);
      break;
    case "post_call_audio":
      await handleCallAudio(event);
      break;
    case "call_initiation_failure":
      await handleCallFailure(event);
      break;
    case "speech_to_text.completed":
      await handleSTTCompleted(event);
      break;
    default:
      console.log("Unhandled event type:", eventType);
  }
}
```

### Step 5: Event Handlers

```typescript
// Conversational AI post-call transcript
async function handleTranscription(event: any) {
  const {
    conversation_id,
    transcript,       // Full conversation text
    analysis,         // AI analysis of the call
    metadata,         // Custom metadata from agent config
    recording_url,    // Audio recording URL (if enabled)
  } = event.data;

  console.log(`[Transcript] Conversation ${conversation_id}`);
  console.log(`Transcript: ${transcript?.substring(0, 200)}...`);

  // Store in your database
  // await db.conversations.upsert({ conversation_id, transcript, analysis });
}

// Post-call audio recording
async function handleCallAudio(event: any) {
  const {
    conversation_id,
    audio_base64,     // Base64-encoded audio of the full conversation
  } = event.data;

  if (audio_base64) {
    const audioBuffer = Buffer.from(audio_base64, "base64");
    console.log(`[Audio] Received ${audioBuffer.length} bytes for ${conversation_id}`);
    // Save audio: await fs.writeFile(`recordings/${conversation_id}.mp3`, audioBuffer);
  }
}

// Failed outbound call
async function handleCallFailure(event: any) {
  const {
    conversation_id,
    failure_reason,
    metadata,
  } = event.data;

  console.error(`[Call Failed] ${conversation_id}: ${failure_reason}`);
  // Alert: await alerting.notify("Call initiation failed", { conversation_id, failure_reason });
}

// Async Speech-to-Text completion
async function handleSTTCompleted(event: any) {
  const {
    transcription_id,
    text,
    words,           // Word-level timestamps
    language,
  } = event.data;

  console.log(`[STT Complete] ${transcription_id}: ${language}`);
  console.log(`Text: ${text?.substring(0, 200)}...`);
  // Process transcription results
}
```

### Step 6: Idempotency Protection

```typescript
// Prevent duplicate processing if ElevenLabs retries delivery
const processedEvents = new Set<string>();

async function withIdempotency(
  eventId: string,
  handler: () => Promise<void>
): Promise<void> {
  if (processedEvents.has(eventId)) {
    console.log(`Event ${eventId} already processed, skipping`);
    return;
  }

  await handler();
  processedEvents.add(eventId);

  // Clean up old entries (in production, use Redis with TTL)
  if (processedEvents.size > 10000) {
    const oldest = Array.from(processedEvents).slice(0, 5000);
    oldest.forEach(id => processedEvents.delete(id));
  }
}
```

### Step 7: Local Testing with ngrok

```bash
# Expose local server to internet
ngrok http 3000

# Use the ngrok URL as webhook endpoint in ElevenLabs dashboard
# https://abc123.ngrok.io/webhooks/elevenlabs

# Test with curl (simulated event)
curl -X POST http://localhost:3000/webhooks/elevenlabs \
  -H "Content-Type: application/json" \
  -H "ElevenLabs-Signature: t=$(date +%s),v1=test" \
  -d '{"type":"speech_to_text.completed","data":{"text":"Hello world"}}'
```

## Webhook Reliability

| Behavior | Detail |
|----------|--------|
| Retry policy | ElevenLabs retries failed deliveries |
| Auto-disable | After 10 consecutive failures AND 7+ days since last success |
| Timeout | Your endpoint must respond within a few seconds |
| Re-enable | Manually re-enable in dashboard after fixing the endpoint |
| Authentication | HMAC-SHA256 via `ElevenLabs-Signature` header |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Signature mismatch | Wrong secret or body parsing | Use `express.raw()`, verify secret matches dashboard |
| Webhook auto-disabled | 10+ consecutive failures | Fix endpoint, re-enable in dashboard |
| Duplicate events | Retried delivery | Implement idempotency with event ID tracking |
| Handler timeout | Slow processing | Return 200 immediately, process async |
| Replay attack | Old timestamp reused | Check timestamp age (reject > 5 min) |

## Resources

- [ElevenLabs Webhooks Guide](https://elevenlabs.io/docs/overview/administration/webhooks)
- [Post-Call Webhooks](https://elevenlabs.io/docs/agents-platform/workflows/post-call-webhooks)
- [STT Webhooks](https://elevenlabs.io/docs/cookbooks/speech-to-text/webhooks)
- [Webhook API Reference](https://elevenlabs.io/docs/api-reference/webhooks/list)

## Next Steps

For performance optimization, see `elevenlabs-performance-tuning`.
