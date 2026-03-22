---
name: figma-debug-bundle
description: |
  Collect Figma API diagnostic evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Figma API problems.
  Trigger with phrases like "figma debug", "figma support bundle",
  "collect figma logs", "figma diagnostic".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Debug Bundle

## Overview
Collect all diagnostic data needed to troubleshoot Figma REST API issues or submit a support request. Outputs a redacted archive with connectivity tests, token validation, rate limit status, and API response samples.

## Prerequisites
- `FIGMA_PAT` environment variable set
- `curl` and `jq` available
- A Figma file key to test against

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
# figma-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="figma-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Figma Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "---" >> "$BUNDLE_DIR/summary.txt"

# 1. Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -srm)" >> "$BUNDLE_DIR/summary.txt"
echo "PAT configured: ${FIGMA_PAT:+YES (${#FIGMA_PAT} chars)}" >> "$BUNDLE_DIR/summary.txt"
echo "File key: ${FIGMA_FILE_KEY:-NOT SET}" >> "$BUNDLE_DIR/summary.txt"

# 2. API connectivity test
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "GET /v1/me: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o "$BUNDLE_DIR/me.json" -w "%{http_code} %{time_total}s" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# 3. File access test (if key is set)
if [ -n "${FIGMA_FILE_KEY:-}" ]; then
  echo -n "GET /v1/files: " >> "$BUNDLE_DIR/summary.txt"
  curl -s -o "$BUNDLE_DIR/file-meta.json" -w "%{http_code} %{time_total}s" \
    -H "X-Figma-Token: ${FIGMA_PAT}" \
    "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1" >> "$BUNDLE_DIR/summary.txt"
  echo "" >> "$BUNDLE_DIR/summary.txt"
fi

# 4. Rate limit check (capture response headers)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Rate Limit Headers ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -D "$BUNDLE_DIR/headers.txt" -o /dev/null \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me
grep -iE "(rate|retry|figma)" "$BUNDLE_DIR/headers.txt" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "No rate limit headers" >> "$BUNDLE_DIR/summary.txt"

# 5. Redact sensitive data
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Redaction ---" >> "$BUNDLE_DIR/summary.txt"
# Remove email from /v1/me response
if [ -f "$BUNDLE_DIR/me.json" ]; then
  jq '{handle: .handle, id: .id, img_url: "[REDACTED]", email: "[REDACTED]"}' \
    "$BUNDLE_DIR/me.json" > "$BUNDLE_DIR/me-redacted.json" 2>/dev/null || true
  rm -f "$BUNDLE_DIR/me.json"
fi

# Remove raw headers (may contain token in other tools)
rm -f "$BUNDLE_DIR/headers.txt"

echo "Redaction complete" >> "$BUNDLE_DIR/summary.txt"

# 6. Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

### Step 2: Run the Bundle
```bash
chmod +x figma-debug-bundle.sh
./figma-debug-bundle.sh
```

### Step 3: Review Before Sharing
```bash
# Inspect the bundle contents
tar -tzf figma-debug-*.tar.gz
# Extract and review
tar -xzf figma-debug-*.tar.gz
cat figma-debug-*/summary.txt
```

## Output
- `figma-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` -- environment, connectivity, rate limit status
  - `me-redacted.json` -- authenticated user (email redacted)
  - `file-meta.json` -- file metadata (if file key provided)

## Error Handling
| Item | What It Catches | Why It Matters |
|------|----------------|----------------|
| `/v1/me` response code | Token validity | 403 = expired/invalid PAT |
| `/v1/files` response code | File access | 404 = wrong key, 403 = not shared |
| Rate limit headers | Throttling state | `Retry-After` shows if currently limited |
| Response time | Latency issues | >2s suggests network or server problems |

## Examples

### ALWAYS REDACT Before Sharing
- Personal access tokens (`figd_*`)
- Email addresses
- OAuth client secrets
- File content (unless relevant to the bug)

### Safe to Include
- HTTP status codes and response times
- Error message text
- Node IDs and file keys (not secrets)
- Rate limit header values

## Resources
- [Figma Support](https://help.figma.com/hc/en-us/requests/new)
- [Figma Status Page](https://status.figma.com)
- [Figma Developer Forum](https://forum.figma.com/)

## Next Steps
For rate limit issues, see `figma-rate-limits`.
