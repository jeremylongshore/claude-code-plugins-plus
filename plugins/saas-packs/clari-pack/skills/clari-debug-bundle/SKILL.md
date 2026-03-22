---
name: clari-debug-bundle
description: |
  Collect Clari API diagnostic info for support cases.
  Use when preparing a support ticket, collecting API response samples,
  or documenting integration issues.
  Trigger with phrases like "clari debug", "clari support bundle",
  "collect clari diagnostics", "clari troubleshoot".
allowed-tools: Read, Bash(curl:*), Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Debug Bundle

## Overview

Collect Clari API diagnostic information for support: API connectivity, forecast list, job history, and error responses. All secrets are redacted.

## Instructions

### Debug Bundle Script

```bash
#!/bin/bash
# clari-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="clari-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Clari Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u)" | tee -a "$BUNDLE_DIR/summary.txt"

# 1. API connectivity
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/forecast/list)
echo "API Status: HTTP ${HTTP_CODE}" >> "$BUNDLE_DIR/summary.txt"

# 2. Forecast list (no sensitive data)
curl -s -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/forecast/list \
  | jq '.forecasts[] | {forecastName, forecastId}' \
  > "$BUNDLE_DIR/forecasts.json" 2>&1

# 3. Recent export jobs
curl -s -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/jobs \
  | jq '.jobs[] | {jobId, status, createdAt, forecastName}' \
  > "$BUNDLE_DIR/jobs.json" 2>&1

# 4. Environment info (redacted)
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "CLARI_API_KEY: ${CLARI_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
python3 --version >> "$BUNDLE_DIR/summary.txt" 2>&1
pip3 show requests 2>/dev/null | grep Version >> "$BUNDLE_DIR/summary.txt" || true

# 5. Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle: $BUNDLE_DIR.tar.gz"
```

**Safe to share**: Forecast names, job IDs, HTTP status codes, library versions.
**Never share**: API key, forecast amounts, rep names, email addresses.

## Resources

- [Clari Community](https://community.clari.com)
- [Clari Developer Portal](https://developer.clari.com)

## Next Steps

For rate limit handling, see `clari-rate-limits`.
