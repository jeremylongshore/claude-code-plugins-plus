---
name: adobe-debug-bundle
description: |
  Collect Adobe debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Adobe API problems.
  Trigger with phrases like "adobe debug", "adobe support bundle",
  "collect adobe logs", "adobe diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Debug Bundle

## Overview

Collect all necessary diagnostic information for Adobe support tickets. This script gathers SDK versions, credential validation status, API connectivity, and redacted configuration into a support-ready archive.

## Prerequisites

- Adobe credentials configured (env vars or `.env` file)
- Node.js or Python environment with Adobe SDKs installed
- Permission to run network diagnostics

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# adobe-debug-bundle.sh — Collects diagnostic info for Adobe support

set -euo pipefail
BUNDLE_DIR="adobe-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Adobe Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "Hostname: $(hostname)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- Environment ---
echo "--- Runtime Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Node.js: not found" >> "$BUNDLE_DIR/summary.txt"
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "npm: not found" >> "$BUNDLE_DIR/summary.txt"
python3 --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Python: not found" >> "$BUNDLE_DIR/summary.txt"

# --- Adobe SDK Versions ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Adobe SDK Versions ---" >> "$BUNDLE_DIR/summary.txt"
npm list @adobe/pdfservices-node-sdk 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "PDF Services SDK: not installed" >> "$BUNDLE_DIR/summary.txt"
npm list @adobe/firefly-apis 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Firefly APIs: not installed" >> "$BUNDLE_DIR/summary.txt"
npm list @adobe/photoshop-apis 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Photoshop APIs: not installed" >> "$BUNDLE_DIR/summary.txt"
npm list @adobe/lightroom-apis 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Lightroom APIs: not installed" >> "$BUNDLE_DIR/summary.txt"
npm list @adobe/aio-sdk 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "AIO SDK: not installed" >> "$BUNDLE_DIR/summary.txt"

# --- Credential Status (NEVER log actual values) ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Credential Status ---" >> "$BUNDLE_DIR/summary.txt"
echo "ADOBE_CLIENT_ID: ${ADOBE_CLIENT_ID:+[SET, length=${#ADOBE_CLIENT_ID}]}" >> "$BUNDLE_DIR/summary.txt"
echo "ADOBE_CLIENT_ID: ${ADOBE_CLIENT_ID:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "ADOBE_CLIENT_SECRET: ${ADOBE_CLIENT_SECRET:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "ADOBE_CLIENT_SECRET: ${ADOBE_CLIENT_SECRET:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "ADOBE_SCOPES: ${ADOBE_SCOPES:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "ADOBE_IMS_ORG_ID: ${ADOBE_IMS_ORG_ID:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"

# --- OAuth Token Test ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- OAuth Token Test ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "${ADOBE_CLIENT_ID:-}" ] && [ -n "${ADOBE_CLIENT_SECRET:-}" ]; then
  TOKEN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
    'https://ims-na1.adobelogin.com/ims/token/v3' \
    -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES:-openid}" 2>&1)
  HTTP_CODE=$(echo "$TOKEN_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
  echo "IMS Token Endpoint: HTTP $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"
  if [ "$HTTP_CODE" != "200" ]; then
    echo "$TOKEN_RESPONSE" | grep -v "HTTP_CODE:" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Error: {d.get(\"error\",\"unknown\")} - {d.get(\"error_description\",\"no description\")}')" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "Could not parse error response" >> "$BUNDLE_DIR/summary.txt"
  fi
else
  echo "Skipped: credentials not set" >> "$BUNDLE_DIR/summary.txt"
fi

# --- API Connectivity ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- API Endpoint Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
for endpoint in "ims-na1.adobelogin.com" "firefly-api.adobe.io" "image.adobe.io" "pdf-services.adobe.io" "developer.adobe.com"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "https://$endpoint" 2>/dev/null || echo "UNREACHABLE")
  echo "$endpoint: $STATUS" >> "$BUNDLE_DIR/summary.txt"
done

# --- DNS Resolution ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- DNS Resolution ---" >> "$BUNDLE_DIR/summary.txt"
for host in "ims-na1.adobelogin.com" "firefly-api.adobe.io" "image.adobe.io"; do
  nslookup "$host" 2>&1 | tail -2 >> "$BUNDLE_DIR/summary.txt"
done

# --- Redacted Config ---
if [ -f .env ]; then
  echo "" >> "$BUNDLE_DIR/summary.txt"
  echo "--- Config (values redacted) ---" >> "$BUNDLE_DIR/summary.txt"
  sed 's/=.*/=***REDACTED***/' .env >> "$BUNDLE_DIR/config-redacted.txt"
fi

# --- Package ---
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review contents before sharing with Adobe Support."
```

### Step 2: Run the Bundle

```bash
chmod +x adobe-debug-bundle.sh
./adobe-debug-bundle.sh
```

### Step 3: Review Before Sharing

**ALWAYS review the bundle before sending to Adobe Support:**

```bash
tar -tzf adobe-debug-*.tar.gz  # List contents
tar -xzf adobe-debug-*.tar.gz  # Extract and inspect
cat adobe-debug-*/summary.txt  # Review summary
```

**NEVER include:**
- `ADOBE_CLIENT_SECRET` values
- Private keys or certificates
- PII (customer emails, names, IDs)
- Full `.env` files

**Safe to include:**
- Error messages and HTTP status codes
- SDK and runtime versions
- Connectivity test results
- Redacted configuration keys

## Output

- `adobe-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` — Environment, SDK versions, credential status, connectivity
  - `config-redacted.txt` — Configuration keys with values masked

## Error Handling

| Item | Purpose | Collected |
|------|---------|-----------|
| Node/Python versions | SDK compatibility | Yes |
| SDK package versions | Version-specific bugs | Yes |
| OAuth token test | Auth validation | Status code only |
| DNS resolution | Network issues | Yes |
| API connectivity | Firewall/proxy issues | HTTP status codes |

## Resources

- [Adobe Developer Support](https://developer.adobe.com/support)
- [Adobe Status Page](https://status.adobe.com)
- [Adobe Community Forums](https://community.adobe.com/t5/adobe-developer/ct-p/adobe-developer)

## Next Steps

For rate limit issues, see `adobe-rate-limits`.
