---
name: elevenlabs-common-errors
description: |
  Diagnose and fix ElevenLabs API errors by HTTP status code.
  Use when encountering ElevenLabs errors, debugging failed TTS/STS requests,
  or troubleshooting voice cloning and streaming issues.
  Trigger with "elevenlabs error", "fix elevenlabs", "elevenlabs not working",
  "debug elevenlabs", "elevenlabs 401", "elevenlabs 429", "elevenlabs 400".
allowed-tools: Bash(curl:*), Bash(node:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- debugging
- errors
compatibility: Designed for Claude Code
---
# ElevenLabs Common Errors

## Overview

Quick diagnostic reference for ElevenLabs API errors organized by HTTP status
code: run the connectivity probe, map the observed status code to a fix, then
confirm with the debug checklist. This file is the fast index; the full
per-error catalog (payloads + code fixes for every status code) lives in
[references/error-reference.md](references/error-reference.md).

## Prerequisites

- ElevenLabs SDK installed
- API key configured (`ELEVENLABS_API_KEY`)
- Access to error logs or console output

## Instructions

### Step 1: Quick Diagnostic

Run the connectivity probe to isolate auth from quota from request problems:

```bash
# Test API connectivity and auth
curl -s -w "\nHTTP %{http_code}" \
  https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}"

# Check character quota
curl -s https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
  jq '.subscription | {tier, character_count, character_limit}'

# List available voices (confirms API access)
curl -s https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | jq '.voices | length'
```

### Step 2: Map the Status Code to a Fix

Match the HTTP status code (and the `detail.status` string in the response body)
to its row below, then open the linked catalog entry for the exact payload and
copy-paste fix:

| Status | `detail.status` | Root cause | First move |
|--------|-----------------|------------|-----------|
| 401 | `invalid_api_key` | Key missing/malformed/revoked | Re-check `ELEVENLABS_API_KEY`, regenerate if needed |
| 401 | `quota_exceeded` | Monthly character limit hit | Check usage, upgrade or enable usage-based billing |
| 400 | `voice_not_found` | Bad `voice_id` in path | `GET /v1/voices` to list valid IDs |
| 400 | `text_too_long` | TTS text > 5,000 chars | Chunk text with `previous_text`/`next_text` |
| 400 | `model_not_found` | Bad `model_id` string | Use an exact model ID (see catalog) |
| 429 | `too_many_concurrent_requests` | Over plan concurrency | Queue requests to your plan limit |
| 429 | `system_busy` | ElevenLabs under load | Retry with backoff (`maxRetries`) |
| 422 | `invalid_voice_sample` | Clone audio bad format/too short | MP3/WAV/M4A/FLAC, ≥30s, clean speech |
| — | WebSocket fails silently | Missing `xi_api_key` / `eleven_v3` on WS | Send key in first WS message, use `eleven_flash_v2_5` |

Full payloads, causes, and fix snippets for every row:
[references/error-reference.md](references/error-reference.md).

### Step 3: Debug Checklist

1. Verify API key: `curl -s https://api.elevenlabs.io/v1/user -H "xi-api-key: $ELEVENLABS_API_KEY"`
2. Check quota: Look at `character_count` vs `character_limit` in the response
3. Verify voice_id: `GET /v1/voices` to list valid IDs
4. Check model_id: Must be an exact match (see catalog)
5. Check request size: Text must be under 5,000 characters
6. Check concurrency: Are you exceeding your plan's concurrent limit?
7. Check ElevenLabs status: https://status.elevenlabs.io

## Output

Working through this skill produces:

- A resolved HTTP status code and `detail.status` string identifying the exact failure.
- The applied fix (corrected key/quota, valid `voice_id`/`model_id`, chunked text,
  request queue, or WebSocket handshake correction).
- A clean re-run of the Step 1 probe returning `HTTP 200` from `/v1/user` and a
  non-zero voice count, confirming the request path is healthy.

## Error Handling

| HTTP | Error | Retryable | Action |
|------|-------|-----------|--------|
| 400 | Bad request | No | Fix request parameters |
| 401 | Auth/quota | No | Check key or upgrade plan |
| 404 | Not found | No | Verify voice_id/model_id |
| 422 | Validation | No | Fix input data format |
| 429 | Rate limit | Yes | Backoff + queue requests |
| 500+ | Server error | Yes | Retry with backoff |

## Examples

**401 after key rotation** — the probe returns `HTTP 401` with
`invalid_api_key`. The old key is still in the shell env:

```bash
echo "${ELEVENLABS_API_KEY:0:8}..."   # confirms which key is loaded
# export the freshly generated key, then re-run the Step 1 probe → HTTP 200
```

**429 under load** — batch TTS returns `too_many_concurrent_requests`. Cap
concurrency to the plan limit instead of firing all requests at once:

```typescript
import PQueue from "p-queue";
const queue = new PQueue({ concurrency: 5 }); // Match your plan
await queue.add(() => client.textToSpeech.convert(voiceId, options));
```

**400 on long input** — a 7,000-character request returns `text_too_long`.
Split it and preserve prosody across chunks:

```typescript
const audio = await client.textToSpeech.convert(voiceId, {
  text: currentChunk,
  previous_text: previousChunk,  // Helps maintain flow
  next_text: nextChunk,          // Helps maintain flow
  model_id: "eleven_multilingual_v2",
});
```

See [references/error-reference.md](references/error-reference.md) for the full
payload and fix for every status code above.

## Resources

- [Full error catalog by status code](references/error-reference.md)
- [API Error 429 Help](https://help.elevenlabs.io/hc/en-us/articles/19571824571921)
- [API Error 401 Help](https://help.elevenlabs.io/hc/en-us/articles/19572237925521)
- [ElevenLabs Status](https://status.elevenlabs.io)

## Next Steps

For comprehensive debugging, see `elevenlabs-debug-bundle`. For rate limit handling, see `elevenlabs-rate-limits`.
