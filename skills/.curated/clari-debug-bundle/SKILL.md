---
name: clari-debug-bundle
description: 'Collect Clari API diagnostic info for support cases.

  Use when preparing a support ticket, collecting API response samples,

  or documenting integration issues.

  Trigger with phrases like "clari debug", "clari support bundle",

  "collect clari diagnostics", "clari troubleshoot".

  '
allowed-tools: Read, Bash(curl:*), Bash(python3:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- revenue-intelligence
- forecasting
- clari
compatibility: Designed for Claude Code
---
# Clari Debug Bundle

## Overview

Collect Clari API diagnostic information for support: API connectivity, forecast list, job history, and error responses. All secrets are redacted.

## Prerequisites

- Authorized diagnostic access to the affected environment
- `CLARI_API_KEY` injected by an approved secret mechanism
- A secure local workspace with enough storage for the bundle
- A support/incident record that defines what metadata may be shared

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

## Error Handling

| Condition | Response |
|---|---|
| API request fails or times out | Keep the HTTP status and timestamp, then stop rather than repeatedly retrying. |
| Bundle contains unexpected sensitive data | Quarantine it, redact or regenerate it, and do not attach it externally. |
| Archive creation fails | Preserve the unarchived directory locally, diagnose storage/permissions, then clean it under retention policy. |
| Support needs additional fields | Obtain data-owner approval before collecting or sharing them. |

## Output

Generate a timestamped, redacted archive and a summary with environment,
sanitized connectivity status, job IDs, collection failures, and integrity
review decision. The archive is support evidence, not a data-export mechanism;
it must exclude live credentials and individual forecast records.

## Examples

During a failed scheduled export, generate the bundle, inspect `summary.txt`
and JSON files locally, and remove any unapproved identifiers before attaching
the archive to the named support case. If the provider is returning 429, include
the redacted timestamps and job state rather than continuing to poll it.

## Resources

- [Clari Community](https://community.clari.com)
- [Clari Developer Portal](https://developer.clari.com)

## Next Steps

For rate limit handling, see `clari-rate-limits`.
