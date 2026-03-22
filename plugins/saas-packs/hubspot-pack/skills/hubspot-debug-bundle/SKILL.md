---
name: hubspot-debug-bundle
description: |
  Collect HubSpot debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for HubSpot API problems.
  Trigger with phrases like "hubspot debug", "hubspot support bundle",
  "collect hubspot logs", "hubspot diagnostic", "hubspot correlation id".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Debug Bundle

## Overview

Collect all necessary diagnostic information for HubSpot API troubleshooting and support ticket escalation, including correlation IDs, rate limit state, and SDK versions.

## Prerequisites

- `@hubspot/api-client` installed
- Access to application logs
- `HUBSPOT_ACCESS_TOKEN` environment variable set

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# hubspot-debug-bundle.sh

BUNDLE_DIR="hubspot-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== HubSpot Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment and SDK Info

```bash
echo "--- Runtime ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "HUBSPOT_ACCESS_TOKEN: ${HUBSPOT_ACCESS_TOKEN:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# SDK version
echo "--- @hubspot/api-client ---" >> "$BUNDLE_DIR/summary.txt"
npm list @hubspot/api-client 2>/dev/null >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Test API Connectivity and Rate Limits

```bash
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"

# Test the API and capture headers
curl -sI https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer ${HUBSPOT_ACCESS_TOKEN}" \
  > "$BUNDLE_DIR/api-headers.txt" 2>&1

# Extract key info
echo "HTTP Status: $(head -1 "$BUNDLE_DIR/api-headers.txt")" >> "$BUNDLE_DIR/summary.txt"
grep -i "x-hubspot-ratelimit" "$BUNDLE_DIR/api-headers.txt" >> "$BUNDLE_DIR/summary.txt"
grep -i "x-request-id" "$BUNDLE_DIR/api-headers.txt" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Test specific endpoints
for endpoint in contacts companies deals tickets; do
  STATUS=$(curl -so /dev/null -w "%{http_code}" \
    "https://api.hubapi.com/crm/v3/objects/${endpoint}?limit=1" \
    -H "Authorization: Bearer ${HUBSPOT_ACCESS_TOKEN}")
  echo "${endpoint}: HTTP ${STATUS}" >> "$BUNDLE_DIR/summary.txt"
done
echo "" >> "$BUNDLE_DIR/summary.txt"

# Check scopes via token info
echo "--- Token Info ---" >> "$BUNDLE_DIR/summary.txt"
curl -s "https://api.hubapi.com/oauth/v1/access-tokens/${HUBSPOT_ACCESS_TOKEN}" \
  2>/dev/null | jq '{user: .user, hub_id: .hub_id, scopes: .scopes, token_type: .token_type}' \
  >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "Token info unavailable (private app tokens)" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Collect Application Logs (Redacted)

```bash
echo "--- Recent Logs (redacted) ---" >> "$BUNDLE_DIR/summary.txt"

# Collect recent HubSpot-related errors from application logs
if [ -f "logs/app.log" ]; then
  grep -i "hubspot\|hubapi\|crm/v3" logs/app.log 2>/dev/null | tail -100 \
    | sed -E 's/pat-[a-z0-9-]+/[REDACTED_TOKEN]/g' \
    | sed -E 's/"email":"[^"]+/"email":"[REDACTED]/g' \
    > "$BUNDLE_DIR/logs-redacted.txt"
fi

# Capture correlationIds from recent errors
grep -oP '"correlationId":"[^"]+"' logs/app.log 2>/dev/null | sort -u \
  > "$BUNDLE_DIR/correlation-ids.txt"

# Redact all secrets from config
if [ -f ".env" ]; then
  sed 's/=.*/=***REDACTED***/' .env > "$BUNDLE_DIR/config-redacted.txt"
fi
```

### Step 5: Package and Verify

```bash
# Check HubSpot status page
echo "--- HubSpot Status ---" >> "$BUNDLE_DIR/summary.txt"
curl -s https://status.hubspot.com/api/v2/summary.json 2>/dev/null \
  | jq '{status: .status.description, incidents: [.incidents[] | {name, status}]}' \
  >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "Status page unreachable" >> "$BUNDLE_DIR/summary.txt"

# Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "REVIEW FOR SENSITIVE DATA BEFORE SHARING"
```

### Programmatic Debug Info

```typescript
import * as hubspot from '@hubspot/api-client';

async function collectHubSpotDiagnostics() {
  const client = new hubspot.Client({
    accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  });

  const diagnostics: Record<string, any> = {
    timestamp: new Date().toISOString(),
    sdkVersion: require('@hubspot/api-client/package.json').version,
    nodeVersion: process.version,
  };

  // Test each CRM object type
  const objectTypes = ['contacts', 'companies', 'deals', 'tickets'];
  for (const objType of objectTypes) {
    try {
      const start = Date.now();
      await client.apiRequest({
        method: 'GET',
        path: `/crm/v3/objects/${objType}?limit=1`,
      });
      diagnostics[objType] = { status: 'OK', latencyMs: Date.now() - start };
    } catch (error: any) {
      diagnostics[objType] = {
        status: 'ERROR',
        code: error.code || error.statusCode,
        message: error.body?.message || error.message,
        correlationId: error.body?.correlationId,
      };
    }
  }

  return diagnostics;
}
```

## Output

- `hubspot-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` -- environment, SDK version, API status, rate limits
  - `api-headers.txt` -- raw HTTP response headers
  - `correlation-ids.txt` -- unique error correlation IDs
  - `logs-redacted.txt` -- recent logs with secrets removed
  - `config-redacted.txt` -- configuration (values masked)

## Error Handling

| Item | Purpose | Included |
|------|---------|----------|
| SDK version | Version-specific bugs | Yes |
| HTTP status per object | Scope/permission issues | Yes |
| Rate limit headers | Throttling diagnosis | Yes |
| Correlation IDs | HubSpot support reference | Yes |
| HubSpot status page | Platform outage detection | Yes |

## Examples

### What to Redact Before Sharing

**ALWAYS REDACT:**
- Access tokens (start with `pat-` or JWT)
- Email addresses and phone numbers
- Company names from test data
- Portal IDs (unless sharing with HubSpot support)

**Safe to Include:**
- Error messages and categories
- Correlation IDs (HubSpot support needs these)
- HTTP status codes
- SDK/runtime versions
- Rate limit remaining counts

## Resources

- [HubSpot Support Portal](https://help.hubspot.com/)
- [HubSpot Status Page](https://status.hubspot.com)
- [Error Handling Guide](https://developers.hubspot.com/docs/api-reference/error-handling)

## Next Steps

For rate limit issues, see `hubspot-rate-limits`.
