---
name: assemblyai-webhooks-events
description: |
  Implement AssemblyAI webhook handling for transcription completion events.
  Use when setting up webhook endpoints, handling transcription callbacks,
  or processing async transcription results via webhooks.
  Trigger with phrases like "assemblyai webhook", "assemblyai events",
  "assemblyai transcription callback", "handle assemblyai webhook".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription, webhooks]
compatible-with: claude-code
---

# AssemblyAI Webhooks & Events

## Overview
Handle AssemblyAI webhooks for transcription completion. When you submit a transcript with `webhook_url`, AssemblyAI sends a POST request to your URL when the transcript is completed or fails. One webhook per transcript — no complex event routing needed.

## Prerequisites
- HTTPS endpoint accessible from the internet
- `assemblyai` package installed
- API key configured

## How AssemblyAI Webhooks Work

1. You submit a transcription with `webhook_url` parameter
2. AssemblyAI processes the audio asynchronously
3. When done (completed or error), AssemblyAI sends a POST to your URL
4. Your endpoint receives transcript ID and status, then fetches the full transcript

**Key difference from other APIs:** AssemblyAI webhooks are per-transcript (set at submission time), not a global webhook registration. There are no event types to subscribe to — you get one callback per transcript.

## Instructions

### Step 1: Submit Transcription with Webhook

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

// submit() queues the job and returns immediately (doesn't poll)
const transcript = await client.transcripts.submit({
  audio: 'https://example.com/meeting-recording.mp3',
  webhook_url: 'https://your-app.com/webhooks/assemblyai',

  // Optional: auth header for webhook verification
  webhook_auth_header_name: 'X-Webhook-Secret',
  webhook_auth_header_value: process.env.ASSEMBLYAI_WEBHOOK_SECRET!,

  // Enable features — results will be available when webhook fires
  speaker_labels: true,
  sentiment_analysis: true,
  auto_highlights: true,
});

console.log('Submitted:', transcript.id);
// Returns immediately, webhook fires when processing completes
```

### Step 2: Webhook Endpoint (Express.js)

```typescript
import express from 'express';
import { AssemblyAI, type Transcript } from 'assemblyai';

const app = express();
const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

app.post('/webhooks/assemblyai', express.json(), async (req, res) => {
  // Step 1: Verify authenticity via custom auth header
  const secret = req.headers['x-webhook-secret'];
  if (secret !== process.env.ASSEMBLYAI_WEBHOOK_SECRET) {
    console.warn('Webhook auth failed');
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Step 2: Extract payload
  const { transcript_id, status } = req.body;
  console.log(`Webhook received: ${transcript_id} — ${status}`);

  // Step 3: Respond quickly (within 10 seconds)
  res.status(200).json({ received: true });

  // Step 4: Process asynchronously
  try {
    if (status === 'completed') {
      const transcript = await client.transcripts.get(transcript_id);
      await processCompletedTranscript(transcript);
    } else if (status === 'error') {
      await handleFailedTranscript(transcript_id, req.body.error);
    }
  } catch (error) {
    console.error('Webhook processing error:', error);
  }
});

async function processCompletedTranscript(transcript: Transcript) {
  console.log(`Processing transcript ${transcript.id}:`);
  console.log(`  Text: ${transcript.text?.length} chars`);
  console.log(`  Duration: ${transcript.audio_duration}s`);
  console.log(`  Speakers: ${transcript.utterances?.length ?? 0} utterances`);

  // Store in database, notify user, trigger LeMUR analysis, etc.

  // Example: Run LeMUR summarization after transcription completes
  if (transcript.text && transcript.text.length > 100) {
    const { response } = await client.lemur.summary({
      transcript_ids: [transcript.id],
      answer_format: 'bullet points',
    });
    console.log('Auto-summary:', response);
  }
}

async function handleFailedTranscript(transcriptId: string, error?: string) {
  console.error(`Transcript ${transcriptId} failed: ${error}`);
  // Alert ops team, retry with different settings, etc.
}

app.listen(3000, () => console.log('Listening on :3000'));
```

### Step 3: Webhook Endpoint (Next.js App Router)

```typescript
// app/api/webhooks/assemblyai/route.ts
import { AssemblyAI } from 'assemblyai';
import { NextRequest, NextResponse } from 'next/server';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

export async function POST(req: NextRequest) {
  const secret = req.headers.get('x-webhook-secret');
  if (secret !== process.env.ASSEMBLYAI_WEBHOOK_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await req.json();
  const { transcript_id, status } = body;

  if (status === 'completed') {
    const transcript = await client.transcripts.get(transcript_id);
    // Process transcript...
    console.log(`Completed: ${transcript_id}, ${transcript.text?.length} chars`);
  }

  return NextResponse.json({ received: true });
}
```

### Step 4: Idempotent Processing

```typescript
// Prevent duplicate processing if webhook is retried
const processedTranscripts = new Set<string>();
// In production, use Redis or a database instead of in-memory Set

async function idempotentProcess(transcriptId: string, handler: () => Promise<void>) {
  if (processedTranscripts.has(transcriptId)) {
    console.log(`Already processed: ${transcriptId}`);
    return;
  }

  await handler();
  processedTranscripts.add(transcriptId);
}

// Usage in webhook handler:
await idempotentProcess(transcript_id, async () => {
  const transcript = await client.transcripts.get(transcript_id);
  await processCompletedTranscript(transcript);
});
```

### Step 5: Testing Webhooks Locally

```bash
# Option 1: ngrok
ngrok http 3000
# Use the HTTPS URL as your webhook_url

# Option 2: Simulate webhook manually
curl -X POST http://localhost:3000/webhooks/assemblyai \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "transcript_id": "test-id-123",
    "status": "completed"
  }'
```

### Webhook Payload Reference

AssemblyAI sends a POST with this JSON body:

```json
{
  "transcript_id": "6wij2z3g66-...",
  "status": "completed"
}
```

For errors:
```json
{
  "transcript_id": "6wij2z3g66-...",
  "status": "error",
  "error": "Download error: unable to download audio from URL"
}
```

If `redact_pii_audio` was enabled, a second webhook fires when redacted audio is ready.

## Output
- Webhook endpoint that receives transcription completion events
- Auth header verification for secure webhook handling
- Idempotent processing to handle retries
- LeMUR auto-analysis triggered on completion

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not received | URL not accessible from internet | Verify HTTPS URL, check firewall |
| 401 on webhook | Wrong auth header value | Match `webhook_auth_header_value` from submission |
| Duplicate processing | Webhook retried after timeout | Implement idempotency (check transcript_id) |
| Webhook timeout | Processing > 10 seconds | Return 200 immediately, process async |
| Missing transcript data | Fetching too early | Fetch with `client.transcripts.get()` after webhook |

## Resources
- [AssemblyAI Webhooks Guide](https://www.assemblyai.com/docs/getting-started/webhooks)
- [Webhook API Reference](https://www.assemblyai.com/docs/api-reference/transcripts/submit)
- [Streaming Webhooks](https://www.assemblyai.com/docs/streaming/webhooks)

## Next Steps
For performance optimization, see `assemblyai-performance-tuning`.
