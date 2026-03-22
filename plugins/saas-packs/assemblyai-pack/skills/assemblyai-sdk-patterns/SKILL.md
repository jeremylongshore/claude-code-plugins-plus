---
name: assemblyai-sdk-patterns
description: |
  Apply production-ready AssemblyAI SDK patterns for TypeScript and Python.
  Use when implementing AssemblyAI integrations, refactoring SDK usage,
  or establishing team coding standards for transcription workflows.
  Trigger with phrases like "assemblyai SDK patterns", "assemblyai best practices",
  "assemblyai code patterns", "idiomatic assemblyai".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI SDK Patterns

## Overview
Production-ready patterns for the `assemblyai` npm package covering client initialization, type-safe wrappers, error handling, and multi-tenant architectures.

## Prerequisites
- `assemblyai` package installed (`npm install assemblyai`)
- Familiarity with async/await and TypeScript generics

## Instructions

### Step 1: Type-Safe Singleton Client

```typescript
// src/assemblyai/client.ts
import { AssemblyAI } from 'assemblyai';

let instance: AssemblyAI | null = null;

export function getAssemblyAI(): AssemblyAI {
  if (!instance) {
    const apiKey = process.env.ASSEMBLYAI_API_KEY;
    if (!apiKey) throw new Error('ASSEMBLYAI_API_KEY is required');
    instance = new AssemblyAI({ apiKey });
  }
  return instance;
}
```

### Step 2: Transcription Service Wrapper

```typescript
// src/assemblyai/transcription-service.ts
import { AssemblyAI, type Transcript, type TranscriptParams } from 'assemblyai';

export interface TranscriptionResult {
  id: string;
  text: string;
  duration: number;
  words: Array<{ text: string; start: number; end: number; confidence: number }>;
  speakers?: Array<{ speaker: string; text: string }>;
}

export class TranscriptionService {
  constructor(private client: AssemblyAI) {}

  async transcribe(
    audio: string,
    options: Partial<TranscriptParams> = {}
  ): Promise<TranscriptionResult> {
    const transcript = await this.client.transcripts.transcribe({
      audio,
      ...options,
    });

    if (transcript.status === 'error') {
      throw new Error(`Transcription failed: ${transcript.error}`);
    }

    return {
      id: transcript.id,
      text: transcript.text ?? '',
      duration: transcript.audio_duration ?? 0,
      words: (transcript.words ?? []).map(w => ({
        text: w.text,
        start: w.start,
        end: w.end,
        confidence: w.confidence,
      })),
      speakers: transcript.utterances?.map(u => ({
        speaker: u.speaker,
        text: u.text,
      })),
    };
  }

  async getTranscript(id: string): Promise<Transcript> {
    return this.client.transcripts.get(id);
  }

  async listTranscripts(params?: { limit?: number; status?: string }) {
    const page = await this.client.transcripts.list(params);
    return page.transcripts;
  }

  async deleteTranscript(id: string): Promise<void> {
    await this.client.transcripts.delete(id);
  }
}
```

### Step 3: Error Handling Wrapper

```typescript
// src/assemblyai/errors.ts

export class AssemblyAIServiceError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number,
    public readonly retryable: boolean = false,
    public readonly transcriptId?: string
  ) {
    super(message);
    this.name = 'AssemblyAIServiceError';
  }
}

export async function safeTranscribe<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: AssemblyAIServiceError | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err: any) {
    const statusCode = err.status ?? err.statusCode;
    const retryable = statusCode === 429 || (statusCode >= 500 && statusCode < 600);

    return {
      data: null,
      error: new AssemblyAIServiceError(
        err.message ?? 'Unknown AssemblyAI error',
        statusCode,
        retryable
      ),
    };
  }
}

// Usage
const { data, error } = await safeTranscribe(() =>
  client.transcripts.transcribe({ audio: audioUrl })
);
if (error?.retryable) {
  // Implement retry logic
}
```

### Step 4: Retry with Exponential Backoff

```typescript
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      if (attempt === maxRetries) throw err;

      const status = err.status ?? err.statusCode;
      // Only retry on rate limits (429) and server errors (5xx)
      if (status && status !== 429 && (status < 500 || status >= 600)) throw err;

      const delay = baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;
      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}

// Usage
const transcript = await withRetry(() =>
  client.transcripts.transcribe({ audio: audioUrl })
);
```

### Step 5: Multi-Tenant Client Factory

```typescript
// For apps serving multiple customers with their own API keys
const clients = new Map<string, AssemblyAI>();

export function getClientForTenant(tenantId: string): AssemblyAI {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId); // from your secrets store
    clients.set(tenantId, new AssemblyAI({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Patterns

```python
import assemblyai as aai
from dataclasses import dataclass
from typing import Optional

aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]

@dataclass
class TranscriptionResult:
    id: str
    text: str
    duration: float
    status: str

def transcribe_audio(audio_url: str, speaker_labels: bool = False) -> TranscriptionResult:
    config = aai.TranscriptionConfig(speaker_labels=speaker_labels)
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_url, config=config)

    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"Transcription failed: {transcript.error}")

    return TranscriptionResult(
        id=transcript.id,
        text=transcript.text,
        duration=transcript.audio_duration,
        status=transcript.status.value,
    )
```

## Output
- Type-safe singleton client with environment validation
- Transcription service wrapper with clean return types
- Error handling wrapper that classifies retryable vs non-retryable errors
- Exponential backoff with jitter for rate limits
- Multi-tenant client factory pattern

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeTranscribe` | All API calls | Prevents uncaught exceptions, classifies errors |
| `withRetry` | Rate-limited operations | Auto-retry on 429 and 5xx |
| Service wrapper | Domain logic | Clean types, hides SDK internals |
| Multi-tenant factory | SaaS apps | Per-customer isolation |

## Resources
- [AssemblyAI Node SDK Reference](https://assemblyai.github.io/assemblyai-node-sdk/)
- [AssemblyAI TypeScript Types](https://github.com/AssemblyAI/assemblyai-node-sdk/tree/main/src/types)
- [AssemblyAI API Reference](https://www.assemblyai.com/docs/api-reference/overview)

## Next Steps
Apply patterns in `assemblyai-core-workflow-a` (async transcription) and `assemblyai-core-workflow-b` (real-time streaming).
