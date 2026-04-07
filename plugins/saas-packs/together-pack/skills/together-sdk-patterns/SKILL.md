---
name: together-sdk-patterns
description: |
  Together AI sdk patterns for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together sdk patterns".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI SDK Patterns

## Overview
Production-ready patterns for Together AI inference. Together exposes an OpenAI-compatible REST API at `https://api.together.xyz/v1`, meaning any OpenAI client library works with a base URL swap. This makes Together a drop-in replacement for OpenAI when running open-source models (Llama, Mixtral, Qwen, FLUX). A singleton client centralizes the base URL override and enables seamless backend switching.

## Singleton Client
```typescript
import OpenAI from 'openai';
let _client: OpenAI | null = null;
export function getClient(): OpenAI {
  if (!_client) {
    const apiKey = process.env.TOGETHER_API_KEY;
    if (!apiKey) throw new Error('TOGETHER_API_KEY must be set — get it from api.together.xyz/settings');
    _client = new OpenAI({ apiKey, baseURL: 'https://api.together.xyz/v1' });
  }
  return _client;
}
// Usage: const client = getClient();
// await client.chat.completions.create({ model: 'meta-llama/Meta-Llama-3.1-70B-Instruct', messages: [...] });
```

## Error Wrapper
```typescript
export class TogetherError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}
export async function safeCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    const status = err.status ?? err.response?.status ?? 0;
    if (status === 429) { await new Promise(r => setTimeout(r, 3000)); return fn(); }
    if (status === 401) throw new TogetherError(401, 'AUTH', 'Invalid TOGETHER_API_KEY');
    if (status === 404) throw new TogetherError(404, 'MODEL', `${operation}: model not found — use client.models.list()`);
    throw new TogetherError(status, 'API_ERROR', `${operation} failed [${status}]: ${err.message}`);
  }
}
```

## Request Builder
```typescript
class TogetherRequest {
  private params: Record<string, any> = {};
  model(m: string) { this.params.model = m; return this; }
  messages(msgs: Array<{ role: string; content: string }>) { this.params.messages = msgs; return this; }
  temperature(t: number) { this.params.temperature = t; return this; }
  maxTokens(n: number) { this.params.max_tokens = n; return this; }
  stream(s = true) { this.params.stream = s; return this; }
  jsonMode() { this.params.response_format = { type: 'json_object' }; return this; }
  build() { return this.params; }
}
// Usage: new TogetherRequest().model('meta-llama/Meta-Llama-3.1-70B-Instruct')
//   .messages([{ role: 'user', content: 'Summarize this' }]).temperature(0.3).jsonMode().build();
```

## Response Types
```typescript
interface TogetherModel {
  id: string; type: 'chat' | 'language' | 'image' | 'embedding' | 'code';
  display_name: string; context_length: number; pricing: { input: number; output: number };
}
interface ChatCompletion {
  id: string; model: string; created: number;
  choices: Array<{ message: { role: string; content: string }; finish_reason: string }>;
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
}
interface EmbeddingResponse {
  data: Array<{ embedding: number[]; index: number }>;
  model: string; usage: { prompt_tokens: number; total_tokens: number };
}
interface FineTuneJob {
  id: string; model: string; status: 'pending' | 'running' | 'completed' | 'failed';
  training_file: string; created_at: string; fine_tuned_model?: string;
}
```

## Testing Utilities
```typescript
export function mockCompletion(content = 'Hello!', overrides: Partial<ChatCompletion> = {}): ChatCompletion {
  return { id: 'cmpl-001', model: 'meta-llama/Meta-Llama-3.1-70B-Instruct', created: Date.now(),
    choices: [{ message: { role: 'assistant', content }, finish_reason: 'stop' }],
    usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 }, ...overrides };
}
export function mockModel(overrides: Partial<TogetherModel> = {}): TogetherModel {
  return { id: 'meta-llama/Meta-Llama-3.1-70B-Instruct', type: 'chat',
    display_name: 'Meta Llama 3.1 70B Instruct', context_length: 131072,
    pricing: { input: 0.88, output: 0.88 }, ...overrides };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| `safeCall` wrapper | All Together API calls | Structured error with operation context |
| Retry on 429 | High-throughput inference | Reads `Retry-After` header for backoff |
| Model validation | Before inference calls | 404 directs to `client.models.list()` |
| Streaming fallback | Long completions timeout | Switch `stream: true` on timeout |

## Resources
- [Together AI Docs](https://docs.together.ai/)

## Next Steps
Apply patterns in `together-core-workflow-a`.
