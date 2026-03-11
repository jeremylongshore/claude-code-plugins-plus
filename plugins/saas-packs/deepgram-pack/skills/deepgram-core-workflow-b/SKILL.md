---
name: deepgram-core-workflow-b
description: |
  Implement real-time streaming transcription with Deepgram.
  Use when building live transcription, voice interfaces,
  or real-time audio processing applications.
  Trigger with phrases like "deepgram streaming", "real-time transcription",
  "live transcription", "websocket transcription", "voice streaming".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Core Workflow B: Streaming Transcription

## Overview
Build real-time streaming transcription with Deepgram WebSocket API. Covers live audio capture, WebSocket connection management, interim/final result handling, and speaker diarization in streaming mode.

## Prerequisites
- Deepgram API key
- `@deepgram/sdk` npm package installed
- Microphone access (for live capture) or audio stream source
- WebSocket support in your runtime

## Instructions

### Step 1: WebSocket Streaming Connection
```typescript
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

async function startLiveTranscription(onTranscript: (text: string, isFinal: boolean) => void) {
  const connection = deepgram.listen.live({
    model: 'nova-2',
    language: 'en-US',
    smart_format: true,
    interim_results: true,
    utterance_end_ms: 1000,
    vad_events: true,
    diarize: true,
  });

  connection.on(LiveTranscriptionEvents.Open, () => {
    console.log('Deepgram connection opened');
  });

  connection.on(LiveTranscriptionEvents.Transcript, (data) => {
    const transcript = data.channel.alternatives[0];
    if (transcript.transcript) {
      onTranscript(transcript.transcript, data.is_final);
    }
  });

  connection.on(LiveTranscriptionEvents.UtteranceEnd, () => {
    onTranscript('\n', true); // End of utterance
  });

  connection.on(LiveTranscriptionEvents.Error, (err) => {
    console.error('Deepgram error:', err);
  });

  connection.on(LiveTranscriptionEvents.Close, () => {
    console.log('Deepgram connection closed');
  });

  return connection;
}
```

### Step 2: Audio Stream from Microphone
```typescript
import { Readable } from 'stream';

// Node.js: capture audio from system microphone
async function captureAndTranscribe() {
  const connection = await startLiveTranscription((text, isFinal) => {
    if (isFinal) {
      process.stdout.write(text);
    }
  });

  // Using Sox for audio capture (install: apt-get install sox)
  const { spawn } = await import('child_process');
  const mic = spawn('rec', [
    '-q',            // Quiet
    '-t', 'raw',     // Raw format
    '-r', '16000',   // 16kHz sample rate
    '-e', 'signed',  // Signed integer encoding
    '-b', '16',      // 16-bit
    '-c', '1',       // Mono
    '-',             // Output to stdout
  ]);

  mic.stdout.on('data', (chunk: Buffer) => {
    connection.send(chunk);
  });

  // Stop after 30 seconds
  setTimeout(() => {
    mic.kill();
    connection.finish();
  }, 30000);
}
```

### Step 3: Handle Interim and Final Results
```typescript
class TranscriptionManager {
  private finalTranscript = '';
  private interimTranscript = '';

  handleResult(text: string, isFinal: boolean) {
    if (isFinal) {
      this.finalTranscript += text + ' ';
      this.interimTranscript = '';
    } else {
      this.interimTranscript = text;
    }
  }

  getDisplayText(): string {
    return this.finalTranscript + this.interimTranscript;
  }

  getFinalTranscript(): string {
    return this.finalTranscript.trim();
  }

  reset() {
    this.finalTranscript = '';
    this.interimTranscript = '';
  }
}

// Usage with WebSocket
const manager = new TranscriptionManager();
const connection = await startLiveTranscription((text, isFinal) => {
  manager.handleResult(text, isFinal);
  // Update UI with current display text
  updateUI(manager.getDisplayText());
});
```

### Step 4: Speaker Diarization in Streaming
```typescript
interface SpeakerSegment {
  speaker: number;
  text: string;
  startTime: number;
  endTime: number;
}

function processDiarizedTranscript(data: any): SpeakerSegment[] {
  const words = data.channel.alternatives[0].words || [];
  const segments: SpeakerSegment[] = [];
  let currentSegment: SpeakerSegment | null = null;

  for (const word of words) {
    if (!currentSegment || currentSegment.speaker !== word.speaker) {
      if (currentSegment) segments.push(currentSegment);
      currentSegment = {
        speaker: word.speaker,
        text: word.punctuated_word || word.word,
        startTime: word.start,
        endTime: word.end,
      };
    } else {
      currentSegment.text += ' ' + (word.punctuated_word || word.word);
      currentSegment.endTime = word.end;
    }
  }

  if (currentSegment) segments.push(currentSegment);
  return segments;
}

// Display with speaker labels
function formatDiarizedOutput(segments: SpeakerSegment[]): string {
  return segments
    .map(s => `[Speaker ${s.speaker}]: ${s.text}`)
    .join('\n');
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| WebSocket disconnects | Network instability | Implement auto-reconnect with backoff |
| No audio data | Microphone not captured | Check audio device permissions and format |
| High latency | Network congestion | Use `interim_results: true` for perceived speed |
| Missing speakers | Diarization not enabled | Set `diarize: true` in connection options |

## Examples

### Express SSE Streaming Endpoint
```typescript
app.get('/api/transcribe-stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');

  const connection = startLiveTranscription((text, isFinal) => {
    res.write(`data: ${JSON.stringify({ text, isFinal })}\n\n`);
  });

  req.on('close', () => connection.finish());
});
```

## Resources
- [Deepgram Streaming API](https://developers.deepgram.com/docs/streaming)
- [Deepgram Node SDK](https://github.com/deepgram/deepgram-node-sdk)
- [Deepgram Models](https://developers.deepgram.com/docs/models-overview)
