---
name: firecrawl-debug-bundle
description: |
  Collect Firecrawl debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Firecrawl problems.
  Trigger with phrases like "firecrawl debug", "firecrawl support bundle",
  "collect firecrawl logs", "firecrawl diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, debugging]

---
# Firecrawl Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`npm list @mendable/firecrawl-js 2>/dev/null | grep firecrawl || echo 'SDK not installed'`

## Overview
Collect all diagnostic information needed for Firecrawl support tickets. Tests API connectivity, checks SDK version, verifies credentials, captures error context, and packages it all into a redacted bundle.

## Prerequisites
- Firecrawl SDK installed
- `FIRECRAWL_API_KEY` environment variable set
- Access to application logs

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
set -euo pipefail
# firecrawl-debug-bundle.sh

BUNDLE_DIR="firecrawl-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Firecrawl Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Environment
echo "--- Runtime ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Node: N/A" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -a)" >> "$BUNDLE_DIR/summary.txt"
echo "FIRECRAWL_API_KEY: ${FIRECRAWL_API_KEY:+SET (${#FIRECRAWL_API_KEY} chars)}" >> "$BUNDLE_DIR/summary.txt"
echo "FIRECRAWL_API_URL: ${FIRECRAWL_API_URL:-https://api.firecrawl.dev (default)}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect SDK and API Status
```bash
set -euo pipefail
# SDK version
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- SDK ---" >> "$BUNDLE_DIR/summary.txt"
npm list @mendable/firecrawl-js 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Not found in npm" >> "$BUNDLE_DIR/summary.txt"
pip show firecrawl-py 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || true

# API connectivity test
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
API_RESPONSE=$(curl -s -w "\n%{http_code}" https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY:-missing}" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}' 2>&1)
HTTP_CODE=$(echo "$API_RESPONSE" | tail -1)
echo "API Status: HTTP $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"

# Credit balance
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Credits ---" >> "$BUNDLE_DIR/summary.txt"
curl -s https://api.firecrawl.dev/v1/team/credits \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY:-missing}" 2>/dev/null | \
  jq '{credits_remaining, plan}' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "Could not fetch credits" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Capture Error Context
```bash
set -euo pipefail
# Recent error logs (redacted)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Recent Errors ---" >> "$BUNDLE_DIR/summary.txt"
grep -ri "firecrawl\|scrape\|crawl" /tmp/*.log 2>/dev/null | tail -30 >> "$BUNDLE_DIR/errors.txt" || echo "No log files found" >> "$BUNDLE_DIR/errors.txt"

# Redact secrets from any config
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
cat .env 2>/dev/null | sed 's/\(API_KEY\|SECRET\|TOKEN\|PASSWORD\)=.*/\1=***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt" || echo "No .env file" >> "$BUNDLE_DIR/config-redacted.txt"
```

### Step 4: Run Diagnostic Scrape
```typescript
// diagnostic-scrape.ts — include output in debug bundle
import FirecrawlApp from "@mendable/firecrawl-js";

async function runDiagnostic() {
  const firecrawl = new FirecrawlApp({
    apiKey: process.env.FIRECRAWL_API_KEY!,
  });

  const tests = [
    { name: "Basic scrape", fn: () => firecrawl.scrapeUrl("https://example.com", { formats: ["markdown"] }) },
    { name: "Map endpoint", fn: () => firecrawl.mapUrl("https://example.com") },
  ];

  for (const test of tests) {
    const start = Date.now();
    try {
      const result = await test.fn();
      console.log(`PASS: ${test.name} (${Date.now() - start}ms)`);
    } catch (err: any) {
      console.log(`FAIL: ${test.name} (${Date.now() - start}ms) — ${err.statusCode}: ${err.message}`);
    }
  }
}

runDiagnostic();
```

### Step 5: Package Bundle
```bash
set -euo pipefail
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review for sensitive data before sharing!"
rm -rf "$BUNDLE_DIR"
```

## Output
- `firecrawl-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` — Runtime, SDK version, API status, credits
  - `errors.txt` — Recent error logs
  - `config-redacted.txt` — Configuration with secrets masked

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| Node/Python version | Compatibility check | Yes |
| SDK version | Version-specific bugs | Yes |
| API HTTP status | Connectivity | Yes |
| Credit balance | Quota issues | Yes |
| Diagnostic scrape | End-to-end test | Yes |

## ALWAYS REDACT
- API keys (anything starting with `fc-`)
- Passwords, tokens, secrets
- PII in scraped content

## Resources
- [Firecrawl Status](https://firecrawl.dev/status)
- [Firecrawl Dashboard](https://firecrawl.dev/app)
- [GitHub Issues](https://github.com/mendableai/firecrawl/issues)

## Next Steps
For rate limit issues, see `firecrawl-rate-limits`.
