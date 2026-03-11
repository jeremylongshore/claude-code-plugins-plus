# Deepgram Migration Deep Dive - Implementation Details

## Migration Adapter Pattern
```typescript
export interface TranscriptionResult {
  transcript: string;
  confidence: number;
  words?: Array<{ word: string; start: number; end: number; confidence: number }>;
  speakers?: Array<{ speaker: number; start: number; end: number }>;
  language?: string;
  provider: string;
}

export interface TranscriptionAdapter {
  name: string;
  transcribe(audioUrl: string, options: TranscriptionOptions): Promise<TranscriptionResult>;
  transcribeFile(audioBuffer: Buffer, options: TranscriptionOptions): Promise<TranscriptionResult>;
}
```

## Deepgram Adapter
```typescript
import { createClient } from '@deepgram/sdk';

export class DeepgramAdapter implements TranscriptionAdapter {
  name = 'deepgram';
  private client;

  constructor(apiKey: string) { this.client = createClient(apiKey); }

  async transcribe(audioUrl: string, options: TranscriptionOptions): Promise<TranscriptionResult> {
    const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
      { url: audioUrl },
      { model: 'nova-2', language: options.language || 'en', diarize: options.diarization ?? false, punctuate: options.punctuation ?? true, smart_format: true }
    );
    if (error) throw error;
    return this.normalizeResult(result);
  }

  private normalizeResult(result: any): TranscriptionResult {
    const channel = result.results.channels[0];
    const alternative = channel.alternatives[0];
    return {
      transcript: alternative.transcript,
      confidence: alternative.confidence,
      words: alternative.words?.map((w: any) => ({ word: w.punctuated_word || w.word, start: w.start, end: w.end, confidence: w.confidence })),
      language: channel.detected_language,
      provider: this.name,
    };
  }
}
```

## AWS Transcribe Adapter (for comparison)
```typescript
import { TranscribeClient, StartTranscriptionJobCommand, GetTranscriptionJobCommand } from '@aws-sdk/client-transcribe';

export class AWSTranscribeAdapter implements TranscriptionAdapter {
  name = 'aws-transcribe';
  private transcribe: TranscribeClient;

  constructor() { this.transcribe = new TranscribeClient({}); }

  async transcribe(audioUrl: string, options: TranscriptionOptions): Promise<TranscriptionResult> {
    const jobName = `job-${Date.now()}`;
    await this.transcribe.send(new StartTranscriptionJobCommand({
      TranscriptionJobName: jobName,
      Media: { MediaFileUri: audioUrl },
      LanguageCode: options.language || 'en-US',
    }));
    const result = await this.waitForJob(jobName);
    return this.normalizeResult(result);
  }
  // ... polling and normalization
}
```

## Migration Router
```typescript
export class MigrationRouter {
  private deepgram: TranscriptionAdapter;
  private legacy: TranscriptionAdapter;
  private config: MigrationConfig;

  async transcribe(audioUrl: string, options: TranscriptionOptions): Promise<TranscriptionResult> {
    const useDeepgram = Math.random() * 100 < this.config.deepgramPercentage;
    if (this.config.compareResults) {
      const [deepgramResult, legacyResult] = await Promise.all([
        this.deepgram.transcribe(audioUrl, options).catch(() => null),
        this.legacy.transcribe(audioUrl, options).catch(() => null),
      ]);
      if (deepgramResult && legacyResult) this.compareAndLog(deepgramResult, legacyResult, audioUrl);
      if (useDeepgram && deepgramResult) return deepgramResult;
      if (legacyResult) return legacyResult;
      throw new Error('Both providers failed');
    }
    return (useDeepgram ? this.deepgram : this.legacy).transcribe(audioUrl, options);
  }

  private calculateSimilarity(a: string, b: string): number {
    const setA = new Set(a.toLowerCase().split(/\s+/));
    const setB = new Set(b.toLowerCase().split(/\s+/));
    const intersection = new Set([...setA].filter(x => setB.has(x)));
    const union = new Set([...setA, ...setB]);
    return intersection.size / union.size;
  }
}
```

## Feature Mapping
```typescript
export const awsToDeepgram: FeatureMap[] = [
  { source: 'LanguageCode: en-US', deepgram: 'language: "en"', notes: 'ISO 639-1 codes' },
  { source: 'ShowSpeakerLabels: true', deepgram: 'diarize: true', notes: 'Similar functionality' },
  { source: 'VocabularyName: custom', deepgram: 'keywords: ["term:1.5"]', notes: 'Use keywords with boost' },
  { source: 'ContentRedaction', deepgram: 'redact: ["pci", "ssn"]', notes: 'Built-in PII redaction' },
];

export const googleToDeepgram: FeatureMap[] = [
  { source: 'encoding: LINEAR16', deepgram: 'mimetype: "audio/wav"', notes: 'Auto-detected' },
  { source: 'enableWordTimeOffsets: true', deepgram: 'Default behavior', notes: 'Always included' },
  { source: 'enableAutomaticPunctuation: true', deepgram: 'punctuate: true', notes: 'Same functionality' },
  { source: 'model: video', deepgram: 'model: "nova-2"', notes: 'Nova-2 handles all use cases' },
];
```

## Migration Validation & Rollback
See the full validation script, rollback manager, and migration checklist in the detailed implementation guide.
