---
name: deepgram-core-workflow-b
description: |
  Implement real-time streaming transcription with Deepgram WebSocket.
  Use when building live transcription, voice interfaces,
  real-time captioning, or voice AI applications.
  Trigger: "deepgram streaming", "real-time transcription", "live transcription",
  "websocket transcription", "voice streaming", "deepgram live".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, voice-ai, transcription, streaming, websocket]

---
# Deepgram Core Workflow B: Live Streaming Transcription

## Overview
Real-time streaming transcription using Deepgram's WebSocket API. The SDK manages the WebSocket connection via `listen.live()`. Covers microphone capture, interim/final result handling, speaker diarization, UtteranceEnd detection, auto-reconnect, and building an SSE endpoint for browser clients.

## Prerequisites
- `@deepgram/sdk` installed, `DEEPGRAM_API_KEY` configured
- Audio source: microphone (via Sox/`rec`), file stream, or WebSocket audio from browser
- For mic capture: `sox` installed (`apt install sox` / `brew install sox`)

## Instructions

### Step 1: Basic Live Transcription

```typescript
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

const connection = deepgram.listen.live({
  model: 'nova-3',
  language: 'en',
  smart_format: true,
  punctuate: true,
  interim_results: true,      // Show in-progress results
  utterance_end_ms: 1000,     // Silence threshold for utterance end
  vad_events: true,           // Voice activity detection events
  encoding: 'linear16',       // 16-bit PCM
  sample_rate: 16000,         // 16 kHz
  channels: 1,                // Mono
});

// Connection lifecycle events
connection.on(LiveTranscriptionEvents.Open, () => {
  console.log('WebSocket connected to Deepgram');
});

connection.on(LiveTranscriptionEvents.Close, () => {
  console.log('WebSocket closed');
});

connection.on(LiveTranscriptionEvents.Error, (err) => {
  console.error('Deepgram error:', err);
});

// Transcript events
connection.on(LiveTranscriptionEvents.Transcript, (data) => {
  const transcript = data.channel.alternatives[0]?.transcript;
  if (!transcript) return;

  if (data.is_final) {
    console.log(`[FINAL] ${transcript}`);
  } else {
    process.stdout.write(`\r[interim] ${transcript}`);
  }
});

// UtteranceEnd — fires when speaker pauses
connection.on(LiveTranscriptionEvents.UtteranceEnd, () => {
  console.log('\n--- utterance end ---');
});
```

### Step 2: Microphone Capture with Sox

```typescript
import { spawn } from 'child_process';

function startMicrophone(connection: any) {
  // Sox captures from default mic: 16kHz, 16-bit signed LE, mono
  const mic = spawn('rec', [
    '-q',              // Quiet (no progress)
    '-r', '16000',     // Sample rate
    '-e', 'signed',    // Encoding
    '-b', '16',        // Bit depth
    '-c', '1',         // Mono
    '-t', 'raw',       // Raw PCM output
    '-',               // Output to stdout
  ]);

  mic.stdout.on('data', (chunk: Buffer) => {
    if (connection.getReadyState() === 1) {  // WebSocket.OPEN
      connection.send(chunk);
    }
  });

  mic.on('error', (err) => {
    console.error('Microphone error:', err.message);
    console.log('Install sox: apt install sox / brew install sox');
  });

  return mic;
}

// Usage
const mic = startMicrophone(connection);

// Graceful shutdown
process.on('SIGINT', () => {
  mic.kill();
  connection.finish();  // Sends CloseStream message, waits for final results
  setTimeout(() => process.exit(0), 2000);
});
```

### Step 3: Live Diarization

```typescript
const connection = deepgram.listen.live({
  model: 'nova-3',
  smart_format: true,
  diarize: true,
  interim_results: false,  // Only final for cleaner diarization
  utterance_end_ms: 1500,
  encoding: 'linear16',
  sample_rate: 16000,
  channels: 1,
});

connection.on(LiveTranscriptionEvents.Transcript, (data) => {
  if (!data.is_final) return;

  const words = data.channel.alternatives[0]?.words ?? [];
  if (words.length === 0) return;

  // Group consecutive words by speaker
  let currentSpeaker = words[0].speaker;
  let segment = '';

  for (const word of words) {
    if (word.speaker !== currentSpeaker) {
      console.log(`Speaker ${currentSpeaker}: ${segment.trim()}`);
      currentSpeaker = word.speaker;
      segment = '';
    }
    segment += ` ${word.punctuated_word ?? word.word}`;
  }
  console.log(`Speaker ${currentSpeaker}: ${segment.trim()}`);
});
```

### Step 4: Auto-Reconnect with Backoff

```typescript
class ReconnectingLiveTranscription {
  private client: ReturnType<typeof createClient>;
  private connection: any = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseDelay = 1000;

  constructor(apiKey: string, private options: Record<string, any>) {
    this.client = createClient(apiKey);
  }

  connect() {
    this.connection = this.client.listen.live(this.options);

    this.connection.on(LiveTranscriptionEvents.Open, () => {
      console.log('Connected');
      this.reconnectAttempts = 0;  // Reset on success
    });

    this.connection.on(LiveTranscriptionEvents.Close, () => {
      this.scheduleReconnect();
    });

    this.connection.on(LiveTranscriptionEvents.Error, (err: Error) => {
      console.error('Connection error:', err.message);
      this.scheduleReconnect();
    });

    return this.connection;
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }
    const delay = this.baseDelay * Math.pow(2, this.reconnectAttempts)
      + Math.random() * 1000;  // Jitter
    this.reconnectAttempts++;
    console.log(`Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => this.connect(), delay);
  }

  send(chunk: Buffer) {
    if (this.connection?.getReadyState() === 1) {
      this.connection.send(chunk);
    }
  }

  close() {
    this.maxReconnectAttempts = 0;  // Prevent reconnect
    this.connection?.finish();
  }
}
```

### Step 5: SSE Endpoint for Browser Clients

```typescript
import express from 'express';
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk';

const app = express();

app.get('/api/transcribe/stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);
  const connection = deepgram.listen.live({
    model: 'nova-3',
    smart_format: true,
    interim_results: true,
    encoding: 'linear16',
    sample_rate: 16000,
    channels: 1,
  });

  connection.on(LiveTranscriptionEvents.Transcript, (data) => {
    const transcript = data.channel.alternatives[0]?.transcript;
    if (transcript) {
      res.write(`data: ${JSON.stringify({
        transcript,
        is_final: data.is_final,
        speech_final: data.speech_final,
      })}\n\n`);
    }
  });

  // Client provides audio via a paired WebSocket (see browser setup)
  req.on('close', () => {
    connection.finish();
  });
});
```

### Step 6: KeepAlive for Long Sessions

```typescript
// Deepgram closes idle connections after ~10s of no audio.
// Send KeepAlive messages during silence periods.
connection.on(LiveTranscriptionEvents.Open, () => {
  const keepAliveInterval = setInterval(() => {
    if (connection.getReadyState() === 1) {
      connection.keepAlive();
    }
  }, 8000);  // Every 8 seconds

  connection.on(LiveTranscriptionEvents.Close, () => {
    clearInterval(keepAliveInterval);
  });
});
```

## Output
- Live WebSocket transcription with interim/final results
- Microphone capture pipeline (Sox -> Deepgram)
- Speaker diarization in streaming mode
- Auto-reconnect with exponential backoff and jitter
- SSE endpoint for browser integration
- KeepAlive handling for long sessions

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| WebSocket closes immediately | Invalid API key or bad encoding params | Check key, verify `encoding`/`sample_rate` match audio |
| No transcripts received | Audio not being sent or wrong format | Verify `connection.send(chunk)` is called with raw PCM |
| High latency | Network congestion | Use `interim_results: true` for perceived speed |
| `rec` command not found | Sox not installed | `apt install sox` or `brew install sox` |
| Connection drops after 10s | No audio + no KeepAlive | Send `connection.keepAlive()` every 8s |
| Garbled output | Sample rate mismatch | Ensure audio sample rate matches `sample_rate` option |

## Resources
- [Live Streaming Audio](https://developers.deepgram.com/docs/live-streaming-audio)
- [Streaming API Reference](https://developers.deepgram.com/reference/speech-to-text/listen-streaming)
- [End of Speech Detection](https://developers.deepgram.com/docs/understanding-end-of-speech-detection)
- [SDK LiveTranscriptionEvents](https://github.com/deepgram/deepgram-js-sdk)

## Next Steps
Proceed to `deepgram-data-handling` for transcript processing and storage patterns.
