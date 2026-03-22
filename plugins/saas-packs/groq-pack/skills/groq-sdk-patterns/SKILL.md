---
name: groq-sdk-patterns
description: |
  Apply production-ready Groq SDK patterns for TypeScript and Python.
  Use when implementing Groq integrations, refactoring SDK usage,
  or establishing team coding standards for Groq.
  Trigger with phrases like "groq SDK patterns", "groq best practices",
  "groq code patterns", "idiomatic groq".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, python, typescript]

---
# Groq SDK Patterns

## Overview
Production patterns for the `groq-sdk` package. The Groq SDK mirrors the OpenAI SDK interface (`chat.completions.create`), so patterns feel familiar but must account for Groq-specific behavior: extreme speed (500+ tok/s), aggressive rate limits on free tier, and unique response metadata like `queue_time` and `completion_time`.

## Prerequisites
- `groq-sdk` installed
- Understanding of async/await and error handling
- Familiarity with OpenAI SDK patterns (Groq is API-compatible)

## Instructions

### Step 1: Typed Client Singleton
```typescript
// src/groq/client.ts
import Groq from "groq-sdk";

let _client: Groq | null = null;

export function getGroq(): Groq {
  if (!_client) {
    _client = new Groq({
      apiKey: process.env.GROQ_API_KEY,
      maxRetries: 3,
      timeout: 30_000,
    });
  }
  return _client;
}
```

### Step 2: Type-Safe Completion Wrapper
```typescript
import Groq from "groq-sdk";
import type { ChatCompletionMessageParam } from "groq-sdk/resources/chat/completions";

const groq = getGroq();

interface CompletionResult {
  content: string;
  model: string;
  tokens: { prompt: number; completion: number; total: number };
  timing: { queueMs: number; totalMs: number; tokensPerSec: number };
}

async function complete(
  messages: ChatCompletionMessageParam[],
  model = "llama-3.3-70b-versatile",
  options?: { maxTokens?: number; temperature?: number }
): Promise<CompletionResult> {
  const response = await groq.chat.completions.create({
    model,
    messages,
    max_tokens: options?.maxTokens ?? 1024,
    temperature: options?.temperature ?? 0.7,
  });

  const usage = response.usage!;
  return {
    content: response.choices[0].message.content || "",
    model: response.model,
    tokens: {
      prompt: usage.prompt_tokens,
      completion: usage.completion_tokens,
      total: usage.total_tokens,
    },
    timing: {
      queueMs: (usage.queue_time ?? 0) * 1000,
      totalMs: (usage.total_time ?? 0) * 1000,
      tokensPerSec: usage.completion_tokens / ((usage.completion_time ?? 1) || 1),
    },
  };
}
```

### Step 3: Streaming with Typed Events
```typescript
async function* streamCompletion(
  messages: ChatCompletionMessageParam[],
  model = "llama-3.3-70b-versatile"
): AsyncGenerator<string> {
  const stream = await groq.chat.completions.create({
    model,
    messages,
    stream: true,
    max_tokens: 2048,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content;
    if (content) yield content;
  }
}

// Usage
async function printStream(prompt: string) {
  const messages: ChatCompletionMessageParam[] = [
    { role: "user", content: prompt },
  ];

  for await (const token of streamCompletion(messages)) {
    process.stdout.write(token);
  }
}
```

### Step 4: Error Handling with Groq Error Types
```typescript
import Groq from "groq-sdk";

async function safeComplete(
  messages: ChatCompletionMessageParam[],
  model = "llama-3.3-70b-versatile"
): Promise<{ data: CompletionResult | null; error: string | null }> {
  try {
    const data = await complete(messages, model);
    return { data, error: null };
  } catch (err) {
    if (err instanceof Groq.APIError) {
      // Groq SDK throws typed API errors
      if (err.status === 429) {
        const retryAfter = err.headers?.["retry-after"];
        return { data: null, error: `Rate limited. Retry after ${retryAfter}s` };
      }
      if (err.status === 401) {
        return { data: null, error: "Invalid API key. Check GROQ_API_KEY." };
      }
      return { data: null, error: `API error ${err.status}: ${err.message}` };
    }
    if (err instanceof Groq.APIConnectionError) {
      return { data: null, error: "Network error connecting to api.groq.com" };
    }
    throw err; // Unknown error, let it propagate
  }
}
```

### Step 5: Retry with Exponential Backoff
```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (err instanceof Groq.APIError && err.status === 429) {
        const retryAfter = parseInt(err.headers?.["retry-after"] || "0");
        const delay = retryAfter > 0
          ? retryAfter * 1000
          : baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;
        console.warn(`Rate limited. Waiting ${(delay / 1000).toFixed(1)}s...`);
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
      throw err; // Non-retryable error
    }
  }
  throw new Error(`Failed after ${maxRetries} retries`);
}
```

### Step 6: Python Patterns
```python
# Synchronous client
from groq import Groq

client = Groq()  # Reads GROQ_API_KEY from env

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello"}],
)

# Async client
from groq import AsyncGroq

async_client = AsyncGroq()

async def async_complete(prompt: str) -> str:
    completion = await async_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content

# Streaming
stream = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True,
)
for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="")
```

### Step 7: Multi-Tenant Client Factory
```typescript
const clients = new Map<string, Groq>();

export function getClientForTenant(tenantId: string, apiKey: string): Groq {
  if (!clients.has(tenantId)) {
    clients.set(tenantId, new Groq({ apiKey, maxRetries: 3 }));
  }
  return clients.get(tenantId)!;
}
```

## Key SDK Differences from OpenAI
| Feature | OpenAI SDK | Groq SDK |
|---------|-----------|----------|
| Package name | `openai` | `groq-sdk` |
| Import | `import OpenAI from "openai"` | `import Groq from "groq-sdk"` |
| Base URL | `api.openai.com/v1` | `api.groq.com/openai/v1` |
| Response `usage` | Standard fields | Adds `queue_time`, `prompt_time`, `completion_time`, `total_time` |
| Error types | `OpenAI.APIError` | `Groq.APIError`, `Groq.APIConnectionError` |

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeComplete` wrapper | All API calls | Prevents uncaught exceptions |
| `withRetry` | Rate-limited calls | Respects `retry-after` header |
| Typed error checking | `instanceof Groq.APIError` | Handles each status code specifically |
| Client singleton | App-wide usage | Single connection pool, consistent config |

## Resources
- [Groq TypeScript SDK](https://github.com/groq/groq-typescript)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [Groq Error Codes](https://console.groq.com/docs/errors)

## Next Steps
Apply patterns in `groq-core-workflow-a` for real-world chat completions.
