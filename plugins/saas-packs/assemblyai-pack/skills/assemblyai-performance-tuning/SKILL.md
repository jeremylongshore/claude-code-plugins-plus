---
name: assemblyai-performance-tuning
description: |
  Optimize AssemblyAI API performance with caching, parallel processing, and model selection.
  Use when experiencing slow transcriptions, implementing caching strategies,
  or optimizing throughput for batch transcription workloads.
  Trigger with phrases like "assemblyai performance", "optimize assemblyai",
  "assemblyai latency", "assemblyai caching", "assemblyai slow", "assemblyai batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription, performance]
compatible-with: claude-code
---

# AssemblyAI Performance Tuning

## Overview
Optimize AssemblyAI transcription performance through model selection, parallel processing, caching, and webhook-based architectures.

## Prerequisites
- `assemblyai` package installed
- Understanding of async patterns
- Redis or in-memory cache available (optional)

## Latency Benchmarks (Actual)

### Async Transcription
| Audio Duration | Approx. Processing Time | Notes |
|----------------|------------------------|-------|
| 30 seconds | ~10-15 seconds | Includes queue time |
| 5 minutes | ~30-60 seconds | Scales sub-linearly |
| 1 hour | ~3-5 minutes | Depends on queue load |
| 10 hours | ~15-30 minutes | Max async duration |

### Streaming
| Metric | Value |
|--------|-------|
| First partial transcript | ~300ms (P50) |
| Final transcript latency | ~500ms (P50) |
| End-of-turn detection | Automatic with endpointing |

### Model Speed vs. Accuracy
| Model | Speed | Accuracy | Price/hr |
|-------|-------|----------|----------|
| `nano` | Fastest | Good | $0.12 |
| `best` (Universal-3) | Standard | Highest | $0.37 |
| `nova-3` (streaming) | Real-time | High | $0.47 |
| `nova-3-pro` (streaming) | Real-time | Highest | $0.47 |

## Instructions

### Step 1: Choose the Right Model

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

// For highest accuracy (default)
const accurate = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'best',
});

// For fastest processing and lowest cost
const fast = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'nano',
});
```

### Step 2: Parallel Batch Processing

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 10 });

async function batchTranscribe(audioUrls: string[]) {
  const results = await Promise.all(
    audioUrls.map(url =>
      queue.add(() =>
        client.transcripts.transcribe({ audio: url, speech_model: 'nano' })
      )
    )
  );

  return results.filter(t => t.status === 'completed');
}

// Process 100 files with 10 concurrent jobs
const urls = Array.from({ length: 100 }, (_, i) => `https://storage.example.com/audio-${i}.mp3`);
const transcripts = await batchTranscribe(urls);
console.log(`Completed: ${transcripts.length}/${urls.length}`);
```

### Step 3: Use Webhooks Instead of Polling

```typescript
// SLOW: transcribe() polls every 3 seconds until done
const slow = await client.transcripts.transcribe({ audio: audioUrl });

// FAST: submit() returns immediately, webhook notifies on completion
const fast = await client.transcripts.submit({
  audio: audioUrl,
  webhook_url: 'https://your-app.com/webhooks/assemblyai',
});
// Your webhook handler processes the result — no polling overhead
```

### Step 4: Cache Transcript Results

```typescript
import { LRUCache } from 'lru-cache';
import type { Transcript } from 'assemblyai';

const transcriptCache = new LRUCache<string, Transcript>({
  max: 500,
  ttl: 60 * 60 * 1000, // 1 hour
});

async function getCachedTranscript(transcriptId: string): Promise<Transcript> {
  const cached = transcriptCache.get(transcriptId);
  if (cached) return cached;

  const transcript = await client.transcripts.get(transcriptId);
  if (transcript.status === 'completed') {
    transcriptCache.set(transcriptId, transcript);
  }
  return transcript;
}
```

### Step 5: Redis Cache for Distributed Systems

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!);

async function getCachedTranscriptRedis(transcriptId: string): Promise<Transcript> {
  const cached = await redis.get(`transcript:${transcriptId}`);
  if (cached) return JSON.parse(cached);

  const transcript = await client.transcripts.get(transcriptId);
  if (transcript.status === 'completed') {
    await redis.setex(
      `transcript:${transcriptId}`,
      3600, // 1 hour TTL
      JSON.stringify(transcript)
    );
  }
  return transcript;
}
```

### Step 6: Minimize Feature Overhead

```typescript
// Only enable features you actually need — each adds processing time

// Minimal (fastest)
const minimal = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'nano',
  punctuate: true,
  format_text: true,
});

// Full intelligence (slower, more expensive)
const full = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'best',
  speaker_labels: true,
  sentiment_analysis: true,
  entity_detection: true,
  auto_highlights: true,
  content_safety: true,
  iab_categories: true,
  summarization: true,
  summary_type: 'bullets',
});
```

### Step 7: Performance Monitoring

```typescript
async function timedTranscribe(audioUrl: string, options: Record<string, any> = {}) {
  const start = Date.now();
  const transcript = await client.transcripts.transcribe({
    audio: audioUrl,
    ...options,
  });
  const durationMs = Date.now() - start;

  const stats = {
    transcriptId: transcript.id,
    status: transcript.status,
    audioDuration: transcript.audio_duration,
    processingTimeMs: durationMs,
    ratio: transcript.audio_duration
      ? (durationMs / 1000 / transcript.audio_duration).toFixed(2)
      : 'N/A',
    wordCount: transcript.words?.length ?? 0,
    model: options.speech_model ?? 'best',
  };

  console.log('Transcription stats:', stats);
  return { transcript, stats };
}
```

## Output
- Optimal model selection based on speed/accuracy/cost trade-offs
- Parallel batch processing with concurrency control
- Webhook-based architecture (eliminates polling overhead)
- In-memory and Redis caching for transcript retrieval
- Performance monitoring with processing time ratios

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow transcription | Large file + best model | Use `nano` model or split audio |
| Queue backlog | Too many concurrent submissions | Limit concurrency with p-queue |
| Cache stale data | Transcript re-processed | Set appropriate TTL, invalidate on webhook |
| Polling overhead | Using `transcribe()` for many files | Switch to `submit()` + webhooks |

## Resources
- [AssemblyAI Speech Models](https://www.assemblyai.com/docs/speech-to-text/speech-recognition)
- [AssemblyAI Processing FAQ](https://www.assemblyai.com/docs/concepts/faq)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For cost optimization, see `assemblyai-cost-tuning`.
