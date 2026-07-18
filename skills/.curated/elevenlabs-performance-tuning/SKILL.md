---
name: elevenlabs-performance-tuning
description: |
  Optimize ElevenLabs TTS latency with model selection, streaming, caching, and
  audio format tuning. Use when experiencing slow TTS responses, implementing
  real-time voice features, or optimizing audio generation throughput.
  Trigger with "elevenlabs performance", "optimize elevenlabs", "elevenlabs
  latency", "elevenlabs slow", "fast TTS", "reduce elevenlabs latency", or
  "TTS streaming".
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- performance
- optimization
compatibility: Designed for Claude Code
---
# ElevenLabs Performance Tuning

## Overview

Optimize ElevenLabs TTS latency and throughput through model selection, streaming strategies, audio format tuning, and caching. Latency ranges from ~75ms (Flash) to ~500ms (v3) depending on configuration.

The two highest-leverage, lowest-effort levers — model choice (Step 1) and output format (Step 2) — are documented inline below. The four deeper integrations (HTTP streaming, WebSocket streaming, caching, parallel generation) are summarized here with copy-ready code in [the full implementation walkthrough](references/implementation.md).

## Prerequisites

- ElevenLabs SDK installed (`@elevenlabs/elevenlabs-js`)
- An ElevenLabs API key exported as `ELEVENLABS_API_KEY` (used by the SDK and passed as `xi_api_key` on the WebSocket handshake)
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

Call `client.textToSpeech.stream()` instead of `.convert()` and write each chunk to the response as it arrives, so playback starts before generation finishes — roughly halving time-to-first-byte. Set `style: 0.0` in `voice_settings` to shave another 10–20%. Full server handler: [implementation.md § Step 3](references/implementation.md).

### Step 4: WebSocket Streaming for Lowest Latency

For interactive apps where text arrives incrementally (e.g., an LLM token stream), open a `stream-input` WebSocket, `sendText()` chunks as they arrive, and tune `chunk_length_schedule` — fewer characters per chunk means lower latency but less prosody context. Full bidirectional client: [implementation.md § Step 4](references/implementation.md).

### Step 5: Audio Caching

Cache generated audio for repeated content (greetings, prompts, errors) in an LRU cache keyed by a SHA-256 of `voiceId:modelId:text`, so a changed voice or model never serves stale audio. This eliminates ~99% of latency for repeated phrases. Full `cachedTTS` helper: [implementation.md § Step 5](references/implementation.md).

### Step 6: Parallel Generation

Generate multiple segments concurrently with a `p-queue` whose `concurrency` matches your plan's request limit (going higher returns 429s, not more throughput). Full chapter-generator: [implementation.md § Step 6](references/implementation.md).

## Output

Applying these levers produces:

- A model + output-format choice matched to the use case (Steps 1–2).
- A streaming code path (HTTP or WebSocket) that logs measured time-to-first-byte, e.g. `Time to first byte: 78ms` / `WebSocket TTFB: 91ms`.
- An LRU audio cache emitting `[Cache HIT]` / `[Cache MISS]` telemetry for repeated content.
- A concurrency-bounded batch path that logs per-segment generation time.

Expected latency after tuning: ~75–150ms first byte on Flash/Turbo with streaming, versus ~300–500ms for a blocking `convert()` call on a higher-quality model.

## Performance Optimization Checklist

| Optimization | Latency Impact | Implementation |
|-------------|----------------|----------------|
| Flash model | -60% vs v2, -85% vs v3 | Change `model_id` |
| Streaming endpoint | -50% time-to-first-byte | Use `.stream()` instead of `.convert()` |
| WebSocket streaming | Best for LLM integration | See [Step 4](references/implementation.md) |
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
| HTTP 429 | Concurrency above plan limit | Lower `p-queue` `concurrency` |

## Examples

**Real-time IVR (lowest latency).** Pick `eleven_flash_v2_5` + `ulaw_8000` via `selectModel("realtime")`, then stream over HTTP:

```typescript
await streamToResponse(greeting, voiceId, res); // logs "Time to first byte: 78ms"
```

**LLM voice agent (incremental text).** Open a WebSocket and forward tokens as they stream from the model, ending with `finish()`:

```typescript
const stream = await createTTSStream({ voiceId, chunkLengthSchedule: [50, 100, 150] });
stream.sendText("Hello, "); stream.sendText("how are you?");
const audio = await stream.finish();
```

**Audiobook batch (throughput).** Cache repeated phrases and generate chapters concurrently:

```typescript
const buffers = await generateChapters(chapters, voiceId); // 5-wide, cache-backed
```

Full, runnable versions of every snippet above are in [the implementation walkthrough](references/implementation.md).

## Resources

- [ElevenLabs Streaming API](https://elevenlabs.io/docs/api-reference/text-to-speech/stream)
- [WebSocket API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input)
- [ElevenLabs Models](https://elevenlabs.io/docs/overview/models)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [Full implementation walkthrough](references/implementation.md) — copy-ready HTTP streaming, WebSocket, caching, and parallel-generation code

## Next Steps

For cost optimization once latency is tuned, see the `elevenlabs-cost-tuning` skill, which covers character-usage budgeting, model-tier cost tradeoffs, and cache-hit-rate targets.
