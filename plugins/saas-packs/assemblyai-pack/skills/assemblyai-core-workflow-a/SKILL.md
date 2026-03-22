---
name: assemblyai-core-workflow-a
description: |
  Execute AssemblyAI primary workflow: async transcription with audio intelligence.
  Use when transcribing audio/video files, enabling speaker diarization,
  sentiment analysis, entity detection, PII redaction, or content moderation.
  Trigger with phrases like "assemblyai transcribe", "assemblyai transcription",
  "transcribe audio", "speaker diarization assemblyai".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI Core Workflow A — Async Transcription

## Overview
Primary money-path workflow: submit audio for async transcription with audio intelligence features. The SDK handles file upload (for local files), queues the transcription job, and polls until completion.

## Prerequisites
- `assemblyai` package installed
- API key configured in `ASSEMBLYAI_API_KEY`

## Instructions

### Step 1: Basic Async Transcription

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

// Remote URL — SDK queues and polls automatically
const transcript = await client.transcripts.transcribe({
  audio: 'https://example.com/meeting-recording.mp3',
});

console.log(transcript.text);
console.log(`Duration: ${transcript.audio_duration}s`);
console.log(`Words: ${transcript.words?.length}`);
```

### Step 2: Local File Upload

```typescript
// The SDK uploads the file and transcribes in one call
const transcript = await client.transcripts.transcribe({
  audio: './recordings/interview.wav',
});

// Or from a buffer/stream
import fs from 'fs';
const buffer = fs.readFileSync('./recordings/interview.wav');
const transcript2 = await client.transcripts.transcribe({
  audio: buffer,
});
```

### Step 3: Speaker Diarization

```typescript
const transcript = await client.transcripts.transcribe({
  audio: audioUrl,
  speaker_labels: true,
  speakers_expected: 3,  // Optional: hint for expected speaker count
});

// Utterances are grouped by speaker
for (const utterance of transcript.utterances ?? []) {
  console.log(`Speaker ${utterance.speaker}: ${utterance.text}`);
  // Speaker A: Good morning, thanks for joining.
  // Speaker B: Happy to be here.
}
```

### Step 4: Full Audio Intelligence Stack

```typescript
const transcript = await client.transcripts.transcribe({
  audio: audioUrl,

  // Speaker identification
  speaker_labels: true,

  // Content analysis
  sentiment_analysis: true,
  entity_detection: true,
  auto_highlights: true,
  iab_categories: true,       // Topic detection (IAB taxonomy)
  content_safety: true,        // Flag sensitive content
  summarization: true,
  summary_model: 'informative',
  summary_type: 'bullets',

  // Formatting
  punctuate: true,
  format_text: true,
  language_code: 'en',

  // Word boost for domain terms
  word_boost: ['AssemblyAI', 'LeMUR', 'transcription'],
  boost_param: 'high',
});

// --- Access results ---

// Sentiment per sentence
for (const s of transcript.sentiment_analysis_results ?? []) {
  console.log(`[${s.sentiment}] ${s.text}`);
  // [POSITIVE] I really enjoyed working on this project.
}

// Named entities
for (const e of transcript.entities ?? []) {
  console.log(`${e.entity_type}: ${e.text}`);
  // person_name: John Smith
  // location: San Francisco
}

// Auto-highlighted key phrases
for (const h of transcript.auto_highlights_result?.results ?? []) {
  console.log(`"${h.text}" (count: ${h.count}, rank: ${h.rank})`);
}

// IAB content categories
const categories = transcript.iab_categories_result?.summary ?? {};
for (const [category, relevance] of Object.entries(categories)) {
  if ((relevance as number) > 0.5) {
    console.log(`Topic: ${category} (${((relevance as number) * 100).toFixed(0)}%)`);
  }
}

// Content safety labels
for (const result of transcript.content_safety_labels?.results ?? []) {
  for (const label of result.labels) {
    console.log(`Safety: ${label.label} (${(label.confidence * 100).toFixed(0)}%)`);
  }
}

// Summary
console.log('Summary:', transcript.summary);
```

### Step 5: PII Redaction

```typescript
const transcript = await client.transcripts.transcribe({
  audio: audioUrl,
  redact_pii: true,
  redact_pii_policies: [
    'email_address',
    'phone_number',
    'person_name',
    'credit_card_number',
    'social_security_number',
    'date_of_birth',
  ],
  redact_pii_sub: 'hash',  // Replace PII with hash. Options: 'hash' | 'entity_name'
  redact_pii_audio: true,  // Also generate redacted audio file
});

// Text has PII replaced: "My name is ####" or "My name is [PERSON_NAME]"
console.log(transcript.text);

// Get redacted audio URL (takes extra processing time)
if (transcript.redact_pii_audio_quality) {
  const redactedAudio = await client.transcripts.redactedAudio(transcript.id);
  console.log('Redacted audio URL:', redactedAudio.redacted_audio_url);
}
```

### Step 6: Manage Transcripts

```typescript
// List recent transcripts
const page = await client.transcripts.list({ limit: 20 });
for (const t of page.transcripts) {
  console.log(`${t.id} | ${t.status} | ${t.audio_duration}s`);
}

// Get a specific transcript
const existing = await client.transcripts.get('transcript-id');

// Delete a transcript (GDPR compliance)
await client.transcripts.delete('transcript-id');
```

## Supported Audio Formats
MP3, WAV, FLAC, M4A, OGG, WebM, MP4, AAC. Max file size: 5 GB. Max duration: 10 hours (async). The SDK auto-detects format.

## Output
- Complete transcript with word-level timestamps and confidence scores
- Speaker-labeled utterances (with `speaker_labels: true`)
- Sentiment analysis, entity detection, key phrases, topic categories
- PII-redacted text and audio
- Content safety labels for moderation

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `transcript.status === 'error'` | Corrupted audio or unsupported format | Verify audio file plays locally |
| `download_url must be accessible` | Private/expired URL | Use a publicly accessible URL or upload locally |
| `Could not process audio` | File too short (<200ms) or silent | Ensure audio has speech content |
| `word_boost` has no effect | Misspelled terms or wrong model | Check spelling; word boost works with Best model tier |

## Resources
- [Transcription API Reference](https://www.assemblyai.com/docs/api-reference/transcripts/submit)
- [Audio Intelligence Models](https://www.assemblyai.com/docs/audio-intelligence)
- [PII Redaction Guide](https://www.assemblyai.com/docs/audio-intelligence/pii-redaction)
- [Speaker Diarization](https://www.assemblyai.com/docs/speech-to-text/speaker-diarization)

## Next Steps
For real-time streaming transcription, see `assemblyai-core-workflow-b`.
For LLM-powered analysis of transcripts, see `assemblyai-sdk-patterns` (LeMUR examples).
