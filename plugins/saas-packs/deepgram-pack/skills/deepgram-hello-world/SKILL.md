---
name: deepgram-hello-world
description: |
  Create a minimal working Deepgram transcription example.
  Use when starting a new Deepgram integration, testing your setup,
  or learning basic Deepgram API patterns.
  Trigger: "deepgram hello world", "deepgram example", "deepgram quick start",
  "simple transcription", "transcribe audio".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, api, testing, transcription, quickstart]

---
# Deepgram Hello World

## Overview
Minimal working examples for Deepgram speech-to-text. Transcribe an audio URL in 5 lines with `createClient` + `listen.prerecorded.transcribeUrl`. Includes local file transcription, Python equivalent, and Nova-3 model selection.

## Prerequisites
- `npm install @deepgram/sdk` completed
- `DEEPGRAM_API_KEY` environment variable set
- Audio source: URL or local file (WAV, MP3, FLAC, OGG, M4A)

## Instructions

### Step 1: Transcribe Audio from URL (TypeScript)

```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

async function main() {
  const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
    { url: 'https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav' },
    {
      model: 'nova-3',        // Latest model — best accuracy
      smart_format: true,     // Auto-punctuation, paragraphs, numerals
      language: 'en',
    }
  );

  if (error) throw error;

  const transcript = result.results.channels[0].alternatives[0].transcript;
  console.log('Transcript:', transcript);
  console.log('Confidence:', result.results.channels[0].alternatives[0].confidence);
}

main();
```

### Step 2: Transcribe a Local File

```typescript
import { createClient } from '@deepgram/sdk';
import { readFileSync } from 'fs';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

async function transcribeFile(filePath: string) {
  const audio = readFileSync(filePath);

  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    audio,
    {
      model: 'nova-3',
      smart_format: true,
      // Deepgram auto-detects format, but you can specify:
      mimetype: 'audio/wav',
    }
  );

  if (error) throw error;

  console.log(result.results.channels[0].alternatives[0].transcript);
}

transcribeFile('./meeting-recording.wav');
```

### Step 3: Python Equivalent

```python
import os
from deepgram import DeepgramClient, PrerecordedOptions

client = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])

# URL transcription
url = {"url": "https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav"}
options = PrerecordedOptions(model="nova-3", smart_format=True, language="en")

response = client.listen.rest.v("1").transcribe_url(url, options)
transcript = response.results.channels[0].alternatives[0].transcript
print(f"Transcript: {transcript}")
print(f"Confidence: {response.results.channels[0].alternatives[0].confidence}")
```

```python
# Local file transcription
with open("meeting.wav", "rb") as audio:
    source = {"buffer": audio.read(), "mimetype": "audio/wav"}
    response = client.listen.rest.v("1").transcribe_file(source, options)
    print(response.results.channels[0].alternatives[0].transcript)
```

### Step 4: Add Features

```typescript
// Enable diarization (speaker identification)
const { result } = await deepgram.listen.prerecorded.transcribeUrl(
  { url: audioUrl },
  {
    model: 'nova-3',
    smart_format: true,
    diarize: true,         // Speaker labels
    utterances: true,      // Turn-by-turn segments
    paragraphs: true,      // Paragraph formatting
  }
);

// Print speaker-labeled output
if (result.results.utterances) {
  for (const utterance of result.results.utterances) {
    console.log(`Speaker ${utterance.speaker}: ${utterance.transcript}`);
  }
}
```

### Step 5: Explore Model Options

| Model | Use Case | Speed | Accuracy |
|-------|----------|-------|----------|
| `nova-3` | General — best accuracy | Fast | Highest |
| `nova-2` | General — proven stable | Fast | Very High |
| `nova-2-meeting` | Conference rooms, multiple speakers | Fast | High |
| `nova-2-phonecall` | Low-bandwidth phone audio | Fast | High |
| `base` | Cost-sensitive, high-volume | Fastest | Good |
| `whisper-large` | Multilingual (100+ languages) | Slow | High |

### Step 6: Run It

```bash
# TypeScript
npx tsx hello-deepgram.ts

# Python
python hello_deepgram.py
```

## Output
- Working transcription from URL or local file
- Printed transcript text with confidence score
- Optional: speaker-labeled utterances

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check `DEEPGRAM_API_KEY` |
| `400 Bad Request` | Unsupported audio format | Use WAV, MP3, FLAC, OGG, or M4A |
| Empty transcript | No speech in audio | Verify audio has audible speech |
| `ENOTFOUND` | URL not reachable | Check audio URL is publicly accessible |
| `Cannot find module '@deepgram/sdk'` | SDK not installed | Run `npm install @deepgram/sdk` |

## Resources
- [Pre-recorded Audio Guide](https://developers.deepgram.com/docs/pre-recorded-audio)
- [Model Options](https://developers.deepgram.com/docs/model)
- [Smart Formatting](https://developers.deepgram.com/docs/smart-format)
- [Sample Audio Files](https://static.deepgram.com/examples/)

## Next Steps
Proceed to `deepgram-core-workflow-a` for production transcription patterns or `deepgram-core-workflow-b` for live streaming.
