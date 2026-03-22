---
name: elevenlabs-reference-architecture
description: |
  Implement ElevenLabs reference architecture for production TTS/voice applications.
  Use when designing new ElevenLabs integrations, reviewing project structure,
  or building a scalable audio generation service.
  Trigger: "elevenlabs architecture", "elevenlabs project structure",
  "how to organize elevenlabs", "TTS service architecture",
  "elevenlabs design patterns", "voice API architecture".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, architecture, patterns]
compatible-with: claude-code
---

# ElevenLabs Reference Architecture

## Overview

Production-ready architecture for ElevenLabs TTS/voice applications. Covers project layout, service layers, caching, streaming, and multi-model orchestration.

## Prerequisites

- Understanding of layered architecture patterns
- ElevenLabs SDK knowledge (see `elevenlabs-sdk-patterns`)
- TypeScript project with async patterns
- Redis (optional, for distributed caching)

## Instructions

### Step 1: Project Structure

```
my-elevenlabs-service/
├── src/
│   ├── elevenlabs/
│   │   ├── client.ts            # Singleton client with retry config
│   │   ├── config.ts            # Environment-aware configuration
│   │   ├── models.ts            # Model selection logic
│   │   ├── errors.ts            # Error classification (see sdk-patterns)
│   │   └── types.ts             # TypeScript interfaces
│   ├── services/
│   │   ├── tts-service.ts       # Text-to-Speech orchestration
│   │   ├── voice-service.ts     # Voice management (clone, list, settings)
│   │   ├── audio-service.ts     # SFX, isolation, transcription
│   │   └── cache-service.ts     # Audio caching layer
│   ├── api/
│   │   ├── routes/
│   │   │   ├── tts.ts           # POST /api/tts
│   │   │   ├── voices.ts        # GET/POST /api/voices
│   │   │   ├── webhooks.ts      # POST /webhooks/elevenlabs
│   │   │   └── health.ts        # GET /health
│   │   └── middleware/
│   │       ├── rate-limit.ts    # Request throttling
│   │       └── auth.ts          # Your app's auth (not ElevenLabs auth)
│   ├── queue/
│   │   ├── tts-queue.ts         # Async TTS job processing
│   │   └── workers.ts           # Queue workers
│   └── monitoring/
│       ├── metrics.ts           # Latency, error rate, quota tracking
│       └── alerts.ts            # Budget and health alerts
├── tests/
│   ├── unit/
│   │   ├── tts-service.test.ts
│   │   └── cache-service.test.ts
│   └── integration/
│       └── tts-smoke.test.ts
├── config/
│   ├── development.json
│   ├── staging.json
│   └── production.json
└── .env.example
```

### Step 2: Configuration Layer

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

### Step 3: TTS Service Layer

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

### Step 4: Voice Management Service

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

### Step 5: Data Flow Diagram

```
                         ┌──────────────┐
                         │   Client     │
                         │  (Browser/   │
                         │   Mobile)    │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │   API Layer  │
                         │   /api/tts   │
                         │   /api/voice │
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
             ┌──────▼──┐ ┌─────▼─────┐ ┌──▼──────┐
             │  Cache   │ │   TTS     │ │  Voice  │
             │ Service  │ │  Service  │ │ Service │
             └──────┬───┘ └─────┬─────┘ └────────┘
                    │           │
              ┌─────▼─┐  ┌─────▼──────────┐
              │ Redis/ │  │ Concurrency    │
              │ LRU    │  │ Queue (p-queue)│
              └────────┘  └─────┬──────────┘
                                │
                         ┌──────▼───────┐
                         │  ElevenLabs  │
                         │  Client SDK  │
                         │  (singleton) │
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
             ┌──────▼──┐ ┌─────▼─────┐ ┌──▼──────┐
             │ /v1/tts  │ │ /v1/voices│ │ /v1/sfx │
             │ REST/WS  │ │  REST     │ │  REST   │
             └──────────┘ └───────────┘ └─────────┘
                    ElevenLabs API (api.elevenlabs.io)
```

### Step 6: Health Check Composition

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

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Client pattern | Singleton | One connection pool, shared retry config |
| Concurrency | p-queue | Respects plan limits, prevents 429 |
| Caching | LRU (local) or Redis (distributed) | Repeated content is common in TTS |
| Long text | Sentence-boundary splitting | Preserves natural speech prosody |
| Error handling | Classification + retry | Different strategies for 429 vs 401 vs 500 |
| Model selection | Environment-based | Flash in dev (cheap), Multilingual in prod (quality) |
| Streaming | HTTP streaming + WebSocket | HTTP for simple, WS for LLM integration |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Services depend on client, never reverse |
| Cold start latency | Client initialization | Pre-warm in server startup |
| Memory pressure | Unbounded audio cache | Set `maxSizeMB` on cache |
| Type errors | SDK version mismatch | Pin SDK version in package.json |

## Resources

- [ElevenLabs API Reference](https://elevenlabs.io/docs/api-reference/introduction)
- [ElevenLabs SDK Source](https://github.com/elevenlabs/elevenlabs-js)
- [p-queue](https://github.com/sindresorhus/p-queue)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)

## Next Steps

Start with `elevenlabs-install-auth` for setup, then apply this architecture. Use `elevenlabs-core-workflow-a` and `elevenlabs-core-workflow-b` for feature implementation.
