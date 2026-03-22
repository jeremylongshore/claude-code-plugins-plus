---
name: salesloft-debug-bundle
description: |
  Collect SalesLoft debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic info for SalesLoft API problems.
  Trigger: "salesloft debug", "salesloft diagnostic", "salesloft support bundle".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Debug Bundle

## Overview

Collect diagnostic data for SalesLoft API issues: authentication state, rate limit usage, endpoint reachability, and API log entries. SalesLoft provides API Logs in the developer portal for request-level debugging.

## Prerequisites

- SalesLoft API key or OAuth token
- `curl` and `jq` available
- Access to SalesLoft developer portal for API logs

## Instructions

### Step 1: Create Debug Script

```bash
#!/bin/bash
# salesloft-debug.sh
set -euo pipefail

BUNDLE="salesloft-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
TOKEN="${SALESLOFT_API_KEY:?Set SALESLOFT_API_KEY}"

echo "=== SalesLoft Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
```

### Step 2: Check Authentication & Identity

```bash
echo "--- Auth Check ---" >> "$BUNDLE/summary.txt"
curl -s -w "\nHTTP_STATUS: %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" \
  https://api.salesloft.com/v2/me.json \
  | jq '{id: .data.id, email: .data.email, name: .data.name, role: .data.role}' \
  >> "$BUNDLE/auth.json" 2>&1
```

### Step 3: Check Rate Limit State

```bash
echo "--- Rate Limits ---" >> "$BUNDLE/summary.txt"
curl -sI -H "Authorization: Bearer $TOKEN" \
  https://api.salesloft.com/v2/people.json?per_page=1 \
  | grep -iE '(ratelimit|retry-after|x-request-id)' \
  >> "$BUNDLE/rate-limits.txt" 2>&1
```

### Step 4: Test Key Endpoints

```bash
echo "--- Endpoint Health ---" >> "$BUNDLE/summary.txt"
for endpoint in people.json cadences.json activities/emails.json; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "https://api.salesloft.com/v2/$endpoint?per_page=1")
  echo "$endpoint: HTTP $STATUS" >> "$BUNDLE/endpoints.txt"
done
```

### Step 5: Collect Environment Info

```bash
echo "--- Environment ---" >> "$BUNDLE/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'N/A')" >> "$BUNDLE/env.txt"
echo "Python: $(python3 --version 2>/dev/null || echo 'N/A')" >> "$BUNDLE/env.txt"
echo "SALESLOFT_BASE_URL: ${SALESLOFT_BASE_URL:-default}" >> "$BUNDLE/env.txt"
echo "SALESLOFT_API_KEY: ${SALESLOFT_API_KEY:+[SET]}" >> "$BUNDLE/env.txt"

# Redact .env secrets
cat .env 2>/dev/null | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE/config-redacted.txt" || true
```

### Step 6: Check API Logs

```bash
echo "--- API Logs ---" >> "$BUNDLE/summary.txt"
echo "View request-level logs at:" >> "$BUNDLE/summary.txt"
echo "  https://developers.salesloft.com/docs/platform/guides/api-logs/" >> "$BUNDLE/summary.txt"
echo "Filter by: date range, HTTP method, status code, endpoint" >> "$BUNDLE/summary.txt"
```

### Step 7: Package

```bash
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz ($(du -h "$BUNDLE.tar.gz" | cut -f1))"
```

## Output

- `auth.json` -- Identity and role info
- `rate-limits.txt` -- Current rate limit headers
- `endpoints.txt` -- Status of key API endpoints
- `env.txt` -- Runtime environment (secrets redacted)

## Error Handling

| Finding | Likely Issue | Action |
|---------|-------------|--------|
| auth.json shows 401 | Token expired | Refresh OAuth token |
| rate-limits.txt shows 0 remaining | Hit rate limit | Wait for reset, reduce request volume |
| Endpoint returns 403 | Scope mismatch | Check OAuth app scopes |
| Endpoint returns 5xx | SalesLoft outage | Check status.salesloft.com |

## Resources

- [SalesLoft API Logs](https://developers.salesloft.com/docs/platform/guides/api-logs/)
- [SalesLoft Status](https://status.salesloft.com)

## Next Steps

For rate limit issues, see `salesloft-rate-limits`.
