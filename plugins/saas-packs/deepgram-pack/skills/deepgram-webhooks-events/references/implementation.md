# Deepgram Webhooks Events - Implementation Details

## TypeScript Callback Server (Express)
```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use('/webhooks/deepgram', express.raw({ type: 'application/json' }));
app.use(express.json());

interface DeepgramCallback {
  request_id: string;
  metadata: { request_id: string; duration: number; channels: number; models: string[] };
  results: { channels: Array<{ alternatives: Array<{ transcript: string; confidence: number; words: Array<{ word: string; start: number; end: number; confidence: number }> }> }> };
}

function verifyDeepgramSignature(payload: Buffer, signature: string | undefined, secret: string): boolean {
  if (!signature) return false;
  const expectedSignature = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature));
}

app.post('/webhooks/deepgram', async (req, res) => {
  const signature = req.headers['x-deepgram-signature'] as string;
  const webhookSecret = process.env.DEEPGRAM_WEBHOOK_SECRET;
  if (webhookSecret && !verifyDeepgramSignature(req.body, signature, webhookSecret)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  const callback: DeepgramCallback = JSON.parse(req.body.toString());
  const transcript = callback.results.channels[0]?.alternatives[0]?.transcript;
  await storeTranscription({ requestId: callback.request_id, transcript, metadata: callback.metadata });
  await notifyClient(callback.request_id, { status: 'completed', transcript });
  res.status(200).json({ received: true });
});
```

## Async Transcription Service
```typescript
import { createClient } from '@deepgram/sdk';
import { v4 as uuidv4 } from 'uuid';

export class AsyncTranscriptionService {
  private client;
  private callbackBaseUrl: string;

  constructor(apiKey: string, callbackBaseUrl: string) {
    this.client = createClient(apiKey);
    this.callbackBaseUrl = callbackBaseUrl;
  }

  async submitTranscription(audioUrl: string, options = {}) {
    const jobId = uuidv4();
    const callbackUrl = `${this.callbackBaseUrl}/webhooks/deepgram?job=${jobId}`;
    const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
      { url: audioUrl },
      { model: 'nova-2', smart_format: true, callback: callbackUrl, ...options }
    );
    if (error) throw new Error(`Submission failed: ${error.message}`);
    await redis.hset(`transcription:${jobId}`, { status: 'processing', requestId: result.request_id, submittedAt: new Date().toISOString() });
    return { jobId, requestId: result.request_id };
  }
}
```

## Callback Retry Handler
```typescript
export class CallbackRetryHandler {
  private config: { maxRetries: number; baseDelay: number; maxDelay: number };

  async processWithRetry(requestId: string, processor: () => Promise<void>): Promise<void> {
    let attempt = 0;
    while (attempt < this.config.maxRetries) {
      try { await processor(); return; }
      catch (error) {
        attempt++;
        if (attempt >= this.config.maxRetries) throw error;
        const delay = Math.min(this.config.baseDelay * Math.pow(2, attempt - 1), this.config.maxDelay);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
}
```

## Testing Callbacks Locally
```bash
# Use ngrok to expose local server
ngrok http 3000

# Test callback endpoint
curl -X POST https://your-ngrok-url.ngrok.io/webhooks/deepgram \
  -H "Content-Type: application/json" \
  -d '{"request_id":"test-123","metadata":{"request_id":"test-123","duration":10.5},"results":{"channels":[{"alternatives":[{"transcript":"This is a test.","confidence":0.95}]}]}}'
```

## Client SDK for Async Transcription
```typescript
export class AsyncTranscriptionClient {
  private baseUrl: string;
  private pollInterval: number;

  constructor(baseUrl: string, pollInterval = 2000) {
    this.baseUrl = baseUrl;
    this.pollInterval = pollInterval;
  }

  async transcribe(audioUrl: string): Promise<{ transcript: string; confidence: number }> {
    const response = await fetch(`${this.baseUrl}/transcribe/async`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audioUrl }),
    });
    const { jobId } = await response.json();
    return this.waitForResult(jobId);
  }

  async waitForResult(jobId: string, timeout = 300000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      const response = await fetch(`${this.baseUrl}/transcribe/status/${jobId}`);
      const data = await response.json();
      if (data.status === 'completed') return data.result;
      if (data.status === 'failed') throw new Error('Transcription failed');
      await new Promise(r => setTimeout(r, this.pollInterval));
    }
    throw new Error('Transcription timeout');
  }
}
```
