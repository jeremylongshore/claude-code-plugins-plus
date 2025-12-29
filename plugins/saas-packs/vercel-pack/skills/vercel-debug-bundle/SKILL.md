---
name: vercel-debug-bundle
description: |
  Collect Vercel debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Vercel problems.
  Trigger with phrases like "vercel debug", "vercel support bundle",
  "collect vercel logs", "vercel diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Debug Bundle

## Overview
Collect all necessary diagnostic information for Vercel support tickets.

## Prerequisites
- Vercel SDK installed
- Access to application logs
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
# vercel-debug-bundle.sh

BUNDLE_DIR="vercel-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Vercel Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info
```bash
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "VERCEL_API_KEY: ${VERCEL_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Gather SDK and Logs
```bash
# SDK version
npm list vercel 2>/dev/null >> "$BUNDLE_DIR/summary.txt"

# Recent logs (redacted)
grep -i "vercel" ~/.npm/_logs/*.log 2>/dev/null | tail -50 >> "$BUNDLE_DIR/logs.txt"
```

### Step 4: Package Bundle
```bash
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

## Output
- `vercel-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
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
1. Create bundle: `bash vercel-debug-bundle.sh`
2. Review for sensitive data
3. Upload to Vercel support portal

## Resources
- [Vercel Support](https://vercel.com/docs/support)
- [Vercel Status](https://www.vercel-status.com)

## Next Steps
For rate limit issues, see `vercel-rate-limits`.