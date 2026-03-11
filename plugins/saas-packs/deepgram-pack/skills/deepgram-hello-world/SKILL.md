---
name: deepgram-hello-world
description: |
  Create a minimal working Deepgram transcription example.
  Use when starting a new Deepgram integration, testing your setup,
  or learning basic Deepgram API patterns.
  Trigger with phrases like "deepgram hello world", "deepgram example",
  "deepgram quick start", "simple transcription", "transcribe audio".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Hello World

## Overview
Minimal working example demonstrating core Deepgram speech-to-text functionality.

## Prerequisites
- Completed `deepgram-install-auth` setup
- Valid API credentials configured
- Audio file for transcription (or use URL)

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY);
```

### Step 3: Transcribe Audio from URL
```typescript
async function transcribe() {
  const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
    { url: 'https://static.deepgram.com/examples/nasa-podcast.wav' },
    { model: 'nova-2', smart_format: true }
  );

  if (error) throw error;
  console.log(result.results.channels[0].alternatives[0].transcript);
}

transcribe();
```

## Output
- Working code file with Deepgram client initialization
- Successful transcription response
- Console output showing transcribed text

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list @deepgram/sdk` |
| Auth Error | Invalid credentials | Check environment variable is set |
| Audio Format Error | Unsupported format | Use WAV, MP3, FLAC, or OGG |
| URL Not Accessible | Cannot fetch audio | Ensure URL is publicly accessible |

## Examples

### TypeScript - Transcribe URL
```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY);

async function main() {
  const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
    { url: 'https://static.deepgram.com/examples/nasa-podcast.wav' },
    { model: 'nova-2', smart_format: true }
  );

  if (error) throw error;
  console.log('Transcript:', result.results.channels[0].alternatives[0].transcript);
}

main().catch(console.error);
```

### TypeScript - Transcribe Local File
```typescript
import { createClient } from '@deepgram/sdk';
import { readFileSync } from 'fs';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY);

async function transcribeFile(filePath: string) {
  const audio = readFileSync(filePath);

  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    audio,
    { model: 'nova-2', smart_format: true, mimetype: 'audio/wav' }
  );

  if (error) throw error;
  console.log('Transcript:', result.results.channels[0].alternatives[0].transcript);
}

transcribeFile('./audio.wav');
```

### Python Example
```python
from deepgram import DeepgramClient, PrerecordedOptions
import os

deepgram = DeepgramClient(os.environ.get('DEEPGRAM_API_KEY'))

options = PrerecordedOptions(
    model="nova-2",
    smart_format=True,
)

url = {"url": "https://static.deepgram.com/examples/nasa-podcast.wav"}
response = deepgram.listen.rest.v("1").transcribe_url(url, options)

print(response.results.channels[0].alternatives[0].transcript)
```

## Resources
- [Deepgram Getting Started](https://developers.deepgram.com/docs/getting-started)
- [Deepgram API Reference](https://developers.deepgram.com/reference)
- [Deepgram Models](https://developers.deepgram.com/docs/models)

## Next Steps
Proceed to `deepgram-local-dev-loop` for development workflow setup.