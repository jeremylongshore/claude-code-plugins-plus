---
name: assemblyai-core-workflow-b
description: |
  Execute AssemblyAI streaming transcription and LeMUR workflows.
  Use when implementing real-time speech-to-text, live captions,
  voice agents, or LLM-powered audio analysis with LeMUR.
  Trigger with phrases like "assemblyai streaming", "assemblyai real-time",
  "assemblyai live transcription", "assemblyai LeMUR", "assemblyai summarize audio".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, streaming, lemur]
compatible-with: claude-code
---

# AssemblyAI Core Workflow B — Streaming & LeMUR

## Overview
Two advanced workflows: (1) real-time streaming transcription via WebSocket for live captioning and voice agents, and (2) LeMUR for applying LLMs to transcripts — summarization, Q&A, action items, and custom tasks.

## Prerequisites
- `assemblyai` package installed (`npm install assemblyai`)
- API key configured in `ASSEMBLYAI_API_KEY`
- For streaming: microphone or audio stream source

## Part 1: Real-Time Streaming Transcription

### Step 1: Basic Streaming Setup

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

const transcriber = client.streaming.createService({
  // Model options: 'nova-3' (default), 'nova-3-pro' (highest accuracy)
  speech_model: 'nova-3',
  sample_rate: 16000,
});

transcriber.on('open', ({ sessionId }) => {
  console.log('Session opened:', sessionId);
});

transcriber.on('transcript', (message) => {
  // message_type: 'PartialTranscript' or 'FinalTranscript'
  if (message.message_type === 'FinalTranscript') {
    console.log('[Final]', message.text);
  } else {
    process.stdout.write(`\r[Partial] ${message.text}`);
  }
});

transcriber.on('error', (error) => {
  console.error('Streaming error:', error);
});

transcriber.on('close', (code, reason) => {
  console.log('Session closed:', code, reason);
});

await transcriber.connect();

// Send audio chunks (16-bit PCM, 16kHz mono)
// transcriber.sendAudio(audioBuffer);

// When done:
// await transcriber.close();
```

### Step 2: Stream from Microphone (Node.js)

```typescript
import { AssemblyAI } from 'assemblyai';
import { spawn } from 'child_process';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

const transcriber = client.streaming.createService({
  speech_model: 'nova-3',
  sample_rate: 16000,
});

transcriber.on('transcript', (msg) => {
  if (msg.message_type === 'FinalTranscript' && msg.text) {
    console.log(msg.text);
  }
});

await transcriber.connect();

// Use SoX to capture microphone audio as raw PCM
const mic = spawn('sox', [
  '-d',                  // default audio device
  '-t', 'raw',           // raw PCM output
  '-b', '16',            // 16-bit
  '-r', '16000',         // 16kHz sample rate
  '-c', '1',             // mono
  '-e', 'signed-integer',
  '-',                   // pipe to stdout
]);

mic.stdout.on('data', (chunk: Buffer) => {
  transcriber.sendAudio(chunk);
});

mic.on('close', async () => {
  await transcriber.close();
});

// Handle Ctrl+C
process.on('SIGINT', async () => {
  mic.kill();
  await transcriber.close();
  process.exit(0);
});
```

### Step 3: Browser-Safe Temporary Token

```typescript
// Server-side: generate a short-lived token for the browser
const token = await client.streaming.createTemporaryToken({
  expires_in_seconds: 300, // 5 minutes
});

// Send `token` to your frontend
// Client-side uses token instead of API key:
// const transcriber = new StreamingTranscriber({ token: receivedToken });
```

### Step 4: Streaming with Word Boost and Speaker Labels

```typescript
const transcriber = client.streaming.createService({
  speech_model: 'nova-3-pro',
  sample_rate: 16000,
  word_boost: ['AssemblyAI', 'LeMUR', 'transcription'],
  enable_extra_session_information: true,
});

transcriber.on('turn', (turn) => {
  // Speaker-labeled turns (available with nova-3-pro)
  console.log(`Speaker ${turn.speaker}: ${turn.transcript}`);
});
```

## Part 2: LeMUR — LLM-Powered Audio Analysis

### Step 5: Summarize a Transcript

```typescript
// First transcribe (or use an existing transcript_id)
const transcript = await client.transcripts.transcribe({
  audio: 'https://example.com/meeting.mp3',
});

// Summarize with LeMUR
const { response } = await client.lemur.summary({
  transcript_ids: [transcript.id],
  context: 'This is a weekly engineering standup meeting.',
  answer_format: 'bullet points',
});

console.log('Summary:', response);
```

### Step 6: Ask Questions About Audio

```typescript
const { response: answers } = await client.lemur.questionAnswer({
  transcript_ids: [transcript.id],
  questions: [
    { question: 'What decisions were made?', answer_format: 'list' },
    { question: 'Were there any blockers discussed?', answer_format: 'short sentence' },
    { question: 'Who owns the next action items?', answer_format: 'list' },
  ],
});

for (const qa of answers) {
  console.log(`Q: ${qa.question}`);
  console.log(`A: ${qa.answer}\n`);
}
```

### Step 7: Extract Action Items

```typescript
const { response: actionItems } = await client.lemur.actionItems({
  transcript_ids: [transcript.id],
  context: 'This is a product planning meeting.',
  answer_format: 'Each action item should include the owner and deadline.',
});

console.log('Action Items:', actionItems);
```

### Step 8: Custom LeMUR Task

```typescript
const { response } = await client.lemur.task({
  transcript_ids: [transcript.id],
  prompt: `Analyze this customer support call and provide:
    1. Customer sentiment (positive/neutral/negative)
    2. Issue category
    3. Resolution status
    4. CSAT prediction (1-5)
    Format as JSON.`,
});

const analysis = JSON.parse(response);
console.log(analysis);
```

### Step 9: Multi-Transcript Analysis

```typescript
// LeMUR can analyze up to 100 hours of audio in a single request
const transcriptIds = [
  'transcript-1', 'transcript-2', 'transcript-3',
];

const { response } = await client.lemur.task({
  transcript_ids: transcriptIds,
  prompt: 'Compare themes across these three customer interviews. What patterns emerge?',
});

console.log(response);
```

## Streaming Specifications
| Spec | Value |
|------|-------|
| Audio format | 16-bit PCM, mono |
| Sample rates | 8000, 16000, 22050, 44100, 48000 Hz |
| Latency (P50) | ~300ms |
| Max concurrent streams (free) | 5 new/min |
| Max concurrent streams (paid) | 100 new/min, auto-scales 10%/60s |
| Languages | 99+ (with Universal-3) |
| Models | `nova-3` (default), `nova-3-pro` (highest accuracy) |

## Output
- Real-time partial and final transcripts via WebSocket
- Speaker-labeled streaming turns (nova-3-pro)
- LeMUR summaries, Q&A responses, action items
- Custom LLM analysis with structured output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Session limit reached` | Too many concurrent streams | Wait or upgrade plan |
| `Invalid audio encoding` | Wrong PCM format | Use 16-bit signed integer, mono |
| `WebSocket disconnected` | Network interruption | Implement reconnection logic |
| `LeMUR context too long` | >100 hours of audio | Split into smaller batches |
| `transcript not found` | Invalid transcript_id | Verify ID exists via `client.transcripts.get()` |

## Resources
- [Streaming Speech-to-Text Guide](https://www.assemblyai.com/docs/getting-started/transcribe-streaming-audio)
- [LeMUR Documentation](https://www.assemblyai.com/docs/lemur)
- [LeMUR API Reference](https://www.assemblyai.com/docs/api-reference/lemur/task)
- [Streaming API Reference](https://www.assemblyai.com/docs/api-reference/streaming)

## Next Steps
For error troubleshooting, see `assemblyai-common-errors`.
