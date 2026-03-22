---
name: elevenlabs-hello-world
description: |
  Generate your first ElevenLabs text-to-speech audio file.
  Use when starting a new ElevenLabs integration, testing your setup,
  or learning basic TTS API patterns.
  Trigger: "elevenlabs hello world", "elevenlabs example",
  "elevenlabs quick start", "first elevenlabs TTS", "text to speech demo".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, tts, audio]
compatible-with: claude-code
---

# ElevenLabs Hello World

## Overview

Generate speech from text using the ElevenLabs TTS API. This skill covers the core `POST /v1/text-to-speech/{voice_id}` endpoint with real voice IDs, model selection, and audio output.

## Prerequisites

- Completed `elevenlabs-install-auth` setup
- Valid API key in `ELEVENLABS_API_KEY`

## Instructions

### Step 1: Text-to-Speech with the SDK

**TypeScript (recommended):**
```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createWriteStream } from "fs";
import { Readable } from "stream";
import { pipeline } from "stream/promises";

const client = new ElevenLabsClient();

async function generateSpeech() {
  // Use a pre-made voice — "Rachel" is a default voice available on all accounts
  // Find voice IDs via: GET /v1/voices
  const audio = await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
    text: "Hello! This is your first ElevenLabs text-to-speech generation.",
    model_id: "eleven_multilingual_v2",  // Best quality, 29 languages
    voice_settings: {
      stability: 0.5,           // 0-1: lower = more expressive
      similarity_boost: 0.75,   // 0-1: higher = closer to original voice
      style: 0.0,               // 0-1: higher = more dramatic (costs more latency)
      speed: 1.0,               // 0.7-1.2: speech speed multiplier
    },
  });

  // audio is a ReadableStream — pipe to file
  await pipeline(
    Readable.fromWeb(audio as any),
    createWriteStream("output.mp3")
  );

  console.log("Audio saved to output.mp3");
}

generateSpeech().catch(console.error);
```

**Python:**
```python
from elevenlabs.client import ElevenLabsClient

client = ElevenLabsClient()

audio = client.text_to_speech.convert(
    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
    text="Hello! This is your first ElevenLabs text-to-speech generation.",
    model_id="eleven_multilingual_v2",
    voice_settings={
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.0,
    },
)

with open("output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)

print("Audio saved to output.mp3")
```

### Step 2: Using cURL (Raw REST API)

```bash
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from the ElevenLabs API!",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
      "stability": 0.5,
      "similarity_boost": 0.75
    }
  }' \
  --output output.mp3
```

### Step 3: Streaming TTS (Low Latency)

For real-time playback, use the streaming endpoint:

```typescript
async function streamSpeech() {
  const audioStream = await client.textToSpeech.stream("21m00Tcm4TlvDq8ikWAM", {
    text: "This audio is streamed in real-time for low-latency playback.",
    model_id: "eleven_flash_v2_5",  // Optimized for streaming (~75ms latency)
    output_format: "mp3_22050_32",  // codec_sampleRate_bitrate
  });

  // Stream chunks arrive as they're generated
  const writer = createWriteStream("streamed.mp3");
  for await (const chunk of audioStream) {
    writer.write(chunk);
  }
  writer.end();
  console.log("Streamed audio saved to streamed.mp3");
}
```

## Available Models

| Model ID | Quality | Latency | Languages | Cost (credits/char) |
|----------|---------|---------|-----------|---------------------|
| `eleven_v3` | Highest expressiveness | Medium | 70+ | 1.0 |
| `eleven_multilingual_v2` | High quality, emotional | Medium | 29 | 1.0 |
| `eleven_flash_v2_5` | Good, ultra-fast | ~75ms | 32 | 0.5 |
| `eleven_turbo_v2_5` | Good, fast | Low | 32 | 0.5 |
| `eleven_monolingual_v1` | English only | Low | 1 | 0.5 |

## Common Default Voice IDs

| Voice | ID | Style |
|-------|----|-------|
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Calm, narration |
| Domi | `AZnzlk1XvdvUeBnXmlld` | Strong, assertive |
| Bella | `EXAVITQu4vr4xnSDxMaL` | Soft, warm |
| Antoni | `ErXwobaYiN019PkySvjV` | Well-rounded, male |
| Josh | `TxGEqnHWrfWFTfGW9XjX` | Deep, narrative |

## Output Formats

Specified as `codec_sampleRate_bitrate`:
- `mp3_44100_128` (default, high quality)
- `mp3_22050_32` (smaller file, streaming)
- `pcm_16000` (raw PCM for processing)
- `pcm_44100` (high-quality raw)
- `ulaw_8000` (telephony)

## Error Handling

| Error | HTTP | Cause | Solution |
|-------|------|-------|----------|
| `voice_not_found` | 404 | Invalid voice_id | Use `GET /v1/voices` to list valid IDs |
| `invalid_api_key` | 401 | Bad or missing key | Check `ELEVENLABS_API_KEY` env var |
| `model_not_found` | 400 | Wrong model_id string | Use exact IDs from models table |
| `text_too_long` | 400 | Exceeds 5,000 chars | Split into chunks; use streaming for long text |
| `quota_exceeded` | 401 | Monthly character limit hit | Check usage at elevenlabs.io/app/usage |

## Resources

- [TTS API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
- [Stream API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech/stream)
- [Models Overview](https://elevenlabs.io/docs/overview/models)
- [Voice Library](https://elevenlabs.io/voice-library)

## Next Steps

Proceed to `elevenlabs-local-dev-loop` for development workflow setup, or `elevenlabs-core-workflow-a` for voice cloning.
