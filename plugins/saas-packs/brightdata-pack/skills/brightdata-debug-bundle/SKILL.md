---
name: brightdata-debug-bundle
description: |
  Collect Bright Data debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Bright Data problems.
  Trigger with phrases like "brightdata debug", "brightdata support bundle",
  "collect brightdata logs", "brightdata diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Debug Bundle

## Overview

Collect all diagnostic information needed for Bright Data support tickets: proxy connectivity, zone status, response headers, and error logs.

## Prerequisites

- Bright Data zone credentials configured
- curl available
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# brightdata-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="brightdata-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Bright Data Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u)" | tee -a "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment and Connectivity

```bash
# Runtime versions
echo "--- Runtime ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Node.js: not found" >> "$BUNDLE_DIR/summary.txt"
python3 --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Python: not found" >> "$BUNDLE_DIR/summary.txt"

# Credential check (presence only, never log values)
echo "--- Credentials ---" >> "$BUNDLE_DIR/summary.txt"
echo "BRIGHTDATA_CUSTOMER_ID: ${BRIGHTDATA_CUSTOMER_ID:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "BRIGHTDATA_ZONE: ${BRIGHTDATA_ZONE:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "BRIGHTDATA_ZONE_PASSWORD: ${BRIGHTDATA_ZONE_PASSWORD:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "BRIGHTDATA_API_TOKEN: ${BRIGHTDATA_API_TOKEN:+[SET]}" >> "$BUNDLE_DIR/summary.txt"

# SSL cert check
echo "--- SSL Certificate ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f "./brd-ca.crt" ]; then
  openssl x509 -in ./brd-ca.crt -noout -subject -enddate >> "$BUNDLE_DIR/summary.txt" 2>&1
else
  echo "brd-ca.crt: NOT FOUND" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 3: Test Proxy Connectivity with Verbose Headers

```bash
# Proxy connectivity test with full response headers
echo "--- Proxy Test ---" >> "$BUNDLE_DIR/summary.txt"
PROXY_USER="brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}"
curl -x "http://${PROXY_USER}:${BRIGHTDATA_ZONE_PASSWORD}@brd.superproxy.io:33335" \
  -s -D "$BUNDLE_DIR/proxy-headers.txt" \
  -o "$BUNDLE_DIR/proxy-response.txt" \
  -w "HTTP %{http_code} in %{time_total}s\n" \
  https://lumtest.com/myip.json 2>> "$BUNDLE_DIR/summary.txt" || echo "Proxy FAILED" >> "$BUNDLE_DIR/summary.txt"

# Extract X-Luminati headers (error details)
grep -i "x-luminati\|x-brd" "$BUNDLE_DIR/proxy-headers.txt" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || true

# Direct connectivity test (bypasses proxy)
echo "--- Direct Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "brightdata.com: HTTP %{http_code}\n" https://brightdata.com >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "status page: HTTP %{http_code}\n" https://status.brightdata.com >> "$BUNDLE_DIR/summary.txt"

# Port check
echo "--- Port Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
nc -zv brd.superproxy.io 33335 >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Port 33335: BLOCKED" >> "$BUNDLE_DIR/summary.txt"
nc -zv brd.superproxy.io 9222 >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Port 9222: BLOCKED" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Check Zone Status via API

```bash
# Zone status (requires API token)
if [ -n "${BRIGHTDATA_API_TOKEN:-}" ]; then
  echo "--- Zone Status ---" >> "$BUNDLE_DIR/summary.txt"
  curl -s -H "Authorization: Bearer ${BRIGHTDATA_API_TOKEN}" \
    "https://api.brightdata.com/zone/get_active_zones" \
    | python3 -m json.tool >> "$BUNDLE_DIR/zone-status.json" 2>/dev/null || true
fi
```

### Step 5: Package and Report

```bash
# Collect recent error logs (redacted)
if [ -d "logs" ]; then
  grep -i "brightdata\|proxy\|502\|407\|luminati" logs/*.log 2>/dev/null \
    | tail -100 | sed 's/password=[^ ]*/password=***REDACTED***/g' \
    >> "$BUNDLE_DIR/error-logs.txt"
fi

# Package bundle
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Contents:"
ls -la "$BUNDLE_DIR/"
echo ""
echo "REVIEW FOR SENSITIVE DATA BEFORE SHARING"
```

## Output

- `summary.txt` — credentials check, connectivity results, error headers
- `proxy-headers.txt` — full proxy response headers with X-Luminati diagnostics
- `proxy-response.txt` — proxy test response body
- `zone-status.json` — zone configuration and status
- `error-logs.txt` — recent errors (passwords redacted)

## Sensitive Data Checklist

**ALWAYS REDACT before sharing:**
- API tokens and zone passwords
- Customer IDs
- Target URLs (if confidential)

**Safe to include:**
- Error codes and X-Luminati headers
- Response timing
- Runtime versions
- Port connectivity results

## Resources

- [Bright Data Support Portal](https://brightdata.com/cp/support)
- [Status Page](https://status.brightdata.com)
- [Troubleshooting Guide](https://docs.brightdata.com/general/account/troubleshooting)

## Next Steps

For rate limit issues, see `brightdata-rate-limits`.
