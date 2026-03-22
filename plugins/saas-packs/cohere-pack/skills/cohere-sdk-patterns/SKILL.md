---
name: cohere-sdk-patterns
description: |
  Apply production-ready Cohere SDK patterns for TypeScript and Python.
  Use when implementing Cohere integrations, refactoring SDK usage,
  or establishing team coding standards for Cohere API v2.
  Trigger with phrases like "cohere SDK patterns", "cohere best practices",
  "cohere code patterns", "idiomatic cohere", "cohere wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere SDK Patterns

## Overview
Production-ready patterns for the `cohere-ai` TypeScript SDK (CohereClientV2) and Python `cohere` package. Real model names, real API shapes, real error types.

## Prerequisites
- `cohere-ai` v7+ installed (TypeScript) or `cohere` v5+ (Python)
- Familiarity with async/await patterns
- Understanding of Cohere API v2 endpoints

## Instructions

### Pattern 1: Singleton Client with Retry

```typescript
// src/cohere/client.ts
import { CohereClientV2, CohereError, CohereTimeoutError } from 'cohere-ai';

let instance: CohereClientV2 | null = null;

export function getCohere(): CohereClientV2 {
  if (!instance) {
    if (!process.env.CO_API_KEY) {
      throw new Error('CO_API_KEY environment variable is required');
    }
    instance = new CohereClientV2({
      token: process.env.CO_API_KEY,
    });
  }
  return instance;
}

export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === maxRetries) throw err;

      // Only retry on rate limits (429) and server errors (5xx)
      if (err instanceof CohereError) {
        const status = err.statusCode;
        if (status && status !== 429 && status < 500) throw err;
      } else if (!(err instanceof CohereTimeoutError)) {
        throw err;
      }

      const delay = baseDelayMs * Math.pow(2, attempt - 1);
      const jitter = Math.random() * 500;
      await new Promise(r => setTimeout(r, delay + jitter));
    }
  }
  throw new Error('Unreachable');
}
```

### Pattern 2: Type-Safe Chat Wrapper

```typescript
// src/cohere/chat.ts
import { getCohere, withRetry } from './client';

interface ChatOptions {
  message: string;
  systemPrompt?: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
  documents?: Array<{ id?: string; data: Record<string, string> }>;
}

export async function chat(options: ChatOptions): Promise<string> {
  const cohere = getCohere();

  const messages: Array<{ role: string; content: string }> = [];

  if (options.systemPrompt) {
    messages.push({ role: 'system', content: options.systemPrompt });
  }
  messages.push({ role: 'user', content: options.message });

  const response = await withRetry(() =>
    cohere.chat({
      model: options.model ?? 'command-a-03-2025',
      messages,
      maxTokens: options.maxTokens,
      temperature: options.temperature,
      documents: options.documents,
    })
  );

  return response.message?.content?.[0]?.text ?? '';
}
```

### Pattern 3: Streaming Chat

```typescript
// src/cohere/stream.ts
export async function* streamChat(
  message: string,
  model = 'command-a-03-2025'
): AsyncGenerator<string> {
  const cohere = getCohere();

  const stream = await cohere.chatStream({
    model,
    messages: [{ role: 'user', content: message }],
  });

  for await (const event of stream) {
    if (event.type === 'content-delta') {
      const text = event.delta?.message?.content?.text;
      if (text) yield text;
    }
  }
}

// Usage
for await (const chunk of streamChat('Explain RAG in 3 sentences')) {
  process.stdout.write(chunk);
}
```

### Pattern 4: Batch Embedding

```typescript
// src/cohere/embed.ts
type InputType = 'search_document' | 'search_query' | 'classification' | 'clustering';

export async function embedTexts(
  texts: string[],
  inputType: InputType = 'search_document',
  model = 'embed-v4.0'
): Promise<number[][]> {
  const cohere = getCohere();

  // Cohere embed accepts up to 96 texts per call
  const BATCH_SIZE = 96;
  const allEmbeddings: number[][] = [];

  for (let i = 0; i < texts.length; i += BATCH_SIZE) {
    const batch = texts.slice(i, i + BATCH_SIZE);
    const response = await withRetry(() =>
      cohere.embed({
        model,
        texts: batch,
        inputType,
        embeddingTypes: ['float'],
      })
    );
    allEmbeddings.push(...response.embeddings.float);
  }

  return allEmbeddings;
}
```

### Pattern 5: Rerank with Type Safety

```typescript
// src/cohere/rerank.ts
interface RerankResult {
  text: string;
  score: number;
  originalIndex: number;
}

export async function rerankDocuments(
  query: string,
  documents: string[],
  topN = 5,
  model = 'rerank-v3.5'
): Promise<RerankResult[]> {
  const cohere = getCohere();

  const response = await withRetry(() =>
    cohere.rerank({ model, query, documents, topN })
  );

  return response.results.map(r => ({
    text: documents[r.index],
    score: r.relevanceScore,
    originalIndex: r.index,
  }));
}
```

### Pattern 6: Structured JSON Output

```typescript
export async function chatJSON<T>(
  message: string,
  schema?: Record<string, unknown>
): Promise<T> {
  const cohere = getCohere();

  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: `${message}\n\nRespond in valid JSON.` }],
    responseFormat: schema
      ? { type: 'json_object', jsonSchema: schema }
      : { type: 'json_object' },
  });

  const text = response.message?.content?.[0]?.text ?? '{}';
  return JSON.parse(text) as T;
}
```

## Python Equivalents

```python
import cohere
from cohere import ClientV2

# Singleton
_client: ClientV2 | None = None

def get_cohere() -> ClientV2:
    global _client
    if _client is None:
        _client = ClientV2()  # reads CO_API_KEY
    return _client

# Chat
def chat(message: str, model: str = "command-a-03-2025") -> str:
    co = get_cohere()
    response = co.chat(
        model=model,
        messages=[{"role": "user", "content": message}],
    )
    return response.message.content[0].text

# Embed
def embed(texts: list[str], input_type: str = "search_document") -> list[list[float]]:
    co = get_cohere()
    response = co.embed(
        model="embed-v4.0",
        texts=texts,
        input_type=input_type,
        embedding_types=["float"],
    )
    return response.embeddings.float
```

## Error Handling
| Error Type | When | Recovery |
|------------|------|----------|
| `CohereError` (status 400) | Bad request params | Fix request, do not retry |
| `CohereError` (status 401) | Invalid API key | Check CO_API_KEY |
| `CohereError` (status 429) | Rate limited | Retry with backoff |
| `CohereError` (status 5xx) | Server error | Retry with backoff |
| `CohereTimeoutError` | Network timeout | Retry with backoff |

## Resources
- [Cohere TypeScript SDK](https://github.com/cohere-ai/cohere-typescript)
- [Cohere Python SDK](https://github.com/cohere-ai/cohere-python)
- [API v2 Reference](https://docs.cohere.com/reference/about)

## Next Steps
Apply patterns in `cohere-core-workflow-a` for RAG workflows.
