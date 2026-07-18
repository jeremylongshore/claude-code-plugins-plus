---
name: groq-core-workflow-b
description: |
  Use when you need Groq's non-chat endpoints — transcribing or translating
  audio with Whisper, understanding images with Llama 4 vision, generating
  speech (TTS), or benchmarking models for speed vs quality.
  Trigger with phrases like "groq whisper", "groq transcription",
  "groq audio", "groq vision", "groq TTS", "groq speech".
allowed-tools: Read, Bash(npm:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- workflow
- audio
- vision
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Core Workflow B: Audio, Vision & Speech

## Overview

Beyond chat completions, Groq offers ultra-fast Whisper transcription (216x real-time), Llama 4 vision, and text-to-speech — all on the same `groq-sdk` client. This skill covers transcription/translation, vision, TTS, and model benchmarking, with full runnable code in [references/implementation.md](references/implementation.md) and worked scripts in [references/examples.md](references/examples.md).

## Prerequisites

- `groq-sdk` installed, `GROQ_API_KEY` set (the SDK reads it from the environment automatically)
- For audio: audio files in a supported format
- For vision: image URLs or base64-encoded images

## Audio Models

| Model ID | Languages | Speed | Best For |
|----------|-----------|-------|----------|
| `whisper-large-v3` | 100+ | 164x real-time | Best accuracy, multilingual |
| `whisper-large-v3-turbo` | 100+ | 216x real-time | Best speed/accuracy balance |

**Supported audio formats**: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm

## Instructions

Each workflow is a single SDK call on the shared `groq` client. Pick the endpoint for your task, then follow the full walkthrough in [references/implementation.md](references/implementation.md) for the complete, copy-pasteable version of each.

1. **Transcription** — `groq.audio.transcriptions.create({ file, model: "whisper-large-v3-turbo", response_format })`. Use `response_format: "verbose_json"` with `timestamp_granularities: ["segment"]` to get per-segment start/end times.
2. **Translation** — `groq.audio.translations.create({ file, model: "whisper-large-v3" })` transcribes any-language audio directly to English text.
3. **Vision** — a normal `groq.chat.completions.create` call where `content` is an array mixing `{ type: "text" }` and `{ type: "image_url" }` parts. Accepts up to 5 images (URL or `data:` base64) with `meta-llama/llama-4-scout-17b-16e-instruct`.
4. **Text-to-Speech** — `groq.audio.speech.create({ model: "playai-tts", input, voice, response_format })`, then write `Buffer.from(await response.arrayBuffer())` to a file.
5. **Benchmarking** — loop a prompt across several chat models and time each call to compare latency and tokens/sec (see [references/examples.md](references/examples.md)).

Minimal transcription skeleton:

```typescript
import Groq from "groq-sdk";
import fs from "fs";

const groq = new Groq();

async function transcribe(filePath: string): Promise<string> {
  const transcription = await groq.audio.transcriptions.create({
    file: fs.createReadStream(filePath),
    model: "whisper-large-v3-turbo",
    response_format: "json",
  });
  return transcription.text;
}
```

## Output

- **Transcription/translation**: a `transcription.text` string. With `verbose_json`, a `segments[]` array where each segment has `start`, `end`, and `text`.
- **Vision**: the assistant reply at `completion.choices[0].message.content` (a natural-language answer about the image(s)).
- **Text-to-Speech**: an audio response you convert to a `Buffer` and write to disk (`wav`, `mp3`, `flac`, `opus`, or `aac`).
- **Benchmarking**: one console line per model — latency in ms, throughput in tok/s, and total tokens.

## Vision Model Limits

- Maximum 5 images per request
- Supported formats: JPEG, PNG, GIF, WebP
- Images fetched from URL or embedded as base64
- Vision models also support tool use, JSON mode, and streaming

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid file format` | Unsupported audio type | Convert to mp3/wav/flac first |
| `File too large` | Audio exceeds 25MB | Split into smaller chunks |
| `model_not_found` | Vision model ID wrong | Use full path: `meta-llama/llama-4-scout-17b-16e-instruct` |
| `max_images_exceeded` | >5 images in request | Reduce to 5 or fewer images |
| `429` on Whisper | Audio RPM limit hit | Queue transcription requests |

## Examples

Complete, runnable scripts live in [references/examples.md](references/examples.md):

- **Python transcription with timestamps** — transcribe a local MP3 and print each segment with its start/end time.
- **Model benchmarking** — run one prompt across `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`, and `llama-3.3-70b-specdec` and print latency + throughput per model.

Quick vision example (analyze one image by URL):

```typescript
const completion = await groq.chat.completions.create({
  model: "meta-llama/llama-4-scout-17b-16e-instruct",
  messages: [{
    role: "user",
    content: [
      { type: "text", text: "What is in this image?" },
      { type: "image_url", image_url: { url: imageUrl } },
    ],
  }],
  max_tokens: 1024,
});
console.log(completion.choices[0].message.content);
```

## Resources

- [Groq Speech-to-Text](https://console.groq.com/docs/speech-to-text)
- [Groq Text-to-Speech](https://console.groq.com/docs/text-to-speech)
- [Groq Vision](https://console.groq.com/docs/vision)
- [Groq Models](https://console.groq.com/docs/models)

## Next Steps

For common errors and troubleshooting patterns across all Groq workflows, see the `groq-common-errors` skill. For chat completions, streaming, tool use, and JSON mode, see `groq-core-workflow-a`.
