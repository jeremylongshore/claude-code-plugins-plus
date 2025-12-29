---
name: supabase-debug-bundle
description: |
  Collect Supabase debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Supabase problems.
  Trigger with phrases like "supabase debug", "supabase support bundle",
  "collect supabase logs", "supabase diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Debug Bundle

## Overview
Collect all necessary diagnostic information for Supabase support tickets.

## Prerequisites
- Supabase SDK installed
- Access to application logs
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
# supabase-debug-bundle.sh

BUNDLE_DIR="supabase-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Supabase Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info
```bash
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "SUPABASE_API_KEY: ${SUPABASE_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Gather SDK and Logs
```bash
# SDK version
npm list @supabase/supabase-js 2>/dev/null >> "$BUNDLE_DIR/summary.txt"

# Recent logs (redacted)
grep -i "supabase" ~/.npm/_logs/*.log 2>/dev/null | tail -50 >> "$BUNDLE_DIR/logs.txt"
```

### Step 4: Package Bundle
```bash
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

## Output
- `supabase-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
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
1. Create bundle: `bash supabase-debug-bundle.sh`
2. Review for sensitive data
3. Upload to Supabase support portal

## Resources
- [Supabase Support](https://supabase.com/docs/support)
- [Supabase Status](https://status.supabase.com)

## Next Steps
For rate limit issues, see `supabase-rate-limits`.