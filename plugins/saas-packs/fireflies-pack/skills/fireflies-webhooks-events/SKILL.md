---
name: fireflies-webhooks-events
description: |
  Implement Fireflies.ai webhook receiver with HMAC signature verification and event processing.
  Use when setting up webhook endpoints, handling transcript-ready notifications,
  or building real-time meeting intelligence pipelines.
  Trigger with phrases like "fireflies webhook", "fireflies events",
  "fireflies webhook signature", "handle fireflies events", "fireflies notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, webhooks]

---
# Fireflies.ai Webhooks & Events

## Overview
Handle Fireflies.ai webhook events for real-time transcript notifications. Fireflies fires a webhook when a transcript finishes processing. The payload is signed with HMAC-SHA256 for verification.

## Prerequisites
- Fireflies.ai Business or Enterprise plan
- `FIREFLIES_API_KEY` and `FIREFLIES_WEBHOOK_SECRET` in environment
- HTTPS endpoint accessible from the internet

## Webhook Event Reference

Fireflies currently fires one event type:

| Event | `eventType` Value | Trigger |
|-------|-------------------|---------|
| Transcription completed | `"Transcription completed"` | Transcript is fully processed and ready |

### Payload Format
```json
{
  "meetingId": "ASxwZxCstx",
  "eventType": "Transcription completed",
  "clientReferenceId": "be582c46-4ac9-4565-9ba6-6ab4264496a8"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `meetingId` | String | Transcript ID -- use in `transcript(id:)` query |
| `eventType` | String | Always `"Transcription completed"` currently |
| `clientReferenceId` | ID | Your custom ID from `uploadAudio` (null if bot-recorded) |

## Important Constraints
- Webhooks fire **only for meetings you own** (organizer_email matches your account)
- Super Admin webhooks (Enterprise only) fire for all team-owned meetings

## Instructions

### Step 1: Register Webhook in Dashboard
1. Go to [app.fireflies.ai/settings](https://app.fireflies.ai/settings)
2. Select **Developer settings** tab
3. Enter your HTTPS webhook URL
4. Enter or generate a 16-32 character secret
5. Save

### Step 2: Build Webhook Receiver with Signature Verification
```typescript
import express from "express";
import crypto from "crypto";

const app = express();

// IMPORTANT: Use raw body for HMAC verification
app.post("/webhooks/fireflies",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["x-hub-signature"] as string;
    const rawBody = req.body.toString();

    // Verify HMAC-SHA256 signature
    if (!signature || !verifySignature(rawBody, signature)) {
      console.warn("Rejected webhook: invalid signature");
      return res.status(401).json({ error: "Invalid signature" });
    }

    // Acknowledge immediately -- process async
    res.status(200).json({ received: true });

    const event = JSON.parse(rawBody);
    console.log(`Webhook: ${event.eventType} for meeting ${event.meetingId}`);

    // Process in background
    processTranscriptReady(event.meetingId, event.clientReferenceId)
      .catch(err => console.error("Webhook processing failed:", err));
  }
);

function verifySignature(payload: string, signature: string): boolean {
  const secret = process.env.FIREFLIES_WEBHOOK_SECRET!;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

### Step 3: Fetch and Process the Transcript
```typescript
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

async function processTranscriptReady(meetingId: string, clientRefId?: string) {
  const res = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({
      query: `
        query GetTranscript($id: String!) {
          transcript(id: $id) {
            id title date duration
            organizer_email
            speakers { name }
            sentences { speaker_name text start_time end_time }
            summary {
              overview
              action_items
              keywords
              short_summary
            }
            meeting_attendees { displayName email }
          }
        }
      `,
      variables: { id: meetingId },
    }),
  });

  const json = await res.json();
  if (json.errors) throw new Error(json.errors[0].message);

  const transcript = json.data.transcript;
  console.log(`Processing: "${transcript.title}" (${transcript.duration}min)`);
  console.log(`Speakers: ${transcript.speakers.map((s: any) => s.name).join(", ")}`);
  console.log(`Action items: ${transcript.summary?.action_items?.length || 0}`);

  // Route to downstream systems
  await Promise.all([
    storeTranscript(transcript),
    createTasksFromActionItems(transcript),
    notifyTeam(transcript),
  ]);
}

async function storeTranscript(transcript: any) {
  // Store in your database
  console.log(`Stored transcript: ${transcript.id}`);
}

async function createTasksFromActionItems(transcript: any) {
  const items = transcript.summary?.action_items || [];
  for (const item of items) {
    console.log(`Task created: ${item}`);
    // await taskManager.create({ title: item, source: transcript.title });
  }
}

async function notifyTeam(transcript: any) {
  // Send Slack/email notification
  const summary = transcript.summary?.short_summary || transcript.summary?.overview;
  console.log(`Notification: "${transcript.title}" -- ${summary}`);
}
```

### Step 4: Per-Upload Webhook (Alternative)
Instead of dashboard-level webhook, include a webhook URL in `uploadAudio`:
```typescript
await fetch(FIREFLIES_API, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
  },
  body: JSON.stringify({
    query: `
      mutation($input: AudioUploadInput) {
        uploadAudio(input: $input) { success title message }
      }
    `,
    variables: {
      input: {
        url: "https://storage.example.com/recording.mp3",
        title: "Client Call 2026-03-22",
        webhook: "https://api.yourapp.com/webhooks/fireflies",
        client_reference_id: "order-12345",
      },
    },
  }),
});
```

### Step 5: Test Webhook
```bash
set -euo pipefail
# Test by uploading a short audio file
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($input: AudioUploadInput) { uploadAudio(input: $input) { success message } }",
    "variables": { "input": { "url": "https://example.com/test-audio.mp3", "title": "Webhook Test" } }
  }' | jq .
# The webhook will fire when transcription completes (usually 2-5 minutes)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | URL not saved in dashboard | Re-register at app.fireflies.ai/settings |
| Invalid signature | Secret mismatch | Verify secret matches dashboard value |
| Missing `meetingId` | Malformed payload | Log raw body, check Fireflies status |
| Webhook only fires for some meetings | Owner-only constraint | Webhooks fire only for your meetings |
| `clientReferenceId` is null | Bot-recorded meeting | Only set on `uploadAudio` calls |

## Output
- HTTPS webhook endpoint with HMAC-SHA256 signature verification
- Automatic transcript fetch on completion events
- Action item extraction and downstream routing
- Per-upload webhook support for custom tracking

## Resources
- [Fireflies Webhooks](https://docs.fireflies.ai/graphql-api/webhooks)
- [Webhook Verification Example](https://replit.com/@firefliesai/Firefliesai-Verifying-webhook-requests)

## Next Steps
For deployment setup, see `fireflies-deploy-integration`.
