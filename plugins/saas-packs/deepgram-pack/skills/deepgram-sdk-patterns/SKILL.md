---
name: deepgram-sdk-patterns
description: |
  Apply production-ready Deepgram SDK patterns for TypeScript and Python.
  Use when implementing Deepgram integrations, refactoring SDK usage,
  or establishing team coding standards for Deepgram.
  Trigger with phrases like "deepgram SDK patterns", "deepgram best practices",
  "deepgram code patterns", "idiomatic deepgram", "deepgram typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram SDK Patterns

## Overview
Production patterns for the Deepgram speech-to-text SDK (`deepgram-sdk`). Covers pre-recorded transcription, live streaming, speaker diarization, and multi-language support with proper error handling.

## Prerequisites
- `pip install deepgram-sdk` or `npm install @deepgram/sdk`
- `DEEPGRAM_API_KEY` environment variable
- Audio files or microphone access

## Instructions

### Step 1: Client Initialization

```python
from deepgram import DeepgramClient, PrerecordedOptions, LiveOptions
import os

def get_deepgram_client() -> DeepgramClient:
    return DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
```

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';
const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);
```

### Step 2: Pre-Recorded Transcription

```python
def transcribe_file(file_path: str, language: str = "en") -> dict:
    client = get_deepgram_client()
    with open(file_path, "rb") as audio:
        response = client.listen.rest.v("1").transcribe_file(
            {"buffer": audio.read(), "mimetype": get_mimetype(file_path)},
            PrerecordedOptions(
                model="nova-2",
                language=language,
                smart_format=True,
                punctuate=True,
                diarize=True,
                utterances=True,
                paragraphs=True
            )
        )
    transcript = response.results.channels[0].alternatives[0]
    return {
        "text": transcript.transcript,
        "confidence": transcript.confidence,
        "words": [{"word": w.word, "start": w.start, "end": w.end, "speaker": getattr(w, 'speaker', None)}
                  for w in (transcript.words or [])]
    }
```

### Step 3: Live Streaming Transcription

```python
import asyncio

async def stream_microphone():
    client = get_deepgram_client()
    connection = client.listen.asyncwebsocket.v("1")

    async def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if transcript:
            print(f"[{result.type}] {transcript}")

    connection.on("Results", on_message)

    options = LiveOptions(
        model="nova-2",
        language="en",
        smart_format=True,
        interim_results=True,
        endpointing=300  # 300: timeout: 5 minutes
    )

    await connection.start(options)
    # Send audio chunks from microphone...
    # await connection.send(audio_bytes)
    await connection.finish()
```

### Step 4: Batch Processing with Concurrency Control

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def batch_transcribe(files: list[str], max_concurrent: int = 5) -> list:
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []

    async def process_one(path):
        async with semaphore:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, transcribe_file, path)
            return {"file": path, **result}

    tasks = [process_one(f) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r if not isinstance(r, Exception) else {"error": str(r)} for r in results]
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check `DEEPGRAM_API_KEY` |
| `400 Unsupported format` | Bad audio codec | Convert to WAV/MP3/FLAC |
| Empty transcript | No speech in audio | Check audio quality and volume |
| WebSocket disconnect | Network instability | Implement reconnection logic |

## Examples

### Speaker-Labeled Transcript
```python
result = transcribe_file("meeting.wav")
current_speaker = None
for word in result["words"]:
    if word["speaker"] != current_speaker:
        current_speaker = word["speaker"]
        print(f"\nSpeaker {current_speaker}:", end=" ")
    print(word["word"], end=" ")
```

## Resources
- [Deepgram SDK Python](https://github.com/deepgram/deepgram-python-sdk)
- [Deepgram API Docs](https://developers.deepgram.com/docs)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale