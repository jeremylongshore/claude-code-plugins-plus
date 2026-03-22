---
name: assemblyai-rate-limits
description: |
  Implement AssemblyAI rate limiting, backoff, and queue-based throttling.
  Use when handling rate limit errors, implementing retry logic,
  or managing concurrent transcription throughput.
  Trigger with phrases like "assemblyai rate limit", "assemblyai throttling",
  "assemblyai 429", "assemblyai retry", "assemblyai backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI Rate Limits

## Overview
Handle AssemblyAI rate limits with exponential backoff, queue-based throttling, and concurrency management. AssemblyAI auto-scales limits for paid users.

## Prerequisites
- `assemblyai` package installed
- Understanding of async/await patterns

## Rate Limit Tiers (Actual)

### Async Transcription API
| Endpoint | Free | Pay-as-you-go |
|----------|------|---------------|
| `POST /v2/transcript` | 5/min | Scales with usage |
| `GET /v2/transcript/:id` | No hard limit | No hard limit |
| `POST /v2/upload` | 5/min | Scales with usage |

### Streaming (WebSocket)
| Metric | Free | Pay-as-you-go |
|--------|------|---------------|
| New streams/min | 5 | 100 (auto-scales) |
| Concurrent streams | ~5 | Unlimited (auto-scales 10% every 60s at 70% usage) |

### LeMUR
| Metric | Free | Paid |
|--------|------|------|
| Requests/min | Limited | Scales with usage |
| Max audio input | 100 hours per request | 100 hours per request |

**Note:** AssemblyAI auto-scales paid limits. At 70%+ utilization, the new session rate limit increases by 10% every 60 seconds with no ceiling cap.

## Instructions

### Step 1: Exponential Backoff with Jitter

```typescript
import { AssemblyAI, type Transcript } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

async function transcribeWithBackoff(
  audioUrl: string,
  options: Record<string, any> = {},
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 30000 }
): Promise<Transcript> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await client.transcripts.transcribe({
        audio: audioUrl,
        ...options,
      });
    } catch (err: any) {
      if (attempt === config.maxRetries) throw err;

      const status = err.status ?? err.statusCode;
      // Only retry on 429 (rate limit) and 5xx (server errors)
      if (status && status !== 429 && (status < 500 || status >= 600)) throw err;

      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.baseDelayMs;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.warn(`[${attempt + 1}/${config.maxRetries}] Retrying in ${delay.toFixed(0)}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 2: Queue-Based Concurrency Control

```typescript
import PQueue from 'p-queue';

// Limit to N concurrent transcription jobs
const transcriptionQueue = new PQueue({
  concurrency: 5,           // Max 5 concurrent jobs
  interval: 60_000,         // Per minute window
  intervalCap: 50,           // Max 50 new jobs per minute
});

async function queuedTranscribe(audioUrl: string): Promise<Transcript> {
  return transcriptionQueue.add(() =>
    transcribeWithBackoff(audioUrl)
  );
}

// Process a batch of files
const audioUrls = [
  'https://example.com/audio1.mp3',
  'https://example.com/audio2.mp3',
  'https://example.com/audio3.mp3',
];

const results = await Promise.all(
  audioUrls.map(url => queuedTranscribe(url))
);

console.log(`Completed ${results.length} transcriptions`);
console.log(`Queue size: ${transcriptionQueue.size}, pending: ${transcriptionQueue.pending}`);
```

### Step 3: Batch Processing with Progress

```typescript
async function batchTranscribe(
  audioUrls: string[],
  onProgress?: (completed: number, total: number) => void
): Promise<Transcript[]> {
  const queue = new PQueue({ concurrency: 5 });
  const results: Transcript[] = [];
  let completed = 0;

  const promises = audioUrls.map(url =>
    queue.add(async () => {
      const transcript = await transcribeWithBackoff(url);
      completed++;
      onProgress?.(completed, audioUrls.length);
      return transcript;
    })
  );

  return Promise.all(promises);
}

// Usage
await batchTranscribe(
  urls,
  (done, total) => console.log(`Progress: ${done}/${total}`)
);
```

### Step 4: Streaming Rate Limit Handling

```typescript
async function connectStreamingWithRetry(maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const transcriber = client.streaming.createService({
        speech_model: 'nova-3',
        sample_rate: 16000,
      });

      transcriber.on('error', (error) => {
        console.error('Streaming error:', error);
      });

      await transcriber.connect();
      return transcriber;
    } catch (err: any) {
      if (attempt === maxRetries) throw err;

      // WebSocket code 4008 = session limit
      const delay = Math.pow(2, attempt) * 2000;
      console.warn(`Stream connect failed. Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

## Output
- Automatic retry with exponential backoff and jitter
- Queue-based concurrency control with p-queue
- Batch transcription with progress reporting
- Streaming reconnection logic

## Error Handling
| Scenario | Status | Strategy |
|----------|--------|----------|
| Rate limited (async) | 429 | Exponential backoff, honor `Retry-After` header |
| Server error | 500-503 | Retry with backoff |
| Session limit (streaming) | WS 4008 | Wait and reconnect |
| Auth error | 401 | Do not retry, fix credentials |
| Invalid input | 400 | Do not retry, fix request |

## Resources
- [AssemblyAI Rate Limits](https://www.assemblyai.com/docs/deployment/account-management)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [AssemblyAI Streaming Limits](https://www.assemblyai.com/docs/streaming)

## Next Steps
For security configuration, see `assemblyai-security-basics`.
