---
name: deepgram-core-workflow-a
description: |
  Implement production pre-recorded speech-to-text with Deepgram.
  Use when building audio transcription, batch processing,
  or implementing diarization and intelligence features.
  Trigger: "deepgram transcription", "speech to text", "transcribe audio",
  "batch transcription", "deepgram nova", "diarize audio".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, voice-ai, transcription, workflow, stt]

---
# Deepgram Core Workflow A: Pre-recorded Transcription

## Overview
Production pre-recorded transcription service using Deepgram's REST API. Covers `transcribeUrl` and `transcribeFile`, speaker diarization, audio intelligence (summarization, topic detection, sentiment, intent), batch processing with concurrency control, and callback-based async transcription for large files.

## Prerequisites
- `@deepgram/sdk` installed, `DEEPGRAM_API_KEY` configured
- Audio files: WAV, MP3, FLAC, OGG, M4A, or WebM
- For batch: `p-limit` package (`npm install p-limit`)

## Instructions

### Step 1: Transcription Service Class

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';
import { readFileSync } from 'fs';

interface TranscribeOptions {
  model?: 'nova-3' | 'nova-2' | 'nova-2-meeting' | 'nova-2-phonecall' | 'base';
  language?: string;
  diarize?: boolean;
  utterances?: boolean;
  paragraphs?: boolean;
  smart_format?: boolean;
  summarize?: boolean;      // Audio intelligence
  detect_topics?: boolean;  // Topic detection
  sentiment?: boolean;      // Sentiment analysis
  intents?: boolean;        // Intent recognition
  keywords?: string[];      // Keyword boosting: ["term:weight"]
  callback?: string;        // Async callback URL
}

class DeepgramTranscriber {
  private client: DeepgramClient;

  constructor(apiKey: string) {
    this.client = createClient(apiKey);
  }

  async transcribeUrl(url: string, opts: TranscribeOptions = {}) {
    const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
      { url },
      {
        model: opts.model ?? 'nova-3',
        language: opts.language ?? 'en',
        smart_format: opts.smart_format ?? true,
        diarize: opts.diarize ?? false,
        utterances: opts.utterances ?? false,
        paragraphs: opts.paragraphs ?? false,
        summarize: opts.summarize ? 'v2' : undefined,
        detect_topics: opts.detect_topics ?? false,
        sentiment: opts.sentiment ?? false,
        intents: opts.intents ?? false,
        keywords: opts.keywords,
        callback: opts.callback,
      }
    );
    if (error) throw new Error(`Transcription failed: ${error.message}`);
    return result;
  }

  async transcribeFile(filePath: string, opts: TranscribeOptions = {}) {
    const audio = readFileSync(filePath);
    const mimetype = this.detectMimetype(filePath);

    const { result, error } = await this.client.listen.prerecorded.transcribeFile(
      audio,
      {
        model: opts.model ?? 'nova-3',
        smart_format: opts.smart_format ?? true,
        mimetype,
        diarize: opts.diarize ?? false,
        utterances: opts.utterances ?? false,
        summarize: opts.summarize ? 'v2' : undefined,
        detect_topics: opts.detect_topics ?? false,
        sentiment: opts.sentiment ?? false,
      }
    );
    if (error) throw new Error(`File transcription failed: ${error.message}`);
    return result;
  }

  private detectMimetype(path: string): string {
    const ext = path.split('.').pop()?.toLowerCase();
    const map: Record<string, string> = {
      wav: 'audio/wav', mp3: 'audio/mpeg', flac: 'audio/flac',
      ogg: 'audio/ogg', m4a: 'audio/mp4', webm: 'audio/webm',
    };
    return map[ext ?? ''] ?? 'audio/wav';
  }
}
```

### Step 2: Extract Structured Results

```typescript
function formatResult(result: any) {
  const channel = result.results.channels[0];
  const alt = channel.alternatives[0];

  return {
    transcript: alt.transcript,
    confidence: alt.confidence,
    words: alt.words?.map((w: any) => ({
      word: w.word,
      start: w.start,
      end: w.end,
      confidence: w.confidence,
      speaker: w.speaker,       // Only if diarize: true
      punctuated_word: w.punctuated_word,
    })),
    // Speaker segments (requires utterances: true + diarize: true)
    utterances: result.results.utterances?.map((u: any) => ({
      speaker: u.speaker,
      text: u.transcript,
      start: u.start,
      end: u.end,
      confidence: u.confidence,
    })),
    // Audio intelligence results
    summary: result.results.summary?.short,
    topics: result.results.topics?.segments,
    sentiments: result.results.sentiments?.segments,
    intents: result.results.intents?.segments,
    metadata: {
      duration: result.metadata.duration,
      channels: result.metadata.channels,
      model: result.metadata.model_info,
      request_id: result.metadata.request_id,
    },
  };
}
```

### Step 3: Batch Processing

```typescript
import pLimit from 'p-limit';

async function batchTranscribe(
  files: string[],
  opts: TranscribeOptions = {},
  concurrency = 5
) {
  const transcriber = new DeepgramTranscriber(process.env.DEEPGRAM_API_KEY!);
  const limit = pLimit(concurrency);

  const results = await Promise.allSettled(
    files.map(file =>
      limit(async () => {
        const result = await transcriber.transcribeFile(file, opts);
        console.log(`Done: ${file} (${result.metadata.duration}s)`);
        return { file, result: formatResult(result) };
      })
    )
  );

  const succeeded = results.filter(r => r.status === 'fulfilled');
  const failed = results.filter(r => r.status === 'rejected');
  console.log(`Batch complete: ${succeeded.length} ok, ${failed.length} failed`);
  return results;
}
```

### Step 4: Async Callback Transcription (Large Files)

```typescript
// For files >2 hours or when you don't want to hold a connection open,
// use Deepgram's callback feature. Deepgram POSTs results to your URL.
async function submitAsync(audioUrl: string, callbackUrl: string) {
  const transcriber = new DeepgramTranscriber(process.env.DEEPGRAM_API_KEY!);

  // Deepgram returns a request_id immediately, processes in background
  const result = await transcriber.transcribeUrl(audioUrl, {
    model: 'nova-3',
    diarize: true,
    callback: callbackUrl,  // Your HTTPS endpoint
  });

  console.log('Submitted. Request ID:', result.metadata.request_id);
  // Deepgram will POST results to callbackUrl when done
  // Retries up to 10 times with 30s delay on failure
}
```

### Step 5: Keyword Boosting

```typescript
// Boost domain-specific terms for higher accuracy
const result = await transcriber.transcribeUrl(audioUrl, {
  model: 'nova-3',
  keywords: [
    'Kubernetes:1.5',    // Boost weight 1.0-2.0
    'PostgreSQL:1.5',
    'microservices:1.3',
  ],
});
```

## Output
- `DeepgramTranscriber` class with URL and file transcription
- Structured result extraction with word-level timing, speakers, and intelligence
- Batch processing with configurable concurrency via `p-limit`
- Async callback pattern for large files
- Keyword boosting for domain vocabulary

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `400 Bad Request` | Invalid audio format | Verify file header bytes (WAV: `RIFF`, MP3: `0xFFF3/0xFFFB`) |
| `413 Payload Too Large` | File exceeds limit | Use callback URL for async processing |
| Empty transcript | No speech in audio | Check audio volume, try `alternatives: 3` for confidence |
| `408 Timeout` | Long file, sync mode | Switch to callback-based async |
| Low confidence | Background noise | Preprocess: `ffmpeg -i input.wav -af "highpass=f=200,lowpass=f=3000" clean.wav` |

## Resources
- [Pre-recorded API](https://developers.deepgram.com/docs/pre-recorded-audio)
- [Speaker Diarization](https://developers.deepgram.com/docs/diarization)
- [Audio Intelligence](https://deepgram.com/product/audio-intelligence)
- [Summarization](https://developers.deepgram.com/docs/summarization)
- [Callback Feature](https://developers.deepgram.com/docs/callback)

## Next Steps
Proceed to `deepgram-core-workflow-b` for real-time streaming transcription.
