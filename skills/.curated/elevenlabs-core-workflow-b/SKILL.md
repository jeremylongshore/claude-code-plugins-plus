---
name: elevenlabs-core-workflow-b
description: |
  Implement ElevenLabs speech-to-speech, sound effects, audio isolation, and
  speech-to-text.

  Use when converting one voice to another, generating sound effects from a text
  description, removing background noise from a recording, or transcribing audio.

  Trigger with "elevenlabs speech to speech", "voice changer", "sound effects",
  "audio isolation", "remove background noise", "elevenlabs transcribe".
allowed-tools: Read, Write, Bash(npm:*), Bash(curl:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- speech-to-speech
- sound-effects
- audio-isolation
compatibility: Designed for Claude Code
---
# ElevenLabs Core Workflow B — Speech-to-Speech, Sound Effects & Audio Isolation

## Overview

Secondary ElevenLabs workflows beyond TTS: (1) Speech-to-Speech voice conversion,
(2) Sound Effects generation from text descriptions, (3) Audio Isolation for noise
removal, and (4) Speech-to-Text transcription. Each maps to one API endpoint and
has both a TypeScript SDK and a cURL path.

Full code for every step lives in [references/implementation.md](references/implementation.md);
copy-ready invocations are in [references/examples.md](references/examples.md).

## Prerequisites

- Completed `elevenlabs-install-auth` setup.
- For STS: source audio file in MP3/WAV/M4A format.
- For audio isolation: noisy audio file to clean.

## Authentication

The SDK client (`new ElevenLabsClient()`) reads the API key from the
`ELEVENLABS_API_KEY` environment variable automatically — never hardcode it. cURL
requests send it as the `xi-api-key: ${ELEVENLABS_API_KEY}` header. Full auth setup
is covered by the `elevenlabs-install-auth` skill.

## Instructions

Import the SDK once, then call the relevant module. The client authenticates from
the environment:

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createReadStream, createWriteStream } from "fs";
import { Readable } from "stream";
import { pipeline } from "stream/promises";

const client = new ElevenLabsClient();
```

1. **Speech-to-Speech (voice changer)** — `client.speechToSpeech.convert(voiceId, …)`
   against `POST /v1/speech-to-speech/{voice_id}`. Use `model_id: "eleven_english_sts_v2"`
   and set `remove_background_noise: true` for built-in cleanup.
2. **Sound Effects** — `client.textToSoundEffects.convert({ text, … })` against
   `POST /v1/sound-generation`. Tune `duration_seconds` (0.5–30) and
   `prompt_influence` (0–1; higher follows the prompt more closely).
3. **Audio Isolation** — `client.audioIsolation.audioIsolation({ audio })` against
   `POST /v1/audio-isolation`, or the streaming variant for large files.
4. **Speech-to-Text** — `client.speechToText.convert({ audio, model_id: "scribe_v1" })`
   against `POST /v1/speech-to-text`; optionally enable `diarize` and word timestamps.

Each returns an audio stream (steps 1–3) piped to disk, or a transcript object
(step 4). See [references/implementation.md](references/implementation.md) for the
complete helper functions and cURL equivalents.

### First example — Speech-to-Speech skeleton

```typescript
async function speechToSpeech(sourceAudioPath, targetVoiceId, outputPath) {
  const audio = await client.speechToSpeech.convert(targetVoiceId, {
    audio: createReadStream(sourceAudioPath),
    model_id: "eleven_english_sts_v2",
    voice_settings: JSON.stringify({ stability: 0.5, similarity_boost: 0.8 }),
    remove_background_noise: true,
  });
  await pipeline(Readable.fromWeb(audio as any), createWriteStream(outputPath));
}
```

## API Endpoint Summary

| Feature | Method | Endpoint | Billing |
|---------|--------|----------|---------|
| Speech-to-Speech | POST | `/v1/speech-to-speech/{voice_id}` | Per character |
| Sound Effects | POST | `/v1/sound-generation` | Per generation |
| Audio Isolation | POST | `/v1/audio-isolation` | 1,000 chars/min of audio |
| Audio Isolation Stream | POST | `/v1/audio-isolation/stream` | 1,000 chars/min of audio |
| Speech-to-Text | POST | `/v1/speech-to-text` | Per audio minute |

## Output

- **Steps 1–3** write an audio file to the `outputPath` you pass and log a
  confirmation, e.g. `Voice-converted audio saved to converted.mp3` or
  `Clean audio saved to clean_interview.mp3`.
- **Step 4** returns a transcript object: `result.text` holds the full
  transcription, and `result.words` (when present) carries word-level
  `{ start, end, text }` timestamps.
- cURL paths stream the resulting audio directly to the `--output` file.

## Error Handling

| Error | HTTP | Cause | Solution |
|-------|------|-------|----------|
| `model_can_not_do_voice_conversion` | 400 | Wrong model for STS | Use `eleven_english_sts_v2` |
| `audio_too_short` | 400 | STS input under 1 second | Use longer audio clip |
| `audio_too_long` | 400 | STS input over limit | Trim to under 5 minutes |
| `invalid_sound_prompt` | 400 | Nonsensical SFX description | Write descriptive, specific prompts |
| `file_too_large` | 413 | Audio isolation over 500MB | Compress or split the file |
| `quota_exceeded` | 401 | Character/generation limit hit | Check usage dashboard |

## Examples

Worked, copy-ready invocations for all four workflows — including the three
sound-effect variants (rain, laser, seamless forest loop), the "Rachel" voice
conversion, an audio-isolation clean-up, and a transcription with word timestamps —
are in [references/examples.md](references/examples.md). A one-liner:

```typescript
// Generate a 10-second rain sound effect, faithful to the prompt
await generateSoundEffect(
  "Heavy rain on a tin roof with distant thunder",
  "rain.mp3",
  { duration: 10, promptInfluence: 0.6 }
);
```

## Resources

- [Full implementation walkthrough](references/implementation.md) — every step's
  SDK + cURL code, sound-effect tips, and audio-isolation limits.
- [Worked examples](references/examples.md) — copy-ready invocations per workflow.
- [Speech-to-Speech API](https://elevenlabs.io/docs/api-reference/speech-to-speech/convert)
- [Sound Effects API](https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert)
- [Audio Isolation API](https://elevenlabs.io/docs/api-reference/audio-isolation/convert)
- [Speech-to-Text API](https://elevenlabs.io/docs/api-reference/speech-to-text/convert)

## Next Steps

For common errors, see `elevenlabs-common-errors`. For SDK patterns, see `elevenlabs-sdk-patterns`.
