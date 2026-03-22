---
name: deepgram-sdk-patterns
description: |
  Apply production-ready Deepgram SDK patterns for TypeScript and Python.
  Use when implementing Deepgram integrations, refactoring SDK usage,
  or establishing team coding standards for Deepgram.
  Trigger: "deepgram SDK patterns", "deepgram best practices",
  "deepgram code patterns", "idiomatic deepgram", "deepgram typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, python, typescript, patterns]

---
# Deepgram SDK Patterns

## Overview
Production patterns for `@deepgram/sdk` (TypeScript) and `deepgram-sdk` (Python). Covers singleton client, typed wrappers, text-to-speech with Aura, audio intelligence pipeline, error handling, and SDK v5 migration path.

## Prerequisites
- `npm install @deepgram/sdk` or `pip install deepgram-sdk`
- `DEEPGRAM_API_KEY` environment variable configured

## Instructions

### Step 1: Singleton Client (TypeScript)

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';

class DeepgramService {
  private static instance: DeepgramService;
  private client: DeepgramClient;

  private constructor() {
    const apiKey = process.env.DEEPGRAM_API_KEY;
    if (!apiKey) throw new Error('DEEPGRAM_API_KEY is required');
    this.client = createClient(apiKey);
  }

  static getInstance(): DeepgramService {
    if (!this.instance) this.instance = new DeepgramService();
    return this.instance;
  }

  getClient(): DeepgramClient { return this.client; }
}

export const deepgram = DeepgramService.getInstance().getClient();
```

### Step 2: Text-to-Speech with Aura

```typescript
import { createClient } from '@deepgram/sdk';
import { writeFileSync } from 'fs';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

async function textToSpeech(text: string, outputPath: string) {
  const response = await deepgram.speak.request(
    { text },
    {
      model: 'aura-2-thalia-en',  // Female English voice
      encoding: 'linear16',
      container: 'wav',
      sample_rate: 24000,
    }
  );

  const stream = await response.getStream();
  if (!stream) throw new Error('No audio stream returned');

  // Collect stream into buffer
  const reader = stream.getReader();
  const chunks: Uint8Array[] = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }

  const buffer = Buffer.concat(chunks);
  writeFileSync(outputPath, buffer);
  console.log(`Audio saved: ${outputPath} (${buffer.length} bytes)`);
  return buffer;
}

// Aura-2 voice options:
// aura-2-thalia-en    — Female, warm
// aura-2-asteria-en   — Female, default
// aura-2-orion-en     — Male, deep
// aura-2-luna-en      — Female, soft
// aura-2-helios-en    — Male, authoritative
// aura-asteria-en     — Aura v1 fallback
```

### Step 3: Audio Intelligence Pipeline

```typescript
async function analyzeConversation(audioUrl: string) {
  const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
    { url: audioUrl },
    {
      model: 'nova-3',
      smart_format: true,
      diarize: true,
      utterances: true,
      // Audio Intelligence features
      summarize: 'v2',       // Generates a short summary
      detect_topics: true,   // Identifies key topics
      sentiment: true,       // Per-segment sentiment analysis
      intents: true,         // Identifies speaker intents
    }
  );
  if (error) throw error;

  return {
    transcript: result.results.channels[0].alternatives[0].transcript,
    summary: result.results.summary?.short,
    topics: result.results.topics?.segments?.map((s: any) => ({
      text: s.text,
      topics: s.topics.map((t: any) => t.topic),
    })),
    sentiments: result.results.sentiments?.segments?.map((s: any) => ({
      text: s.text,
      sentiment: s.sentiment,
      confidence: s.sentiment_score,
    })),
    intents: result.results.intents?.segments?.map((s: any) => ({
      text: s.text,
      intent: s.intents[0]?.intent,
      confidence: s.intents[0]?.confidence_score,
    })),
  };
}
```

### Step 4: Python Production Patterns

```python
from deepgram import DeepgramClient, PrerecordedOptions, LiveOptions, SpeakOptions
import os

class DeepgramService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
        return cls._instance

    def transcribe_url(self, url: str, **kwargs):
        options = PrerecordedOptions(
            model=kwargs.get("model", "nova-3"),
            smart_format=True,
            diarize=kwargs.get("diarize", False),
            summarize=kwargs.get("summarize", False),
        )
        source = {"url": url}
        return self.client.listen.rest.v("1").transcribe_url(source, options)

    def transcribe_file(self, path: str, **kwargs):
        with open(path, "rb") as f:
            source = {"buffer": f.read(), "mimetype": self._mimetype(path)}
        options = PrerecordedOptions(
            model=kwargs.get("model", "nova-3"),
            smart_format=True,
            diarize=kwargs.get("diarize", False),
        )
        return self.client.listen.rest.v("1").transcribe_file(source, options)

    def text_to_speech(self, text: str, output_path: str):
        options = SpeakOptions(model="aura-2-thalia-en", encoding="linear16")
        response = self.client.speak.rest.v("1").save(output_path, {"text": text}, options)
        return response

    @staticmethod
    def _mimetype(path: str) -> str:
        ext = path.rsplit(".", 1)[-1].lower()
        return {"wav": "audio/wav", "mp3": "audio/mpeg", "flac": "audio/flac",
                "ogg": "audio/ogg", "m4a": "audio/mp4"}.get(ext, "audio/wav")
```

### Step 5: Typed Response Helpers

```typescript
// Extract clean types from Deepgram responses
interface TranscriptWord {
  word: string;
  start: number;
  end: number;
  confidence: number;
  speaker?: number;
  punctuated_word?: string;
}

interface TranscriptResult {
  transcript: string;
  confidence: number;
  words: TranscriptWord[];
  duration: number;
  requestId: string;
}

function parseResult(result: any): TranscriptResult {
  const alt = result.results.channels[0].alternatives[0];
  return {
    transcript: alt.transcript,
    confidence: alt.confidence,
    words: alt.words ?? [],
    duration: result.metadata.duration,
    requestId: result.metadata.request_id,
  };
}
```

### Step 6: SDK v5 Migration Notes

```typescript
// v3/v4 (current stable):
import { createClient } from '@deepgram/sdk';
const dg = createClient(apiKey);
await dg.listen.prerecorded.transcribeUrl(source, options);
await dg.listen.live(options);
await dg.speak.request({ text }, options);

// v5 (auto-generated, Fern-based):
import { DeepgramClient } from '@deepgram/sdk';
const dg = new DeepgramClient({ apiKey });
await dg.listen.v1.media.transcribeUrl(source, options);
await dg.listen.v1.connect(options);  // async
await dg.speak.v1.audio.generate({ text }, options);
```

## Output
- Singleton client pattern with environment validation
- Text-to-speech (Aura-2) with stream-to-file
- Audio intelligence pipeline (summary, topics, sentiment, intents)
- Python production service class
- Typed response helpers
- v5 migration reference

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check `DEEPGRAM_API_KEY` value |
| `400 Unsupported format` | Bad audio codec | Convert to WAV/MP3/FLAC |
| `speak.request is not a function` | SDK version mismatch | Check import, v5 uses `speak.v1.audio.generate` |
| Empty TTS response | Empty text input | Validate text is non-empty before calling |
| `summarize` returns null | Feature not enabled | Pass `summarize: 'v2'` (string, not boolean) |

## Resources
- [JavaScript SDK](https://github.com/deepgram/deepgram-js-sdk)
- [Python SDK](https://github.com/deepgram/deepgram-python-sdk)
- [SDK Feature Matrix](https://developers.deepgram.com/sdks/sdk-features)
- [TTS Voices](https://developers.deepgram.com/docs/tts-models)
- [Audio Intelligence](https://developers.deepgram.com/docs/text-intelligence)

## Next Steps
Proceed to `deepgram-data-handling` for transcript storage and processing patterns.
