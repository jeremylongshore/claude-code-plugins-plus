---
name: groq-debug-bundle
description: 'Collect Groq debug evidence for support tickets and troubleshooting.

  Use when encountering persistent issues, preparing support tickets,

  or collecting diagnostic information for Groq problems.

  Trigger with phrases like "groq debug", "groq support bundle",

  "collect groq logs", "groq diagnostic".

  '
allowed-tools: Bash(grep:*), Bash(curl:*), Bash(tar:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- debugging
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Debug Bundle

## Current State

!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`npm list groq-sdk 2>/dev/null | grep groq-sdk || echo 'groq-sdk not installed'`

## Overview

Collect all diagnostic information needed to resolve Groq API issues. Produces a redacted support bundle (a `.tar.gz`) with environment info, SDK version, connectivity test results, rate limit headers, per-model latency, and redacted application logs — everything a Groq support engineer needs, with secrets masked before the archive is written.

## Prerequisites

- `GROQ_API_KEY` set in environment
- `curl` and `jq` available
- Access to application logs (optional — the log step is skipped if `logs/` is absent)

## Instructions

The bundle is assembled by a six-step shell script. Each step appends to a file inside a timestamped `$BUNDLE_DIR`; the final step tars it and deletes the working copy. Run the steps in order in one shell, or paste the whole sequence into a script.

1. **Environment** — capture OS, Node/Python versions, installed Groq SDK versions, and a masked key fingerprint (length + 4-char prefix only, never the key).
2. **Connectivity** — hit `GET /openai/v1/models` to confirm auth and count available models.
3. **Rate limits** — send a 1-token completion and grab the `x-ratelimit-*`, `retry-after`, and `x-request-id` response headers.
4. **Latency** — time a minimal completion against each model of interest.
5. **Log extraction** — grep recent Groq/429/rate-limit errors from `logs/*.log` and mask any `gsk_` keys and `.env` values.
6. **Package** — `tar -czf` the directory, remove the working copy, and print a review reminder.

The skeleton of Step 1 (the rest is in the full walkthrough):

```bash
#!/bin/bash
set -euo pipefail
BUNDLE_DIR="groq-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"
# ... append environment, connectivity, rate-limits, latency, logs ...
```

See **[references/implementation.md](references/implementation.md)** for the complete, copy-pasteable six-step script.

## Output

A single archive named `groq-debug-TIMESTAMP.tar.gz` (where TIMESTAMP is `YYYYMMDD-HHMMSS`) containing:

| File | Purpose | Sensitive? |
|------|---------|-----------|
| `environment.txt` | Node/Python versions, SDK version, key fingerprint | Key prefix only |
| `connectivity.txt` | API reachability, model count | No |
| `rate-limits.txt` | Current rate limit headers | No |
| `latency.txt` | Response times per model | No |
| `app-logs.txt` | Recent error logs (redacted) | Redacted |
| `config-redacted.txt` | Config keys only (values masked) | Redacted |

The TypeScript diagnostic (see Examples) instead prints a JSON report with `auth`, `modelsAvailable`, `completion`, `latencyMs`, `model`, and `usage`.

## Error Handling

- **`GROQ_API_KEY` unset** — `environment.txt` records `NOT SET` and every `curl` step returns `401`; export the key before collecting.
- **`401 Invalid API Key`** — the key is wrong or revoked; the bundle still captures the failure, which is the evidence support needs.
- **`jq: command not found`** — install `jq`, or the connectivity/model-count lines will be empty (the rest of the bundle still builds).
- **No `logs/` directory** — Step 5 is skipped silently; the bundle omits `app-logs.txt` rather than failing.
- **`429` during latency/rate-limit steps** — expected when debugging throttling; the captured `retry-after` and `x-ratelimit-*` headers are the point. For deeper 429 handling see `groq-rate-limits`.

## ALWAYS Redact Before Sharing

- API keys (anything starting with `gsk_`)
- Bearer tokens
- PII (emails, names, IDs)
- Internal hostnames and IPs

## Examples

A quick SDK-based diagnostic that confirms auth, lists models, times a completion, and prints a JSON report:

```typescript
import Groq from "groq-sdk";
const groq = new Groq();
const models = await groq.models.list();  // 401 here = bad key
console.log(models.data.map((m) => m.id));
```

Full TypeScript diagnostic, healthy/bad-key sample outputs, and an end-to-end shell run with the resulting tarball listing are in **[references/examples.md](references/examples.md)**.

## Resources

- [Groq Error Codes](https://console.groq.com/docs/errors)
- [Groq Status Page](https://status.groq.com)
- [Full implementation walkthrough](references/implementation.md)
- [Diagnostic examples & sample output](references/examples.md)

## Next Steps

For rate limit and 429 throttling issues, escalate to the `groq-rate-limits` skill, which covers backoff strategy and quota inspection in depth.
