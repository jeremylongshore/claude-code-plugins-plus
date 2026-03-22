---
name: deepgram-webhooks-events
description: |
  Implement Deepgram callback and webhook handling for async transcription.
  Use when implementing callback URLs, processing async transcription results,
  or handling Deepgram event notifications.
  Trigger: "deepgram callback", "deepgram webhook", "async transcription",
  "deepgram events", "deepgram notifications", "deepgram async".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, webhooks, transcription, async]

---
# Deepgram Webhooks & Callbacks

## Overview
Implement async transcription with Deepgram's callback feature. When you pass a `callback` URL, Deepgram returns a `request_id` immediately, processes audio in the background, and POSTs results to your endpoint. Supports HTTP and WebSocket callbacks with automatic retry (10 attempts, 30s intervals).

## Deepgram Callback Flow
```
1. Client -> POST /v1/listen?callback=https://you.com/webhook  (with audio)
2. Deepgram -> 200 { request_id: "..." }                       (immediate)
3. Deepgram processes audio asynchronously
4. Deepgram -> POST https://you.com/webhook                    (results)
   Retries up to 10 times (30s delay) on non-2xx response
```

## Instructions

### Step 1: Submit Async Transcription

```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

async function submitAsync(audioUrl: string, callbackUrl: string) {
  // Deepgram sends transcription via callback URL instead of
  // holding the connection open.
  const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
    { url: audioUrl },
    {
      model: 'nova-3',
      smart_format: true,
      diarize: true,
      utterances: true,
      callback: callbackUrl,  // Your HTTPS endpoint
      // callback_method: 'put',  // Optional: use PUT instead of POST
    }
  );

  if (error) throw new Error(`Submit failed: ${error.message}`);

  // Deepgram returns immediately with request_id
  const requestId = result.metadata.request_id;
  console.log(`Submitted. Request ID: ${requestId}`);
  console.log(`Results will be POSTed to: ${callbackUrl}`);
  return requestId;
}

// Also works with direct curl:
// curl -X POST 'https://api.deepgram.com/v1/listen?model=nova-3&callback=https://you.com/webhook' \
//   -H "Authorization: Token $DEEPGRAM_API_KEY" \
//   -H "Content-Type: application/json" \
//   -d '{"url":"https://example.com/audio.wav"}'
```

### Step 2: Callback Server

```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();

// IMPORTANT: Use raw body for HMAC signature verification
app.use('/webhooks/deepgram', express.raw({ type: 'application/json', limit: '50mb' }));

app.post('/webhooks/deepgram', async (req, res) => {
  try {
    // 1. Verify signature (if webhook secret configured)
    const signature = req.headers['x-deepgram-signature'] as string;
    if (process.env.DEEPGRAM_WEBHOOK_SECRET && signature) {
      const expected = crypto
        .createHmac('sha256', process.env.DEEPGRAM_WEBHOOK_SECRET)
        .update(req.body)
        .digest('hex');

      // Timing-safe comparison to prevent timing attacks
      if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
        console.error('Invalid webhook signature');
        return res.status(401).json({ error: 'Invalid signature' });
      }
    }

    // 2. Parse result
    const result = JSON.parse(req.body.toString());
    const requestId = result.metadata?.request_id;
    const transcript = result.results?.channels?.[0]?.alternatives?.[0]?.transcript;
    const duration = result.metadata?.duration;

    console.log(`Callback received: ${requestId}`);
    console.log(`Duration: ${duration}s`);
    console.log(`Transcript: ${transcript?.substring(0, 200)}...`);

    // 3. Process and store
    await processTranscriptionResult(requestId, result);

    // 4. Return 200 — Deepgram retries on non-2xx
    res.status(200).json({ received: true, request_id: requestId });
  } catch (err: any) {
    console.error('Callback processing error:', err.message);
    // Return 500 to trigger Deepgram retry
    res.status(500).json({ error: 'Processing failed' });
  }
});

async function processTranscriptionResult(requestId: string, result: any) {
  const transcript = result.results.channels[0].alternatives[0];

  // Store transcript
  const record = {
    requestId,
    transcript: transcript.transcript,
    confidence: transcript.confidence,
    duration: result.metadata.duration,
    words: transcript.words?.length ?? 0,
    utterances: result.results.utterances?.map((u: any) => ({
      speaker: u.speaker,
      text: u.transcript,
      start: u.start,
      end: u.end,
    })),
    processedAt: new Date().toISOString(),
  };

  // Save to database / notify clients / trigger downstream
  console.log('Processed:', JSON.stringify(record, null, 2));
  return record;
}
```

### Step 3: Job Tracking with Redis

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL ?? 'redis://localhost:6379');

class TranscriptionJobTracker {
  async submit(requestId: string, metadata: Record<string, any>) {
    await redis.hset(`job:${requestId}`, {
      status: 'processing',
      submittedAt: new Date().toISOString(),
      ...metadata,
    });
    // Auto-expire after 24 hours
    await redis.expire(`job:${requestId}`, 86400);
  }

  async complete(requestId: string, result: any) {
    await redis.hset(`job:${requestId}`, {
      status: 'completed',
      completedAt: new Date().toISOString(),
      transcript: result.results.channels[0].alternatives[0].transcript,
      duration: result.metadata.duration,
    });
    // Publish for real-time notification
    await redis.publish('transcription:complete', JSON.stringify({
      requestId,
      duration: result.metadata.duration,
    }));
  }

  async getStatus(requestId: string) {
    return redis.hgetall(`job:${requestId}`);
  }
}

// Client-facing status endpoint
app.get('/api/transcription/:requestId', async (req, res) => {
  const tracker = new TranscriptionJobTracker();
  const status = await tracker.getStatus(req.params.requestId);

  if (!status || Object.keys(status).length === 0) {
    return res.status(404).json({ error: 'Job not found' });
  }
  res.json(status);
});
```

### Step 4: Client SDK with Submit/Poll/Wait

```typescript
class AsyncTranscriptionClient {
  private deepgram: ReturnType<typeof createClient>;
  private baseUrl: string;

  constructor(apiKey: string, serverBaseUrl: string) {
    this.deepgram = createClient(apiKey);
    this.baseUrl = serverBaseUrl;
  }

  async submit(audioUrl: string): Promise<string> {
    const callbackUrl = `${this.baseUrl}/webhooks/deepgram`;
    const { result, error } = await this.deepgram.listen.prerecorded.transcribeUrl(
      { url: audioUrl },
      { model: 'nova-3', smart_format: true, diarize: true, callback: callbackUrl }
    );
    if (error) throw error;
    return result.metadata.request_id;
  }

  async poll(requestId: string): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/transcription/${requestId}`);
    if (res.status === 404) return null;
    return res.json();
  }

  async waitForResult(requestId: string, timeoutMs = 300000): Promise<any> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const status = await this.poll(requestId);
      if (status?.status === 'completed') return status;
      if (status?.status === 'failed') throw new Error('Transcription failed');
      await new Promise(r => setTimeout(r, 2000));  // Poll every 2s
    }
    throw new Error('Timeout waiting for transcription');
  }
}

// Usage:
const client = new AsyncTranscriptionClient(
  process.env.DEEPGRAM_API_KEY!,
  'https://your-server.com'
);
const requestId = await client.submit('https://example.com/long-recording.wav');
const result = await client.waitForResult(requestId);
```

### Step 5: Local Testing with ngrok

```bash
# Expose local callback server to Deepgram
ngrok http 3000

# Use the ngrok URL as callback
curl -X POST 'https://api.deepgram.com/v1/listen?model=nova-3&callback=https://abc123.ngrok.io/webhooks/deepgram' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://static.deepgram.com/examples/nasa-podcast.wav"}'
```

### Step 6: Idempotent Processing

```typescript
// Deepgram retries callbacks — ensure idempotent processing
const processedRequests = new Set<string>();

app.post('/webhooks/deepgram', async (req, res) => {
  const result = JSON.parse(req.body.toString());
  const requestId = result.metadata?.request_id;

  // Skip if already processed
  if (processedRequests.has(requestId)) {
    console.log(`Duplicate callback for ${requestId} — skipping`);
    return res.status(200).json({ received: true, duplicate: true });
  }

  processedRequests.add(requestId);
  // In production, use Redis SET with NX for distributed dedup:
  // const isNew = await redis.set(`processed:${requestId}`, '1', 'NX', 'EX', 86400);
  // if (!isNew) return res.status(200).json({ duplicate: true });

  await processTranscriptionResult(requestId, result);
  res.status(200).json({ received: true });
});
```

## Output
- Async transcription submission with callback URL
- Callback server with signature verification
- Redis-backed job tracking with pub/sub notifications
- Client SDK with submit/poll/wait pattern
- Idempotent callback processing
- Local testing setup with ngrok

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Callback not received | Endpoint unreachable | Check HTTPS, firewall, use ngrok for local |
| Duplicate callbacks | Deepgram retry after slow response | Implement idempotency with request_id |
| Invalid signature | Wrong webhook secret | Verify `DEEPGRAM_WEBHOOK_SECRET` matches Console |
| Processing timeout | Slow downstream | Return 200 immediately, process async |
| Large payload | Long audio transcript | Increase `express.raw` limit |

## Resources
- [Callback Feature](https://developers.deepgram.com/docs/callback)
- [Callback Not Received](https://developers.deepgram.com/docs/payload-too-large)
- [STT Callback API](https://developers.deepgram.com/docs/using-callbacks-to-return-transcripts-to-your-server)
