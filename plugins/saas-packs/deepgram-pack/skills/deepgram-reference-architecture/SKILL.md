---
name: deepgram-reference-architecture
description: |
  Implement Deepgram reference architecture for scalable transcription systems.
  Use when designing transcription pipelines, building production architectures,
  or planning Deepgram integration at scale.
  Trigger: "deepgram architecture", "transcription pipeline", "deepgram system design",
  "deepgram at scale", "enterprise deepgram", "deepgram queue".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, architecture, scaling]

---
# Deepgram Reference Architecture

## Overview
Four reference architectures for Deepgram transcription at scale: synchronous REST for short files, async queue (BullMQ) for batch processing, WebSocket proxy for real-time streaming, and a hybrid router that auto-selects the best pattern based on audio duration.

## Architecture Selection Guide

| Pattern | Best For | Latency | Throughput | Complexity |
|---------|----------|---------|------------|------------|
| Sync REST | Files <60s, low volume | Low | Low | Simple |
| Async Queue | Batch, files >60s | Medium | High | Medium |
| WebSocket Proxy | Live audio, real-time | Real-time | Medium | Medium |
| Hybrid Router | Mixed workloads | Varies | High | High |
| Callback | Files >5min, fire-and-forget | N/A | Very High | Low |

## Instructions

### Step 1: Synchronous REST Pattern

```typescript
import express from 'express';
import { createClient } from '@deepgram/sdk';

const app = express();
app.use(express.json());

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

// Direct API call — best for short files (<60s)
app.post('/api/transcribe', async (req, res) => {
  const { url, model = 'nova-3', diarize = false } = req.body;

  try {
    const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
      { url },
      { model, smart_format: true, diarize, utterances: diarize }
    );
    if (error) return res.status(502).json({ error: error.message });

    res.json({
      transcript: result.results.channels[0].alternatives[0].transcript,
      confidence: result.results.channels[0].alternatives[0].confidence,
      duration: result.metadata.duration,
      request_id: result.metadata.request_id,
      utterances: diarize ? result.results.utterances : undefined,
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});
```

### Step 2: Async Queue Pattern (BullMQ)

```typescript
import { Queue, Worker, Job } from 'bullmq';
import { createClient } from '@deepgram/sdk';
import Redis from 'ioredis';

const connection = new Redis(process.env.REDIS_URL ?? 'redis://localhost:6379');

// Producer: submit transcription jobs
const transcriptionQueue = new Queue('transcription', { connection });

async function submitJob(audioUrl: string, options: Record<string, any> = {}) {
  const job = await transcriptionQueue.add('transcribe', {
    audioUrl,
    model: options.model ?? 'nova-3',
    diarize: options.diarize ?? false,
    submittedAt: new Date().toISOString(),
  }, {
    attempts: 3,
    backoff: { type: 'exponential', delay: 5000 },
    removeOnComplete: { age: 86400 },  // Keep for 24h
  });

  console.log(`Job submitted: ${job.id}`);
  return job.id;
}

// Consumer: process transcription jobs
const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

const worker = new Worker('transcription', async (job: Job) => {
  const { audioUrl, model, diarize } = job.data;
  console.log(`Processing job ${job.id}: ${audioUrl}`);

  const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
    { url: audioUrl },
    { model, smart_format: true, diarize, utterances: diarize }
  );

  if (error) throw new Error(`Deepgram error: ${error.message}`);

  const output = {
    transcript: result.results.channels[0].alternatives[0].transcript,
    confidence: result.results.channels[0].alternatives[0].confidence,
    duration: result.metadata.duration,
    request_id: result.metadata.request_id,
  };

  // Store result (database, S3, etc.)
  console.log(`Job ${job.id} complete: ${output.duration}s audio`);
  return output;
}, {
  connection,
  concurrency: 10,     // Process 10 jobs simultaneously
  limiter: {
    max: 50,           // Max 50 per time window
    duration: 60000,   // Per minute
  },
});

worker.on('completed', (job) => console.log(`Completed: ${job.id}`));
worker.on('failed', (job, err) => console.error(`Failed: ${job?.id}`, err.message));
```

### Step 3: WebSocket Proxy for Real-Time

```typescript
import { WebSocketServer, WebSocket } from 'ws';
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk';

const wss = new WebSocketServer({ port: 8080 });

wss.on('connection', (clientWs: WebSocket) => {
  console.log('Client connected');

  const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);
  const dgConnection = deepgram.listen.live({
    model: 'nova-3',
    smart_format: true,
    interim_results: true,
    utterance_end_ms: 1000,
    encoding: 'linear16',
    sample_rate: 16000,
    channels: 1,
  });

  // Forward Deepgram transcripts to client
  dgConnection.on(LiveTranscriptionEvents.Transcript, (data) => {
    const transcript = data.channel.alternatives[0]?.transcript;
    if (transcript && clientWs.readyState === WebSocket.OPEN) {
      clientWs.send(JSON.stringify({
        type: 'transcript',
        text: transcript,
        is_final: data.is_final,
        speech_final: data.speech_final,
      }));
    }
  });

  dgConnection.on(LiveTranscriptionEvents.UtteranceEnd, () => {
    if (clientWs.readyState === WebSocket.OPEN) {
      clientWs.send(JSON.stringify({ type: 'utterance_end' }));
    }
  });

  // Forward client audio to Deepgram
  clientWs.on('message', (data: Buffer) => {
    if (dgConnection.getReadyState() === 1) {
      dgConnection.send(data);
    }
  });

  // Cleanup on disconnect
  clientWs.on('close', () => {
    dgConnection.finish();
    console.log('Client disconnected');
  });

  dgConnection.on(LiveTranscriptionEvents.Error, (err) => {
    console.error('Deepgram error:', err.message);
    clientWs.close();
  });
});

console.log('WebSocket proxy on ws://localhost:8080');
```

### Step 4: Hybrid Router

```typescript
import { createClient } from '@deepgram/sdk';

class TranscriptionRouter {
  private client: ReturnType<typeof createClient>;
  private queue: typeof transcriptionQueue;

  constructor(apiKey: string, queue: any) {
    this.client = createClient(apiKey);
    this.queue = queue;
  }

  async route(audioUrl: string, options: {
    mode?: 'sync' | 'async' | 'callback' | 'auto';
    estimatedDuration?: number;  // seconds
    callbackUrl?: string;
    model?: string;
    diarize?: boolean;
  } = {}) {
    const mode = options.mode ?? 'auto';
    const duration = options.estimatedDuration ?? 0;

    // Auto-select based on duration
    const selectedMode = mode === 'auto'
      ? duration > 300 ? 'callback'   // >5 min: use callback
        : duration > 60 ? 'async'     // >60s: use queue
        : 'sync'                       // <60s: direct API
      : mode;

    console.log(`Routing: ${selectedMode} (est. ${duration}s)`);

    switch (selectedMode) {
      case 'sync':
        return this.syncTranscribe(audioUrl, options);
      case 'async':
        return this.asyncTranscribe(audioUrl, options);
      case 'callback':
        return this.callbackTranscribe(audioUrl, options);
    }
  }

  private async syncTranscribe(url: string, opts: any) {
    const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
      { url },
      { model: opts.model ?? 'nova-3', smart_format: true, diarize: opts.diarize }
    );
    if (error) throw error;
    return { mode: 'sync', result };
  }

  private async asyncTranscribe(url: string, opts: any) {
    const jobId = await submitJob(url, opts);
    return { mode: 'async', jobId };
  }

  private async callbackTranscribe(url: string, opts: any) {
    const { result } = await this.client.listen.prerecorded.transcribeUrl(
      { url },
      { model: opts.model ?? 'nova-3', smart_format: true, callback: opts.callbackUrl }
    );
    return { mode: 'callback', requestId: result.metadata.request_id };
  }
}
```

### Step 5: Architecture Diagram

```
                    ┌──────────────┐
                    │   Client     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   API Gateway │
                    │  /transcribe  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Hybrid Router │
                    └──┬───┬───┬───┘
                       │   │   │
           ┌───────────┘   │   └───────────┐
           ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │   Sync   │   │  Queue   │   │ Callback │
    │  (<60s)  │   │ (BullMQ) │   │  (>5min) │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         └──────────┬───┘──────────────┘
                    │
            ┌───────▼──────┐
            │  Deepgram    │
            │  API         │
            └───────┬──────┘
                    │
            ┌───────▼──────┐
            │   Results    │
            │   Store      │
            └──────────────┘
```

## Output
- Sync REST endpoint for short files
- BullMQ queue with workers for batch processing
- WebSocket proxy for real-time streaming
- Hybrid router with auto-mode selection
- Architecture diagram

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Sync timeout on large file | Wrong pattern selected | Use async queue or callback |
| Queue backlog growing | Workers overloaded | Scale workers, increase concurrency |
| WebSocket disconnects | Network instability | Auto-reconnect with backoff |
| Callback not received | Endpoint unreachable | Check HTTPS, verify callback URL |

## Resources
- [Deepgram Architecture Guide](https://developers.deepgram.com/docs/architecture)
- [BullMQ Documentation](https://docs.bullmq.io/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
