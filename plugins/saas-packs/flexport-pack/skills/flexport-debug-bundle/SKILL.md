---
name: flexport-debug-bundle
description: |
  Collect Flexport API debug evidence for support tickets and troubleshooting.
  Use when encountering persistent API issues, preparing support tickets,
  or collecting diagnostic information for Flexport logistics problems.
  Trigger: "flexport debug", "flexport support bundle", "flexport diagnostic".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Debug Bundle

## Overview

Collect all necessary diagnostic information for Flexport support tickets. The bundle captures API connectivity, authentication status, recent shipment data, and error logs while automatically redacting secrets.

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# flexport-debug.sh — run with: bash flexport-debug.sh
set -euo pipefail

BUNDLE="flexport-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

echo "=== Flexport Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'not found')" >> "$BUNDLE/summary.txt"
echo "API Key set: ${FLEXPORT_API_KEY:+YES}" >> "$BUNDLE/summary.txt"
```

### Step 2: Test API Connectivity

```bash
# API health and auth check
echo -e "\n--- API Connectivity ---" >> "$BUNDLE/summary.txt"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $FLEXPORT_API_KEY" \
  -H "Flexport-Version: 2" \
  https://api.flexport.com/shipments?per=1 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "HTTP Status: $HTTP_CODE" >> "$BUNDLE/summary.txt"
echo "$BODY" | jq '{total_count: .data.total_count, has_records: (.data.records | length > 0)}' \
  >> "$BUNDLE/api-test.json" 2>/dev/null || echo "Parse failed" >> "$BUNDLE/api-test.json"
```

### Step 3: Capture Recent Errors

```bash
# Collect recent error logs (redacted)
echo -e "\n--- Recent Errors ---" >> "$BUNDLE/summary.txt"
grep -i "flexport\|FLEXPORT" /var/log/app/*.log 2>/dev/null | \
  tail -50 | \
  sed 's/Bearer [^ ]*/Bearer ***REDACTED***/g' \
  >> "$BUNDLE/errors.txt" 2>/dev/null || echo "No app logs found" >> "$BUNDLE/errors.txt"

# Capture env config (redacted)
env | grep -i FLEXPORT | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE/env-redacted.txt"
```

### Step 4: Check Status Page and Package

```bash
# Flexport platform status
echo -e "\n--- Platform Status ---" >> "$BUNDLE/summary.txt"
curl -s https://status.flexport.com/api/v2/status.json | \
  jq '{status: .status.description, updated: .page.updated_at}' \
  >> "$BUNDLE/status.json" 2>/dev/null || echo "Status page unreachable" >> "$BUNDLE/status.json"

# Package and output
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
rm -rf "$BUNDLE"
echo "Bundle created: $BUNDLE.tar.gz"
echo "Review contents before sharing: tar -tzf $BUNDLE.tar.gz"
```

## Checklist Before Submitting

| Item | Included | Sensitive? |
|------|----------|------------|
| API connectivity test | Yes | No |
| HTTP status codes | Yes | No |
| Platform status | Yes | No |
| Error logs (redacted) | Yes | Redacted |
| Environment vars | Yes | Redacted |
| Request IDs | Include from `X-Request-Id` header | No |

**ALWAYS verify:** No API keys, tokens, passwords, or PII in the bundle before submitting.

## Resources

- [Flexport Status](https://status.flexport.com)
- [Flexport Support](https://support.flexport.com)

## Next Steps

For rate limit issues, see `flexport-rate-limits`.
