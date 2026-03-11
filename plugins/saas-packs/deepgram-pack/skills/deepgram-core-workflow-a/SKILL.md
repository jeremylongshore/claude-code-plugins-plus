---
name: deepgram-core-workflow-a
description: |
  Implement speech-to-text transcription workflow with Deepgram.
  Use when building pre-recorded audio transcription, batch processing,
  or implementing core transcription features.
  Trigger with phrases like "deepgram transcription", "speech to text",
  "transcribe audio", "audio transcription workflow", "batch transcription".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Core Workflow A: Pre-recorded Transcription

## Overview
Implement a complete pre-recorded audio transcription workflow using Deepgram's Nova-2 model.

## Prerequisites
- Completed `deepgram-install-auth` setup
- Understanding of async patterns
- Audio files or URLs to transcribe

## Instructions

### Step 1: Set Up Transcription Service
Create a service class to handle transcription operations.

### Step 2: Implement File and URL Transcription
Add methods for both local files and remote URLs.

### Step 3: Add Feature Options
Configure punctuation, diarization, and formatting.

### Step 4: Process Results
Extract and format transcription results.

## Output
- Transcription service class
- Support for file and URL transcription
- Configurable transcription options
- Formatted transcript output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Audio Too Long | Exceeds limits | Split into chunks or use async |
| Unsupported Format | Invalid audio type | Convert to WAV/MP3/FLAC |
| Empty Response | No speech detected | Check audio quality |
| Timeout | Large file processing | Use callback URL pattern |

## Examples

### TypeScript Transcription Service
```typescript
// services/transcription.ts
import { createClient } from '@deepgram/sdk';
import { readFile } from 'fs/promises';

export interface TranscriptionOptions {
  model?: 'nova-2' | 'nova' | 'enhanced' | 'base';
  language?: string;
  punctuate?: boolean;
  diarize?: boolean;
  smartFormat?: boolean;
  utterances?: boolean;
  paragraphs?: boolean;
}

export interface TranscriptionResult {
  transcript: string;
  confidence: number;
  words: Array<{
    word: string;
    start: number;
    end: number;
    confidence: number;
  }>;
  utterances?: Array<{
    speaker: number;
    transcript: string;
    start: number;
    end: number;
  }>;
}

export class TranscriptionService {
  private client;

  constructor(apiKey: string) {
    this.client = createClient(apiKey);
  }

  async transcribeUrl(
    url: string,
    options: TranscriptionOptions = {}
  ): Promise<TranscriptionResult> {
    const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
      { url },
      {
        model: options.model || 'nova-2',
        language: options.language || 'en',
        punctuate: options.punctuate ?? true,
        diarize: options.diarize ?? false,
        smart_format: options.smartFormat ?? true,
        utterances: options.utterances ?? false,
        paragraphs: options.paragraphs ?? false,
      }
    );

    if (error) throw new Error(error.message);

    return this.formatResult(result);
  }

  async transcribeFile(
    filePath: string,
    options: TranscriptionOptions = {}
  ): Promise<TranscriptionResult> {
    const audio = await readFile(filePath);
    const mimetype = this.getMimeType(filePath);

    const { result, error } = await this.client.listen.prerecorded.transcribeFile(
      audio,
      {
        model: options.model || 'nova-2',
        language: options.language || 'en',
        punctuate: options.punctuate ?? true,
        diarize: options.diarize ?? false,
        smart_format: options.smartFormat ?? true,
        mimetype,
      }
    );

    if (error) throw new Error(error.message);

    return this.formatResult(result);
  }

  private formatResult(result: any): TranscriptionResult {
    const channel = result.results.channels[0];
    const alternative = channel.alternatives[0];

    return {
      transcript: alternative.transcript,
      confidence: alternative.confidence,
      words: alternative.words || [],
      utterances: result.results.utterances,
    };
  }

  private getMimeType(filePath: string): string {
    const ext = filePath.split('.').pop()?.toLowerCase();
    const mimeTypes: Record<string, string> = {
      wav: 'audio/wav',
      mp3: 'audio/mpeg',
      flac: 'audio/flac',
      ogg: 'audio/ogg',
      m4a: 'audio/mp4',
      webm: 'audio/webm',
    };
    return mimeTypes[ext || ''] || 'audio/wav';
  }
}
```

### Batch Transcription
```typescript
// services/batch-transcription.ts
import { TranscriptionService, TranscriptionResult } from './transcription';

export async function batchTranscribe(
  files: string[],
  options: { concurrency?: number } = {}
): Promise<Map<string, TranscriptionResult | Error>> {
  const service = new TranscriptionService(process.env.DEEPGRAM_API_KEY!);
  const results = new Map<string, TranscriptionResult | Error>();
  const concurrency = options.concurrency || 5;

  // Process in batches
  for (let i = 0; i < files.length; i += concurrency) {
    const batch = files.slice(i, i + concurrency);

    const batchResults = await Promise.allSettled(
      batch.map(file => service.transcribeFile(file))
    );

    batchResults.forEach((result, index) => {
      const file = batch[index];
      if (result.status === 'fulfilled') {
        results.set(file, result.value);
      } else {
        results.set(file, result.reason);
      }
    });
  }

  return results;
}
```

### Speaker Diarization
```typescript
// Example with speaker diarization
const result = await service.transcribeFile('./meeting.wav', {
  diarize: true,
  utterances: true,
});

// Format as conversation
result.utterances?.forEach(utterance => {
  console.log(`Speaker ${utterance.speaker}: ${utterance.transcript}`);
});
```

### Python Example
```python
# services/transcription.py
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from pathlib import Path
from typing import Optional
import mimetypes

class TranscriptionService:
    def __init__(self, api_key: str):
        self.client = DeepgramClient(api_key)

    def transcribe_url(
        self,
        url: str,
        model: str = 'nova-2',
        language: str = 'en',
        diarize: bool = False
    ) -> dict:
        options = PrerecordedOptions(
            model=model,
            language=language,
            smart_format=True,
            punctuate=True,
            diarize=diarize,
        )

        response = self.client.listen.rest.v("1").transcribe_url(
            {"url": url},
            options
        )

        return self._format_result(response)

    def transcribe_file(
        self,
        file_path: str,
        model: str = 'nova-2',
        diarize: bool = False
    ) -> dict:
        with open(file_path, 'rb') as f:
            audio = f.read()

        mimetype, _ = mimetypes.guess_type(file_path)

        source = FileSource(audio, mimetype or 'audio/wav')

        options = PrerecordedOptions(
            model=model,
            smart_format=True,
            punctuate=True,
            diarize=diarize,
        )

        response = self.client.listen.rest.v("1").transcribe_file(
            source,
            options
        )

        return self._format_result(response)

    def _format_result(self, response) -> dict:
        channel = response.results.channels[0]
        alternative = channel.alternatives[0]

        return {
            'transcript': alternative.transcript,
            'confidence': alternative.confidence,
            'words': alternative.words,
        }
```

## Resources
- [Deepgram Pre-recorded API](https://developers.deepgram.com/docs/getting-started-with-pre-recorded-audio)
- [Deepgram Models](https://developers.deepgram.com/docs/models)
- [Speaker Diarization](https://developers.deepgram.com/docs/diarization)

## Next Steps
Proceed to `deepgram-core-workflow-b` for real-time streaming transcription.