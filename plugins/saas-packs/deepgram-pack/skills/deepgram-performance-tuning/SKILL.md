---
name: deepgram-performance-tuning
description: |
  Optimize Deepgram API performance for faster transcription and lower latency.
  Use when improving transcription speed, reducing latency,
  or optimizing audio processing pipelines.
  Trigger: "deepgram performance", "speed up deepgram", "optimize transcription",
  "deepgram latency", "deepgram faster", "deepgram throughput".
allowed-tools: Read, Write, Edit, Bash(ffmpeg:*), Bash(ffprobe:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, api, performance, optimization]

---
# Deepgram Performance Tuning

## Overview
Optimize Deepgram transcription performance through audio preprocessing with ffmpeg, model selection for speed vs accuracy, streaming for large files, parallel processing, result caching, and connection reuse. Targets: <2s latency for short files, 100+ files/minute batch throughput.

## Performance Levers

| Factor | Impact | Default | Optimized |
|--------|--------|---------|-----------|
| Audio format | High | Any format | 16kHz mono WAV |
| Model | High | nova-3 | base (speed) or nova-3 (accuracy) |
| File size | High | Full file sync | Stream >60s, callback >5min |
| Concurrency | Medium | Sequential | 50 parallel (p-limit) |
| Caching | Medium | None | Redis hash by audio+options |
| Features | Medium | All enabled | Disable unused (diarize, utterances) |

## Instructions

### Step 1: Audio Preprocessing with ffmpeg

```bash
# Optimal format for Deepgram: 16kHz, 16-bit, mono, WAV
ffmpeg -i input.mp3 \
  -ar 16000 \          # 16kHz sample rate (ideal for speech)
  -ac 1 \              # Mono channel
  -acodec pcm_s16le \  # 16-bit signed LE PCM
  -f wav \
  output.wav

# Remove silence (saves API cost + processing time)
ffmpeg -i input.wav \
  -af "silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-30dB" \
  -ar 16000 -ac 1 -acodec pcm_s16le \
  trimmed.wav

# Noise reduction + normalization
ffmpeg -i input.wav \
  -af "highpass=f=200,lowpass=f=3000,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 16000 -ac 1 -acodec pcm_s16le \
  clean.wav
```

```typescript
import { execSync } from 'child_process';
import { statSync } from 'fs';

function preprocessAudio(inputPath: string, outputPath: string): {
  originalSize: number;
  optimizedSize: number;
  savings: string;
} {
  const originalSize = statSync(inputPath).size;

  execSync(`ffmpeg -y -i "${inputPath}" \
    -af "silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-30dB,\
    highpass=f=200,lowpass=f=3000" \
    -ar 16000 -ac 1 -acodec pcm_s16le \
    "${outputPath}" 2>/dev/null`);

  const optimizedSize = statSync(outputPath).size;
  const savings = ((1 - optimizedSize / originalSize) * 100).toFixed(1);

  console.log(`Preprocessed: ${inputPath}`);
  console.log(`  Original: ${(originalSize / 1024).toFixed(0)}KB`);
  console.log(`  Optimized: ${(optimizedSize / 1024).toFixed(0)}KB (${savings}% smaller)`);

  return { originalSize, optimizedSize, savings };
}
```

### Step 2: Model Selection Strategy

```typescript
import { createClient } from '@deepgram/sdk';

type Priority = 'accuracy' | 'speed' | 'cost';

function selectModel(priority: Priority, audioDuration: number): string {
  // Nova-3: Best accuracy, fast, $0.0043/min (STT)
  // Nova-2: Proven stable, fast, $0.0043/min
  // Base:   Fastest, lower accuracy, $0.0048/min
  // Whisper: Multilingual (100+ langs), slower, $0.0048/min

  switch (priority) {
    case 'accuracy':
      return 'nova-3';
    case 'speed':
      return audioDuration > 300 ? 'base' : 'nova-2';  // Base for long files
    case 'cost':
      return 'nova-2';  // Same price as Nova-3, slightly faster
    default:
      return 'nova-3';
  }
}

// Feature cost: disable what you don't need
function optimizedOptions(priority: Priority) {
  return {
    model: selectModel(priority, 0),
    smart_format: true,      // Free — always enable
    punctuate: true,         // Free — always enable
    // These add processing time:
    diarize: priority === 'accuracy',   // Adds latency
    utterances: priority === 'accuracy',
    paragraphs: priority === 'accuracy',
    summarize: false,        // Only when needed
    detect_topics: false,    // Only when needed
    sentiment: false,        // Only when needed
  };
}
```

### Step 3: Streaming for Large Files

```typescript
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk';
import { createReadStream } from 'fs';

async function streamLargeFile(filePath: string): Promise<string> {
  const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);
  const transcripts: string[] = [];

  return new Promise((resolve, reject) => {
    const connection = deepgram.listen.live({
      model: 'nova-3',
      smart_format: true,
      encoding: 'linear16',
      sample_rate: 16000,
      channels: 1,
    });

    connection.on(LiveTranscriptionEvents.Open, () => {
      // Stream file in 32KB chunks
      const stream = createReadStream(filePath, { highWaterMark: 32 * 1024 });

      stream.on('data', (chunk: Buffer) => {
        connection.send(chunk);
      });

      stream.on('end', () => {
        // Signal end of audio
        connection.finish();
      });

      stream.on('error', reject);
    });

    connection.on(LiveTranscriptionEvents.Transcript, (data) => {
      if (data.is_final) {
        const text = data.channel.alternatives[0]?.transcript;
        if (text) transcripts.push(text);
      }
    });

    connection.on(LiveTranscriptionEvents.Close, () => {
      resolve(transcripts.join(' '));
    });

    connection.on(LiveTranscriptionEvents.Error, reject);
  });
}
```

### Step 4: Parallel Batch Processing

```typescript
import pLimit from 'p-limit';
import { createClient } from '@deepgram/sdk';

async function batchTranscribe(
  files: string[],
  concurrency = 50,   // Stay under your plan's concurrency limit
  model = 'nova-3'
) {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);
  const limit = pLimit(concurrency);
  const startTime = Date.now();

  const results = await Promise.allSettled(
    files.map((file, i) =>
      limit(async () => {
        const fileStart = Date.now();
        const { result, error } = await client.listen.prerecorded.transcribeFile(
          require('fs').readFileSync(file),
          { model, smart_format: true, mimetype: 'audio/wav' }
        );
        if (error) throw error;

        const elapsed = Date.now() - fileStart;
        console.log(`[${i + 1}/${files.length}] ${file} — ${elapsed}ms (${result.metadata.duration}s audio)`);
        return { file, result, elapsed };
      })
    )
  );

  const totalTime = Date.now() - startTime;
  const succeeded = results.filter(r => r.status === 'fulfilled').length;
  console.log(`\nBatch: ${succeeded}/${files.length} in ${totalTime}ms`);
  console.log(`Throughput: ${(files.length / (totalTime / 60000)).toFixed(1)} files/min`);

  return results;
}
```

### Step 5: Result Caching

```typescript
import { createHash } from 'crypto';
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL ?? 'redis://localhost:6379');

function cacheKey(audioUrl: string, options: Record<string, any>): string {
  const hash = createHash('sha256')
    .update(audioUrl + JSON.stringify(options))
    .digest('hex');
  return `dg:cache:${hash}`;
}

async function cachedTranscribe(
  client: ReturnType<typeof createClient>,
  url: string,
  options: Record<string, any>,
  ttlSeconds = 3600  // 1 hour default
) {
  const key = cacheKey(url, options);

  // Check cache
  const cached = await redis.get(key);
  if (cached) {
    console.log('Cache hit:', url.substring(0, 60));
    return JSON.parse(cached);
  }

  // Transcribe and cache
  const { result, error } = await client.listen.prerecorded.transcribeUrl(
    { url }, options
  );
  if (error) throw error;

  await redis.setex(key, ttlSeconds, JSON.stringify(result));
  console.log('Cached result:', url.substring(0, 60));
  return result;
}
```

### Step 6: Performance Benchmarking

```typescript
async function benchmark(audioUrl: string) {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);
  const models = ['nova-3', 'nova-2', 'base'] as const;

  console.log('Performance Benchmark');
  console.log('='.repeat(60));

  for (const model of models) {
    const times: number[] = [];
    for (let i = 0; i < 3; i++) {
      const start = Date.now();
      const { result, error } = await client.listen.prerecorded.transcribeUrl(
        { url: audioUrl }, { model, smart_format: true }
      );
      times.push(Date.now() - start);
      if (error) { console.error(`${model} error:`, error.message); break; }
    }
    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    console.log(`${model}: avg ${avg.toFixed(0)}ms (${times.map(t => `${t}ms`).join(', ')})`);
  }
}
```

## Output
- Audio preprocessing pipeline (16kHz mono, silence removal, noise reduction)
- Model selection strategy by priority (accuracy/speed/cost)
- Streaming transcription for large files (>60s)
- Parallel batch processing with configurable concurrency
- Redis-backed result caching with TTL
- Performance benchmarking script

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow transcription | Unoptimized audio format | Preprocess to 16kHz mono WAV |
| 429 in batch | Concurrency too high | Reduce `p-limit` to 50% of plan limit |
| ffmpeg not found | Not installed | `apt install ffmpeg` / `brew install ffmpeg` |
| Cache stale | Audio changed at same URL | Include hash of audio content in cache key |

## Resources
- [Audio Best Practices](https://developers.deepgram.com/docs/audio-best-practices)
- [Model Options](https://developers.deepgram.com/docs/model)
- [Concurrency Limits](https://developers.deepgram.com/docs/working-with-concurrency-rate-limits)
