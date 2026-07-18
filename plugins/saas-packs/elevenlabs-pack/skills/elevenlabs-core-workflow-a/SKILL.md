---
name: elevenlabs-core-workflow-a
description: |
  Implement ElevenLabs text-to-speech and voice cloning workflows.
  Use when building TTS features, cloning voices from audio samples, streaming
  speech to a chatbot, or implementing the primary ElevenLabs money-path: voice
  generation.
  Trigger with "elevenlabs TTS", "text to speech", "voice cloning elevenlabs",
  "clone a voice", "generate speech", "elevenlabs voice".
allowed-tools: Read, Write, Bash(npm:*), Bash(curl:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- tts
- voice-cloning
compatibility: Designed for Claude Code
---
# ElevenLabs Core Workflow A — TTS & Voice Cloning

## Overview

The primary ElevenLabs workflows: (1) Text-to-Speech with voice settings, (2) Instant Voice Cloning from audio samples, (3) streaming TTS via WebSocket for real-time applications, and (4) voice-library management. This SKILL.md walks the full flow at a high level and carries the first TTS example inline; the deep code for cloning, streaming, and management lives in [the full implementation walkthrough](references/implementation.md).

## Prerequisites

- Completed `elevenlabs-install-auth` setup
- Valid API key with sufficient character quota
- For voice cloning: audio recording(s) of the target voice (min 30 seconds, clean audio)

## Instructions

### Step 1: Advanced Text-to-Speech

Instantiate the client, call `textToSpeech.convert(voiceId, opts)`, and pipe the returned stream to a file. The `voice_settings` block is where you tune delivery:

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

await generateSpeech("Welcome to our platform.", "21m00Tcm4TlvDq8ikWAM", "stable.mp3");
```

### Step 2: Instant Voice Cloning (IVC)

Clone a voice from 1-25 audio samples with `client.voices.add({ name, description, files })`, which returns a `voice_id` you can use immediately in `textToSpeech.convert`. Use `similarity_boost: 0.85` on cloned voices to stay close to the original. Full `cloneVoice` implementation: [implementation.md](references/implementation.md), Step 2.

### Step 3: WebSocket Streaming TTS

For real-time apps (chatbots, live narration), open `wss://api.elevenlabs.io/v1/text-to-speech/{voiceId}/stream-input` with the low-latency `eleven_flash_v2_5` model. Send a space as Beginning-of-Stream, stream text chunks, then an empty string as End-of-Stream; collect base64 audio frames until `isFinal`. Full `streamTTSWebSocket` implementation: [implementation.md](references/implementation.md), Step 3.

### Step 4: Voice Management

List, inspect, update, and delete voices with `client.voices.getAll()`, `getSettings`, `editSettings`, and `delete`. Full helpers: [implementation.md](references/implementation.md), Step 4.

## Tuning Reference

Two lookup tables — the voice-cloning input requirements and the full
`voice_settings` range/effect guide with per-use-case starting points — live in
[implementation.md](references/implementation.md). Quick defaults:

- Narration: `stability=0.5, similarity_boost=0.75, style=0.0`
- Conversational: `stability=0.4, similarity_boost=0.6, style=0.3`
- Cloned voice: `stability=0.5, similarity_boost=0.85, style=0.0`

## Output

- **Text-to-Speech (Step 1):** an audio stream written to `outputPath` (e.g. `stable.mp3`); console logs `Generated:` plus the output path.
- **Voice cloning (Step 2):** a new `voice_id` (logged as `Cloned voice created:` plus the id) plus an immediately-usable audio stream in the cloned timbre.
- **WebSocket streaming (Step 3):** a concatenated `Buffer` of base64-decoded audio chunks assembled as frames arrive.
- **Voice management (Step 4):** printed voice listings (name, voice_id, category), current/updated settings, or a delete confirmation.

## Error Handling

| Error | HTTP | Cause | Solution |
|-------|------|-------|----------|
| `voice_not_found` | 404 | Invalid voice_id | List voices first: `GET /v1/voices` |
| `text_too_long` | 400 | Over 5,000 chars per request | Split text and use `previous_text`/`next_text` for prosody |
| `quota_exceeded` | 401 | Character limit reached | Check usage, upgrade plan |
| `too_many_concurrent_requests` | 429 | Exceeds plan concurrency | Queue requests; see concurrency limits |
| `invalid_voice_sample` | 400 | Bad audio file for cloning | Use clean audio, supported format, 30s+ |
| WebSocket `model_not_supported` | N/A | eleven_v3 not available for WS | Use `eleven_flash_v2_5` or `eleven_multilingual_v2` |

## Examples

Four complete input-to-audio scenarios are in [references/examples.md](references/examples.md):

1. **Generate narration from a script** — batch a marketing script to one MP3 with a premade voice.
2. **Clone a narrator voice and speak with it** — clone from two samples, then synthesize with the returned `voice_id`.
3. **Stream an LLM response as speech** — pipe chatbot chunks through the WebSocket for real-time playback.
4. **Audit and prune your voice library** — list every voice by category, then delete a stale clone.

## Resources

- [TTS API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
- [Voice Cloning Guide](https://elevenlabs.io/docs/eleven-api/guides/cookbooks/voices/instant-voice-cloning)
- [WebSocket Streaming](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input)
- [Voice Settings](https://elevenlabs.io/docs/api-reference/voices/settings/get)

## Next Steps

For speech-to-speech, sound effects, and audio isolation, see the companion skill `elevenlabs-core-workflow-b`, which covers the remaining ElevenLabs audio-transformation endpoints.
