---
name: customerio-debug-bundle
description: |
  Collect Customer.io debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Customer.io problems.
  Trigger with phrases like "customerio debug", "customerio support bundle",
  "collect customerio logs", "customerio diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io Debug Bundle

## Overview
Collect all necessary diagnostic information for Customer.io support tickets.

## Prerequisites
- Customer.io SDK installed
- Access to application logs
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
# customerio-debug-bundle.sh

BUNDLE_DIR="customerio-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Customer.io Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info
```bash
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "CUSTOMERIO_API_KEY: ${CUSTOMERIO_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Gather SDK and Logs
```bash
# SDK version
npm list @customerio/sdk 2>/dev/null >> "$BUNDLE_DIR/summary.txt"

# Recent logs (redacted)
grep -i "customerio" ~/.npm/_logs/*.log 2>/dev/null | tail -50 >> "$BUNDLE_DIR/logs.txt"

# Configuration (redacted - secrets masked)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
cat .env 2>/dev/null | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt"

# Network connectivity test
echo "--- Network Test ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "API Health: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" https://api.customerio.com/health >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Package Bundle
```bash
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

## Output
- `customerio-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - Environment and SDK info
  - `logs.txt` - Recent redacted logs
  - `config-redacted.txt` - Configuration (secrets removed)

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| Environment versions | Compatibility check | ✓ |
| SDK version | Version-specific bugs | ✓ |
| Error logs (redacted) | Root cause analysis | ✓ |
| Config (redacted) | Configuration issues | ✓ |
| Network test | Connectivity issues | ✓ |

## Examples

### Sensitive Data Handling
**ALWAYS REDACT:**
- API keys and tokens
- Passwords and secrets
- PII (emails, names, IDs)

**Safe to Include:**
- Error messages
- Stack traces (redacted)
- SDK/runtime versions

### Submit to Support
1. Create bundle: `bash customerio-debug-bundle.sh`
2. Review for sensitive data
3. Upload to Customer.io support portal

## Resources
- [Customer.io Support](https://docs.customerio.com/support)
- [Customer.io Status](https://status.customerio.com)

## Next Steps
For rate limit issues, see `customerio-rate-limits`.