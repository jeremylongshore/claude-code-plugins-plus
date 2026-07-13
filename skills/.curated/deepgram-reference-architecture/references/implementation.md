# Deepgram Reference Architecture - Implementation Details

## Pattern 1: Synchronous API

```typescript
import express from 'express';
import { createClient } from '@deepgram/sdk';

const app = express();
const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

app.post('/transcribe', async (req, res) => {
  const { audioUrl, userId } = req.body;
  try {
    const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
      { url: audioUrl }, { model: 'nova-2', smart_format: true }
    );
    if (error) throw error;
    const transcript = result.results.channels[0].alternatives[0].transcript;
    await db.transcripts.create({ userId, audioUrl, transcript, metadata: result.metadata });
    res.json({ transcript, requestId: result.metadata.request_id });
  } catch (err) { res.status(500).json({ error: 'Transcription failed' }); }
});
```

## Pattern 2: Asynchronous Queue

```typescript
// Producer
import { Queue } from 'bullmq';
import { v4 as uuidv4 } from 'uuid';

const transcriptionQueue = new Queue('transcription', { connection: redis });

export async function submitTranscription(audioUrl: string, options: { priority?: number; userId?: string } = {}) {
  const jobId = uuidv4();
  await transcriptionQueue.add('transcribe', { audioUrl, userId: options.userId }, {
    jobId, priority: options.priority ?? 0, attempts: 3,
    backoff: { type: 'exponential', delay: 5000 },
  });
  return jobId;
}

// Worker
import { Worker, Job } from 'bullmq';

const worker = new Worker('transcription', async (job: Job) => {
  const { audioUrl, userId } = job.data;
  const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
    { url: audioUrl }, { model: 'nova-2', smart_format: true }
  );
  if (error) throw error;
  const transcript = result.results.channels[0].alternatives[0].transcript;
  await db.transcripts.create({ jobId: job.id, userId, audioUrl, transcript, metadata: result.metadata });
  await notifyClient(userId, { jobId: job.id, status: 'completed', transcript });
  return { transcript };
}, { connection: redis, concurrency: 10 });
```

## Pattern 3: Real-time Streaming

```typescript
import { WebSocketServer, WebSocket } from 'ws';
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk';

const wss = new WebSocketServer({ port: 8080 });
const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

wss.on('connection', (clientWs: WebSocket) => {
  const dgConnection = deepgram.listen.live({ model: 'nova-2', smart_format: true, interim_results: true });

  dgConnection.on(LiveTranscriptionEvents.Transcript, (data) => {
    clientWs.send(JSON.stringify({
      type: 'transcript', transcript: data.channel.alternatives[0].transcript, isFinal: data.is_final,
    }));
  });

  dgConnection.on(LiveTranscriptionEvents.Error, (error) => {
    clientWs.send(JSON.stringify({ type: 'error', error: error.message }));
  });

  clientWs.on('message', (data: Buffer) => dgConnection.send(data));
  clientWs.on('close', () => dgConnection.finish());
});
```

## Pattern 4: Hybrid Router

```typescript
import express from 'express';

const app = express();

app.post('/transcribe', async (req, res) => {
  const { audioUrl, mode, audioDuration } = req.body;
  let selectedMode = mode;
  if (!selectedMode) {
    if (audioDuration && audioDuration < 60) selectedMode = 'sync';
    else if (audioDuration && audioDuration > 300) selectedMode = 'async';
    else selectedMode = 'sync';
  }
  switch (selectedMode) {
    case 'sync': return syncHandler(req, res);
    case 'async': return asyncHandler(req, res);
    case 'stream': return streamHandler(req, res);
    default: return syncHandler(req, res);
  }
});
```

## Enterprise Configuration

```typescript
export const config = {
  regions: ['us-east-1', 'us-west-2', 'eu-west-1'],
  redis: {
    cluster: true,
    nodes: [
      { host: 'redis-us-east.example.com', port: 6379 },
      { host: 'redis-us-west.example.com', port: 6379 },
      { host: 'redis-eu-west.example.com', port: 6379 },
    ],
  },
  workers: { concurrency: 20, maxRetries: 5 },
  rateLimit: { maxRequestsPerMinute: 1000, maxConcurrent: 100 },
  monitoring: { metricsEndpoint: '/metrics', healthEndpoint: '/health', tracingEnabled: true },
};
```

## Monitoring Architecture

```typescript
import { Registry, collectDefaultMetrics, Counter, Histogram, Gauge } from 'prom-client';

export const registry = new Registry();
collectDefaultMetrics({ register: registry });

export const requestsTotal = new Counter({
  name: 'transcription_requests_total', help: 'Total transcription requests',
  labelNames: ['status', 'model', 'region'], registers: [registry],
});

export const latencyHistogram = new Histogram({
  name: 'transcription_latency_seconds', help: 'Transcription latency',
  labelNames: ['model'], buckets: [0.5, 1, 2, 5, 10, 30, 60, 120], registers: [registry],
});

export const queueDepth = new Gauge({
  name: 'transcription_queue_depth', help: 'Number of jobs in queue', registers: [registry],
});

export const activeConnections = new Gauge({
  name: 'deepgram_active_connections', help: 'Active Deepgram connections', registers: [registry],
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
