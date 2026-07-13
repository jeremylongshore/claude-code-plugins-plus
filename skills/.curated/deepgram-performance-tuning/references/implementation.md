# Deepgram Performance Tuning - Implementation Details

## Audio Preprocessing

```typescript
import ffmpeg from 'fluent-ffmpeg';
import { Readable } from 'stream';

interface OptimizedAudio {
  buffer: Buffer;
  mimetype: string;
  sampleRate: number;
  channels: number;
  duration: number;
}

export async function optimizeAudio(inputPath: string): Promise<OptimizedAudio> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    ffmpeg(inputPath)
      .audioCodec('pcm_s16le')
      .audioChannels(1)
      .audioFrequency(16000)
      .format('wav')
      .on('error', reject)
      .on('end', () => {
        const buffer = Buffer.concat(chunks);
        resolve({ buffer, mimetype: 'audio/wav', sampleRate: 16000, channels: 1, duration: buffer.length / (16000 * 2) });
      })
      .pipe()
      .on('data', (chunk: Buffer) => chunks.push(chunk));
  });
}

export async function optimizeAudioBuffer(audioBuffer: Buffer, inputFormat: string): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    const readable = new Readable();
    readable.push(audioBuffer);
    readable.push(null);
    ffmpeg(readable)
      .inputFormat(inputFormat)
      .audioCodec('pcm_s16le').audioChannels(1).audioFrequency(16000).format('wav')
      .on('error', reject)
      .on('end', () => resolve(Buffer.concat(chunks)))
      .pipe()
      .on('data', (chunk: Buffer) => chunks.push(chunk));
  });
}
```

## Connection Pooling

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';

class DeepgramConnectionPool {
  private pool: DeepgramClient[] = [];
  private inUse: Set<DeepgramClient> = new Set();
  private waiting: Array<(client: DeepgramClient) => void> = [];
  private config: { minSize: number; maxSize: number; acquireTimeout: number; idleTimeout: number };

  constructor(apiKey: string, config: Partial<typeof this.config> = {}) {
    this.config = { minSize: config.minSize ?? 2, maxSize: config.maxSize ?? 10, acquireTimeout: config.acquireTimeout ?? 10000, idleTimeout: config.idleTimeout ?? 60000 };
    for (let i = 0; i < this.config.minSize; i++) this.pool.push(createClient(apiKey));
  }

  async acquire(): Promise<DeepgramClient> {
    if (this.pool.length > 0) { const client = this.pool.pop()!; this.inUse.add(client); return client; }
    if (this.inUse.size < this.config.maxSize) { const client = createClient(process.env.DEEPGRAM_API_KEY!); this.inUse.add(client); return client; }
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => { reject(new Error('Connection acquire timeout')); }, this.config.acquireTimeout);
      this.waiting.push((client) => { clearTimeout(timeout); resolve(client); });
    });
  }

  release(client: DeepgramClient): void {
    this.inUse.delete(client);
    if (this.waiting.length > 0) { const waiter = this.waiting.shift()!; this.inUse.add(client); waiter(client); }
    else { this.pool.push(client); }
  }

  async execute<T>(fn: (client: DeepgramClient) => Promise<T>): Promise<T> {
    const client = await this.acquire();
    try { return await fn(client); } finally { this.release(client); }
  }

  getStats() { return { poolSize: this.pool.length, inUse: this.inUse.size, waiting: this.waiting.length }; }
}

export const pool = new DeepgramConnectionPool(process.env.DEEPGRAM_API_KEY!);
```

## Streaming for Large Files

```typescript
import { createClient } from '@deepgram/sdk';
import { createReadStream, statSync } from 'fs';

export async function streamLargeFile(filePath: string, options: { chunkSize?: number; model?: string } = {}): Promise<string> {
  const { chunkSize = 1024 * 1024, model = 'nova-2' } = options;
  const client = createClient(process.env.DEEPGRAM_API_KEY!);
  const transcripts: string[] = [];

  const connection = client.listen.live({ model, smart_format: true, punctuate: true });

  return new Promise((resolve, reject) => {
    connection.on('open', () => {
      const stream = createReadStream(filePath, { highWaterMark: chunkSize });
      stream.on('data', (chunk: Buffer) => connection.send(chunk));
      stream.on('end', () => connection.finish());
      stream.on('error', reject);
    });
    connection.on('transcript', (data) => { if (data.is_final) transcripts.push(data.channel.alternatives[0].transcript); });
    connection.on('close', () => resolve(transcripts.join(' ')));
    connection.on('error', reject);
  });
}
```

## Model Selection for Speed

```typescript
const models: Record<string, { name: string; accuracy: string; speed: string; costPerMinute: number }> = {
  'nova-2': { name: 'Nova-2', accuracy: 'high', speed: 'fast', costPerMinute: 0.0043 },
  'nova': { name: 'Nova', accuracy: 'high', speed: 'fast', costPerMinute: 0.0043 },
  'enhanced': { name: 'Enhanced', accuracy: 'medium', speed: 'fast', costPerMinute: 0.0145 },
  'base': { name: 'Base', accuracy: 'low', speed: 'fast', costPerMinute: 0.0048 },
};

export function selectModel(requirements: { prioritize: 'accuracy' | 'speed' | 'cost'; minAccuracy?: string }): string {
  const { prioritize, minAccuracy = 'low' } = requirements;
  const accuracyOrder = ['high', 'medium', 'low'];
  const minAccuracyIndex = accuracyOrder.indexOf(minAccuracy);
  const eligible = Object.entries(models).filter(([_, config]) => accuracyOrder.indexOf(config.accuracy) <= minAccuracyIndex);

  if (prioritize === 'cost') return eligible.reduce((best, [name, config]) => config.costPerMinute < models[best].costPerMinute ? name : best, eligible[0][0]);
  return 'nova-2';
}
```

## Parallel Processing

```typescript
import pLimit from 'p-limit';

export async function transcribeMultiple(audioUrls: string[], concurrency = 5) {
  const limit = pLimit(concurrency);
  const startTime = Date.now();

  const results = await Promise.all(
    audioUrls.map((url) => limit(async () => {
      const itemStart = Date.now();
      const result = await pool.execute(async (client) => {
        const { result, error } = await client.listen.prerecorded.transcribeUrl({ url }, { model: 'nova-2', smart_format: true });
        if (error) throw error;
        return result;
      });
      return { file: url, transcript: result.results.channels[0].alternatives[0].transcript, duration: Date.now() - itemStart };
    }))
  );

  console.log(`Processed ${audioUrls.length} files in ${Date.now() - startTime}ms`);
  return results;
}
```

## Caching Results

```typescript
import { createHash } from 'crypto';

export class TranscriptionCache {
  private ttl: number;
  constructor(options: { ttl?: number } = {}) { this.ttl = options.ttl ?? 3600; }

  private getCacheKey(audioUrl: string, options: Record<string, unknown>): string {
    return `transcription:${createHash('sha256').update(JSON.stringify({ audioUrl, options })).digest('hex')}`;
  }

  async transcribeWithCache(transcribeFn: () => Promise<string>, audioUrl: string, options: Record<string, unknown>) {
    const cached = await redis.get(this.getCacheKey(audioUrl, options));
    if (cached) return { transcript: cached, cached: true };
    const transcript = await transcribeFn();
    await redis.setex(this.getCacheKey(audioUrl, options), this.ttl, transcript);
    return { transcript, cached: false };
  }
}
```

## Performance Metrics

```typescript
import { Histogram, Counter, Gauge } from 'prom-client';

export const transcriptionLatency = new Histogram({
  name: 'deepgram_transcription_latency_seconds', help: 'Latency of transcription requests',
  labelNames: ['model', 'status'], buckets: [0.5, 1, 2, 5, 10, 30, 60],
});

export const audioDuration = new Histogram({
  name: 'deepgram_audio_duration_seconds', help: 'Duration of audio files processed',
  buckets: [10, 30, 60, 120, 300, 600, 1800],
});

export const processingRatio = new Gauge({
  name: 'deepgram_processing_ratio', help: 'Ratio of processing time to audio duration',
  labelNames: ['model'],
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
