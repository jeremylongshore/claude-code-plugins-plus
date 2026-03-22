---
name: mistral-reference-architecture
description: |
  Implement Mistral AI reference architecture with best-practice project layout.
  Use when designing new Mistral AI integrations, reviewing project structure,
  or establishing architecture standards for Mistral AI applications.
  Trigger with phrases like "mistral architecture", "mistral best practices",
  "mistral project structure", "how to organize mistral".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, mistral-reference]

---
# Mistral AI Reference Architecture

## Overview
Production-ready architecture patterns for Mistral AI integrations: layered project structure, singleton client, Zod-validated config, custom error classes, service layer with caching, health checks, prompt templates, and model routing.

## Prerequisites
- TypeScript/Node.js project (ESM)
- `@mistralai/mistralai` SDK
- `zod` for config validation
- Testing framework (Vitest)

## Layer Architecture

```
API Layer (Routes, Controllers, Middleware)
    |
Service Layer (Business Logic, Orchestration)
    |
Mistral Layer (Client, Config, Errors, Prompts)
    |
Infrastructure Layer (Cache, Queue, Monitoring)
```

## Instructions

### Step 1: Directory Structure

```
src/
├── mistral/
│   ├── client.ts         # Singleton client factory
│   ├── config.ts         # Zod-validated config
│   ├── errors.ts         # Custom error classes
│   ├── types.ts          # Shared types
│   └── prompts.ts        # Prompt templates
├── services/
│   ├── chat.service.ts   # Chat with caching + retry
│   ├── embed.service.ts  # Embeddings + search
│   └── rag.service.ts    # RAG pipeline
├── api/
│   ├── chat.route.ts     # HTTP endpoints
│   └── health.route.ts   # Health check
└── config/
    ├── base.ts           # Shared config
    ├── development.ts    # Dev overrides
    └── production.ts     # Prod overrides
```

### Step 2: Config with Zod Validation

```typescript
// src/mistral/config.ts
import { z } from 'zod';

const MistralConfigSchema = z.object({
  apiKey: z.string().min(10, 'MISTRAL_API_KEY required'),
  defaultModel: z.string().default('mistral-small-latest'),
  timeoutMs: z.number().default(30_000),
  maxRetries: z.number().default(3),
  cache: z.object({
    enabled: z.boolean().default(true),
    ttlMs: z.number().default(3_600_000),
    maxSize: z.number().default(5000),
  }).default({}),
});

export type MistralConfig = z.infer<typeof MistralConfigSchema>;

export function loadConfig(): MistralConfig {
  return MistralConfigSchema.parse({
    apiKey: process.env.MISTRAL_API_KEY,
    defaultModel: process.env.MISTRAL_MODEL,
    timeoutMs: process.env.MISTRAL_TIMEOUT ? Number(process.env.MISTRAL_TIMEOUT) : undefined,
  });
}
```

### Step 3: Singleton Client

```typescript
// src/mistral/client.ts
import { Mistral } from '@mistralai/mistralai';
import { loadConfig, type MistralConfig } from './config.js';

let _client: Mistral | null = null;
let _config: MistralConfig | null = null;

export function getMistralClient(): Mistral {
  if (!_client) {
    _config = loadConfig();
    _client = new Mistral({
      apiKey: _config.apiKey,
      timeoutMs: _config.timeoutMs,
      maxRetries: _config.maxRetries,
    });
  }
  return _client;
}

export function getConfig(): MistralConfig {
  if (!_config) loadConfig();
  return _config!;
}

export function resetClient(): void {
  _client = null;
  _config = null;
}
```

### Step 4: Custom Error Classes

```typescript
// src/mistral/errors.ts
export type MistralErrorCode =
  | 'AUTH_ERROR'
  | 'RATE_LIMIT'
  | 'BAD_REQUEST'
  | 'SERVICE_ERROR'
  | 'TIMEOUT'
  | 'CONTEXT_OVERFLOW';

export class MistralServiceError extends Error {
  constructor(
    message: string,
    public readonly code: MistralErrorCode,
    public readonly status: number,
    public readonly retryable: boolean,
  ) {
    super(message);
    this.name = 'MistralServiceError';
  }

  static fromApiError(error: any): MistralServiceError {
    const status = error.status ?? error.statusCode ?? 500;
    if (status === 401) return new MistralServiceError('Authentication failed', 'AUTH_ERROR', 401, false);
    if (status === 429) return new MistralServiceError('Rate limit exceeded', 'RATE_LIMIT', 429, true);
    if (status === 400) return new MistralServiceError(error.message, 'BAD_REQUEST', 400, false);
    if (status >= 500) return new MistralServiceError('Service error', 'SERVICE_ERROR', status, true);
    return new MistralServiceError(error.message, 'SERVICE_ERROR', status, false);
  }
}
```

### Step 5: Service Layer with Caching

```typescript
// src/services/chat.service.ts
import { createHash } from 'crypto';
import { LRUCache } from 'lru-cache';
import { getMistralClient, getConfig } from '../mistral/client.js';
import { MistralServiceError } from '../mistral/errors.js';

const cache = new LRUCache<string, any>({ max: 5000, ttl: 3_600_000 });

export class ChatService {
  async complete(messages: any[], options?: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
  }) {
    const config = getConfig();
    const model = options?.model ?? config.defaultModel;
    const temperature = options?.temperature ?? 0.7;

    // Cache deterministic requests
    if (temperature === 0 && config.cache.enabled) {
      const key = createHash('sha256').update(JSON.stringify({ model, messages })).digest('hex');
      const cached = cache.get(key);
      if (cached) return cached;

      const result = await this.executeChat(model, messages, { ...options, temperature: 0 });
      cache.set(key, result);
      return result;
    }

    return this.executeChat(model, messages, options);
  }

  async *stream(messages: any[], model?: string) {
    const client = getMistralClient();
    try {
      const stream = await client.chat.stream({
        model: model ?? getConfig().defaultModel,
        messages,
      });
      for await (const event of stream) {
        const text = event.data?.choices?.[0]?.delta?.content;
        if (text) yield text;
      }
    } catch (error: any) {
      throw MistralServiceError.fromApiError(error);
    }
  }

  private async executeChat(model: string, messages: any[], options: any = {}) {
    const client = getMistralClient();
    try {
      return await client.chat.complete({ model, messages, ...options });
    } catch (error: any) {
      throw MistralServiceError.fromApiError(error);
    }
  }
}
```

### Step 6: Health Check

```typescript
// src/api/health.route.ts
import { getMistralClient } from '../mistral/client.js';

export async function checkMistralHealth() {
  const start = performance.now();
  try {
    const client = getMistralClient();
    const models = await client.models.list();
    const latencyMs = Math.round(performance.now() - start);

    return {
      status: latencyMs > 5000 ? 'degraded' : 'healthy',
      latencyMs,
      modelCount: models.data?.length ?? 0,
    };
  } catch (error: any) {
    return {
      status: 'unhealthy',
      latencyMs: Math.round(performance.now() - start),
      error: error.message,
    };
  }
}
```

### Step 7: Prompt Templates

```typescript
// src/mistral/prompts.ts
interface PromptTemplate {
  name: string;
  system: string;
  userTemplate: (input: string) => string;
  model: string;
  maxTokens: number;
}

export const PROMPTS: Record<string, PromptTemplate> = {
  summarize: {
    name: 'summarize',
    system: 'Summarize the text in 2-3 sentences. Be factual and concise.',
    userTemplate: (text) => `Summarize:\n\n${text}`,
    model: 'mistral-small-latest',
    maxTokens: 200,
  },
  classify: {
    name: 'classify',
    system: 'Classify the input. Reply with one word only.',
    userTemplate: (text) => text,
    model: 'mistral-small-latest',
    maxTokens: 10,
  },
  codeReview: {
    name: 'codeReview',
    system: 'Review code for bugs, security issues, and improvements. Be specific.',
    userTemplate: (code) => `Review this code:\n\`\`\`\n${code}\n\`\`\``,
    model: 'mistral-large-latest',
    maxTokens: 1000,
  },
};
```

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Config validation error | Missing/invalid env vars | Check Zod error message |
| Rate limit (429) | RPM/TPM exceeded | MistralServiceError has `retryable: true` |
| Auth error (401) | Invalid API key | Not retryable, check credentials |
| Cache ineffective | High temperature | Only cache temperature=0 requests |

## Resources
- [Mistral API Reference](https://docs.mistral.ai/api/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [12-Factor App](https://12factor.net/)

## Output
- Layered directory structure with clear separation
- Zod-validated configuration from environment
- Singleton client with lazy initialization
- Custom error classes with retryability
- Service layer with caching and streaming
- Health check endpoint
- Reusable prompt templates
