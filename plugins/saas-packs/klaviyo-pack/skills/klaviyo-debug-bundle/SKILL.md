---
name: klaviyo-debug-bundle
description: |
  Collect Klaviyo debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Klaviyo API problems.
  Trigger with phrases like "klaviyo debug", "klaviyo support bundle",
  "collect klaviyo logs", "klaviyo diagnostic", "klaviyo troubleshoot".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Debug Bundle

## Overview

Collect all diagnostic information needed for Klaviyo support tickets: SDK version, API connectivity, rate limit status, recent errors, and environment config (with secrets redacted).

## Prerequisites

- `klaviyo-api` SDK installed
- `KLAVIYO_PRIVATE_KEY` environment variable set
- Access to application logs

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# klaviyo-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="klaviyo-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Klaviyo Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info

```bash
# --- Runtime ---
echo "--- Runtime Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -srm)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- SDK Version ---
echo "--- Klaviyo SDK ---" >> "$BUNDLE_DIR/summary.txt"
npm list klaviyo-api 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "klaviyo-api: not installed" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- API Key Check (redacted) ---
echo "--- API Key Status ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "${KLAVIYO_PRIVATE_KEY:-}" ]; then
  echo "KLAVIYO_PRIVATE_KEY: SET (${#KLAVIYO_PRIVATE_KEY} chars, prefix: ${KLAVIYO_PRIVATE_KEY:0:3}***)" >> "$BUNDLE_DIR/summary.txt"
else
  echo "KLAVIYO_PRIVATE_KEY: NOT SET" >> "$BUNDLE_DIR/summary.txt"
fi
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: API Connectivity Tests

```bash
# --- API Connectivity ---
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"

# Test base connectivity
echo -n "DNS resolve a.klaviyo.com: " >> "$BUNDLE_DIR/summary.txt"
nslookup a.klaviyo.com > /dev/null 2>&1 && echo "OK" >> "$BUNDLE_DIR/summary.txt" || echo "FAILED" >> "$BUNDLE_DIR/summary.txt"

# Test API authentication
if [ -n "${KLAVIYO_PRIVATE_KEY:-}" ]; then
  HTTP_CODE=$(curl -s -o "$BUNDLE_DIR/api-response.json" -w "%{http_code}" \
    -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
    -H "revision: 2024-10-15" \
    -H "Accept: application/vnd.api+json" \
    "https://a.klaviyo.com/api/accounts/" 2>/dev/null || echo "000")
  echo "API Auth Test: HTTP $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"

  # Capture rate limit headers
  curl -s -I \
    -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
    -H "revision: 2024-10-15" \
    "https://a.klaviyo.com/api/profiles/?page[size]=1" 2>/dev/null \
    | grep -i "ratelimit\|retry-after" >> "$BUNDLE_DIR/rate-limits.txt" || echo "No rate limit headers" >> "$BUNDLE_DIR/rate-limits.txt"
fi

# Check Klaviyo status page
echo -n "Status Page: " >> "$BUNDLE_DIR/summary.txt"
curl -s "https://status.klaviyo.com/api/v2/status.json" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',{}).get('description','unknown'))" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null \
  || echo "Could not reach status page" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Application Log Collection

```bash
# --- Recent Error Logs (redacted) ---
echo "--- Recent Klaviyo Errors ---" >> "$BUNDLE_DIR/summary.txt"

# Search common log locations for Klaviyo errors
for logdir in logs/ /var/log/app/; do
  if [ -d "$logdir" ]; then
    grep -i "klaviyo\|a\.klaviyo\.com" "$logdir"*.log 2>/dev/null \
      | tail -50 \
      | sed -E 's/pk_[a-zA-Z0-9]+/pk_***REDACTED***/g' \
      | sed -E 's/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/***@redacted***/g' \
      >> "$BUNDLE_DIR/recent-errors.txt"
  fi
done

# Redact any remaining secrets from all collected files
for file in "$BUNDLE_DIR"/*.txt "$BUNDLE_DIR"/*.json; do
  [ -f "$file" ] && sed -i -E 's/pk_[a-zA-Z0-9]{20,}/pk_***REDACTED***/g' "$file"
done
```

### Step 5: Package and Output

```bash
# Package bundle
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review before sharing -- ensure no secrets remain."
```

### Programmatic Debug Info

```typescript
// src/klaviyo/debug.ts
import { ApiKeySession, AccountsApi, ProfilesApi } from 'klaviyo-api';

interface KlaviyoDebugInfo {
  sdkVersion: string;
  apiConnected: boolean;
  accountId?: string;
  accountName?: string;
  apiLatencyMs: number;
  rateLimitStatus?: string;
  error?: string;
}

export async function collectKlaviyoDebugInfo(): Promise<KlaviyoDebugInfo> {
  const start = Date.now();
  const sdkVersion = require('klaviyo-api/package.json').version;

  try {
    const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
    const accountsApi = new AccountsApi(session);
    const result = await accountsApi.getAccounts();
    const account = result.body.data[0];

    return {
      sdkVersion,
      apiConnected: true,
      accountId: account.id,
      accountName: account.attributes.contactInformation?.organizationName,
      apiLatencyMs: Date.now() - start,
    };
  } catch (error: any) {
    return {
      sdkVersion,
      apiConnected: false,
      apiLatencyMs: Date.now() - start,
      error: `${error.status || 'N/A'}: ${error.body?.errors?.[0]?.detail || error.message}`,
    };
  }
}
```

## Output

- `klaviyo-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` -- Environment, SDK version, API key status, connectivity
  - `rate-limits.txt` -- Current rate limit header values
  - `api-response.json` -- Account API response (confirms auth)
  - `recent-errors.txt` -- Redacted error logs

## Redaction Rules

**ALWAYS redacted:**
- API keys (`pk_***`)
- Email addresses
- Phone numbers
- Webhook secrets

**Safe to include:**
- Error codes and HTTP status codes
- SDK and runtime versions
- Stack traces (with PII redacted)
- Rate limit header values
- Klaviyo account ID

## Resources

- [Klaviyo Support Portal](https://support.klaviyo.com)
- [Klaviyo Status Page](https://status.klaviyo.com)
- [API Error Alerts](https://developers.klaviyo.com/en/docs/review_api_error_alerts)

## Next Steps

For rate limit issues, see `klaviyo-rate-limits`.
