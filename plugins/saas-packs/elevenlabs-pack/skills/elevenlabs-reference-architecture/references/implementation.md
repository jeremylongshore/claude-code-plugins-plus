# ElevenLabs Reference Architecture — Implementation Walkthrough

Full code for each service layer. Read after the high-level `Instructions` in `SKILL.md`.

## Configuration Layer

```typescript
// src/elevenlabs/config.ts
export interface ElevenLabsConfig {
  apiKey: string;
  environment: "development" | "staging" | "production";
  defaults: {
    modelId: string;
    voiceId: string;
    outputFormat: string;
    voiceSettings: {
      stability: number;
      similarity_boost: number;
      style: number;
      speed: number;
    };
  };
  performance: {
    maxConcurrency: number;
    timeoutMs: number;
    maxRetries: number;
  };
  cache: {
    enabled: boolean;
    maxSizeMB: number;
    ttlSeconds: number;
  };
}

const ENV_CONFIGS: Record<string, Partial<ElevenLabsConfig>> = {
  development: {
    defaults: {
      modelId: "eleven_flash_v2_5",    // Cheap + fast for dev
      voiceId: "21m00Tcm4TlvDq8ikWAM", // Rachel
      outputFormat: "mp3_22050_32",     // Small files
      voiceSettings: { stability: 0.5, similarity_boost: 0.75, style: 0, speed: 1 },
    },
    performance: { maxConcurrency: 2, timeoutMs: 30_000, maxRetries: 1 },
    cache: { enabled: true, maxSizeMB: 50, ttlSeconds: 3600 },
  },
  production: {
    defaults: {
      modelId: "eleven_multilingual_v2", // High quality for prod
      voiceId: "21m00Tcm4TlvDq8ikWAM",
      outputFormat: "mp3_44100_128",     // High quality
      voiceSettings: { stability: 0.5, similarity_boost: 0.75, style: 0, speed: 1 },
    },
    performance: { maxConcurrency: 10, timeoutMs: 60_000, maxRetries: 3 },
    cache: { enabled: true, maxSizeMB: 500, ttlSeconds: 86_400 },
  },
};

export function loadConfig(): ElevenLabsConfig {
  const env = process.env.NODE_ENV || "development";
  const envConfig = ENV_CONFIGS[env] || ENV_CONFIGS.development;

  return {
    apiKey: process.env.ELEVENLABS_API_KEY!,
    environment: env as any,
    ...envConfig,
  } as ElevenLabsConfig;
}
```

## TTS Service Layer

```typescript
// src/services/tts-service.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import PQueue from "p-queue";
import { loadConfig } from "../elevenlabs/config";
import { classifyError } from "../elevenlabs/errors";

export class TTSService {
  private client: ElevenLabsClient;
  private queue: PQueue;
  private config: ReturnType<typeof loadConfig>;

  constructor() {
    this.config = loadConfig();
    this.client = new ElevenLabsClient({
      apiKey: this.config.apiKey,
      maxRetries: this.config.performance.maxRetries,
      timeoutInSeconds: this.config.performance.timeoutMs / 1000,
    });
    this.queue = new PQueue({
      concurrency: this.config.performance.maxConcurrency,
    });
  }

  async generate(text: string, options?: {
    voiceId?: string;
    modelId?: string;
    outputFormat?: string;
    streaming?: boolean;
  }): Promise<ReadableStream | Buffer> {
    const voiceId = options?.voiceId || this.config.defaults.voiceId;
    const modelId = options?.modelId || this.config.defaults.modelId;
    const format = options?.outputFormat || this.config.defaults.outputFormat;

    return this.queue.add(async () => {
      const start = performance.now();

      try {
        if (options?.streaming) {
          return await this.client.textToSpeech.stream(voiceId, {
            text,
            model_id: modelId,
            output_format: format,
            voice_settings: this.config.defaults.voiceSettings,
          });
        }

        const audio = await this.client.textToSpeech.convert(voiceId, {
          text,
          model_id: modelId,
          output_format: format,
          voice_settings: this.config.defaults.voiceSettings,
        });

        const latency = performance.now() - start;
        console.log(`[TTS] ${text.length} chars, ${modelId}, ${latency.toFixed(0)}ms`);
        return audio;
      } catch (error) {
        throw classifyError(error);
      }
    }) as Promise<ReadableStream | Buffer>;
  }

  // Split long text into chunks with prosody context
  async generateLongText(text: string, voiceId?: string): Promise<Buffer[]> {
    const chunks = this.splitText(text, 4500); // Stay under 5000 limit
    const results: Buffer[] = [];

    for (let i = 0; i < chunks.length; i++) {
      const audio = await this.generate(chunks[i], {
        voiceId,
        // Pass context for natural prosody across chunks
      });
      results.push(audio as Buffer);
    }

    return results;
  }

  private splitText(text: string, maxChars: number): string[] {
    const chunks: string[] = [];
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    let current = "";

    for (const sentence of sentences) {
      if ((current + sentence).length > maxChars) {
        if (current) chunks.push(current.trim());
        current = sentence;
      } else {
        current += sentence;
      }
    }
    if (current) chunks.push(current.trim());
    return chunks;
  }
}
```

## Voice Management Service

```typescript
// src/services/voice-service.ts
export class VoiceService {
  private client: ElevenLabsClient;

  constructor(client: ElevenLabsClient) {
    this.client = client;
  }

  async listVoices(filter?: { category?: "premade" | "cloned" | "generated" }) {
    const { voices } = await this.client.voices.getAll();
    if (filter?.category) {
      return voices.filter(v => v.category === filter.category);
    }
    return voices;
  }

  async cloneVoice(name: string, description: string, audioFiles: NodeJS.ReadableStream[]) {
    return this.client.voices.add({
      name,
      description,
      files: audioFiles,
    });
  }

  async getVoiceSettings(voiceId: string) {
    return this.client.voices.getSettings(voiceId);
  }

  async updateVoiceSettings(voiceId: string, settings: {
    stability: number;
    similarity_boost: number;
  }) {
    return this.client.voices.editSettings(voiceId, settings);
  }

  async deleteVoice(voiceId: string) {
    return this.client.voices.delete(voiceId);
  }
}
```

## Health Check Composition

```typescript
// src/api/routes/health.ts
export async function healthCheck() {
  const checks = await Promise.allSettled([
    checkElevenLabsConnectivity(),
    checkQuotaStatus(),
    checkCacheHealth(),
  ]);

  const elevenlabs = checks[0].status === "fulfilled" ? checks[0].value : null;
  const quota = checks[1].status === "fulfilled" ? checks[1].value : null;
  const cache = checks[2].status === "fulfilled" ? checks[2].value : null;

  const degraded = !elevenlabs || (quota && quota.pctUsed > 90);

  return {
    status: !elevenlabs ? "unhealthy" : degraded ? "degraded" : "healthy",
    services: { elevenlabs, quota, cache },
    timestamp: new Date().toISOString(),
  };
}
```
