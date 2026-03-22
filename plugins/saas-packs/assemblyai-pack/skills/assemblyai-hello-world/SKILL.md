---
name: assemblyai-hello-world
description: |
  Create a minimal working AssemblyAI transcription example.
  Use when starting a new AssemblyAI integration, testing your setup,
  or learning basic transcription patterns.
  Trigger with phrases like "assemblyai hello world", "assemblyai example",
  "assemblyai quick start", "simple assemblyai transcription".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI Hello World

## Overview
Minimal working examples demonstrating AssemblyAI's three core capabilities: async transcription, audio intelligence features, and LeMUR (LLM-powered analysis).

## Prerequisites
- Completed `assemblyai-install-auth` setup
- Valid API key configured in `ASSEMBLYAI_API_KEY`

## Instructions

### Step 1: Basic Transcription (Remote URL)

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

async function transcribeUrl() {
  const transcript = await client.transcripts.transcribe({
    audio: 'https://storage.googleapis.com/aai-web-samples/5_common_sports_702.wav',
  });

  if (transcript.status === 'error') {
    throw new Error(`Transcription failed: ${transcript.error}`);
  }

  console.log('Transcript:', transcript.text);
  console.log('Duration:', transcript.audio_duration, 'seconds');
  console.log('Word count:', transcript.words?.length);
}

transcribeUrl().catch(console.error);
```

### Step 2: Transcribe a Local File

```typescript
async function transcribeLocal() {
  // The SDK handles upload automatically when you pass a local path
  const transcript = await client.transcripts.transcribe({
    audio: './recording.mp3',
  });

  console.log('Transcript:', transcript.text);

  // Access word-level timestamps
  for (const word of transcript.words ?? []) {
    console.log(`[${word.start}ms - ${word.end}ms] ${word.text} (${word.confidence})`);
  }
}
```

### Step 3: Enable Audio Intelligence Features

```typescript
async function transcribeWithIntelligence() {
  const transcript = await client.transcripts.transcribe({
    audio: 'https://storage.googleapis.com/aai-web-samples/5_common_sports_702.wav',
    speaker_labels: true,       // Who said what
    auto_highlights: true,       // Key phrases extraction
    sentiment_analysis: true,    // Sentiment per sentence
    entity_detection: true,      // Named entities (people, orgs, locations)
    summarization: true,         // Auto-summary
    summary_model: 'informative',
    summary_type: 'bullets',
  });

  // Speaker diarization
  for (const utterance of transcript.utterances ?? []) {
    console.log(`Speaker ${utterance.speaker}: ${utterance.text}`);
  }

  // Key phrases
  for (const result of transcript.auto_highlights_result?.results ?? []) {
    console.log(`Key phrase: "${result.text}" (mentioned ${result.count} times)`);
  }

  // Sentiment analysis
  for (const result of transcript.sentiment_analysis_results ?? []) {
    console.log(`${result.sentiment}: "${result.text}"`);
  }

  // Summary
  console.log('Summary:', transcript.summary);
}
```

### Step 4: LeMUR — Ask Questions About Your Audio

```typescript
async function lemurDemo() {
  // First, transcribe
  const transcript = await client.transcripts.transcribe({
    audio: 'https://storage.googleapis.com/aai-web-samples/5_common_sports_702.wav',
  });

  // Then use LeMUR to analyze
  const { response } = await client.lemur.task({
    transcript_ids: [transcript.id],
    prompt: 'Summarize the key topics discussed and list any action items mentioned.',
  });

  console.log('LeMUR response:', response);
}
```

## Output
- Working transcription from a remote URL or local file
- Word-level timestamps with confidence scores
- Speaker-labeled utterances (diarization)
- Key phrases, sentiment analysis, entity detection
- LeMUR-powered summarization and Q&A

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `transcript.status === 'error'` | Bad audio URL/format | Verify URL is publicly accessible, supported format |
| `Authentication error` | Invalid API key | Check `ASSEMBLYAI_API_KEY` environment variable |
| `File not found` | Wrong local path | Verify file exists at the specified path |
| `Unsupported audio format` | Incompatible format | Use MP3, WAV, M4A, FLAC, OGG, or WebM |

## Resources
- [Transcribe an Audio File](https://www.assemblyai.com/docs/getting-started/transcribe-an-audio-file)
- [Audio Intelligence Models](https://www.assemblyai.com/docs/audio-intelligence)
- [LeMUR Documentation](https://www.assemblyai.com/docs/lemur)
- [Supported File Types](https://www.assemblyai.com/docs/concepts/faq#what-audio-and-video-formats-are-supported)

## Next Steps
Proceed to `assemblyai-local-dev-loop` for development workflow setup.
