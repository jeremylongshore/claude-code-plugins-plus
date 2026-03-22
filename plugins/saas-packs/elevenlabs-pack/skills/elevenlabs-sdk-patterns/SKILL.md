---
name: elevenlabs-sdk-patterns
description: |
  Apply production-ready ElevenLabs SDK patterns for TypeScript and Python.
  Use when implementing ElevenLabs integrations, refactoring SDK usage,
  or establishing team coding standards for audio AI applications.
  Trigger: "elevenlabs SDK patterns", "elevenlabs best practices",
  "elevenlabs code patterns", "idiomatic elevenlabs", "elevenlabs typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, sdk, patterns]
compatible-with: claude-code
---

# ElevenLabs SDK Patterns

## Overview

Production-ready patterns for the ElevenLabs TypeScript and Python SDKs. Covers singleton clients, type-safe wrappers, error handling, retry logic, and multi-tenant patterns.

## Prerequisites

- `@elevenlabs/elevenlabs-js` installed (TypeScript) or `elevenlabs` (Python)
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Pattern 1: Singleton Client with Config

```typescript
// src/elevenlabs/client.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

let instance: ElevenLabsClient | null = null;

export function getClient(): ElevenLabsClient {
  if (!instance) {
    if (!process.env.ELEVENLABS_API_KEY) {
      throw new Error("ELEVENLABS_API_KEY environment variable is required");
    }
    instance = new ElevenLabsClient({
      apiKey: process.env.ELEVENLABS_API_KEY,
      maxRetries: 3,        // Auto-retry on 429/5xx (default: 2)
      timeoutInSeconds: 60, // Per-request timeout
    });
  }
  return instance;
}

// Reset for testing
export function resetClient(): void {
  instance = null;
}
```

### Pattern 2: Type-Safe TTS Service

```typescript
// src/elevenlabs/tts-service.ts
import { getClient } from "./client";
import { Readable } from "stream";
import { pipeline } from "stream/promises";
import { createWriteStream } from "fs";

export type VoicePreset = "narration" | "conversational" | "dramatic" | "neutral";

const VOICE_PRESETS: Record<VoicePreset, {
  stability: number;
  similarity_boost: number;
  style: number;
}> = {
  narration:      { stability: 0.6, similarity_boost: 0.75, style: 0.0 },
  conversational: { stability: 0.4, similarity_boost: 0.6,  style: 0.3 },
  dramatic:       { stability: 0.3, similarity_boost: 0.8,  style: 0.7 },
  neutral:        { stability: 0.8, similarity_boost: 0.5,  style: 0.0 },
};

export interface TTSOptions {
  voiceId: string;
  text: string;
  modelId?: "eleven_v3" | "eleven_multilingual_v2" | "eleven_flash_v2_5" | "eleven_turbo_v2_5";
  preset?: VoicePreset;
  outputFormat?: string;
  languageCode?: string;
}

export async function generateSpeech(options: TTSOptions): Promise<ReadableStream> {
  const client = getClient();
  const settings = VOICE_PRESETS[options.preset || "narration"];

  return client.textToSpeech.convert(options.voiceId, {
    text: options.text,
    model_id: options.modelId || "eleven_multilingual_v2",
    voice_settings: settings,
    output_format: options.outputFormat || "mp3_44100_128",
    language_code: options.languageCode,
  });
}

export async function generateToFile(options: TTSOptions, outputPath: string): Promise<void> {
  const audio = await generateSpeech(options);
  await pipeline(
    Readable.fromWeb(audio as any),
    createWriteStream(outputPath)
  );
}
```

### Pattern 3: Error Classification

```typescript
// src/elevenlabs/errors.ts
export type ElevenLabsErrorCode =
  | "auth_failed"
  | "quota_exceeded"
  | "rate_limited"
  | "concurrent_limit"
  | "voice_not_found"
  | "invalid_request"
  | "server_error"
  | "network_error";

export class ElevenLabsServiceError extends Error {
  constructor(
    message: string,
    public readonly code: ElevenLabsErrorCode,
    public readonly httpStatus: number | null,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = "ElevenLabsServiceError";
  }
}

export function classifyError(error: unknown): ElevenLabsServiceError {
  if (error instanceof Error) {
    const status = (error as any).statusCode || (error as any).status;

    if (status === 401) {
      const msg = (error as any).body?.detail?.message || error.message;
      if (msg?.includes("quota")) {
        return new ElevenLabsServiceError(msg, "quota_exceeded", 401, false, error);
      }
      return new ElevenLabsServiceError(msg, "auth_failed", 401, false, error);
    }

    if (status === 429) {
      const msg = (error as any).body?.detail?.message || error.message;
      const code = msg?.includes("concurrent") ? "concurrent_limit" : "rate_limited";
      return new ElevenLabsServiceError(msg, code, 429, true, error);
    }

    if (status === 404) {
      return new ElevenLabsServiceError(error.message, "voice_not_found", 404, false, error);
    }

    if (status === 400) {
      return new ElevenLabsServiceError(error.message, "invalid_request", 400, false, error);
    }

    if (status >= 500) {
      return new ElevenLabsServiceError(error.message, "server_error", status, true, error);
    }

    return new ElevenLabsServiceError(error.message, "network_error", null, true, error);
  }

  return new ElevenLabsServiceError(String(error), "network_error", null, true);
}
```

### Pattern 4: Retry with Concurrency Queue

```typescript
// src/elevenlabs/queue.ts
import PQueue from "p-queue";
import { classifyError, ElevenLabsServiceError } from "./errors";

// Concurrency limits by plan:
// Free: 2, Starter: 3, Creator: 5, Pro: 10, Scale: 15
const queue = new PQueue({
  concurrency: 5,    // Match your plan's concurrent request limit
  interval: 1000,    // Window in ms
  intervalCap: 10,   // Max requests per window
});

export async function queuedRequest<T>(
  operation: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  return queue.add(async () => {
    let lastError: ElevenLabsServiceError | undefined;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await operation();
      } catch (err) {
        lastError = classifyError(err);

        if (!lastError.retryable) throw lastError;

        const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
        const jitter = Math.random() * 500;
        await new Promise(r => setTimeout(r, delay + jitter));
      }
    }

    throw lastError;
  }) as Promise<T>;
}
```

### Pattern 5: Multi-Tenant Client Factory

```typescript
// src/elevenlabs/multi-tenant.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const clients = new Map<string, ElevenLabsClient>();

export function getClientForTenant(tenantId: string, apiKey: string): ElevenLabsClient {
  if (!clients.has(tenantId)) {
    clients.set(tenantId, new ElevenLabsClient({
      apiKey,
      maxRetries: 3,
    }));
  }
  return clients.get(tenantId)!;
}

export function removeTenantClient(tenantId: string): void {
  clients.delete(tenantId);
}
```

### Pattern 6: Python Async Pattern

```python
# elevenlabs_service.py
import os
import asyncio
from elevenlabs.client import AsyncElevenLabsClient

_client: AsyncElevenLabsClient | None = None

def get_async_client() -> AsyncElevenLabsClient:
    global _client
    if _client is None:
        _client = AsyncElevenLabsClient(
            api_key=os.environ["ELEVENLABS_API_KEY"]
        )
    return _client

async def generate_speech(text: str, voice_id: str, output_path: str):
    client = get_async_client()
    audio = await client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings={
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    )

    with open(output_path, "wb") as f:
        async for chunk in audio:
            f.write(chunk)

# Usage
asyncio.run(generate_speech("Hello!", "21m00Tcm4TlvDq8ikWAM", "out.mp3"))
```

## Pattern Summary

| Pattern | Use Case | Key Benefit |
|---------|----------|-------------|
| Singleton client | Single-tenant apps | Memory efficiency, shared retries |
| Type-safe TTS | All TTS work | Voice presets, compile-time checks |
| Error classification | Production error handling | Actionable error codes |
| Concurrency queue | High-throughput apps | Respects plan limits automatically |
| Multi-tenant factory | SaaS platforms | Per-customer isolation |
| Python async | Python backends | Non-blocking I/O |

## Error Handling

| Pattern | Error Type | Benefit |
|---------|-----------|---------|
| `classifyError()` | All API errors | Maps HTTP to actionable codes |
| `queuedRequest()` | 429, 5xx | Auto-retry with exponential backoff |
| Singleton guard | Missing env var | Fails fast at startup, not at first call |

## Resources

- [ElevenLabs JS SDK Source](https://github.com/elevenlabs/elevenlabs-js)
- [ElevenLabs Python SDK](https://pypi.org/project/elevenlabs/)
- [p-queue (Concurrency)](https://github.com/sindresorhus/p-queue)

## Next Steps

Apply patterns in `elevenlabs-core-workflow-a` for TTS, or see `elevenlabs-rate-limits` for advanced throttling.
