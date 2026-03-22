---
name: intercom-debug-bundle
description: |
  Collect Intercom debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Intercom API problems.
  Trigger with phrases like "intercom debug", "intercom support bundle",
  "collect intercom logs", "intercom diagnostic", "intercom troubleshoot".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Debug Bundle

## Overview

Collect diagnostic evidence for Intercom issues including API health, rate limit status, SDK version, recent errors, and configuration validation.

## Prerequisites

- Intercom access token configured
- `curl` and `jq` available
- Access to application logs

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# intercom-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="intercom-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"
TOKEN="${INTERCOM_ACCESS_TOKEN:-}"

echo "=== Intercom Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"

# Token presence check (never log the actual token)
echo "--- Token Status ---" >> "$BUNDLE_DIR/summary.txt"
if [ -z "$TOKEN" ]; then
  echo "ERROR: INTERCOM_ACCESS_TOKEN not set" >> "$BUNDLE_DIR/summary.txt"
  echo "Set INTERCOM_ACCESS_TOKEN and re-run" >&2
  exit 1
fi
echo "Token: [SET] (${#TOKEN} chars)" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect API Health and Auth Status

```bash
# API authentication test
echo "--- API Auth Test ---" >> "$BUNDLE_DIR/summary.txt"
AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  https://api.intercom.io/me 2>&1)
HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -1)
AUTH_BODY=$(echo "$AUTH_RESPONSE" | head -n -1)

echo "HTTP Status: $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"
if [ "$HTTP_CODE" = "200" ]; then
  echo "Auth: OK" >> "$BUNDLE_DIR/summary.txt"
  echo "$AUTH_BODY" | jq '{type, name, email, app: .app.name}' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
else
  echo "Auth: FAILED" >> "$BUNDLE_DIR/summary.txt"
  echo "$AUTH_BODY" | jq '.errors' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
fi
```

### Step 3: Check Rate Limit Status

```bash
# Rate limit headers
echo "--- Rate Limits ---" >> "$BUNDLE_DIR/summary.txt"
HEADERS=$(curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  https://api.intercom.io/me 2>/dev/null)

echo "$HEADERS" | grep -i "x-ratelimit" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "No rate limit headers found" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Intercom Platform Status

```bash
# Intercom status page
echo "--- Intercom Status ---" >> "$BUNDLE_DIR/summary.txt"
STATUS=$(curl -s https://status.intercom.com/api/v2/status.json 2>/dev/null)
echo "$STATUS" | jq '{indicator: .status.indicator, description: .status.description}' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "Could not reach status page" >> "$BUNDLE_DIR/summary.txt"

# Active incidents
INCIDENTS=$(curl -s https://status.intercom.com/api/v2/incidents/unresolved.json 2>/dev/null)
INCIDENT_COUNT=$(echo "$INCIDENTS" | jq '.incidents | length' 2>/dev/null || echo "0")
echo "Active incidents: $INCIDENT_COUNT" >> "$BUNDLE_DIR/summary.txt"
```

### Step 5: SDK and Environment Info

```bash
# Environment
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -s -r)" >> "$BUNDLE_DIR/summary.txt"

# SDK version
echo "--- intercom-client Version ---" >> "$BUNDLE_DIR/summary.txt"
npm list intercom-client 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "intercom-client not in node_modules" >> "$BUNDLE_DIR/summary.txt"

# Endpoint connectivity test
echo "--- Endpoint Latency ---" >> "$BUNDLE_DIR/summary.txt"
for endpoint in "me" "contacts" "conversations" "admins"; do
  LATENCY=$(curl -s -o /dev/null -w "%{time_total}" \
    -H "Authorization: Bearer $TOKEN" \
    "https://api.intercom.io/$endpoint" 2>/dev/null)
  echo "  /$endpoint: ${LATENCY}s" >> "$BUNDLE_DIR/summary.txt"
done
```

### Step 6: Collect Logs (Redacted)

```bash
# Redact sensitive data from logs
echo "--- Recent Intercom Logs (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f "logs/app.log" ]; then
  grep -i "intercom" logs/app.log 2>/dev/null | tail -50 | \
    sed -E 's/(Bearer |token[=:] ?)[^ "]+/\1[REDACTED]/gi' | \
    sed -E 's/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[EMAIL]/g' \
    >> "$BUNDLE_DIR/logs-redacted.txt"
fi

# Configuration (secrets masked)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f ".env" ]; then
  sed 's/=.*/=***REDACTED***/' .env >> "$BUNDLE_DIR/config-redacted.txt"
fi
```

### Step 7: Package and Output

```bash
# Package bundle
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo ""
echo "Debug bundle created: $BUNDLE_DIR.tar.gz"
echo "Review for sensitive data before sharing with support."
```

## Sensitive Data Policy

**ALWAYS redact before sharing:**
- Access tokens and OAuth secrets
- Webhook signing secrets
- Email addresses and PII
- Customer conversation content

**Safe to include:**
- HTTP status codes and error codes
- `request_id` from error responses (Intercom support needs these)
- Rate limit header values
- SDK and runtime versions
- Endpoint latency measurements

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `jq: command not found` | jq not installed | `apt install jq` or `brew install jq` |
| Auth test returns 401 | Token invalid | Regenerate in Developer Hub |
| Status page unreachable | Network issue | Try `curl https://status.intercom.com` directly |
| No rate limit headers | Request failed early | Fix auth first |

## Resources

- [Intercom Status](https://status.intercom.com)
- [Intercom Support](https://www.intercom.com/help)
- [Error Codes Reference](https://developers.intercom.com/docs/references/rest-api/errors/error-codes)

## Next Steps

For rate limit handling, see `intercom-rate-limits`.
