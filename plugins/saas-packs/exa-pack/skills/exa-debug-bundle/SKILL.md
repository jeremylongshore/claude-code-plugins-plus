---
name: exa-debug-bundle
description: |
  Collect Exa debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Exa problems.
  Trigger with phrases like "exa debug", "exa support bundle",
  "collect exa logs", "exa diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, debugging]

---
# Exa Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`npm list exa-js 2>/dev/null | grep exa-js || echo 'exa-js not installed'`
!`echo "EXA_API_KEY: ${EXA_API_KEY:+SET (${#EXA_API_KEY} chars)}"`

## Overview
Collect all necessary diagnostic information for Exa support tickets. Exa error responses include a `requestId` field — always include it when contacting support at hello@exa.ai.

## Instructions

### Step 1: Quick Connectivity Test
```bash
set -euo pipefail

echo "=== Exa Connectivity Test ==="
echo "API Key: ${EXA_API_KEY:+SET (${#EXA_API_KEY} chars)}"
echo ""

# Test basic search endpoint
HTTP_CODE=$(curl -s -o /tmp/exa-debug.json -w "%{http_code}" \
  -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"debug connectivity test","numResults":1}')

echo "HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
  echo "Status: HEALTHY"
  python3 -c "import json; d=json.load(open('/tmp/exa-debug.json')); print(f'Results: {len(d.get(\"results\",[]))}')" 2>/dev/null
else
  echo "Status: UNHEALTHY"
  echo "Response:"
  cat /tmp/exa-debug.json | python3 -m json.tool 2>/dev/null || cat /tmp/exa-debug.json
fi
```

### Step 2: Capture Request/Response Details
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

async function debugSearch(query: string) {
  const startTime = performance.now();
  try {
    const result = await exa.searchAndContents(query, {
      numResults: 3,
      text: { maxCharacters: 500 },
    });

    const duration = performance.now() - startTime;
    console.log("=== Debug Info ===");
    console.log(`Query: "${query}"`);
    console.log(`Duration: ${duration.toFixed(0)}ms`);
    console.log(`Results: ${result.results.length}`);
    console.log(`Has autoprompt: ${!!result.autopromptString}`);
    for (const r of result.results) {
      console.log(`  [${r.score.toFixed(3)}] ${r.title} (${r.url})`);
      console.log(`    Text: ${r.text ? `${r.text.length} chars` : "none"}`);
    }
  } catch (err: any) {
    const duration = performance.now() - startTime;
    console.error("=== Error Debug ===");
    console.error(`Query: "${query}"`);
    console.error(`Duration: ${duration.toFixed(0)}ms`);
    console.error(`Status: ${err.status || "unknown"}`);
    console.error(`Message: ${err.message}`);
    console.error(`RequestId: ${err.requestId || err.request_id || "none"}`);
    console.error(`Error tag: ${err.error_tag || err.tag || "none"}`);
  }
}
```

### Step 3: Create Debug Bundle Script
```bash
#!/bin/bash
set -euo pipefail
# exa-debug-bundle.sh

BUNDLE_DIR="exa-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Exa Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"

# Environment info
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'N/A')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'N/A')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -a)" >> "$BUNDLE_DIR/summary.txt"
echo "EXA_API_KEY: ${EXA_API_KEY:+SET}" >> "$BUNDLE_DIR/summary.txt"

# SDK version
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- SDK ---" >> "$BUNDLE_DIR/summary.txt"
npm list exa-js 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "exa-js not found" >> "$BUNDLE_DIR/summary.txt"

# API connectivity test
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- API Test ---" >> "$BUNDLE_DIR/summary.txt"
HTTP_CODE=$(curl -s -o "$BUNDLE_DIR/api-response.json" -w "%{http_code}" \
  -X POST https://api.exa.ai/search \
  -H "x-api-key: ${EXA_API_KEY:-missing}" \
  -H "Content-Type: application/json" \
  -d '{"query":"debug test","numResults":1}' 2>/dev/null)
echo "HTTP Status: $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"

# Package bundle
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo ""
echo "IMPORTANT: Review $BUNDLE_DIR/summary.txt before sharing."
echo "Include the requestId from any error responses when contacting hello@exa.ai"
```

## Output
- `exa-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` — environment, SDK version, API connectivity
  - `api-response.json` — raw API response from test query

## Sensitive Data Handling
**Always redact before sharing:**
- API keys and tokens
- Query content containing PII
- Internal URLs or domain names

**Safe to include:**
- HTTP status codes and error tags
- `requestId` from error responses
- SDK and runtime versions
- Latency measurements

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `curl: command not found` | curl not installed | Install curl or use node script |
| Empty API response | Network firewall | Check outbound HTTPS to api.exa.ai |
| 401 in connectivity test | Bad API key | Regenerate at dashboard.exa.ai |
| Bundle script fails | Missing permissions | Run with `bash` not `sh` |

## Resources
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)
- [Exa Support](mailto:hello@exa.ai)

## Next Steps
For rate limit issues, see `exa-rate-limits`. For common error solutions, see `exa-common-errors`.
