---
name: cohere-debug-bundle
description: |
  Collect Cohere debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Cohere API problems.
  Trigger with phrases like "cohere debug", "cohere support bundle",
  "collect cohere logs", "cohere diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Debug Bundle

## Overview
Collect all diagnostic information needed to resolve Cohere API v2 issues. Generates a support-ready bundle with environment info, request/response logs, and SDK version data.

## Prerequisites
- `cohere-ai` SDK installed
- Access to application logs
- `curl` and `jq` available

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# cohere-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="cohere-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Cohere Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment and SDK Info

```bash
# Runtime versions
echo "--- Runtime ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Node.js: not found" >> "$BUNDLE_DIR/summary.txt"
python3 --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Python: not found" >> "$BUNDLE_DIR/summary.txt"

# SDK version
echo "--- SDK ---" >> "$BUNDLE_DIR/summary.txt"
npm list cohere-ai 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "cohere-ai: not installed (npm)" >> "$BUNDLE_DIR/summary.txt"
pip show cohere 2>/dev/null | grep Version >> "$BUNDLE_DIR/summary.txt" || echo "cohere: not installed (pip)" >> "$BUNDLE_DIR/summary.txt"

# API key status (never log the actual key)
echo "--- Auth ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "${CO_API_KEY:-}" ]; then
  echo "CO_API_KEY: SET (${#CO_API_KEY} chars, starts with ${CO_API_KEY:0:4}...)" >> "$BUNDLE_DIR/summary.txt"
else
  echo "CO_API_KEY: NOT SET" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 3: Test API Connectivity

```bash
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"

# Test each endpoint
for endpoint in chat embed rerank classify; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "https://api.cohere.com/v2/$endpoint" \
    -H "Authorization: Bearer ${CO_API_KEY:-invalid}" \
    -H "Content-Type: application/json" \
    -d '{}' 2>/dev/null || echo "UNREACHABLE")
  echo "$endpoint: HTTP $STATUS" >> "$BUNDLE_DIR/summary.txt"
done

# Check service status
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Service Status ---" >> "$BUNDLE_DIR/summary.txt"
curl -s https://status.cohere.com/api/v2/status.json 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"][\"description\"]}')" \
  >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "Status page: unreachable" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Capture Request/Response Debug

```typescript
// Add to your app for temporary debug logging
import { CohereClientV2, CohereError } from 'cohere-ai';
import fs from 'fs';

const debugLog: Array<{
  timestamp: string;
  endpoint: string;
  model?: string;
  status: 'success' | 'error';
  durationMs: number;
  error?: string;
  tokensUsed?: { input: number; output: number };
}> = [];

async function debugWrappedCall<T>(
  endpoint: string,
  model: string | undefined,
  fn: () => Promise<T>
): Promise<T> {
  const start = Date.now();
  try {
    const result = await fn();
    debugLog.push({
      timestamp: new Date().toISOString(),
      endpoint,
      model,
      status: 'success',
      durationMs: Date.now() - start,
    });
    return result;
  } catch (err) {
    debugLog.push({
      timestamp: new Date().toISOString(),
      endpoint,
      model,
      status: 'error',
      durationMs: Date.now() - start,
      error: err instanceof CohereError
        ? `${err.statusCode}: ${err.message}`
        : String(err),
    });
    throw err;
  }
}

// Dump log to file
function exportDebugLog(path: string) {
  fs.writeFileSync(path, JSON.stringify(debugLog, null, 2));
}
```

### Step 5: Package and Redact

```bash
# Collect application logs (redacted)
grep -i "cohere\|CohereError\|CO_API_KEY" /var/log/app/*.log 2>/dev/null | \
  sed 's/Bearer [^ ]*/Bearer ***REDACTED***/g' | \
  tail -100 > "$BUNDLE_DIR/app-logs.txt"

# Package bundle
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle: $BUNDLE_DIR.tar.gz ($(du -h "$BUNDLE_DIR.tar.gz" | cut -f1))"
rm -rf "$BUNDLE_DIR"
```

## Bundle Contents

| File | Contents | Sensitive? |
|------|----------|-----------|
| `summary.txt` | Runtime, SDK version, API key status, connectivity | No |
| `app-logs.txt` | Recent Cohere-related log lines (redacted) | Redacted |
| `debug-log.json` | Request timing, errors, token usage | No |

**Always redact:** API keys, bearer tokens, PII in request bodies. **Safe to include:** Error messages, HTTP status codes, SDK versions, timing data.

## Quick One-Liner Diagnostics

```bash
# Full diagnostic in one command
echo "Node: $(node -v 2>/dev/null || echo N/A) | SDK: $(npm list cohere-ai 2>/dev/null | grep cohere || echo N/A) | Key: ${CO_API_KEY:+SET} | API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer ${CO_API_KEY:-x}" https://api.cohere.com/v2/chat -H 'Content-Type: application/json' -d '{}' 2>/dev/null)"
```

## Error Handling
| Item | Purpose |
|------|---------|
| SDK version | Identify version-specific bugs |
| API key status | Auth configuration issues |
| Endpoint connectivity | Network/firewall problems |
| Request timing | Latency and timeout diagnosis |
| Error codes | Classify issue type (4xx vs 5xx) |

## Resources
- [Cohere Status Page](https://status.cohere.com)
- [Cohere Error Codes](https://docs.cohere.com/reference/errors)
- [Cohere Support](https://support.cohere.com)

## Next Steps
For rate limit issues, see `cohere-rate-limits`.
