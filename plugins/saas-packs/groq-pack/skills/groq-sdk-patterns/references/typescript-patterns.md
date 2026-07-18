# Groq SDK — TypeScript Patterns

Full TypeScript implementations for the `groq-sdk` package. Each pattern is production-ready and can be dropped into a project as-is.

## Step 1: Typed Client Singleton

Create one client for the whole app so you share a connection pool and a single config.

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

## Step 2: Type-Safe Completion Wrapper

Surface Groq's unique timing metadata (`queue_time`, `completion_time`, `total_time`) in a typed result so callers can observe throughput.

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

## Step 3: Streaming with Typed Events

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

## Step 4: Error Handling with Groq Error Types

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

## Step 5: Retry with Exponential Backoff

Respect the `retry-after` header Groq returns on 429s; fall back to jittered exponential backoff when it is absent.

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

## Step 7: Multi-Tenant Client Factory

Cache one client per tenant so each tenant's API key stays isolated while still reusing connections.

```typescript
const clients = new Map<string, Groq>();

export function getClientForTenant(tenantId: string, apiKey: string): Groq {
  if (!clients.has(tenantId)) {
    clients.set(tenantId, new Groq({ apiKey, maxRetries: 3 }));
  }
  return clients.get(tenantId)!;
}
```
