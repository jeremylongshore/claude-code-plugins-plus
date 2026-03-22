---
name: elevenlabs-core-workflow-a
description: |
  Implement ElevenLabs text-to-speech and voice cloning workflows.
  Use when building TTS features, cloning voices from audio samples,
  or implementing the primary ElevenLabs money-path: voice generation.
  Trigger: "elevenlabs TTS", "text to speech", "voice cloning elevenlabs",
  "clone a voice", "generate speech", "elevenlabs voice".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, tts, voice-cloning]
compatible-with: claude-code
---

# ElevenLabs Core Workflow A — TTS & Voice Cloning

## Overview

The primary ElevenLabs workflows: (1) Text-to-Speech with voice settings, (2) Instant Voice Cloning from audio samples, and (3) streaming TTS via WebSocket for real-time applications.

## Prerequisites

- Completed `elevenlabs-install-auth` setup
- Valid API key with sufficient character quota
- For voice cloning: audio recording(s) of the target voice (min 30 seconds, clean audio)

## Instructions

### Step 1: Advanced Text-to-Speech

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createWriteStream } from "fs";
import { Readable } from "stream";
import { pipeline } from "stream/promises";

const client = new ElevenLabsClient();

async function generateSpeech(
  text: string,
  voiceId: string,
  outputPath: string
) {
  const audio = await client.textToSpeech.convert(voiceId, {
    text,
    model_id: "eleven_multilingual_v2",
    voice_settings: {
      stability: 0.5,          // Lower = more expressive, higher = more consistent
      similarity_boost: 0.75,  // How closely to match the original voice
      style: 0.3,              // Amplify the speaker's style (adds latency if > 0)
      speed: 1.0,              // 0.7 to 1.2 range
    },
    // Optional: enforce language for multilingual model
    // language_code: "en",    // ISO 639-1
  });

  await pipeline(Readable.fromWeb(audio as any), createWriteStream(outputPath));
  console.log(`Generated: ${outputPath}`);
}

// Generate with different voice settings for comparison
await generateSpeech("Welcome to our platform.", "21m00Tcm4TlvDq8ikWAM", "stable.mp3");
```

### Step 2: Instant Voice Cloning (IVC)

Clone a voice from audio samples using `POST /v1/voices/add`:

```typescript
import { createReadStream } from "fs";

async function cloneVoice(
  name: string,
  description: string,
  audioFiles: string[]  // Paths to audio samples
) {
  const voice = await client.voices.add({
    name,
    description,
    files: audioFiles.map(f => createReadStream(f)),
    // Optional: label the voice for organization
    labels: JSON.stringify({ accent: "american", age: "young" }),
  });

  console.log(`Cloned voice created: ${voice.voice_id}`);
  console.log(`Name: ${name}`);

  // Use the cloned voice immediately
  const audio = await client.textToSpeech.convert(voice.voice_id, {
    text: "This is my cloned voice speaking!",
    model_id: "eleven_multilingual_v2",
    voice_settings: {
      stability: 0.5,
      similarity_boost: 0.85,  // Higher for cloned voices to stay close to original
    },
  });

  return { voiceId: voice.voice_id, audio };
}

// Clone from 1-25 audio samples (more = better quality)
await cloneVoice(
  "My Custom Voice",
  "Professional narrator voice",
  ["sample1.mp3", "sample2.mp3"]
);
```

### Step 3: WebSocket Streaming TTS

For real-time applications (chatbots, live narration), use the WebSocket endpoint:

```typescript
import WebSocket from "ws";

async function streamTTSWebSocket(
  voiceId: string,
  textChunks: string[]
) {
  const modelId = "eleven_flash_v2_5"; // Best for real-time streaming
  const wsUrl = `wss://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream-input?model_id=${modelId}`;

  const ws = new WebSocket(wsUrl);
  const audioChunks: Buffer[] = [];

  return new Promise<Buffer>((resolve, reject) => {
    ws.on("open", () => {
      // Send initial config (BOS - Beginning of Stream)
      ws.send(JSON.stringify({
        text: " ",  // Space signals BOS
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
        },
        xi_api_key: process.env.ELEVENLABS_API_KEY,
        // How many chars to buffer before generating audio
        chunk_length_schedule: [120, 160, 250, 290],
      }));

      // Stream text chunks
      for (const chunk of textChunks) {
        ws.send(JSON.stringify({ text: chunk }));
      }

      // Send EOS (End of Stream)
      ws.send(JSON.stringify({ text: "" }));
    });

    ws.on("message", (data: Buffer) => {
      const msg = JSON.parse(data.toString());
      if (msg.audio) {
        // Base64-encoded audio chunk
        audioChunks.push(Buffer.from(msg.audio, "base64"));
      }
      if (msg.isFinal) {
        ws.close();
      }
    });

    ws.on("close", () => resolve(Buffer.concat(audioChunks)));
    ws.on("error", reject);
  });
}

// Stream from an LLM response in chunks
const chunks = ["Hello, ", "this is ", "streamed ", "speech!"];
const audio = await streamTTSWebSocket("21m00Tcm4TlvDq8ikWAM", chunks);
```

### Step 4: Voice Management

```typescript
// List all available voices
async function listVoices() {
  const { voices } = await client.voices.getAll();
  for (const v of voices) {
    console.log(`${v.name} (${v.voice_id}) — ${v.category}`);
    // category: "premade" | "cloned" | "generated"
  }
}

// Get voice settings defaults
async function getVoiceSettings(voiceId: string) {
  const settings = await client.voices.getSettings(voiceId);
  console.log(`Stability: ${settings.stability}`);
  console.log(`Similarity: ${settings.similarity_boost}`);
}

// Update default voice settings
async function updateVoiceSettings(voiceId: string) {
  await client.voices.editSettings(voiceId, {
    stability: 0.6,
    similarity_boost: 0.8,
  });
}

// Delete a cloned voice
async function deleteVoice(voiceId: string) {
  await client.voices.delete(voiceId);
  console.log(`Voice ${voiceId} deleted.`);
}
```

## Voice Cloning Requirements

| Aspect | Requirement |
|--------|-------------|
| Audio length | Minimum 30 seconds total (1+ minute recommended) |
| Audio quality | Clean, no background noise, no music |
| Format | MP3, WAV, M4A, FLAC, OGG |
| Samples | 1-25 files per voice |
| Languages | Works across all supported languages |
| Plan | Available on all paid plans |

## Voice Settings Guide

| Setting | Range | Low Value Effect | High Value Effect |
|---------|-------|-----------------|-------------------|
| `stability` | 0-1 | More expressive, varied | Consistent, monotone |
| `similarity_boost` | 0-1 | More creative deviation | Strictly matches voice |
| `style` | 0-1 | Neutral delivery | Exaggerated emotion |
| `speed` | 0.7-1.2 | Slower speech | Faster speech |

**Recommended starting points:**
- Narration: stability=0.5, similarity=0.75, style=0.0
- Conversational: stability=0.4, similarity=0.6, style=0.3
- Cloned voice: stability=0.5, similarity=0.85, style=0.0

## Error Handling

| Error | HTTP | Cause | Solution |
|-------|------|-------|----------|
| `voice_not_found` | 404 | Invalid voice_id | List voices first: `GET /v1/voices` |
| `text_too_long` | 400 | Over 5,000 chars per request | Split text and use `previous_text`/`next_text` for prosody |
| `quota_exceeded` | 401 | Character limit reached | Check usage, upgrade plan |
| `too_many_concurrent_requests` | 429 | Exceeds plan concurrency | Queue requests; see concurrency limits |
| `invalid_voice_sample` | 400 | Bad audio file for cloning | Use clean audio, supported format, 30s+ |
| WebSocket `model_not_supported` | N/A | eleven_v3 not available for WS | Use `eleven_flash_v2_5` or `eleven_multilingual_v2` |

## Resources

- [TTS API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
- [Voice Cloning Guide](https://elevenlabs.io/docs/eleven-api/guides/cookbooks/voices/instant-voice-cloning)
- [WebSocket Streaming](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input)
- [Voice Settings](https://elevenlabs.io/docs/api-reference/voices/settings/get)

## Next Steps

For speech-to-speech, sound effects, and audio isolation, see `elevenlabs-core-workflow-b`.
