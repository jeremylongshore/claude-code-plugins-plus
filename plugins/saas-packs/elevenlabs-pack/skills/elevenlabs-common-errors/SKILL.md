---
name: elevenlabs-common-errors
description: |
  Diagnose and fix ElevenLabs API errors by HTTP status code.
  Use when encountering ElevenLabs errors, debugging failed TTS/STS requests,
  or troubleshooting voice cloning and streaming issues.
  Trigger: "elevenlabs error", "fix elevenlabs", "elevenlabs not working",
  "debug elevenlabs", "elevenlabs 401", "elevenlabs 429", "elevenlabs 400".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, debugging, errors]
compatible-with: claude-code
---

# ElevenLabs Common Errors

## Overview

Quick diagnostic reference for ElevenLabs API errors organized by HTTP status code, with real error messages, causes, and solutions.

## Prerequisites

- ElevenLabs SDK installed
- API key configured
- Access to error logs or console output

## Instructions

### Step 1: Quick Diagnostic

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

### Step 2: Error Reference

---

#### HTTP 401 — Authentication / Quota

**Error: `invalid_api_key`**
```json
{
  "detail": {
    "status": "invalid_api_key",
    "message": "Invalid API key"
  }
}
```
**Cause:** API key is missing, malformed, or revoked.
**Fix:**
```bash
# Verify key is set
echo "${ELEVENLABS_API_KEY:0:8}..."

# Test with curl
curl -s https://api.elevenlabs.io/v1/user -H "xi-api-key: ${ELEVENLABS_API_KEY}"

# Regenerate at: https://elevenlabs.io/app/settings/api-keys
```

**Error: `quota_exceeded`**
```json
{
  "detail": {
    "status": "quota_exceeded",
    "message": "You have insufficient quota to complete this request"
  }
}
```
**Cause:** Monthly character limit reached for your plan.
**Fix:** Check usage at https://elevenlabs.io/app/usage. Upgrade plan, or on Creator+ plans, enable usage-based billing in Subscription settings.

---

#### HTTP 400 — Bad Request

**Error: `voice_not_found`**
```json
{
  "detail": {
    "status": "voice_not_found",
    "message": "Voice not found"
  }
}
```
**Cause:** Invalid `voice_id` in request path.
**Fix:**
```bash
# List your available voices
curl -s https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
  jq '.voices[] | {voice_id, name, category}'
```

**Error: `text_too_long`**
```json
{
  "detail": {
    "status": "text_too_long",
    "message": "Text is too long. Maximum text length is 5000 characters."
  }
}
```
**Cause:** Single TTS request exceeds 5,000 characters.
**Fix:** Split text into chunks. Use `previous_text` and `next_text` parameters to maintain prosody across chunks:
```typescript
const audio = await client.textToSpeech.convert(voiceId, {
  text: currentChunk,
  previous_text: previousChunk,  // Helps maintain flow
  next_text: nextChunk,          // Helps maintain flow
  model_id: "eleven_multilingual_v2",
});
```

**Error: `model_not_found`**
```json
{
  "detail": {
    "status": "model_not_found",
    "message": "Model not found"
  }
}
```
**Cause:** Invalid `model_id` string.
**Fix:** Use exact model IDs: `eleven_v3`, `eleven_multilingual_v2`, `eleven_flash_v2_5`, `eleven_turbo_v2_5`, `eleven_monolingual_v1`, `eleven_english_sts_v2`.

---

#### HTTP 429 — Rate Limited

**Error: `too_many_concurrent_requests`**
```json
{
  "detail": {
    "status": "too_many_concurrent_requests",
    "message": "Too many concurrent requests"
  }
}
```
**Cause:** Exceeded concurrent request limit for your plan.
**Fix:** Queue requests. Concurrency limits by plan:

| Plan | Concurrent Requests |
|------|-------------------|
| Free | 2 |
| Starter | 3 |
| Creator | 5 |
| Pro | 10 |
| Scale | 15 |
| Business | 15 |

```typescript
import PQueue from "p-queue";
const queue = new PQueue({ concurrency: 5 }); // Match your plan
await queue.add(() => client.textToSpeech.convert(voiceId, options));
```

**Error: `system_busy`**
```json
{
  "detail": {
    "status": "system_busy",
    "message": "Our services are experiencing high traffic"
  }
}
```
**Cause:** ElevenLabs servers under heavy load.
**Fix:** Retry with exponential backoff (the SDK does this automatically with `maxRetries`):
```typescript
const client = new ElevenLabsClient({
  maxRetries: 3, // Auto-retries 429 and 5xx
});
```

---

#### HTTP 422 — Validation Error

**Error: `invalid_voice_sample`**
```json
{
  "detail": {
    "status": "invalid_voice_sample",
    "message": "Invalid audio file"
  }
}
```
**Cause:** Voice cloning audio file is corrupt, too short, or wrong format.
**Fix:** Ensure audio is MP3/WAV/M4A/FLAC, at least 30 seconds, clean speech without music.

---

#### WebSocket Errors

**Connection fails silently:**
```
WebSocket connection to 'wss://api.elevenlabs.io/v1/text-to-speech/...' failed
```
**Cause:** Missing `xi_api_key` in the first WebSocket message, or using `eleven_v3` model (not supported for WebSocket).
**Fix:**
```typescript
ws.send(JSON.stringify({
  text: " ",
  xi_api_key: process.env.ELEVENLABS_API_KEY,  // Required in WS
  model_id: "eleven_flash_v2_5",  // v3 NOT supported for WS
}));
```

### Step 3: Debug Checklist

1. Verify API key: `curl -s https://api.elevenlabs.io/v1/user -H "xi-api-key: $ELEVENLABS_API_KEY"`
2. Check quota: Look at `character_count` vs `character_limit` in the response
3. Verify voice_id: `GET /v1/voices` to list valid IDs
4. Check model_id: Must be an exact match (see table above)
5. Check request size: Text must be under 5,000 characters
6. Check concurrency: Are you exceeding your plan's concurrent limit?
7. Check ElevenLabs status: https://status.elevenlabs.io

## Error Handling

| HTTP | Error | Retryable | Action |
|------|-------|-----------|--------|
| 400 | Bad request | No | Fix request parameters |
| 401 | Auth/quota | No | Check key or upgrade plan |
| 404 | Not found | No | Verify voice_id/model_id |
| 422 | Validation | No | Fix input data format |
| 429 | Rate limit | Yes | Backoff + queue requests |
| 500+ | Server error | Yes | Retry with backoff |

## Resources

- [ElevenLabs Error Messages](https://elevenlabs.io/docs/developers/resources/error-messages)
- [API Error 429 Help](https://help.elevenlabs.io/hc/en-us/articles/19571824571921)
- [API Error 401 Help](https://help.elevenlabs.io/hc/en-us/articles/19572237925521)
- [ElevenLabs Status](https://status.elevenlabs.io)

## Next Steps

For comprehensive debugging, see `elevenlabs-debug-bundle`. For rate limit handling, see `elevenlabs-rate-limits`.
