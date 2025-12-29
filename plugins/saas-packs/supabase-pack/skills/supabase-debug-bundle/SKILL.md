---
name: supabase-debug-bundle
description: |
  Collect Supabase debug evidence for support tickets and troubleshooting.
  Use when preparing a support ticket or diagnosing persistent issues.
  Trigger with phrases like "supabase debug", "supabase support bundle",
  "collect supabase logs", "supabase diagnostic".
allowed-tools: Read, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Debug Bundle

## Overview
Collect all necessary diagnostic information for Supabase support tickets.

## Prerequisites
- Access to application logs
- Permission to read configuration files
- SUPABASE_API_KEY environment variable configured
- Bash shell available

## Instructions

### Step 1: Run Debug Bundle Script
Create and run the debug bundle collection script:

```bash
#!/bin/bash
# supabase-debug-bundle.sh

BUNDLE_DIR="supabase-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Supabase Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Information
```bash
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "SUPABASE_API_KEY: [${SUPABASE_API_KEY:+SET}]" >> "$BUNDLE_DIR/summary.txt"

# SDK version
echo "--- SDK Version ---" >> "$BUNDLE_DIR/summary.txt"
npm list @supabase/supabase-js 2>/dev/null >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Collect Logs (Redacted)
```bash
# Recent logs (redacted)
grep -i "supabase" ~/.npm/_logs/*.log 2>/dev/null | tail -50 >> "$BUNDLE_DIR/logs.txt"

# Configuration (redacted)
cat .env 2>/dev/null | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt"

# Network connectivity test
curl -s -o /dev/null -w "%{http_code}" https://api.supabase.com >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Create Archive
```bash
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

## Output
- `summary.txt` - Environment and SDK version info
- `logs.txt` - Recent error logs (redacted)
- `config-redacted.txt` - Configuration with secrets removed
- `$BUNDLE_DIR.tar.gz` - Compressed archive for support

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Permission denied | No log access | Run with sudo or check permissions |
| No logs found | Log rotation | Check log archive location |
| Network test failed | Connectivity issue | Check firewall and DNS |
| Missing SDK | Not installed | Run `npm install @supabase/supabase-js` |

## Examples

### Quick Bundle Generation
```bash
bash supabase-debug-bundle.sh
# Output: supabase-debug-20241229-120000.tar.gz
```

### Programmatic Collection
```typescript
import { execSync } from 'child_process';

function collectDebugBundle(): string {
  const bundleDir = `supabase-debug-${Date.now()}`;
  execSync(`mkdir -p ${bundleDir}`);

  // Collect environment info
  const nodeVersion = execSync('node --version').toString();
  const sdkVersion = execSync('npm list @supabase/supabase-js').toString();

  // Write summary
  const summary = `Node: ${nodeVersion}\nSDK: ${sdkVersion}`;
  require('fs').writeFileSync(`${bundleDir}/summary.txt`, summary);

  return bundleDir;
}
```

## Resources
- [Supabase Support Portal](https://supabase.com/support)
- [Status Page](https://status.supabase.com)
- [Community Forum](https://community.supabase.com)

## Next Steps
- Review bundle for sensitive data before submitting
- Upload to Supabase support portal
- Reference bundle ID in support ticket
- For rate limit issues, see `supabase-rate-limits`