---
name: elevenlabs-reference-architecture
description: |
  Implement an ElevenLabs reference architecture for production TTS/voice
  applications. Use when designing new ElevenLabs integrations, reviewing
  project structure, or building a scalable audio generation service.
  Trigger with "elevenlabs architecture", "elevenlabs project structure",
  "how to organize elevenlabs", "TTS service architecture",
  "elevenlabs design patterns", "voice API architecture".
allowed-tools: Read
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- architecture
- patterns
compatibility: Designed for Claude Code
---
# ElevenLabs Reference Architecture

## Overview

Production-ready architecture for ElevenLabs TTS/voice applications. Covers project
layout, service layers, caching, streaming, and multi-model orchestration. The full
code for each layer lives in `references/` so this file stays a navigable map; drill
into a reference file when you need the exact implementation.

## Prerequisites

- Understanding of layered architecture patterns
- ElevenLabs SDK knowledge (see `elevenlabs-sdk-patterns`)
- TypeScript project with async patterns
- Redis (optional, for distributed caching)
- **Auth**: an ElevenLabs API key exported as `ELEVENLABS_API_KEY` (read by the
  config layer). This is the only ElevenLabs credential — your app's own request
  auth (`middleware/auth.ts`) is separate and unrelated.

## Instructions

Build the service in six layers. Each step below is the high-level move; the
verbatim code and diagrams are in the linked reference files.

### Step 1: Lay out the project

Split the codebase into `elevenlabs/` (client, config, models, errors, types),
`services/` (tts, voice, audio, cache), `api/` (routes + middleware), `queue/`, and
`monitoring/`. See the [full project tree](references/architecture.md).

### Step 2: Configuration layer

Define an environment-aware `ElevenLabsConfig` — dev uses the cheap/fast
`eleven_flash_v2_5` and small output format; production uses `eleven_multilingual_v2`
at higher quality, more concurrency, and a larger cache. `loadConfig()` merges the
per-environment defaults with `ELEVENLABS_API_KEY`. Full interface and `ENV_CONFIGS`:
[implementation walkthrough](references/implementation.md).

### Step 3: TTS service layer

Wrap the SDK client in a `TTSService` that owns a singleton client and a `p-queue`
sized to `maxConcurrency` (this is what prevents 429s). `generate()` supports both
streaming and buffered convert, logs latency, and routes errors through
`classifyError`. `generateLongText()` splits on sentence boundaries under the 5000-char
limit to preserve prosody. Full class:
[implementation walkthrough](references/implementation.md).

### Step 4: Voice management service

A `VoiceService` over the client for list/clone/get-settings/update-settings/delete,
with category filtering (premade / cloned / generated). Full class:
[implementation walkthrough](references/implementation.md).

### Step 5: Wire the data flow

Requests flow Client → API layer → Cache/TTS/Voice services → queue → singleton SDK
client → ElevenLabs REST/WS endpoints. See the
[data flow diagram](references/architecture.md).

### Step 6: Health check composition

Compose a `/health` route that runs connectivity, quota, and cache checks with
`Promise.allSettled`, returning `healthy` / `degraded` / `unhealthy` (degraded once
quota exceeds 90%). Full function:
[implementation walkthrough](references/implementation.md).

Every architectural choice (singleton client, p-queue, LRU-vs-Redis, sentence
splitting, environment-based model selection, HTTP-vs-WS streaming) and its rationale
is tabulated in the [architecture decisions table](references/architecture.md).

## Output

Applying this skill produces a layered service scaffold, not a single file:

- A directory tree matching the [project structure](references/architecture.md).
- An environment-aware config module resolving dev/staging/production defaults.
- A `TTSService` (queued, retry-aware, streaming-capable) and a `VoiceService`.
- A `/health` route returning `{ status, services, timestamp }` where `status` is
  `healthy`, `degraded`, or `unhealthy`.
- At runtime, `generate()` returns a `Buffer` (or a `ReadableStream` when
  `streaming: true`); `generateLongText()` returns `Buffer[]`, one per chunk.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Services depend on client, never reverse |
| Cold start latency | Client initialization | Pre-warm in server startup |
| Memory pressure | Unbounded audio cache | Set `maxSizeMB` on cache |
| Type errors | SDK version mismatch | Pin SDK version in package.json |
| Frequent 429s | Concurrency above plan limit | Lower `maxConcurrency` in config |
| Missing API key | `ELEVENLABS_API_KEY` unset | Export it before `loadConfig()` runs |

## Examples

**Generate speech through the service layer:**

```typescript
const tts = new TTSService();
const audio = await tts.generate("Hello from production.", {
  voiceId: "21m00Tcm4TlvDq8ikWAM",
});
```

**Stream a long article with prosody-preserving chunking:**

```typescript
const chunks = await tts.generateLongText(longArticleText);
// chunks: Buffer[] — concatenate or pipe in order
```

For the complete, runnable layers behind these snippets — config, full `TTSService`,
`VoiceService`, and the `/health` composition — see the
[implementation walkthrough](references/implementation.md). For the project tree,
data flow, and decision rationale, see [architecture.md](references/architecture.md).

## Resources

- [ElevenLabs API Reference](https://elevenlabs.io/docs/api-reference/introduction)
- [ElevenLabs SDK Source](https://github.com/elevenlabs/elevenlabs-js)
- [p-queue](https://github.com/sindresorhus/p-queue)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [Implementation walkthrough](references/implementation.md) — full service code
- [Architecture reference](references/architecture.md) — project tree, data flow, decisions

## Next Steps

Start with `elevenlabs-install-auth` for setup, then apply this architecture. Use
`elevenlabs-core-workflow-a` and `elevenlabs-core-workflow-b` for feature implementation.
