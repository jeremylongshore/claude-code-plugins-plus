---
name: elevenlabs-performance-tuning
description: |
  Optimize ElevenLabs TTS latency with model selection, streaming, caching, and audio format tuning.
  Use when experiencing slow TTS responses, implementing real-time voice features,
  or optimizing audio generation throughput.
  Trigger: "elevenlabs performance", "optimize elevenlabs", "elevenlabs latency",
  "elevenlabs slow", "fast TTS", "reduce elevenlabs latency", "TTS streaming".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, performance, optimization]
compatible-with: claude-code
---

# ElevenLabs Performance Tuning

## Overview

Optimize ElevenLabs TTS latency and throughput through model selection, streaming strategies, audio format tuning, and caching. Latency ranges from ~75ms (Flash) to ~500ms (v3) depending on configuration.

## Prerequisites

- ElevenLabs SDK installed
- Understanding of your latency requirements
- Audio playback infrastructure (browser, mobile, server-side)

## Instructions

### Step 1: Model Selection for Latency

The single biggest performance lever is model choice:

| Model | Avg Latency | Quality | Languages | Use Case |
|-------|-------------|---------|-----------|----------|
| `eleven_flash_v2_5` | ~75ms | Good | 32 | Real-time chat, IVR, gaming |
| `eleven_turbo_v2_5` | ~150ms | Good | 32 | Balanced speed/quality |
| `eleven_multilingual_v2` | ~300ms | High | 29 | Narration, content creation |
| `eleven_v3` | ~500ms | Highest | 70+ | Maximum expressiveness |

```typescript
// Select model based on use case
function selectModel(useCase: "realtime" | "balanced" | "quality" | "max_quality"): string {
  const models = {
    realtime:    "eleven_flash_v2_5",
    balanced:    "eleven_turbo_v2_5",
    quality:     "eleven_multilingual_v2",
    max_quality: "eleven_v3",
  };
  return models[useCase];
}
```

### Step 2: Output Format Optimization

Smaller formats = faster transfer:

| Format | Size/Second | Quality | Best For |
|--------|-------------|---------|----------|
| `mp3_44100_128` | ~16 KB/s | High | Downloads, archival |
| `mp3_22050_32` | ~4 KB/s | Medium | Streaming, mobile |
| `pcm_16000` | ~32 KB/s | Raw | Server-side processing |
| `pcm_44100` | ~88 KB/s | Raw | High-quality processing |
| `ulaw_8000` | ~8 KB/s | Phone | Telephony/IVR |

```typescript
// Use smaller format for streaming, higher quality for downloads
const streamingConfig = {
  output_format: "mp3_22050_32",  // 4 KB/s — fast streaming
  model_id: "eleven_flash_v2_5",   // ~75ms first byte
};

const downloadConfig = {
  output_format: "mp3_44100_128", // 16 KB/s — high quality
  model_id: "eleven_multilingual_v2",
};
```

### Step 3: HTTP Streaming for Time-to-First-Byte

Use the streaming endpoint to start playback before full generation completes:

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const client = new ElevenLabsClient();

async function streamToResponse(
  text: string,
  voiceId: string,
  res: Response | import("express").Response
) {
  const startTime = performance.now();

  const stream = await client.textToSpeech.stream(voiceId, {
    text,
    model_id: "eleven_flash_v2_5",
    output_format: "mp3_22050_32",
    voice_settings: {
      stability: 0.5,
      similarity_boost: 0.75,
      style: 0.0,        // style=0 reduces latency
    },
  });

  let firstChunk = true;
  for await (const chunk of stream) {
    if (firstChunk) {
      const ttfb = performance.now() - startTime;
      console.log(`Time to first byte: ${ttfb.toFixed(0)}ms`);
      firstChunk = false;
    }
    // Write chunk to response or audio player
    (res as any).write(chunk);
  }
  (res as any).end();
}
```

### Step 4: WebSocket Streaming for Lowest Latency

For interactive applications where text arrives in chunks (e.g., from an LLM):

```typescript
import WebSocket from "ws";

interface WSStreamConfig {
  voiceId: string;
  modelId?: string;
  chunkLengthSchedule?: number[];
}

async function createTTSStream(config: WSStreamConfig) {
  const model = config.modelId || "eleven_flash_v2_5";
  const url = `wss://api.elevenlabs.io/v1/text-to-speech/${config.voiceId}/stream-input?model_id=${model}`;

  const ws = new WebSocket(url);
  const audioChunks: Buffer[] = [];
  let totalLatency = 0;
  let firstAudioTime = 0;

  await new Promise<void>((resolve, reject) => {
    ws.on("open", resolve);
    ws.on("error", reject);
  });

  // Initialize stream
  ws.send(JSON.stringify({
    text: " ",
    xi_api_key: process.env.ELEVENLABS_API_KEY,
    voice_settings: { stability: 0.5, similarity_boost: 0.75 },
    // Control buffering: fewer chars = lower latency, more = better prosody
    chunk_length_schedule: config.chunkLengthSchedule || [50, 120, 200],
  }));

  return {
    // Send text chunks as they arrive (e.g., from LLM stream)
    sendText(text: string) {
      ws.send(JSON.stringify({ text }));
    },

    // Signal end of input
    finish(): Promise<Buffer> {
      return new Promise((resolve) => {
        const sendTime = Date.now();

        ws.on("message", (data: Buffer) => {
          const msg = JSON.parse(data.toString());
          if (msg.audio) {
            if (!firstAudioTime) {
              firstAudioTime = Date.now();
              totalLatency = firstAudioTime - sendTime;
            }
            audioChunks.push(Buffer.from(msg.audio, "base64"));
          }
          if (msg.isFinal) {
            console.log(`WebSocket TTFB: ${totalLatency}ms`);
            ws.close();
            resolve(Buffer.concat(audioChunks));
          }
        });

        ws.send(JSON.stringify({ text: "" })); // EOS signal
      });
    },
  };
}

// Usage with LLM streaming
const stream = await createTTSStream({
  voiceId: "21m00Tcm4TlvDq8ikWAM",
  chunkLengthSchedule: [50, 100, 150],  // Aggressive buffering for speed
});

// As LLM tokens arrive:
stream.sendText("Hello, ");
stream.sendText("how are ");
stream.sendText("you today?");

const audio = await stream.finish();
```

### Step 5: Audio Caching

Cache generated audio for repeated content (greetings, prompts, errors):

```typescript
import { LRUCache } from "lru-cache";
import crypto from "crypto";

const audioCache = new LRUCache<string, Buffer>({
  max: 500,                    // Max cached audio files
  maxSize: 100 * 1024 * 1024,  // 100MB total
  sizeCalculation: (value) => value.length,
  ttl: 24 * 60 * 60 * 1000,    // 24 hours
});

function cacheKey(text: string, voiceId: string, modelId: string): string {
  return crypto.createHash("sha256")
    .update(`${voiceId}:${modelId}:${text}`)
    .digest("hex");
}

async function cachedTTS(
  text: string,
  voiceId: string,
  modelId = "eleven_multilingual_v2"
): Promise<Buffer> {
  const key = cacheKey(text, voiceId, modelId);

  const cached = audioCache.get(key);
  if (cached) {
    console.log("[Cache HIT]", key.substring(0, 8));
    return cached;
  }

  const stream = await client.textToSpeech.convert(voiceId, {
    text,
    model_id: modelId,
  });

  const chunks: Buffer[] = [];
  for await (const chunk of stream as any) {
    chunks.push(Buffer.from(chunk));
  }
  const audio = Buffer.concat(chunks);

  audioCache.set(key, audio);
  console.log("[Cache MISS]", key.substring(0, 8), `${audio.length} bytes`);
  return audio;
}
```

### Step 6: Parallel Generation

Generate multiple audio segments concurrently:

```typescript
import PQueue from "p-queue";

const queue = new PQueue({ concurrency: 5 }); // Match plan limit

async function generateChapters(
  chapters: { title: string; text: string }[],
  voiceId: string
): Promise<Buffer[]> {
  const results = await Promise.all(
    chapters.map(chapter =>
      queue.add(async () => {
        const start = performance.now();
        const audio = await cachedTTS(chapter.text, voiceId);
        const duration = performance.now() - start;
        console.log(`${chapter.title}: ${duration.toFixed(0)}ms`);
        return audio;
      })
    )
  );

  return results as Buffer[];
}
```

## Performance Optimization Checklist

| Optimization | Latency Impact | Implementation |
|-------------|----------------|----------------|
| Flash model | -60% vs v2, -85% vs v3 | Change `model_id` |
| Streaming endpoint | -50% time-to-first-byte | Use `.stream()` instead of `.convert()` |
| WebSocket streaming | Best for LLM integration | See Step 4 |
| Smaller output format | -30% transfer time | `mp3_22050_32` vs `mp3_44100_128` |
| Audio caching | -99% for repeated content | LRU cache with SHA-256 keys |
| `style: 0` | -10-20% latency | Remove style exaggeration |
| Concurrency queue | Maximize throughput | p-queue matching plan limit |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High TTFB | Wrong model | Switch to `eleven_flash_v2_5` |
| Choppy streaming | Network buffering | Use `pcm_16000` for direct playback |
| Cache miss storm | TTL expired for popular content | Use stale-while-revalidate pattern |
| WebSocket drops | Network instability | Reconnect with buffered text |
| Memory pressure | Audio cache too large | Set `maxSize` limit on LRU cache |

## Resources

- [ElevenLabs Streaming API](https://elevenlabs.io/docs/api-reference/text-to-speech/stream)
- [WebSocket API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input)
- [ElevenLabs Models](https://elevenlabs.io/docs/overview/models)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)

## Next Steps

For cost optimization, see `elevenlabs-cost-tuning`.
