# TwinMind Performance Tuning - Detailed Implementation

## Performance Metrics

```typescript
export interface TranscriptionMetrics {
  wordErrorRate: number;          // Ear-3: ~5.26%
  diarizationErrorRate: number;   // ~3.8%
  confidenceScore: number;
  processingTime: number;
  realtimeFactor: number;         // ~0.3x
  firstWordLatency: number;       // ~300ms
  speakerCount: number;
  noiseLevel: string;
}

export function analyzePerformance(metrics: TranscriptionMetrics): string[] {
  const recommendations: string[] = [];
  if (metrics.wordErrorRate > 0.10) recommendations.push('High WER - improve audio quality');
  if (metrics.diarizationErrorRate > 0.05) recommendations.push('Speaker labeling issues - ensure clear audio');
  if (metrics.realtimeFactor > 0.5) recommendations.push('Slow processing - consider model optimization');
  if (metrics.noiseLevel === 'high') recommendations.push('High noise - apply noise reduction');
  return recommendations;
}
```

## Audio Preprocessing

```typescript
import ffmpeg from 'fluent-ffmpeg';

export async function preprocessAudio(inputPath: string, outputPath: string, options = {}): Promise<void> {
  const opts = { targetSampleRate: 16000, channels: 1, noiseReduction: true, normalization: true, format: 'mp3', ...options };

  return new Promise((resolve, reject) => {
    let command = ffmpeg(inputPath).audioFrequency(opts.targetSampleRate).audioChannels(opts.channels);

    if (opts.noiseReduction) {
      command = command.audioFilters(['highpass=f=200', 'lowpass=f=3000', 'afftdn=nf=-25']);
    }
    if (opts.normalization) {
      command = command.audioFilters(['loudnorm=I=-16:TP=-1.5:LRA=11']);
    }

    command.toFormat(opts.format).on('end', resolve).on('error', reject).save(outputPath);
  });
}

export async function assessAudioQuality(filePath: string) {
  const issues: string[] = [];
  const recommendations: string[] = [];
  const metadata = await getAudioMetadata(filePath);

  if (metadata.sampleRate < 16000) { issues.push(`Low sample rate: ${metadata.sampleRate} Hz`); recommendations.push('Use 16 kHz or higher'); }
  if (metadata.peakLevel > -1) { issues.push('Audio clipping'); recommendations.push('Reduce recording volume'); }
  if (metadata.noiseFloor > -40) { issues.push(`High noise floor: ${metadata.noiseFloor} dB`); recommendations.push('Use noise reduction'); }

  return { quality: issues.length === 0 ? 'excellent' : issues.length <= 1 ? 'good' : 'fair', issues, recommendations };
}
```

## Model Configurations

```typescript
export const modelConfigs: Record<string, ModelConfig> = {
  meeting: {
    model: 'ear-3', language: 'auto', diarization: true, punctuation: true, profanityFilter: false,
  },
  technical: {
    model: 'ear-3', language: 'en', diarization: true, punctuation: true, profanityFilter: false,
    vocabulary: ['API', 'SDK', 'microservice', 'Kubernetes', 'Docker', 'CI/CD', 'GraphQL', 'PostgreSQL'],
  },
  callCenter: {
    model: 'ear-3', language: 'auto', diarization: true, punctuation: true, profanityFilter: true,
  },
  medical: {
    model: 'ear-3-custom', language: 'en', diarization: true, punctuation: true, profanityFilter: false,
    vocabulary: ['diagnosis', 'prognosis', 'contraindication', 'hematology', 'cardiology'],
  },
  lecture: {
    model: 'ear-3', language: 'auto', diarization: false, punctuation: true, profanityFilter: false,
  },
  podcast: {
    model: 'ear-3', language: 'auto', diarization: true, punctuation: true, profanityFilter: false,
  },
};

export function getOptimalConfig(useCase: string): ModelConfig {
  return modelConfigs[useCase] || modelConfigs.meeting;
}
```

## Streaming Optimization

```typescript
export class OptimizedStreamingClient {
  private buffer: Float32Array[] = [];
  private config = { chunkDurationMs: 100, overlapMs: 50, maxBufferMs: 5000, interimResults: true };

  async processChunk(audioChunk: Float32Array): Promise<{ interim?: string; final?: string; confidence: number }> {
    this.buffer.push(audioChunk);
    const totalMs = this.buffer.length * this.config.chunkDurationMs;

    if (totalMs >= this.config.chunkDurationMs * 3) {
      const result = await this.sendToApi(this.concatenateBuffer());
      if (result.isFinal) {
        this.buffer = [];
        return { final: result.text, confidence: result.confidence };
      }
      this.trimBuffer();
      return { interim: result.text, confidence: result.confidence };
    }
    return { confidence: 0 };
  }

  private concatenateBuffer(): Float32Array {
    const total = this.buffer.reduce((sum, arr) => sum + arr.length, 0);
    const result = new Float32Array(total);
    let offset = 0;
    for (const arr of this.buffer) { result.set(arr, offset); offset += arr.length; }
    return result;
  }

  private trimBuffer(): void {
    if (this.buffer.length > 2) this.buffer = this.buffer.slice(-2);
  }
}
```

## Caching and Deduplication

```typescript
import crypto from 'crypto';

class TranscriptCache {
  private cache = new Map<string, { transcriptId: string; expiresAt: Date }>();
  private ttlMs = 24 * 60 * 60 * 1000;

  async hashAudio(audioUrl: string): Promise<string> {
    const response = await fetch(audioUrl);
    const buffer = await response.arrayBuffer();
    return crypto.createHash('sha256').update(Buffer.from(buffer)).digest('hex');
  }

  get(hash: string): string | null {
    const cached = this.cache.get(hash);
    if (!cached || new Date() > cached.expiresAt) { this.cache.delete(hash); return null; }
    return cached.transcriptId;
  }

  set(hash: string, transcriptId: string): void {
    this.cache.set(hash, { transcriptId, expiresAt: new Date(Date.now() + this.ttlMs) });
  }

  async transcribeWithCache(audioUrl: string): Promise<string> {
    const hash = await this.hashAudio(audioUrl);
    const cached = this.get(hash);
    if (cached) { console.log(`Cache hit: ${hash.substring(0, 8)}...`); return cached; }

    const client = getTwinMindClient();
    const result = await client.transcribe(audioUrl);
    this.set(hash, result.id);
    return result.id;
  }
}

export const transcriptCache = new TranscriptCache();
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
