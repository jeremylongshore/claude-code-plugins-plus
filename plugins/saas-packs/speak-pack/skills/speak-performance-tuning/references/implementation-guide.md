# Speak Performance Tuning - Implementation Guide

Detailed implementation reference for the speak-performance-tuning skill.

## Latency Benchmarks

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Session Start | 200ms | 500ms | 1000ms |
| Tutor Prompt | 150ms | 300ms | 600ms |
| Text Response Submit | 100ms | 250ms | 500ms |
| Audio Recognition | 500ms | 1500ms | 3000ms |
| Pronunciation Scoring | 800ms | 2000ms | 4000ms |


## Audio Optimization

### Pre-processing Audio Before Upload
```typescript
class AudioOptimizer {
  // Optimize audio for Speak's speech recognition
  async optimizeForRecognition(audioData: ArrayBuffer): Promise<ArrayBuffer> {
    // Convert to optimal format: 16kHz mono PCM WAV
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const audioBuffer = await audioContext.decodeAudioData(audioData);

    // Convert to mono if stereo
    const monoBuffer = this.toMono(audioBuffer);

    // Normalize audio levels
    const normalizedBuffer = this.normalize(monoBuffer);

    // Remove silence at start/end
    const trimmedBuffer = this.trimSilence(normalizedBuffer);

    // Encode as WAV
    return this.encodeWav(trimmedBuffer);
  }

  private toMono(buffer: AudioBuffer): AudioBuffer {
    if (buffer.numberOfChannels === 1) return buffer;

    const monoData = new Float32Array(buffer.length);
    const left = buffer.getChannelData(0);
    const right = buffer.getChannelData(1);

    for (let i = 0; i < buffer.length; i++) {
      monoData[i] = (left[i] + right[i]) / 2;
    }

    const ctx = new OfflineAudioContext(1, buffer.length, buffer.sampleRate);
    const newBuffer = ctx.createBuffer(1, buffer.length, buffer.sampleRate);
    newBuffer.copyToChannel(monoData, 0);
    return newBuffer;
  }

  private normalize(buffer: AudioBuffer): AudioBuffer {
    const data = buffer.getChannelData(0);
    let max = 0;

    for (let i = 0; i < data.length; i++) {
      max = Math.max(max, Math.abs(data[i]));
    }

    if (max > 0 && max < 0.9) {
      const factor = 0.9 / max;
      for (let i = 0; i < data.length; i++) {
        data[i] *= factor;
      }
    }

    return buffer;
  }

  private trimSilence(buffer: AudioBuffer, threshold = 0.01): AudioBuffer {
    const data = buffer.getChannelData(0);
    let start = 0;
    let end = data.length;

    // Find start
    for (let i = 0; i < data.length; i++) {
      if (Math.abs(data[i]) > threshold) {
        start = Math.max(0, i - 1000); // Keep small buffer
        break;
      }
    }

    // Find end
    for (let i = data.length - 1; i >= 0; i--) {
      if (Math.abs(data[i]) > threshold) {
        end = Math.min(data.length, i + 1000);
        break;
      }
    }

    const trimmedLength = end - start;
    const ctx = new OfflineAudioContext(1, trimmedLength, buffer.sampleRate);
    const newBuffer = ctx.createBuffer(1, trimmedLength, buffer.sampleRate);
    newBuffer.copyToChannel(data.slice(start, end), 0);
    return newBuffer;
  }
}
```

### Streaming Audio for Real-time Recognition
```typescript
class StreamingRecognizer {
  private chunks: ArrayBuffer[] = [];
  private processingPromise: Promise<void> | null = null;

  async streamAudioChunk(chunk: ArrayBuffer): Promise<PartialResult | null> {
    this.chunks.push(chunk);

    // Process in batches to reduce API calls
    if (this.chunks.length >= 5 || this.shouldProcess()) {
      return this.processAccumulated();
    }

    return null;
  }

  private async processAccumulated(): Promise<PartialResult> {
    const combinedSize = this.chunks.reduce((sum, c) => sum + c.byteLength, 0);
    const combined = new ArrayBuffer(combinedSize);
    const view = new Uint8Array(combined);

    let offset = 0;
    for (const chunk of this.chunks) {
      view.set(new Uint8Array(chunk), offset);
      offset += chunk.byteLength;
    }

    this.chunks = [];

    const result = await speakClient.speech.recognizeStream(combined);
    return result;
  }
}
```


## Caching Strategy

### Response Caching for Static Content
```typescript
import { LRUCache } from 'lru-cache';

// Cache tutor prompts and audio URLs
const promptCache = new LRUCache<string, TutorPrompt>({
  max: 500,
  ttl: 60 * 60 * 1000, // 1 hour
  updateAgeOnGet: true,
});

// Cache vocabulary lookups
const vocabularyCache = new LRUCache<string, VocabularyEntry>({
  max: 10000,
  ttl: 24 * 60 * 60 * 1000, // 24 hours
});

async function getCachedVocabulary(
  word: string,
  language: string
): Promise<VocabularyEntry> {
  const key = `${language}:${word}`;
  const cached = vocabularyCache.get(key);
  if (cached) return cached;

  const entry = await speakClient.vocabulary.lookup(word, language);
  vocabularyCache.set(key, entry);
  return entry;
}
```

### Redis Caching for Distributed Systems
```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function cachedWithRedis<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds = 3600
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) {
    return JSON.parse(cached);
  }

  const result = await fetcher();
  await redis.setex(key, ttlSeconds, JSON.stringify(result));
  return result;
}

// Cache user progress
async function getUserProgress(userId: string): Promise<UserProgress> {
  return cachedWithRedis(
    `speak:progress:${userId}`,
    () => speakClient.users.getProgress(userId),
    300 // 5 minutes
  );
}
```

### Audio Asset Caching
```typescript
// Pre-fetch and cache audio assets
class AudioAssetCache {
  private cache: Map<string, ArrayBuffer> = new Map();
  private preloadQueue: Set<string> = new Set();

  async preloadLessonAudio(lessonId: string): Promise<void> {
    const lesson = await speakClient.lessons.get(lessonId);

    // Pre-fetch all audio for the lesson
    const audioUrls = lesson.items.map(item => item.audioUrl);

    await Promise.all(
      audioUrls.map(async (url) => {
        if (!this.cache.has(url) && !this.preloadQueue.has(url)) {
          this.preloadQueue.add(url);
          const response = await fetch(url);
          const buffer = await response.arrayBuffer();
          this.cache.set(url, buffer);
          this.preloadQueue.delete(url);
        }
      })
    );
  }

  async getAudio(url: string): Promise<ArrayBuffer> {
    const cached = this.cache.get(url);
    if (cached) return cached;

    const response = await fetch(url);
    const buffer = await response.arrayBuffer();
    this.cache.set(url, buffer);
    return buffer;
  }
}
```


## Connection Optimization

```typescript
import { Agent } from 'https';

// Keep-alive connection pooling
const agent = new Agent({
  keepAlive: true,
  maxSockets: 10,
  maxFreeSockets: 5,
  timeout: 60000,
});

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  httpAgent: agent,
  timeout: 30000,
});
```


## Request Batching

```typescript
import DataLoader from 'dataloader';

// Batch vocabulary lookups
const vocabularyLoader = new DataLoader<string, VocabularyEntry>(
  async (words) => {
    // Batch API call
    const results = await speakClient.vocabulary.batchLookup(words);
    return words.map(word => results.find(r => r.word === word) || null);
  },
  {
    maxBatchSize: 50,
    batchScheduleFn: callback => setTimeout(callback, 50),
  }
);

// Usage - automatically batched
const [word1, word2, word3] = await Promise.all([
  vocabularyLoader.load('hola'),
  vocabularyLoader.load('buenos'),
  vocabularyLoader.load('días'),
]);
```


## Performance Monitoring

```typescript
interface SpeakMetrics {
  operation: string;
  duration: number;
  success: boolean;
  audioSize?: number;
}

async function measuredSpeakCall<T>(
  operation: string,
  fn: () => Promise<T>,
  metadata?: Record<string, any>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const duration = performance.now() - start;

    // Log metrics
    console.log({
      operation,
      duration,
      success: true,
      ...metadata,
    });

    // Track in metrics system
    metrics.histogram('speak_api_duration', duration, { operation });
    metrics.increment('speak_api_success', { operation });

    return result;
  } catch (error) {
    const duration = performance.now() - start;

    console.error({
      operation,
      duration,
      success: false,
      error,
      ...metadata,
    });

    metrics.histogram('speak_api_duration', duration, { operation });
    metrics.increment('speak_api_error', { operation });

    throw error;
  }
}

// Usage
const result = await measuredSpeakCall(
  'speech.recognize',
  () => speakClient.speech.recognize(audioBuffer),
  { audioSize: audioBuffer.byteLength }
);
```

