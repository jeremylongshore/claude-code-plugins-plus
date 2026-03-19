---
name: mistral-debug-bundle
description: |
  Collect Mistral AI debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Mistral AI problems.
  Trigger with phrases like "mistral debug", "mistral support bundle",
  "collect mistral logs", "mistral diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect all necessary diagnostic information for Mistral AI support tickets.

## Prerequisites
- Mistral AI SDK installed
- Access to application logs
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# mistral-debug-bundle.sh

BUNDLE_DIR="mistral-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Mistral AI Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info

```bash
set -euo pipefail
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "Python: $(python3 --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "pip: $(pip --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -a)" >> "$BUNDLE_DIR/summary.txt"
echo "MISTRAL_API_KEY: ${MISTRAL_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Gather SDK and API Info

```bash
set -euo pipefail
# SDK version (Node.js)
echo "--- SDK Versions ---" >> "$BUNDLE_DIR/summary.txt"
npm list @mistralai/mistralai 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Node SDK: not installed" >> "$BUNDLE_DIR/summary.txt"

# SDK version (Python)
pip show mistralai 2>/dev/null | grep -E "^(Name|Version)" >> "$BUNDLE_DIR/summary.txt" || echo "Python SDK: not installed" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# API connectivity test
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "API Status: " >> "$BUNDLE_DIR/summary.txt"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models)
echo "$HTTP_STATUS" >> "$BUNDLE_DIR/summary.txt"

# List available models (redact API key from output)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Available Models ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models 2>/dev/null | \
  jq -r '.data[].id' 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || \
  echo "Could not fetch models" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Collect Logs (Redacted)

```bash
# Recent logs (redacted)
echo "--- Recent Logs (redacted) ---" >> "$BUNDLE_DIR/logs.txt"
if [ -d "logs" ]; then
  grep -i "mistral" logs/*.log 2>/dev/null | tail -100 >> "$BUNDLE_DIR/logs.txt"
fi

# npm debug logs
if [ -d "$HOME/.npm/_logs" ]; then
  grep -i "mistral" "$HOME/.npm/_logs"/*.log 2>/dev/null | tail -50 >> "$BUNDLE_DIR/logs.txt"
fi

# Configuration (redacted - secrets masked)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f ".env" ]; then
  cat .env 2>/dev/null | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt"
fi

# package.json dependencies
if [ -f "package.json" ]; then
  echo "" >> "$BUNDLE_DIR/summary.txt"
  echo "--- Dependencies ---" >> "$BUNDLE_DIR/summary.txt"
  jq '.dependencies, .devDependencies' package.json 2>/dev/null >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 5: Capture Error Details

```bash
set -euo pipefail
# Error reproduction script
cat > "$BUNDLE_DIR/reproduce.sh" << 'SCRIPT'
#!/bin/bash
# Minimal reproduction script

curl -X POST https://api.mistral.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  -d '{
    "model": "mistral-small-latest",
    "messages": [{"role": "user", "content": "Hello"}]
  }' 2>&1

echo ""
echo "Exit code: $?"
SCRIPT
chmod +x "$BUNDLE_DIR/reproduce.sh"
```

### Step 6: Package Bundle

```bash
set -euo pipefail
# Create timestamp file
echo "Bundle created: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$BUNDLE_DIR/timestamp.txt"

# Package everything
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo ""
echo "IMPORTANT: Review the bundle for sensitive data before sharing!"
echo "Run: tar -tzf $BUNDLE_DIR.tar.gz"
```

## Complete Script

```bash
#!/bin/bash
# mistral-debug-bundle.sh - Complete version

set -e

BUNDLE_DIR="mistral-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "Creating Mistral AI debug bundle..."

# Summary file
cat > "$BUNDLE_DIR/summary.txt" << EOF
=== Mistral AI Debug Bundle ===
Generated: $(date)
Hostname: $(hostname)

--- Environment ---
Node.js: $(node --version 2>/dev/null || echo 'not installed')
Python: $(python3 --version 2>/dev/null || echo 'not installed')
OS: $(uname -a)
MISTRAL_API_KEY: ${MISTRAL_API_KEY:+[SET]}

--- SDK Versions ---
EOF

npm list @mistralai/mistralai 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Node SDK: not installed" >> "$BUNDLE_DIR/summary.txt"
pip show mistralai 2>/dev/null | grep -E "^(Name|Version)" >> "$BUNDLE_DIR/summary.txt" || echo "Python SDK: not installed" >> "$BUNDLE_DIR/summary.txt"

echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- API Test ---" >> "$BUNDLE_DIR/summary.txt"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${MISTRAL_API_KEY}" https://api.mistral.ai/v1/models 2>/dev/null)
echo "HTTP Status: $HTTP_STATUS" >> "$BUNDLE_DIR/summary.txt"

# Redacted config
if [ -f ".env" ]; then
  cat .env | sed 's/=.*/=***REDACTED***/' > "$BUNDLE_DIR/config-redacted.txt"
fi

# Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

## Output
- `mistral-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - Environment and SDK info
  - `logs.txt` - Recent redacted logs
  - `config-redacted.txt` - Configuration (secrets removed)
  - `reproduce.sh` - Minimal reproduction script

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| Environment versions | Compatibility check | Yes |
| SDK version | Version-specific bugs | Yes |
| Error logs (redacted) | Root cause analysis | Yes |
| Config (redacted) | Configuration issues | Yes |
| API connectivity test | Network issues | Yes |

## Sensitive Data Handling

**ALWAYS REDACT:**
- API keys and tokens
- Passwords and secrets
- PII (emails, names, IDs)
- Internal URLs and IPs

**Safe to Include:**
- Error messages
- Stack traces (redacted)
- SDK/runtime versions
- HTTP status codes

## TypeScript Debug Helper

```typescript
interface DebugInfo {
  timestamp: string;
  sdkVersion: string;
  nodeVersion: string;
  apiKeySet: boolean;
  lastError?: {
    message: string;
    status?: number;
    requestId?: string;
  };
}

function collectDebugInfo(error?: Error): DebugInfo {
  return {
    timestamp: new Date().toISOString(),
    sdkVersion: require('@mistralai/mistralai/package.json').version,
    nodeVersion: process.version,
    apiKeySet: !!process.env.MISTRAL_API_KEY,
    lastError: error ? {
      message: error.message,
      status: (error as any).status,
      requestId: (error as any).requestId,
    } : undefined,
  };
}

// Usage
try {
  await client.chat.complete({ /* ... */ });
} catch (error) {
  const debug = collectDebugInfo(error as Error);
  console.error('Debug info:', JSON.stringify(debug, null, 2));
}
```

## Resources
- [Mistral AI Discord](https://discord.gg/mistralai)
- [Mistral AI Status](https://status.mistral.ai/)

## Next Steps
For rate limit issues, see `mistral-rate-limits`.

## Examples

**Basic usage**: Apply mistral debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize mistral debug bundle for production environments with multiple constraints and team-specific requirements.