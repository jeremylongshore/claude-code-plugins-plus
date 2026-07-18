---
name: elevenlabs-debug-bundle
description: |
  Collect ElevenLabs debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing a support ticket, or
  gathering diagnostic information (SDK version, API connectivity, quota, voice
  inventory, model availability) for an ElevenLabs problem, with secrets
  redacted automatically. Trigger with "elevenlabs debug", "elevenlabs support
  bundle", "collect elevenlabs logs", "elevenlabs diagnostic", "elevenlabs
  support ticket".
allowed-tools: Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(node:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- debugging
- support
compatibility: Designed for Claude Code
---
# ElevenLabs Debug Bundle

## Overview

Collect all diagnostic information needed for ElevenLabs support tickets. Gathers SDK version, API connectivity (HTTP status, DNS, TLS), quota status, voice inventory, and model availability into a single archive while redacting all secrets before anything touches disk.

Two collection paths are available and produce equivalent evidence: a shell script (no code dependency — good for servers and CI) and a programmatic TypeScript collector (good when the app already imports the SDK). The full, ready-to-run source for both lives in [references/implementation.md](references/implementation.md); this file is the high-level workflow.

## Prerequisites

- ElevenLabs SDK installed
- API key configured (to test connectivity)
- Access to application logs
- `jq` available (used by the shell script to format API responses)

## Instructions

The workflow is three steps: run a collector, review the output for stray secrets, then attach it to a support ticket. Follow the summary here and open [references/implementation.md](references/implementation.md) for the complete scripts.

### Step 1: Run a collector

**Shell path** — the script writes each section to `summary.txt`, redacts secrets, then tars and removes the working directory. The skeleton:

```bash
#!/bin/bash
# elevenlabs-debug-bundle.sh
set -euo pipefail
BUNDLE_DIR="elevenlabs-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"
# ... collect environment, SDK versions, connectivity, quota, voices, models ...
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR" && rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

**Programmatic path** — build a structured `DebugReport` when the SDK is already a dependency. Each section is wrapped independently so one failure still returns a partial report:

```typescript
const report = await collectDebugReport();
console.log(JSON.stringify(report, null, 2));
```

Full source for both, including the connectivity/TLS probes and quota/voice/model collectors: [references/implementation.md](references/implementation.md).

### Step 2: Review for secrets

Inspect the archive before sharing — API keys, webhook secrets, and any `.env` value are redacted automatically, but confirm nothing sensitive slipped into an error log or stack trace.

### Step 3: Submit to support

Open a ticket at https://help.elevenlabs.io, attach the bundle, and describe what you expected, what happened, steps to reproduce, and any request IDs from error responses.

## Output

- `elevenlabs-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` — Environment, SDK, connectivity, quota, voices, models
  - `config-redacted.txt` — Configuration with secrets masked
  - `errors.txt` — Recent error logs with API keys redacted

## Sensitive Data Handling

**Always redacted automatically:**

- API keys (replaced with `***REDACTED***`)
- Webhook secrets
- Any value after `=` in .env files

**Safe to include:**

- Error messages and stack traces
- SDK/runtime versions
- Voice IDs and model IDs
- HTTP status codes and latency

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `jq: command not found` | jq not installed | `apt install jq` or `brew install jq` |
| HTTP 0 / curl fails | Network issue | Check DNS and firewall |
| HTTP 401 | Bad API key | Regenerate key at elevenlabs.io |
| Empty voice list | No voices on account | Normal for new free accounts |

## Examples

A healthy shell run produces a masked `summary.txt` whose top signals are `HTTP 200`, `TLS valid: yes`, and `character_count` under `character_limit`:

```console
$ bash elevenlabs-debug-bundle.sh
Bundle created: elevenlabs-debug-20260717-143022.tar.gz
Review for sensitive data before sharing with support.
```

The programmatic collector returns the same evidence as JSON — an empty `errors` array with `connectivity.status: 200` is healthy, while `"errors": ["Voices: 429 Too Many Requests"]` alongside `connectivity.status: 200` isolates a rate-limit on one endpoint:

```json
{ "connectivity": { "status": 200, "latencyMs": 214 },
  "voices": { "total": 12, "cloned": 3, "premade": 9 }, "errors": [] }
```

Worked runs for a healthy account, a `401` bad key, and the full JSON report: [references/examples.md](references/examples.md).

## Resources

- [Full implementation (shell + TypeScript)](references/implementation.md)
- [Worked examples and sample output](references/examples.md)
- [ElevenLabs Support](https://help.elevenlabs.io)
- [ElevenLabs Status](https://status.elevenlabs.io)

## Next Steps

For rate limit issues, see `elevenlabs-rate-limits`. For common errors, see `elevenlabs-common-errors`.
