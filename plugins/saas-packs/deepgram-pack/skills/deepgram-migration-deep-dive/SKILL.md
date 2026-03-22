---
name: deepgram-migration-deep-dive
description: |
  Deep dive into migrating to Deepgram from other transcription providers.
  Use when migrating from AWS Transcribe, Google Cloud STT, Azure Speech,
  OpenAI Whisper, AssemblyAI, or Rev.ai to Deepgram.
  Trigger: "deepgram migration", "switch to deepgram", "migrate transcription",
  "deepgram from AWS", "deepgram from Google", "replace whisper with deepgram".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, migration, transcription]

---
# Deepgram Migration Deep Dive

## Current State
!`npm list @deepgram/sdk 2>/dev/null | grep deepgram || echo 'Not installed'`
!`npm list @aws-sdk/client-transcribe 2>/dev/null | grep transcribe || echo 'AWS Transcribe SDK not found'`
!`pip show google-cloud-speech 2>/dev/null | grep Version || echo 'Google STT not found'`

## Overview
Migrate to Deepgram from AWS Transcribe, Google Cloud Speech-to-Text, Azure Cognitive Services, or OpenAI Whisper. Uses an adapter pattern with a unified interface, parallel running for quality validation, percentage-based traffic shifting, and automated rollback.

## Feature Mapping

### AWS Transcribe -> Deepgram
| AWS Transcribe | Deepgram | Notes |
|----------------|----------|-------|
| `LanguageCode: 'en-US'` | `language: 'en'` | ISO 639-1 (2-letter) |
| `ShowSpeakerLabels: true` | `diarize: true` | Same feature, different param |
| `VocabularyName: 'custom'` | `keywords: ['term:1.5']` | Inline boosting, no pre-upload |
| `ContentRedactionType: 'PII'` | `redact: ['pci', 'ssn']` | Granular PII categories |
| `OutputBucketName` | `callback: 'https://...'` | Callback URL, not S3 |
| Job polling model | Sync response or callback | No polling needed |

### Google Cloud STT -> Deepgram
| Google STT | Deepgram | Notes |
|------------|----------|-------|
| `RecognitionConfig.encoding` | Auto-detected | Deepgram auto-detects format |
| `RecognitionConfig.sampleRateHertz` | `sample_rate` (live only) | REST auto-detects |
| `RecognitionConfig.model: 'latest_long'` | `model: 'nova-3'` | Direct mapping |
| `SpeakerDiarizationConfig` | `diarize: true` | Simpler configuration |
| `StreamingRecognize` | `listen.live()` | WebSocket vs gRPC |

### OpenAI Whisper -> Deepgram
| Whisper | Deepgram | Notes |
|---------|----------|-------|
| Local GPU processing | API call | No GPU needed |
| `whisper.transcribe(audio)` | `listen.prerecorded.transcribeFile()` | Similar interface |
| `model='large-v3'` | `model: 'nova-3'` | 10-100x faster |
| `language='en'` | `language: 'en'` | Same format |
| No diarization | `diarize: true` | Deepgram advantage |
| No streaming | `listen.live()` | Deepgram advantage |

## Instructions

### Step 1: Adapter Pattern

```typescript
interface TranscriptionResult {
  transcript: string;
  confidence: number;
  words: Array<{ word: string; start: number; end: number; speaker?: number }>;
  duration: number;
  provider: string;
}

interface TranscriptionAdapter {
  transcribeUrl(url: string, options: any): Promise<TranscriptionResult>;
  transcribeFile(path: string, options: any): Promise<TranscriptionResult>;
  name: string;
}
```

### Step 2: Deepgram Adapter

```typescript
import { createClient } from '@deepgram/sdk';
import { readFileSync } from 'fs';

class DeepgramAdapter implements TranscriptionAdapter {
  name = 'deepgram';
  private client: ReturnType<typeof createClient>;

  constructor(apiKey: string) {
    this.client = createClient(apiKey);
  }

  async transcribeUrl(url: string, options: any = {}): Promise<TranscriptionResult> {
    const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
      { url },
      {
        model: options.model ?? 'nova-3',
        smart_format: true,
        diarize: options.diarize ?? false,
        language: options.language ?? 'en',
        keywords: options.keywords,
        redact: options.redact,
      }
    );
    if (error) throw new Error(`Deepgram: ${error.message}`);
    return this.normalize(result);
  }

  async transcribeFile(path: string, options: any = {}): Promise<TranscriptionResult> {
    const audio = readFileSync(path);
    const { result, error } = await this.client.listen.prerecorded.transcribeFile(
      audio,
      {
        model: options.model ?? 'nova-3',
        smart_format: true,
        diarize: options.diarize ?? false,
      }
    );
    if (error) throw new Error(`Deepgram: ${error.message}`);
    return this.normalize(result);
  }

  private normalize(result: any): TranscriptionResult {
    const alt = result.results.channels[0].alternatives[0];
    return {
      transcript: alt.transcript,
      confidence: alt.confidence,
      words: (alt.words ?? []).map((w: any) => ({
        word: w.punctuated_word ?? w.word,
        start: w.start,
        end: w.end,
        speaker: w.speaker,
      })),
      duration: result.metadata.duration,
      provider: 'deepgram',
    };
  }
}
```

### Step 3: AWS Transcribe Adapter (Legacy)

```typescript
// Legacy adapter — wraps existing AWS Transcribe code for parallel running
import { TranscribeClient, StartTranscriptionJobCommand, GetTranscriptionJobCommand }
  from '@aws-sdk/client-transcribe';

class AWSTranscribeAdapter implements TranscriptionAdapter {
  name = 'aws-transcribe';
  private client: TranscribeClient;

  constructor() {
    this.client = new TranscribeClient({});
  }

  async transcribeUrl(url: string, options: any = {}): Promise<TranscriptionResult> {
    const jobName = `migration-${Date.now()}`;

    await this.client.send(new StartTranscriptionJobCommand({
      TranscriptionJobName: jobName,
      LanguageCode: options.language ?? 'en-US',
      Media: { MediaFileUri: url },
      Settings: {
        ShowSpeakerLabels: options.diarize ?? false,
        MaxSpeakerLabels: options.diarize ? 10 : undefined,
      },
    }));

    // Poll for completion (AWS is async-only)
    let job;
    do {
      await new Promise(r => setTimeout(r, 5000));
      const result = await this.client.send(new GetTranscriptionJobCommand({
        TranscriptionJobName: jobName,
      }));
      job = result.TranscriptionJob;
    } while (job?.TranscriptionJobStatus === 'IN_PROGRESS');

    if (job?.TranscriptionJobStatus !== 'COMPLETED') {
      throw new Error(`AWS Transcribe failed: ${job?.FailureReason}`);
    }

    // Fetch and normalize result
    const response = await fetch(job.Transcript!.TranscriptFileUri!);
    const data = await response.json();

    return {
      transcript: data.results.transcripts[0].transcript,
      confidence: 0, // AWS doesn't provide overall confidence
      words: data.results.items
        .filter((i: any) => i.type === 'pronunciation')
        .map((i: any) => ({
          word: i.alternatives[0].content,
          start: parseFloat(i.start_time),
          end: parseFloat(i.end_time),
          speaker: i.speaker_label ? parseInt(i.speaker_label.replace('spk_', '')) : undefined,
        })),
      duration: 0,
      provider: 'aws-transcribe',
    };
  }

  async transcribeFile(path: string): Promise<TranscriptionResult> {
    throw new Error('Upload to S3 first, then use transcribeUrl');
  }
}
```

### Step 4: Migration Router with Traffic Shifting

```typescript
class MigrationRouter {
  private adapters: Map<string, TranscriptionAdapter> = new Map();
  private deepgramPercent: number;

  constructor(deepgramPercent = 0) {
    this.deepgramPercent = deepgramPercent;
  }

  register(adapter: TranscriptionAdapter) {
    this.adapters.set(adapter.name, adapter);
  }

  setDeepgramPercent(percent: number) {
    this.deepgramPercent = Math.max(0, Math.min(100, percent));
    console.log(`Traffic split: ${this.deepgramPercent}% Deepgram, ${100 - this.deepgramPercent}% legacy`);
  }

  async transcribe(url: string, options: any = {}): Promise<TranscriptionResult> {
    const useDeepgram = Math.random() * 100 < this.deepgramPercent;
    const primary = useDeepgram ? 'deepgram' : this.getLegacyName();
    const adapter = this.adapters.get(primary);

    if (!adapter) throw new Error(`Adapter not found: ${primary}`);

    const start = Date.now();
    const result = await adapter.transcribeUrl(url, options);
    const elapsed = Date.now() - start;

    console.log(`[${primary}] ${elapsed}ms, confidence: ${result.confidence.toFixed(3)}`);
    return result;
  }

  private getLegacyName(): string {
    for (const [name] of this.adapters) {
      if (name !== 'deepgram') return name;
    }
    throw new Error('No legacy adapter registered');
  }
}

// Migration rollout:
const router = new MigrationRouter(0);
router.register(new AWSTranscribeAdapter());
router.register(new DeepgramAdapter(process.env.DEEPGRAM_API_KEY!));

// Week 1: 5% to Deepgram
router.setDeepgramPercent(5);
// Week 2: 25%
router.setDeepgramPercent(25);
// Week 3: 50%
router.setDeepgramPercent(50);
// Week 4: 100% — migration complete
router.setDeepgramPercent(100);
```

### Step 5: Parallel Running and Quality Validation

```typescript
async function validateMigration(
  testAudioUrls: string[],
  legacyAdapter: TranscriptionAdapter,
  deepgramAdapter: TranscriptionAdapter,
  minSimilarity = 0.85
) {
  console.log(`Validating ${testAudioUrls.length} files (min similarity: ${minSimilarity})`);

  const results: Array<{
    url: string;
    similarity: number;
    legacyConfidence: number;
    deepgramConfidence: number;
    legacyTime: number;
    deepgramTime: number;
    pass: boolean;
  }> = [];

  for (const url of testAudioUrls) {
    const legacyStart = Date.now();
    const legacy = await legacyAdapter.transcribeUrl(url);
    const legacyTime = Date.now() - legacyStart;

    const dgStart = Date.now();
    const dg = await deepgramAdapter.transcribeUrl(url);
    const dgTime = Date.now() - dgStart;

    // Jaccard similarity
    const words1 = new Set(legacy.transcript.toLowerCase().split(/\s+/));
    const words2 = new Set(dg.transcript.toLowerCase().split(/\s+/));
    const intersection = new Set([...words1].filter(w => words2.has(w)));
    const union = new Set([...words1, ...words2]);
    const similarity = intersection.size / union.size;

    results.push({
      url: url.substring(url.lastIndexOf('/') + 1),
      similarity,
      legacyConfidence: legacy.confidence,
      deepgramConfidence: dg.confidence,
      legacyTime,
      deepgramTime,
      pass: similarity >= minSimilarity,
    });
  }

  // Report
  const passCount = results.filter(r => r.pass).length;
  console.log(`\n=== Validation Results ===`);
  for (const r of results) {
    console.log(`${r.pass ? 'PASS' : 'FAIL'} ${r.url}: similarity=${(r.similarity * 100).toFixed(1)}% ` +
      `(legacy: ${r.legacyTime}ms, deepgram: ${r.deepgramTime}ms)`);
  }
  console.log(`\n${passCount}/${results.length} passed (${(passCount / results.length * 100).toFixed(0)}%)`);

  return { results, allPassed: passCount === results.length };
}
```

### Step 6: Migration Checklist

| Phase | Actions | Duration |
|-------|---------|----------|
| **Assessment** | Audit current usage, map features, estimate costs | 1 week |
| **Setup** | Install SDK, implement adapter pattern, create test suite | 1 week |
| **Validation** | Parallel run on test corpus, measure similarity | 1 week |
| **Rollout 5%** | Enable for 5% of traffic, monitor closely | 1 week |
| **Rollout 25%** | Increase if no issues, monitor error rate | 1 week |
| **Rollout 50%** | Continue monitoring, compare costs | 1 week |
| **Rollout 100%** | Full cutover, decommission legacy | 1 week |
| **Cleanup** | Remove legacy adapter, update docs | 1 week |

## Output
- Unified TranscriptionAdapter interface
- Deepgram and legacy (AWS/Google) adapter implementations
- Migration router with percentage-based traffic shifting
- Parallel running with Jaccard similarity validation
- Migration timeline and checklist

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Low similarity | Feature mapping incomplete | Check options mapping (language, diarize) |
| Deepgram slower than expected | First request cold start | Pre-warm with test request |
| Missing features | No direct equivalent | Use `keywords` for custom vocab |
| Rollback needed | Quality regression | `router.setDeepgramPercent(0)` immediately |

## Resources
- [Deepgram Migration Guide](https://developers.deepgram.com/docs/migration)
- [Feature Comparison](https://deepgram.com/product/speech-to-text)
- [Pricing Calculator](https://deepgram.com/pricing)
- [Model Comparison](https://deepgram.com/learn/model-comparison-when-to-use-nova-2-vs-nova-3-for-devs)
