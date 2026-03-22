---
name: mistral-sdk-patterns
description: |
  Apply production-ready Mistral AI SDK patterns for TypeScript and Python.
  Use when implementing Mistral integrations, refactoring SDK usage,
  or establishing team coding standards for Mistral AI.
  Trigger with phrases like "mistral SDK patterns", "mistral best practices",
  "mistral code patterns", "idiomatic mistral".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, python, typescript]

---
# Mistral SDK Patterns

## Overview
Production-ready patterns for the Mistral AI SDK. Covers singleton client, retry/backoff, structured output, streaming, function calling, batch embeddings, and async Python — all with proper error handling. SDK is ESM-only for TypeScript (`@mistralai/mistralai`), sync+async for Python (`mistralai`).

## Prerequisites
- `@mistralai/mistralai` (TypeScript) or `mistralai` (Python) installed
- `MISTRAL_API_KEY` environment variable set

## Instructions

### Step 1: Singleton Client with Configuration

**TypeScript**
```typescript
import { Mistral } from '@mistralai/mistralai';

let _client: Mistral | null = null;

export function getMistralClient(): Mistral {
  if (!_client) {
    const apiKey = process.env.MISTRAL_API_KEY;
    if (!apiKey) throw new Error('MISTRAL_API_KEY not set');

    _client = new Mistral({
      apiKey,
      timeoutMs: 30_000,
      maxRetries: 3,
    });
  }
  return _client;
}

// Reset for testing
export function resetClient(): void {
  _client = null;
}
```

**Python**
```python
import os
from mistralai import Mistral

_client = None

def get_client() -> Mistral:
    global _client
    if _client is None:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("MISTRAL_API_KEY not set")
        _client = Mistral(api_key=api_key, timeout_ms=30_000, max_retries=3)
    return _client
```

### Step 2: Structured Output with JSON Schema

```typescript
import { z } from 'zod';

// Define schema with Zod, then convert to JSON Schema for Mistral
const TicketSchema = z.object({
  category: z.enum(['bug', 'feature', 'question']),
  severity: z.enum(['low', 'medium', 'high', 'critical']),
  summary: z.string(),
});

type Ticket = z.infer<typeof TicketSchema>;

async function classifyTicket(text: string): Promise<Ticket> {
  const client = getMistralClient();

  const response = await client.chat.complete({
    model: 'mistral-small-latest',
    messages: [
      { role: 'system', content: 'Classify the support ticket.' },
      { role: 'user', content: text },
    ],
    responseFormat: {
      type: 'json_schema',
      jsonSchema: {
        name: 'ticket_classification',
        schema: {
          type: 'object',
          properties: {
            category: { type: 'string', enum: ['bug', 'feature', 'question'] },
            severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
            summary: { type: 'string' },
          },
          required: ['category', 'severity', 'summary'],
        },
      },
    },
  });

  const raw = JSON.parse(response.choices?.[0]?.message?.content ?? '{}');
  return TicketSchema.parse(raw); // Validate at runtime
}
```

### Step 3: Streaming with Accumulated Result

```typescript
interface StreamResult {
  content: string;
  finishReason: string;
}

async function streamWithAccumulation(
  messages: Array<{ role: string; content: string }>,
  onChunk: (text: string) => void,
): Promise<StreamResult> {
  const client = getMistralClient();
  const stream = await client.chat.stream({
    model: 'mistral-small-latest',
    messages,
  });

  let content = '';
  let finishReason = '';

  for await (const event of stream) {
    const delta = event.data?.choices?.[0];
    if (delta?.delta?.content) {
      content += delta.delta.content;
      onChunk(delta.delta.content);
    }
    if (delta?.finishReason) {
      finishReason = delta.finishReason;
    }
  }

  return { content, finishReason };
}
```

### Step 4: Python Async Pattern

```python
import asyncio
from mistralai import Mistral

async def process_batch(prompts: list[str], model: str = "mistral-small-latest"):
    """Process multiple prompts concurrently with semaphore for rate limiting."""
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

    async def process_one(prompt: str) -> str:
        async with semaphore:
            response = await client.chat.complete_async(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

    results = await asyncio.gather(*[process_one(p) for p in prompts])
    return results
```

### Step 5: Retry with Exponential Backoff

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      const status = error.status ?? error.statusCode;
      const retryable = status === 429 || status >= 500;

      if (!retryable || attempt === maxRetries) throw error;

      // Respect Retry-After header if present
      const retryAfter = error.headers?.get?.('retry-after');
      const delay = retryAfter
        ? parseInt(retryAfter) * 1000
        : Math.min(1000 * 2 ** attempt, 30_000);

      console.warn(`Attempt ${attempt + 1} failed (${status}), retrying in ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}

// Usage
const response = await withRetry(() =>
  client.chat.complete({
    model: 'mistral-large-latest',
    messages: [{ role: 'user', content: 'Hello' }],
  })
);
```

### Step 6: Token Usage Tracking

```typescript
interface UsageStats {
  totalPromptTokens: number;
  totalCompletionTokens: number;
  totalRequests: number;
  costUsd: number;
}

const PRICING: Record<string, { input: number; output: number }> = {
  'mistral-small-latest': { input: 0.1, output: 0.3 },
  'mistral-large-latest': { input: 0.5, output: 1.5 },
  'mistral-embed':        { input: 0.1, output: 0 },
  'codestral-latest':     { input: 0.3, output: 0.9 },
};

class UsageTracker {
  private stats: UsageStats = { totalPromptTokens: 0, totalCompletionTokens: 0, totalRequests: 0, costUsd: 0 };

  record(model: string, usage: { promptTokens?: number; completionTokens?: number }): void {
    const pt = usage.promptTokens ?? 0;
    const ct = usage.completionTokens ?? 0;
    this.stats.totalPromptTokens += pt;
    this.stats.totalCompletionTokens += ct;
    this.stats.totalRequests++;

    const p = PRICING[model] ?? PRICING['mistral-small-latest'];
    this.stats.costUsd += (pt / 1e6) * p.input + (ct / 1e6) * p.output;
  }

  report(): UsageStats { return { ...this.stats }; }
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Verify `MISTRAL_API_KEY` |
| `429 Too Many Requests` | Rate limit hit | Use built-in retry or custom backoff |
| `400 Bad Request` | Invalid model or params | Check model name and parameter values |
| `ERR_REQUIRE_ESM` | CommonJS import | SDK is ESM-only; use `import` syntax |
| Timeout | Large prompt or slow network | Increase `timeoutMs` |

## Resources
- [TypeScript SDK (client-ts)](https://github.com/mistralai/client-ts)
- [Python SDK (client-python)](https://github.com/mistralai/client-python)
- [API Reference](https://docs.mistral.ai/api/)
- [Pricing](https://docs.mistral.ai/deployment/laplateforme/pricing/)

## Output
- Singleton client pattern for TypeScript and Python
- Structured output with JSON Schema validation
- Streaming with accumulation
- Retry/backoff for resilient API calls
- Token usage tracking with cost estimation
