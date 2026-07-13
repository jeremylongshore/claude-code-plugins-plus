# Deepgram Pre-recorded Transcription Implementation

## TypeScript Transcription Service

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

## Batch Transcription

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

## Python Implementation

```python
# services/transcription.py
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from pathlib import Path
import mimetypes

class TranscriptionService:
    def __init__(self, api_key: str):
        self.client = DeepgramClient(api_key)

    def transcribe_url(self, url: str, model: str = 'nova-2',
                       language: str = 'en', diarize: bool = False) -> dict:
        options = PrerecordedOptions(
            model=model, language=language,
            smart_format=True, punctuate=True, diarize=diarize,
        )
        response = self.client.listen.rest.v("1").transcribe_url({"url": url}, options)
        return self._format_result(response)

    def transcribe_file(self, file_path: str, model: str = 'nova-2',
                        diarize: bool = False) -> dict:
        with open(file_path, 'rb') as f:
            audio = f.read()
        mimetype, _ = mimetypes.guess_type(file_path)
        source = FileSource(audio, mimetype or 'audio/wav')
        options = PrerecordedOptions(
            model=model, smart_format=True, punctuate=True, diarize=diarize,
        )
        response = self.client.listen.rest.v("1").transcribe_file(source, options)
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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
