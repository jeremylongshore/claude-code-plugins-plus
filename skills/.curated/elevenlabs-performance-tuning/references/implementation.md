# ElevenLabs Performance Tuning — Full Implementation Walkthrough

This reference holds the complete, copy-ready implementations for the four
deeper latency levers summarized in `SKILL.md`: HTTP streaming, WebSocket
streaming, audio caching, and parallel generation. Steps 1–2 (model selection
and output-format tuning) live inline in `SKILL.md` because they are the
highest-leverage, lowest-effort changes; Steps 3–6 below are the heavier
integrations you drill into once the basics are in place.

## Step 3: HTTP Streaming for Time-to-First-Byte

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

## Step 4: WebSocket Streaming for Lowest Latency

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

The `chunk_length_schedule` is the key latency knob: fewer characters per chunk
means the first audio arrives sooner, but very small chunks can degrade prosody
because the model has less context to plan intonation. `[50, 100, 150]` is an
aggressive, speed-first schedule; `[50, 120, 200]` trades a little latency for
smoother speech.

## Step 5: Audio Caching

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

The SHA-256 cache key covers `voiceId`, `modelId`, and `text`, so changing any
of the three produces a distinct cache entry — you never serve stale audio for
a changed voice or model.

## Step 6: Parallel Generation

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

Set `concurrency` to match your plan's concurrent-request limit — going higher
returns HTTP 429s, not more throughput. The `cachedTTS` call keeps each already-
generated segment out of the API entirely on re-runs.
