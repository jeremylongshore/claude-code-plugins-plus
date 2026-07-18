---
name: elevenlabs-webhooks-events
description: |
  Implement ElevenLabs webhook HMAC signature verification and event handling.
  Use when setting up webhook endpoints for transcription completion, call
  recording, or agent conversation events from ElevenLabs.
  Trigger with "elevenlabs webhook", "elevenlabs events",
  "elevenlabs webhook signature", "handle elevenlabs notifications",
  "elevenlabs post-call webhook", "elevenlabs transcription webhook".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- webhooks
- events
compatibility: Designed for Claude Code
---
# ElevenLabs Webhooks & Events

## Overview

ElevenLabs webhooks send HTTP POST notifications when async operations complete: transcription completion, post-call data from Conversational AI agents, and call initiation failures. Every delivery is signed with an HMAC-SHA256 signature you must verify before processing. This skill builds a secure endpoint that verifies signatures, routes events by type, and acks fast to avoid auto-disable.

## Prerequisites

- ElevenLabs account (webhooks configured in Settings > Webhooks)
- HTTPS endpoint accessible from the internet
- Webhook secret (generated during webhook creation in dashboard)

## Instructions

The full, copy-ready code for each step lives in [references/implementation.md](references/implementation.md); per-event handlers live in [references/examples.md](references/examples.md). The high-level workflow:

1. **Know the event types** — subscribe only to what you handle (table below).
2. **Create the webhook** in the dashboard (Settings > Webhooks) and copy the HMAC secret.
3. **Verify the signature** with HMAC-SHA256 over `"<timestamp>.<raw_body>"`, using a timing-safe compare and a 5-minute replay window. See the [full verifier](references/implementation.md).
4. **Handle the request** with a raw body parser, ack `200` immediately, then process asynchronously. See the [Express handler](references/implementation.md).
5. **Route events** to per-type handlers. See [handler examples](references/examples.md).
6. **Guard against duplicates** with idempotency keyed on the event ID. See [idempotency](references/implementation.md).
7. **Test locally** by tunneling with ngrok. See [local testing](references/implementation.md).

### Webhook event types

| Event Type | Payload | When Triggered |
|------------|---------|----------------|
| `post_call_transcription` | Full conversation transcript, analysis, metadata | After Conversational AI call ends |
| `post_call_audio` | Base64-encoded call audio, minimal metadata | After call ends (if audio recording enabled) |
| `call_initiation_failure` | Failure reason, metadata | When an outbound call fails to connect |
| `speech_to_text.completed` | Transcription result, word timestamps | Async STT job completes |

### Signature verification skeleton

```typescript
// src/elevenlabs/webhook-verify.ts — Header: t=<unix_ts>,v1=<hex_sig>
export function verifyWebhookSignature(rawBody, signatureHeader, secret) {
  const parts = new Map(signatureHeader.split(",").map(p => {
    const [k, ...v] = p.split("="); return [k, v.join("=")];
  }));
  const timestamp = parts.get("t"), signature = parts.get("v1");
  if (Math.floor(Date.now() / 1000) - parseInt(timestamp) > 300) {
    return { valid: false, reason: "Timestamp too old" };   // replay guard
  }
  const expected = crypto.createHmac("sha256", secret)
    .update(`${timestamp}.${rawBody.toString()}`).digest("hex");
  return { valid: crypto.timingSafeEqual(
    Buffer.from(signature, "hex"), Buffer.from(expected, "hex")) };
}
```

See [references/implementation.md](references/implementation.md) for the production-hardened version with full error handling.

## Output

Applying this skill produces:

- `src/elevenlabs/webhook-verify.ts` — reusable HMAC-SHA256 verifier with replay protection and timing-safe comparison.
- `src/api/webhooks/elevenlabs.ts` — Express route that verifies signatures, acks `200` immediately, and routes events to per-type handlers.
- Per-event handler functions (`handleTranscription`, `handleCallAudio`, `handleCallFailure`, `handleSTTCompleted`) extracting the fields each payload carries.
- An idempotency wrapper keyed on event ID so retried deliveries are processed once.

At runtime a verified delivery returns `{ "received": true }` with HTTP `200`; a bad signature or expired timestamp returns HTTP `401` `{ "error": "Invalid signature" }`.

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

## Examples

**Route a decoded event to the right handler:**

```typescript
switch (event.type || event.event_type) {
  case "post_call_transcription": await handleTranscription(event); break;
  case "post_call_audio":         await handleCallAudio(event);     break;
  case "call_initiation_failure": await handleCallFailure(event);   break;
  case "speech_to_text.completed": await handleSTTCompleted(event); break;
  default: console.log("Unhandled event type:", event.type);
}
```

**Simulate a delivery locally with curl:**

```bash
curl -X POST http://localhost:3000/webhooks/elevenlabs \
  -H "Content-Type: application/json" \
  -H "ElevenLabs-Signature: t=$(date +%s),v1=test" \
  -d '{"type":"speech_to_text.completed","data":{"text":"Hello world"}}'
```

Full per-event handlers (transcript, audio, call-failure, STT) with the exact fields each payload carries are in [references/examples.md](references/examples.md).

## Resources

- [Post-Call Webhooks](https://elevenlabs.io/docs/agents-platform/workflows/post-call-webhooks)
- [Webhook API Reference](https://elevenlabs.io/docs/api-reference/webhooks/list)
- [references/implementation.md](references/implementation.md) — full verifier, Express handler, idempotency, ngrok testing
- [references/examples.md](references/examples.md) — per-event handler examples

## Next Steps

For performance optimization, see the `elevenlabs-performance-tuning` skill, which covers connection pooling and batching to keep webhook handlers fast enough to ack within the ElevenLabs timeout window.
