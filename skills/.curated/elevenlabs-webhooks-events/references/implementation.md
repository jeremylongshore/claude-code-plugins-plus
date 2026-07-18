# ElevenLabs Webhooks — Full Implementation Walkthrough

This reference carries the complete, copy-ready implementation for verifying and
handling ElevenLabs webhooks. SKILL.md summarizes the workflow; drill in here for
the full HMAC verifier, the Express handler, and idempotency protection.

## Webhook Setup

```bash
# Create webhook in ElevenLabs dashboard:
# Settings > Webhooks > Create Webhook
# - URL: https://your-app.com/webhooks/elevenlabs
# - Select event types to subscribe to
# - Copy the generated HMAC secret
```

## HMAC Signature Verification

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

## Express Webhook Handler

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

## Idempotency Protection

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

## Local Testing with ngrok

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
