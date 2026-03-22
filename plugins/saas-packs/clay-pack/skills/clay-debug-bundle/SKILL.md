---
name: clay-debug-bundle
description: |
  Collect Clay debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Clay integration problems.
  Trigger with phrases like "clay debug", "clay support bundle",
  "collect clay logs", "clay diagnostic", "clay support ticket".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, debugging]

---
# Clay Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`

## Overview

Collect all diagnostic information needed for Clay support tickets. Clay is a web platform, so debugging focuses on webhook delivery, enrichment column errors, HTTP API responses, and credit consumption -- not pods or clusters.

## Prerequisites

- Clay account with access to affected table
- curl for testing webhook/API connectivity
- Browser developer tools for capturing network requests

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# clay-debug-bundle.sh — collect Clay integration diagnostics
set -euo pipefail

BUNDLE_DIR="clay-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Clay Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Test Webhook Connectivity

```bash
# Test webhook endpoint is reachable
echo "--- Webhook Test ---" >> "$BUNDLE_DIR/summary.txt"
WEBHOOK_URL="${CLAY_WEBHOOK_URL:-not_set}"
if [ "$WEBHOOK_URL" != "not_set" ]; then
  HTTP_CODE=$(curl -s -o "$BUNDLE_DIR/webhook-response.txt" -w "%{http_code}" \
    -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{"_debug": true, "_test": "debug-bundle"}')
  echo "Webhook HTTP Status: $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"
  echo "Webhook URL: ${WEBHOOK_URL:0:50}..." >> "$BUNDLE_DIR/summary.txt"
else
  echo "CLAY_WEBHOOK_URL: NOT SET" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 3: Capture Environment and Configuration

```bash
# Capture environment (redacted)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'N/A')" >> "$BUNDLE_DIR/summary.txt"
echo "Python: $(python3 --version 2>/dev/null || echo 'N/A')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -s -r)" >> "$BUNDLE_DIR/summary.txt"
echo "CLAY_API_KEY: ${CLAY_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "CLAY_WEBHOOK_URL: ${CLAY_WEBHOOK_URL:+[SET]}" >> "$BUNDLE_DIR/summary.txt"

# Capture .env (redacted)
if [ -f .env ]; then
  sed 's/=.*/=***REDACTED***/' .env > "$BUNDLE_DIR/config-redacted.txt"
fi
```

### Step 4: Test Enterprise API (If Available)

```bash
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Enterprise API Test ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "${CLAY_API_KEY:-}" ]; then
  API_CODE=$(curl -s -o "$BUNDLE_DIR/api-response.txt" -w "%{http_code}" \
    -X POST "https://api.clay.com/v1/people/enrich" \
    -H "Authorization: Bearer $CLAY_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}')
  echo "Enterprise API Status: $API_CODE" >> "$BUNDLE_DIR/summary.txt"
else
  echo "Enterprise API: No API key configured" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 5: Capture Application Logs

```bash
# Grab recent Clay-related log entries
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Recent Errors ---" >> "$BUNDLE_DIR/summary.txt"

# Search for Clay errors in common log locations
for logfile in logs/*.log /tmp/clay-*.log; do
  if [ -f "$logfile" ]; then
    grep -i "clay\|webhook\|enrich" "$logfile" 2>/dev/null | tail -50 >> "$BUNDLE_DIR/logs.txt"
  fi
done

# Check npm logs for module issues
if [ -d node_modules ]; then
  echo "Dependencies installed: YES" >> "$BUNDLE_DIR/summary.txt"
  ls package.json 2>/dev/null && echo "package.json: EXISTS" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 6: Collect Clay Table Info (Manual Steps)

Add to the debug bundle manually from the Clay UI:

```markdown
## Clay Table Diagnostics (fill in from Clay UI)

- Table Name: _______________
- Table URL: _______________
- Row Count: _______________
- Enrichment Columns: _______________
- Auto-run enabled: YES / NO
- Error cells visible: YES (count: ___) / NO
- Credit balance remaining: _______________
- Plan tier: Free / Starter / Explorer / Pro / Enterprise

## Error Details (from clicking red cells)
- Error message: _______________
- Error column: _______________
- Error row count: _______________

## Recent Changes
- Last table edit: _______________
- Any new columns added: _______________
- Any provider connections changed: _______________
```

### Step 7: Package and Review

```bash
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo ""
echo "BEFORE SUBMITTING: Review for sensitive data!"
echo "  - Check $BUNDLE_DIR/config-redacted.txt for leaked secrets"
echo "  - Check $BUNDLE_DIR/logs.txt for PII (emails, names)"
echo ""
echo "Submit at: https://community.clay.com or support@clay.com"
```

## Error Handling

| Item | Purpose | Included |
|------|---------|----------|
| Webhook connectivity | Verify data can reach Clay | Automated |
| Environment info | Compatibility check | Automated |
| Enterprise API test | Verify API key validity | Automated |
| Application logs | Error patterns | Automated |
| Table diagnostics | Clay-side configuration | Manual checklist |
| Config (redacted) | Secret management issues | Automated |

## Sensitive Data Handling

**Always redact before submitting:**
- API keys and tokens
- Email addresses and names from enrichment data
- Provider API keys (Apollo, Clearbit, etc.)
- CRM credentials

**Safe to include:**
- Error messages and HTTP status codes
- Column names and table structure
- Credit usage numbers
- Software versions

## Resources

- [Clay Community Support](https://community.clay.com)
- [Clay University Docs](https://university.clay.com)

## Next Steps

For rate limit issues, see `clay-rate-limits`.
