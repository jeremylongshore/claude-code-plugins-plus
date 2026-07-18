---
name: elevenlabs-hello-world
description: |
  Generate your first ElevenLabs text-to-speech audio file. Use when starting a
  new ElevenLabs integration, testing your setup, or learning basic TTS API
  patterns before wiring voice into a real app.
  Trigger with "elevenlabs hello world", "elevenlabs example", "elevenlabs quick
  start", "first elevenlabs TTS", "text to speech demo".
allowed-tools: Read, Write, Bash(npm:*), Bash(node:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- tts
- audio
compatibility: Designed for Claude Code
---
# ElevenLabs Hello World

## Overview

Generate speech from text using the ElevenLabs TTS API. This skill covers the
core `POST /v1/text-to-speech/<voice-id>` endpoint with real voice IDs, model
selection, and audio output. Start from the minimal SDK call below, then drill
into [the full implementation](references/implementation.md) for the cURL,
streaming, and multi-language paths.

## Prerequisites

- Completed the `elevenlabs-install-auth` setup skill so the SDK is installed.
- A valid API key exported as `ELEVENLABS_API_KEY` in your shell environment.
- Node 20+ (for the TypeScript SDK path) or Python 3.9+ (for the Python path).

## Instructions

The whole workflow is one API call: pick a voice ID, pick a model, send text,
write the returned audio stream to a file. The minimal TypeScript path:

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createWriteStream } from "fs";
import { Readable } from "stream";
import { pipeline } from "stream/promises";

const client = new ElevenLabsClient();
const audio = await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
  text: "Hello! This is your first ElevenLabs text-to-speech generation.",
  model_id: "eleven_multilingual_v2",
});
await pipeline(Readable.fromWeb(audio as any), createWriteStream("output.mp3"));
```

The four generation paths, with full copy-paste code and inline commentary on
every `voice_settings` field, live in
[references/implementation.md](references/implementation.md):

1. **SDK (TypeScript / Python)** — batch generation with tuned voice settings.
2. **cURL** — the raw REST call, no SDK, for shell scripts and testing.
3. **Streaming** — the `eleven_flash_v2_5` low-latency path (~75 ms first chunk).
4. **Model / voice / output-format tables** — the exact IDs to plug in above.

Pick the path that matches your stack, swap the voice ID and text, and run it.

## Output

A single audio file written to disk (default `output.mp3`), plus a console line
confirming the write:

- `output.mp3` — MP3 at `mp3_44100_128` by default (~35–50 KB for a one-line
  greeting). Override the codec via `output_format` (see the output-format table
  in [implementation.md](references/implementation.md)).
- stdout: `Audio saved to output.mp3` (or `Streamed audio saved to
  streamed.mp3` on the streaming path).

A non-200 response returns a JSON error body instead of audio — see Error
Handling below.

## Error Handling

| Error | HTTP | Cause | Solution |
|-------|------|-------|----------|
| `voice_not_found` | 404 | Invalid voice ID | Use `GET /v1/voices` to list valid IDs |
| `invalid_api_key` | 401 | Bad or missing key | Check `ELEVENLABS_API_KEY` env var |
| `model_not_found` | 400 | Wrong model_id string | Use exact IDs from the models table |
| `text_too_long` | 400 | Exceeds 5,000 chars | Split into chunks; use streaming for long text |
| `quota_exceeded` | 401 | Monthly character limit hit | Check usage at elevenlabs.io/app/usage |

With cURL, a failure writes the JSON error body to `output.mp3`; inspect it with
`cat output.mp3` before assuming the audio is corrupt.

## Examples

Three end-to-end scenarios — first SDK MP3, one-shot cURL, and low-latency
streaming — with the exact commands and the resulting on-disk artifacts are in
[references/examples.md](references/examples.md). The quickest smoke test:

```bash
export ELEVENLABS_API_KEY="sk_..."
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" -H "Content-Type: application/json" \
  -d '{"text":"Hello from the ElevenLabs API!","model_id":"eleven_multilingual_v2"}' \
  --output output.mp3
```

## Resources

- [Full implementation walkthrough](references/implementation.md) — SDK, cURL,
  streaming, and the model / voice / output-format tables.
- [Worked examples](references/examples.md) — three runnable scenarios.
- [TTS API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
- [Stream API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech/stream)
- [Models Overview](https://elevenlabs.io/docs/overview/models)
- [Voice Library](https://elevenlabs.io/voice-library)

## Next Steps

Once your first file plays back cleanly, proceed to `elevenlabs-local-dev-loop`
for a development workflow with hot-reload and caching, or
`elevenlabs-core-workflow-a` to move from pre-made voices into voice cloning.
