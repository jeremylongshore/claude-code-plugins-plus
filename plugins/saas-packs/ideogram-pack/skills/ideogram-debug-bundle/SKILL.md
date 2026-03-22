---
name: ideogram-debug-bundle
description: |
  Collect Ideogram debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Ideogram problems.
  Trigger with phrases like "ideogram debug", "ideogram support bundle",
  "collect ideogram logs", "ideogram diagnostic".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, debugging, support]

---
# Ideogram Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`echo "IDEOGRAM_API_KEY set: ${IDEOGRAM_API_KEY:+YES}${IDEOGRAM_API_KEY:-NO}"`

## Overview
Collect diagnostic information for Ideogram API issues. Produces a tarball with environment details, API connectivity tests, request/response samples, and redacted configuration -- suitable for attaching to support tickets.

## Prerequisites
- `IDEOGRAM_API_KEY` environment variable set
- `curl` and `tar` available
- Permission to collect environment info

## Instructions

### Step 1: Full Debug Bundle Script
```bash
#!/bin/bash
set -euo pipefail

BUNDLE_DIR="ideogram-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

cat > "$BUNDLE_DIR/summary.txt" <<HEADER
=== Ideogram Debug Bundle ===
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Hostname: $(hostname)
HEADER

# --- Environment ---
{
  echo "--- Runtime ---"
  echo "Node: $(node --version 2>/dev/null || echo 'not installed')"
  echo "Python: $(python3 --version 2>/dev/null || echo 'not installed')"
  echo "OS: $(uname -srm)"
  echo ""
  echo "--- Ideogram Config ---"
  echo "API Key: ${IDEOGRAM_API_KEY:+SET (length=${#IDEOGRAM_API_KEY})}${IDEOGRAM_API_KEY:-NOT SET}"
} >> "$BUNDLE_DIR/summary.txt"

# --- API Connectivity Test ---
{
  echo ""
  echo "--- API Test (Legacy Generate) ---"
  RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}" \
    -X POST https://api.ideogram.ai/generate \
    -H "Api-Key: ${IDEOGRAM_API_KEY:-missing}" \
    -H "Content-Type: application/json" \
    -d '{"image_request":{"prompt":"debug test","model":"V_2_TURBO","magic_prompt_option":"OFF"}}' \
    2>&1 || echo "CURL_FAILED")
  echo "$RESPONSE" | grep -E "HTTP_STATUS|TIME_TOTAL|error" || true
  echo "$RESPONSE" | head -5 > "$BUNDLE_DIR/api-response-sample.json"
} >> "$BUNDLE_DIR/summary.txt"

# --- DNS Resolution ---
{
  echo ""
  echo "--- DNS & Network ---"
  echo "DNS resolve: $(nslookup api.ideogram.ai 2>/dev/null | grep -A1 'Name:' | tail -1 || echo 'nslookup unavailable')"
  echo "TLS test: $(curl -s -o /dev/null -w '%{ssl_verify_result}' https://api.ideogram.ai/ 2>/dev/null || echo 'failed')"
} >> "$BUNDLE_DIR/summary.txt"

# --- Local Configuration (redacted) ---
if [ -f .env ]; then
  sed 's/=.*/=***REDACTED***/' .env > "$BUNDLE_DIR/env-redacted.txt"
fi

# --- Package versions ---
{
  echo ""
  echo "--- Dependencies ---"
  npm list --depth=0 2>/dev/null || echo "No package.json found"
  pip freeze 2>/dev/null | grep -i ideogram || echo "No Python ideogram packages"
} >> "$BUNDLE_DIR/summary.txt"

# --- Package ---
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Contents: summary.txt, api-response-sample.json, env-redacted.txt"
```

### Step 2: Quick One-Line Diagnostics
```bash
set -euo pipefail
# Test API key validity
curl -s -o /dev/null -w "Status: %{http_code} | Time: %{time_total}s\n" \
  -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request":{"prompt":"test","model":"V_2_TURBO","magic_prompt_option":"OFF"}}'

# Test V3 endpoint
curl -s -o /dev/null -w "V3 Status: %{http_code}\n" \
  -X POST https://api.ideogram.ai/v1/ideogram-v3/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -F "prompt=test" -F "rendering_speed=FLASH"
```

### Step 3: Request Logging Wrapper
```typescript
// Add to your client for capturing failed requests
async function debuggableRequest(url: string, init: RequestInit) {
  const start = Date.now();
  const response = await fetch(url, init);
  const elapsed = Date.now() - start;

  if (!response.ok) {
    const body = await response.text();
    console.error(JSON.stringify({
      timestamp: new Date().toISOString(),
      url,
      method: init.method,
      status: response.status,
      elapsed_ms: elapsed,
      error: body.slice(0, 500),
      // Redact API key from headers
      headers: Object.fromEntries(
        Object.entries(init.headers ?? {}).map(([k, v]) =>
          [k, k.toLowerCase() === "api-key" ? "***REDACTED***" : v]
        )
      ),
    }, null, 2));
    throw new Error(`Ideogram ${response.status}: ${body}`);
  }

  return response;
}
```

## Sensitive Data Handling
**ALWAYS REDACT before sharing:**
- API keys and tokens
- `.env` file values
- PII in prompts
- File paths containing usernames

**Safe to include:**
- HTTP status codes and error messages
- Request timing and latency
- Runtime versions (Node, Python)
- Package dependency versions

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| API key status | Auth verification | SET/NOT SET only |
| HTTP status code | Error classification | Full code |
| Response time | Latency diagnosis | Seconds |
| DNS resolution | Network diagnosis | IP only |
| Package versions | Compatibility check | Version strings |

## Output
- `ideogram-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` -- environment, API test, DNS, dependencies
  - `api-response-sample.json` -- truncated API response
  - `env-redacted.txt` -- configuration with values masked

## Resources
- [Ideogram API Overview](https://developer.ideogram.ai/ideogram-api/api-overview)
- Enterprise support: `partnership@ideogram.ai`

## Next Steps
For rate limit issues, see `ideogram-rate-limits`.
