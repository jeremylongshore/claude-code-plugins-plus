---
name: elevenlabs-sdk-patterns
description: |
  Apply production-ready ElevenLabs SDK patterns for TypeScript and Python.
  Use when implementing ElevenLabs integrations, refactoring SDK usage, or
  establishing team coding standards for audio AI applications.
  Trigger with "elevenlabs SDK patterns", "elevenlabs best practices",
  "elevenlabs code patterns", "idiomatic elevenlabs", "elevenlabs typescript".
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- sdk
- patterns
compatibility: Designed for Claude Code
---
# ElevenLabs SDK Patterns

## Overview

Production-ready patterns for the ElevenLabs TypeScript and Python SDKs. Covers singleton
clients, type-safe TTS wrappers, error classification, retry with a concurrency queue, and
multi-tenant client factories. Adopt them incrementally — the singleton client alone fixes the
most common mistakes; add error classification and the queue as throughput grows.

The full, copy-ready code for all six patterns lives in
[references/implementation.md](references/implementation.md). This file gives the high-level
workflow plus the essential skeleton so you can follow it end to end, then drill into the
reference for depth.

## Prerequisites

- `@elevenlabs/elevenlabs-js` installed (TypeScript) or `elevenlabs` (Python)
- `ELEVENLABS_API_KEY` exported in the environment (never hardcode the key)
- Familiarity with async/await patterns and error handling best practices

## Instructions

Apply the patterns in order — each builds on the previous one:

1. **Singleton client.** Create one lazily-initialized `ElevenLabsClient` guarded by an
   `ELEVENLABS_API_KEY` check so misconfiguration fails fast at startup. Expose a `resetClient()`
   for tests. This is the skeleton every other pattern imports:

   ```typescript
   let instance: ElevenLabsClient | null = null;
   export function getClient(): ElevenLabsClient {
     if (!instance) {
       if (!process.env.ELEVENLABS_API_KEY) {
         throw new Error("ELEVENLABS_API_KEY environment variable is required");
       }
       instance = new ElevenLabsClient({
         apiKey: process.env.ELEVENLABS_API_KEY,
         maxRetries: 3,
         timeoutInSeconds: 60,
       });
     }
     return instance;
   }
   ```

2. **Type-safe TTS service.** Wrap `textToSpeech.convert` behind a typed `TTSOptions` interface
   and named `VoicePreset` records (narration / conversational / dramatic / neutral) so voice
   settings are compile-time checked and consistent across the codebase.
3. **Error classification.** Map raw SDK errors to an `ElevenLabsServiceError` carrying a stable
   `code` (auth_failed, quota_exceeded, rate_limited, concurrent_limit, voice_not_found,
   invalid_request, server_error, network_error) and a `retryable` flag driven by HTTP status.
4. **Retry with a concurrency queue.** Route calls through a `p-queue` sized to your plan's
   concurrent-request limit, retrying only `retryable` errors with exponential backoff + jitter.
5. **Multi-tenant factory.** For SaaS platforms, key one client per tenant in a `Map` so each
   customer's API key stays isolated.
6. **Python async.** Mirror the singleton + streaming-to-file pattern with `AsyncElevenLabsClient`
   for non-blocking Python backends.

See [references/implementation.md](references/implementation.md) for the complete code for every
step above.

## Output

Applying these patterns produces a small set of focused SDK modules in the target project:

- `src/elevenlabs/client.ts` — singleton client with config + `resetClient()`
- `src/elevenlabs/tts-service.ts` — typed `generateSpeech()` / `generateToFile()` with voice presets
- `src/elevenlabs/errors.ts` — `ElevenLabsServiceError` + `classifyError()`
- `src/elevenlabs/queue.ts` — `queuedRequest()` with backoff and plan-aware concurrency
- `src/elevenlabs/multi-tenant.ts` — per-tenant client factory (SaaS only)
- `elevenlabs_service.py` — async singleton + streaming generator (Python backends)

TTS calls return an audio stream you pipe to a file or HTTP response; `mp3_44100_128` is the
default output format.

## Error Handling

| Pattern | Error Type | Benefit |
|---------|-----------|---------|
| `classifyError()` | All API errors | Maps HTTP status to actionable codes |
| `queuedRequest()` | 429, 5xx | Auto-retry with exponential backoff + jitter |
| Singleton guard | Missing env var | Fails fast at startup, not at first call |

Only `retryable` codes (`rate_limited`, `concurrent_limit`, `server_error`, `network_error`) are
retried; `auth_failed`, `quota_exceeded`, `voice_not_found`, and `invalid_request` throw
immediately so callers surface a real problem instead of looping.

## Examples

**Generate speech to a file (TypeScript):**

```typescript
import { generateToFile } from "./elevenlabs/tts-service";

await generateToFile(
  { voiceId: "21m00Tcm4TlvDq8ikWAM", text: "Welcome aboard.", preset: "narration" },
  "welcome.mp3"
);
```

**Wrap a call in the retry queue:**

```typescript
import { queuedRequest } from "./elevenlabs/queue";
import { generateSpeech } from "./elevenlabs/tts-service";

const audio = await queuedRequest(() =>
  generateSpeech({ voiceId: "21m00Tcm4TlvDq8ikWAM", text: "High-throughput job." })
);
```

Full runnable examples — including the Python async path and multi-tenant usage — are in
[references/implementation.md](references/implementation.md).

## Resources

- [ElevenLabs JS SDK Source](https://github.com/elevenlabs/elevenlabs-js)
- [ElevenLabs Python SDK](https://pypi.org/project/elevenlabs/)
- [p-queue (Concurrency)](https://github.com/sindresorhus/p-queue)
- [Full implementation walkthrough](references/implementation.md)

## Next Steps

Apply these patterns in `elevenlabs-core-workflow-a` for TTS generation, or see
`elevenlabs-rate-limits` for advanced throttling and plan-aware concurrency tuning.
