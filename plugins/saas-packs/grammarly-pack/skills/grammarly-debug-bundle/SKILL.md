---
name: grammarly-debug-bundle
description: 'Collect Grammarly debug evidence for support tickets and troubleshooting.

  Use when encountering persistent issues, preparing support tickets,

  or collecting diagnostic information for Grammarly problems.

  Trigger with phrases like "grammarly debug", "grammarly support bundle",

  "collect grammarly logs", "grammarly diagnostic".

  '
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
---
# Grammarly Debug Bundle

## Overview

Collect Grammarly API connectivity status, text analysis response quality, authentication state, and rate limit usage into a single diagnostic archive. This bundle helps troubleshoot text check failures, missing suggestions, OAuth token expiration, and API response latency.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-grammarly-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Grammarly Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "GRAMMARLY_API_KEY: ${GRAMMARLY_API_KEY:+[SET]}" >> "$BUNDLE/summary.txt"
echo "GRAMMARLY_CLIENT_ID: ${GRAMMARLY_CLIENT_ID:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity — text check endpoint
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${GRAMMARLY_API_KEY}" \
  -H "Content-Type: application/json" \
  -X POST https://api.grammarly.com/v1/check \
  -d '{"text": "This are a diagnostic test sentence with intentional grammar errors to verify the API returns suggestions."}' \
  2>/dev/null || echo "000")
echo "API Status: HTTP $HTTP" >> "$BUNDLE/summary.txt"

# Full text check response
curl -s -H "Authorization: Bearer ${GRAMMARLY_API_KEY}" \
  -H "Content-Type: application/json" -X POST https://api.grammarly.com/v1/check \
  -d '{"text": "This are a diagnostic test sentence with intentional grammar errors to verify the API returns suggestions."}' \
  > "$BUNDLE/text-check.json" 2>&1 || true

# Account info and rate limit headers
curl -s -D "$BUNDLE/rate-headers.txt" -H "Authorization: Bearer ${GRAMMARLY_API_KEY}" \
  https://api.grammarly.com/v1/account > "$BUNDLE/account.json" 2>&1 || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-grammarly-*.tar.gz
cat debug-grammarly-*/summary.txt                 # Auth + API status
jq '.alerts | length' debug-grammarly-*/text-check.json  # Suggestion count
jq '.alerts[] | {type, text}' debug-grammarly-*/text-check.json  # Suggestion details
grep -i "ratelimit\|retry" debug-grammarly-*/rate-headers.txt
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| API returns 401 | `summary.txt` shows HTTP 401 | Refresh OAuth token or regenerate API key in Grammarly Developer Hub |
| Zero suggestions returned | `text-check.json` has empty alerts array | Verify text exceeds minimum word count (30 words); check language parameter |
| High latency (>5s) | `text-check.json` shows slow response time | Reduce text payload size; check for network proxy interference |
| Rate limited (429) | `rate-headers.txt` shows Retry-After | Implement request queuing; reduce check frequency per user session |
| Client ID mismatch | `account.json` returns permission error | Verify `GRAMMARLY_CLIENT_ID` matches the app registered in Developer Hub |

## Automated Health Check

```typescript
async function checkGrammarly(): Promise<void> {
  const key = process.env.GRAMMARLY_API_KEY;
  if (!key) { console.error("[FAIL] GRAMMARLY_API_KEY not set"); return; }

  const res = await fetch("https://api.grammarly.com/v1/check", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ text: "This are a test sentence with grammar errors for diagnostic purposes and validation." }),
  });
  console.log(`[${res.ok ? "OK" : "FAIL"}] API: HTTP ${res.status}`);

  if (res.ok) {
    const data = await res.json();
    console.log(`[INFO] Suggestions returned: ${data.alerts?.length ?? 0}`);
  }
}
checkGrammarly();
```

## Resources

- [Grammarly Status](https://status.grammarly.com)

## Next Steps

See `grammarly-common-errors`.
