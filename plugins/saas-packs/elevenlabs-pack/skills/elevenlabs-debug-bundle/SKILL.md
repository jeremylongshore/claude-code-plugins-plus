---
name: elevenlabs-debug-bundle
description: |
  Collect ElevenLabs debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for ElevenLabs problems.
  Trigger: "elevenlabs debug", "elevenlabs support bundle",
  "collect elevenlabs logs", "elevenlabs diagnostic", "elevenlabs support ticket".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, debugging, support]
compatible-with: claude-code
---

# ElevenLabs Debug Bundle

## Overview

Collect all diagnostic information needed for ElevenLabs support tickets. Gathers SDK version, API connectivity, quota status, voice inventory, and model availability while redacting all secrets.

## Prerequisites

- ElevenLabs SDK installed
- API key configured (to test connectivity)
- Access to application logs

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# elevenlabs-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="elevenlabs-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== ElevenLabs Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- Environment ---
echo "--- Runtime Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Node.js: not found" >> "$BUNDLE_DIR/summary.txt"
python3 --version 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Python: not found" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -s) $(uname -r)" >> "$BUNDLE_DIR/summary.txt"
echo "API Key: ${ELEVENLABS_API_KEY:+SET (${#ELEVENLABS_API_KEY} chars)}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- SDK Versions ---
echo "--- SDK Versions ---" >> "$BUNDLE_DIR/summary.txt"
npm list @elevenlabs/elevenlabs-js 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "JS SDK: not installed" >> "$BUNDLE_DIR/summary.txt"
pip show elevenlabs 2>/dev/null | grep -E "^(Name|Version)" >> "$BUNDLE_DIR/summary.txt" || echo "Python SDK: not installed" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- API Connectivity ---
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY:-missing}" 2>/dev/null || echo "FAILED")
echo "GET /v1/user: HTTP $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"

DNS_CHECK=$(dig +short api.elevenlabs.io 2>/dev/null | head -1 || echo "DNS lookup failed")
echo "DNS api.elevenlabs.io: $DNS_CHECK" >> "$BUNDLE_DIR/summary.txt"

TLS_CHECK=$(echo | openssl s_client -connect api.elevenlabs.io:443 2>/dev/null | grep -c "Verify return code: 0" || echo "0")
echo "TLS valid: $([ "$TLS_CHECK" = "1" ] && echo "yes" || echo "no")" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- Subscription & Quota ---
if [ "$HTTP_CODE" = "200" ]; then
  echo "--- Subscription ---" >> "$BUNDLE_DIR/summary.txt"
  curl -s https://api.elevenlabs.io/v1/user \
    -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
    jq '{tier: .subscription.tier, character_count: .subscription.character_count, character_limit: .subscription.character_limit, next_reset: .subscription.next_character_count_reset_unix}' \
    >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
  echo "" >> "$BUNDLE_DIR/summary.txt"

  # --- Voice Inventory ---
  echo "--- Voice Inventory ---" >> "$BUNDLE_DIR/summary.txt"
  curl -s https://api.elevenlabs.io/v1/voices \
    -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
    jq '[.voices[] | {name, voice_id, category}]' \
    >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
  echo "" >> "$BUNDLE_DIR/summary.txt"

  # --- Model Availability ---
  echo "--- Available Models ---" >> "$BUNDLE_DIR/summary.txt"
  curl -s https://api.elevenlabs.io/v1/models \
    -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
    jq '[.[] | {model_id, name, can_do_text_to_speech, can_do_voice_conversion}]' \
    >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
fi

# --- Configuration (redacted) ---
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f .env ]; then
  sed 's/=.*/=***REDACTED***/' .env >> "$BUNDLE_DIR/config-redacted.txt"
fi

# --- Recent Error Logs ---
echo "--- Recent Errors ---" >> "$BUNDLE_DIR/summary.txt"
grep -ri "elevenlabs\|ElevenLabs\|xi-api-key" *.log 2>/dev/null | \
  sed 's/sk_[a-zA-Z0-9]*/sk_***REDACTED***/g' | \
  tail -50 >> "$BUNDLE_DIR/errors.txt" 2>/dev/null || echo "No log files found" >> "$BUNDLE_DIR/errors.txt"

# --- Package Bundle ---
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review for sensitive data before sharing with support."
```

### Step 2: Programmatic Debug Collection

```typescript
// src/elevenlabs/debug.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

interface DebugReport {
  timestamp: string;
  sdk: { package: string; version: string };
  connectivity: { status: number; latencyMs: number };
  subscription: { tier: string; used: number; limit: number; resetAt: string } | null;
  voices: { total: number; cloned: number; premade: number } | null;
  models: string[] | null;
  errors: string[];
}

export async function collectDebugReport(): Promise<DebugReport> {
  const client = new ElevenLabsClient();
  const errors: string[] = [];
  const report: DebugReport = {
    timestamp: new Date().toISOString(),
    sdk: { package: "@elevenlabs/elevenlabs-js", version: "unknown" },
    connectivity: { status: 0, latencyMs: 0 },
    subscription: null,
    voices: null,
    models: null,
    errors,
  };

  // Test connectivity + get user info
  const start = Date.now();
  try {
    const user = await client.user.get();
    report.connectivity = { status: 200, latencyMs: Date.now() - start };
    report.subscription = {
      tier: user.subscription.tier,
      used: user.subscription.character_count,
      limit: user.subscription.character_limit,
      resetAt: new Date(user.subscription.next_character_count_reset_unix * 1000).toISOString(),
    };
  } catch (err: any) {
    report.connectivity = { status: err.statusCode || 0, latencyMs: Date.now() - start };
    errors.push(`Auth: ${err.message}`);
  }

  // Voice inventory
  try {
    const { voices } = await client.voices.getAll();
    report.voices = {
      total: voices.length,
      cloned: voices.filter(v => v.category === "cloned").length,
      premade: voices.filter(v => v.category === "premade").length,
    };
  } catch (err: any) {
    errors.push(`Voices: ${err.message}`);
  }

  // Model availability
  try {
    const models = await client.models.getAll();
    report.models = models.map(m => m.model_id);
  } catch (err: any) {
    errors.push(`Models: ${err.message}`);
  }

  return report;
}

// Usage
const report = await collectDebugReport();
console.log(JSON.stringify(report, null, 2));
```

### Step 3: Submit to Support

1. Run: `bash elevenlabs-debug-bundle.sh` (or the programmatic version)
2. Review the output for any accidentally included secrets
3. Open a ticket at https://help.elevenlabs.io
4. Attach the bundle and describe the issue with:
   - What you expected to happen
   - What actually happened
   - Steps to reproduce
   - Request IDs from error responses (if available)

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

## Resources

- [ElevenLabs Support](https://help.elevenlabs.io)
- [ElevenLabs Status](https://status.elevenlabs.io)
- [API Error Reference](https://elevenlabs.io/docs/developers/resources/error-messages)

## Next Steps

For rate limit issues, see `elevenlabs-rate-limits`. For common errors, see `elevenlabs-common-errors`.
