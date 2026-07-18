---
name: groq-common-errors
description: 'Diagnose and fix Groq API errors with real error codes and solutions.

  Use when encountering Groq errors, debugging failed requests,

  or troubleshooting integration issues.

  Trigger with phrases like "groq error", "fix groq",

  "groq not working", "debug groq", "groq 429".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- debugging
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Common Errors

## Overview

Comprehensive reference for Groq API error codes, their root causes, and proven fixes. Groq returns standard HTTP status codes with structured error bodies and rate-limit headers. This skill walks the diagnosis from raw error string to fix, then hands off to the full per-status reference for depth.

Every Groq error body follows one shape — read the `code` and `type` first:

```json
{
  "error": {
    "message": "Rate limit reached for model `llama-3.3-70b-versatile`...",
    "type": "tokens",
    "code": "rate_limit_exceeded"
  }
}
```

## Prerequisites

- `GROQ_API_KEY` exported in the environment (keys start with `gsk_`).
- `curl` and `jq` available for the diagnostic probes below.
- For SDK-level handling: `groq-sdk` (TypeScript) or `groq` (Python) installed.

## Instructions

1. **Capture the failing status and body.** Read the raw error response — the HTTP status plus the `code`/`type` fields determine the whole diagnosis path.
2. **Confirm the key works** before assuming anything deeper:

   ```bash
   set -euo pipefail
   # Verify API key is valid — expect a model count, not an auth error
   curl -s https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY" | jq '.data | length'
   ```

3. **Confirm the model still exists.** Many 400s are deprecated model IDs — list the live models and Grep your codebase for any stale ID:

   ```bash
   curl -s https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY" | jq '.data[].id' | sort
   ```

4. **Map the status to a fix** using the table below, then drill into [references/error-reference.md](references/error-reference.md) for the exact error string, causes, and copy-paste fix.
5. **For SDK integrations**, branch on the typed exception classes — see [references/sdk-error-handling.md](references/sdk-error-handling.md).

## Output

A diagnosis that names the error class, the root cause, and the concrete fix — for example: "429 on TPM: token budget exhausted; add the single-retry `handleRateLimit` wrapper and honor `retry-after`," or "400: `mixtral-8x7b-32768` is deprecated; switch to `llama-3.3-70b-versatile`." When run against real code, the output is the edited call site plus a verification `curl` that returns `200`.

## Error Handling

Map the HTTP status to its cause; full error strings, rate-limit headers, and fixes live in [references/error-reference.md](references/error-reference.md).

| Status | Meaning | First move |
|--------|---------|------------|
| **401** | Invalid / missing key | Confirm `GROQ_API_KEY` starts with `gsk_`; test with `/models` |
| **429** | RPM / TPM / RPD limit hit | Read `retry-after`; back off and single-retry |
| **400** | Deprecated model or bad params | List live models; replace stale IDs |
| **413** | Request over context window | Trim prompt (Llama models cap at 128K tokens) |
| **500 / 503** | Groq-side outage or overload | Retry with backoff; fall back model; check status page |

When the failure is transient (429/500/503), retry with backoff and honor `retry-after` rather than hammering. When it is structural (401/400/413), fix the request — retrying will not help.

## Examples

Minimal end-to-end probe that isolates auth vs. model vs. payload problems:

```bash
# A 200 here means key + model + payload are all valid; a non-200 status
# tells you which layer failed.
curl -s -o /dev/null -w "%{http_code}" \
  https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
```

- **Rate-limit retry wrapper** (TypeScript, honors `retry-after`): see the 429 section of [references/error-reference.md](references/error-reference.md).
- **Typed SDK exception branching** (TypeScript + Python): [references/sdk-error-handling.md](references/sdk-error-handling.md).

## Resources

- [Groq Error Codes](https://console.groq.com/docs/errors)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Model Deprecations](https://console.groq.com/docs/deprecations)
- [Groq Status Page](https://status.groq.com)
- Full per-status reference: [references/error-reference.md](references/error-reference.md)
- SDK error handling + escalation path: [references/sdk-error-handling.md](references/sdk-error-handling.md)
- For comprehensive debugging, see the `groq-debug-bundle` skill.
