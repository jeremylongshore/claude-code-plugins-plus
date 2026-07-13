# Deepgram Streaming Transcription Implementation

## WebSocket Connection Setup

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
    onTranscript('\n', true);
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

## Audio Capture from Microphone

```typescript
// Node.js: capture audio from system microphone using Sox
async function captureAndTranscribe() {
  const connection = await startLiveTranscription((text, isFinal) => {
    if (isFinal) process.stdout.write(text);
  });

  const { spawn } = await import('child_process');
  const mic = spawn('rec', [
    '-q', '-t', 'raw', '-r', '16000', '-e', 'signed', '-b', '16', '-c', '1', '-',
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

## Interim and Final Result Manager

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
```

## Speaker Diarization in Streaming

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

function formatDiarizedOutput(segments: SpeakerSegment[]): string {
  return segments.map(s => `[Speaker ${s.speaker}]: ${s.text}`).join('\n');
}
```

## Express SSE Streaming Endpoint

```typescript
app.get('/api/transcribe-stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');

  const connection = startLiveTranscription((text, isFinal) => {
    res.write(`data: ${JSON.stringify({ text, isFinal })}\n\n`);
  });

  req.on('close', () => connection.finish());
});
```
