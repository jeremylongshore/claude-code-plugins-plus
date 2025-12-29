---
name: supabase-debug-bundle
description: |
  Supabase debug evidence collection for support tickets.
  Trigger phrases: "supabase debug", "supabase support bundle",
  "collect supabase logs", "supabase diagnostic".
allowed-tools: Read, Bash, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Debug Bundle

## Overview
Collect all necessary diagnostic information for Supabase support tickets.

## Quick Bundle Generation
```bash
#!/bin/bash
# supabase-debug-bundle.sh

BUNDLE_DIR="supabase-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Supabase Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"

# 1. Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "SUPABASE_API_KEY: ${SUPABASE_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"

# 2. SDK version
echo "--- SDK Version ---" >> "$BUNDLE_DIR/summary.txt"
npm list @supabase/supabase-js 2>/dev/null >> "$BUNDLE_DIR/summary.txt"

# 3. Recent logs (redacted)
echo "--- Recent Logs ---" >> "$BUNDLE_DIR/summary.txt"
grep -i "supabase" ~/.npm/_logs/*.log 2>/dev/null | tail -50 >> "$BUNDLE_DIR/logs.txt"

# 4. Configuration (redacted)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
cat .env 2>/dev/null | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt"

# 5. Network connectivity
echo "--- Network Test ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" https://api.supabase.com >> "$BUNDLE_DIR/summary.txt"

# Create archive
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

## Bundle Contents Checklist

| Item | Purpose | Included |
|------|---------|----------|
| Environment versions | Compatibility check | ✓ |
| SDK version | Version-specific bugs | ✓ |
| Error logs (redacted) | Root cause analysis | ✓ |
| Config (redacted) | Configuration issues | ✓ |
| Network test | Connectivity issues | ✓ |
| Request/Response samples | API debugging | Manual |

## Sensitive Data Handling

**ALWAYS REDACT:**
- API keys and tokens
- Passwords and secrets
- PII (emails, names, IDs)
- Internal URLs/IPs

**Safe to Include:**
- Error messages
- Stack traces (redacted)
- SDK/runtime versions
- HTTP status codes

## Submitting to Support

1. Create bundle: `bash supabase-debug-bundle.sh`
2. Review for sensitive data
3. Upload to Supabase support portal
4. Reference bundle in ticket

## Programmatic Collection
```typescript
// Programmatic debug collection
```

## Next Steps
For rate limit issues, see `supabase-rate-limits`.