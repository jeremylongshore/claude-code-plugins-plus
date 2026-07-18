---
name: groq-sdk-patterns
description: 'Apply production-ready Groq SDK patterns for TypeScript and Python.

  Use when implementing Groq integrations, refactoring SDK usage,

  or establishing team coding standards for Groq.

  Trigger with phrases like "groq SDK patterns", "groq best practices",

  "groq code patterns", "idiomatic groq".

  '
allowed-tools: Read, Write, Edit
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- python
- typescript
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq SDK Patterns

## Overview

Production patterns for the `groq-sdk` package. The Groq SDK mirrors the OpenAI SDK interface (`chat.completions.create`), so patterns feel familiar but must account for Groq-specific behavior: extreme speed (500+ tok/s), aggressive rate limits on free tier, and unique response metadata like `queue_time` and `completion_time`.

The full, copy-paste-ready implementations live in `references/` so this file stays a fast map of the workflow. Read the summary here, then drill into the language file you need.

## Prerequisites

- `groq-sdk` (TypeScript) or `groq` (Python) installed
- `GROQ_API_KEY` set in the environment
- Understanding of async/await and error handling
- Familiarity with OpenAI SDK patterns (Groq is API-compatible)

## Instructions

Build the integration in layers. Each step below is a one-line summary; the full typed implementation is in [references/typescript-patterns.md](references/typescript-patterns.md) (steps 1–5, 7) and [references/python-patterns.md](references/python-patterns.md) (step 6).

1. **Typed client singleton** — one shared `Groq` client with `maxRetries` and `timeout`, so the whole app reuses one connection pool and config.
2. **Type-safe completion wrapper** — return a typed result that surfaces Groq's unique timing fields (`queue_time`, `completion_time`, `total_time`) and a computed `tokensPerSec`.
3. **Streaming with typed events** — an `AsyncGenerator<string>` that yields `delta.content` tokens.
4. **Error handling with Groq error types** — branch on `Groq.APIError` (429, 401, other) and `Groq.APIConnectionError`; rethrow the unknown.
5. **Retry with exponential backoff** — honor the `retry-after` header on 429s, else jittered backoff.
6. **Python patterns** — sync `Groq()`, `AsyncGroq()`, and streaming (see the Python reference).
7. **Multi-tenant client factory** — cache one client per tenant so API keys stay isolated.

The essential skeleton — a shared singleton every other pattern builds on:

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

Groq differs from OpenAI in a few details (package name, base URL, extra `usage` timing fields, error class names). The full comparison and error-handling matrix are in [references/sdk-differences.md](references/sdk-differences.md).

## Output

Applying these patterns produces:

- A reusable `getGroq()` client module and, for multi-tenant apps, a `getClientForTenant()` factory.
- A `complete()` wrapper returning a typed `CompletionResult` — `content`, `model`, `tokens` (prompt/completion/total), and `timing` (`queueMs`, `totalMs`, `tokensPerSec`).
- A `safeComplete()` variant returning `{ data, error }` so callers never face an uncaught exception.
- Streaming helpers that yield string tokens as they arrive.

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeComplete` wrapper | All API calls | Prevents uncaught exceptions |
| `withRetry` | Rate-limited calls | Respects `retry-after` header |
| Typed error checking | `instanceof Groq.APIError` | Handles each status code specifically |
| Client singleton | App-wide usage | Single connection pool, consistent config |

- **429 (rate limited):** read `err.headers["retry-after"]` and wait that long before retrying; free tier hits this often.
- **401 (bad key):** surface a clear "Check GROQ_API_KEY" message — do not retry.
- **`APIConnectionError`:** network issue reaching `api.groq.com`; retry or fail fast per context.
- **Unknown errors:** rethrow so they are not silently swallowed.

Full typed handlers: [references/typescript-patterns.md](references/typescript-patterns.md) (Step 4 and Step 5).

## Examples

**Non-streaming completion with timing metadata** (full code in [references/typescript-patterns.md](references/typescript-patterns.md), Step 2):

```typescript
const result = await complete(
  [{ role: "user", content: "Summarize Groq's speed advantage." }],
  "llama-3.3-70b-versatile"
);
console.log(result.content);
console.log(`${result.timing.tokensPerSec.toFixed(0)} tok/s`);
```

**Streaming tokens to stdout** (full code in the TS reference, Step 3):

```typescript
for await (const token of streamCompletion([{ role: "user", content: "Hello" }])) {
  process.stdout.write(token);
}
```

**Python one-liner** (full sync/async/streaming in [references/python-patterns.md](references/python-patterns.md)):

```python
from groq import Groq
client = Groq()
print(client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello"}],
).choices[0].message.content)
```

## Resources

- [Groq TypeScript SDK](https://github.com/groq/groq-typescript)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [Groq Error Codes](https://console.groq.com/docs/errors)
- [references/typescript-patterns.md](references/typescript-patterns.md) — full TS implementations (steps 1–5, 7)
- [references/python-patterns.md](references/python-patterns.md) — full Python implementations (step 6)
- [references/sdk-differences.md](references/sdk-differences.md) — OpenAI-vs-Groq comparison and error matrix

## Next Steps

Apply these patterns in `groq-core-workflow-a` for real-world chat completions, then wire `safeComplete` and `withRetry` into every call site so rate limits and network errors are handled consistently across the codebase.
