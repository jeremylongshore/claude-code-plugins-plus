---
name: langfuse-debug-bundle
description: |
  Collect Langfuse debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Langfuse problems.
  Trigger with phrases like "langfuse debug", "langfuse support bundle",
  "collect langfuse logs", "langfuse diagnostic", "langfuse troubleshoot".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect all necessary diagnostic information for Langfuse support tickets.

## Prerequisites
- Langfuse SDK installed
- Access to application logs
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
# langfuse-debug-bundle.sh

BUNDLE_DIR="langfuse-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Langfuse Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
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
echo "OS: $(uname -a)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Langfuse config (redacted)
echo "--- Langfuse Config ---" >> "$BUNDLE_DIR/summary.txt"
echo "LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY:+[SET - ${LANGFUSE_PUBLIC_KEY:0:10}...]}" >> "$BUNDLE_DIR/summary.txt"
echo "LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "LANGFUSE_HOST: ${LANGFUSE_HOST:-[NOT SET - using default]}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Gather SDK and Package Info
```bash
set -euo pipefail
# SDK versions
echo "--- SDK Versions ---" >> "$BUNDLE_DIR/summary.txt"
npm list langfuse 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "npm: langfuse not found" >> "$BUNDLE_DIR/summary.txt"
pip show langfuse 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "pip: langfuse not found" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Related packages
echo "--- Related Packages ---" >> "$BUNDLE_DIR/summary.txt"
npm list openai @anthropic-ai/sdk langchain 2>/dev/null >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Test API Connectivity
```bash
set -euo pipefail
# Network connectivity test
echo "--- Network Test ---" >> "$BUNDLE_DIR/summary.txt"

HOST="${LANGFUSE_HOST:-https://cloud.langfuse.com}"
echo "Testing host: $HOST" >> "$BUNDLE_DIR/summary.txt"

# Health check
echo -n "Health endpoint: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" "$HOST/api/public/health" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Auth test (if keys available)
if [ -n "$LANGFUSE_PUBLIC_KEY" ] && [ -n "$LANGFUSE_SECRET_KEY" ]; then
  echo -n "Auth test: " >> "$BUNDLE_DIR/summary.txt"
  AUTH=$(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Basic $AUTH" \
    "$HOST/api/public/traces?limit=1")
  echo "$HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"
fi
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 5: Collect Application Logs
```bash
# Recent logs (redacted)
echo "--- Recent Logs ---" >> "$BUNDLE_DIR/summary.txt"

# Search for langfuse-related logs
if [ -d "logs" ]; then
  grep -i "langfuse\|trace\|generation" logs/*.log 2>/dev/null | \
    tail -100 | \
    sed 's/sk-lf-[a-zA-Z0-9]*/sk-lf-***REDACTED***/g' | \
    sed 's/pk-lf-[a-zA-Z0-9]*/pk-lf-***REDACTED***/g' \
    >> "$BUNDLE_DIR/logs.txt"
fi

# npm logs
if [ -d "$HOME/.npm/_logs" ]; then
  grep -i "langfuse" "$HOME/.npm/_logs"/*.log 2>/dev/null | \
    tail -50 >> "$BUNDLE_DIR/npm-logs.txt"
fi
echo "Log files collected (if available)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 6: Capture Configuration Files
```bash
# Configuration (redacted)
echo "--- Config Files ---" >> "$BUNDLE_DIR/summary.txt"

# .env (redacted)
if [ -f ".env" ]; then
  cat .env 2>/dev/null | \
    sed 's/=.*/=***REDACTED***/' | \
    grep -i "langfuse\|openai\|anthropic" \
    >> "$BUNDLE_DIR/config-redacted.txt"
  echo ".env: captured (redacted)" >> "$BUNDLE_DIR/summary.txt"
fi

# package.json dependencies
if [ -f "package.json" ]; then
  grep -A 50 '"dependencies"' package.json | head -60 >> "$BUNDLE_DIR/package-deps.txt"
  echo "package.json: captured" >> "$BUNDLE_DIR/summary.txt"
fi

# tsconfig.json
if [ -f "tsconfig.json" ]; then
  cp tsconfig.json "$BUNDLE_DIR/"
  echo "tsconfig.json: captured" >> "$BUNDLE_DIR/summary.txt"
fi
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 7: Package Bundle
```bash
# Add reproduction steps template
cat > "$BUNDLE_DIR/reproduction-steps.md" << 'EOF'
# Reproduction Steps

## Environment
- Node.js version:
- Langfuse SDK version:
- Langfuse host: Cloud / Self-hosted (version: )

## Steps to Reproduce
1.
2.
3.

## Expected Behavior


## Actual Behavior


## Error Messages
```
Paste error messages here
```

## Relevant Code
```typescript
// Paste relevant code here
```
EOF

# Create archive
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo ""
echo "Contents:"
ls -la "$BUNDLE_DIR/"
```

## Output
- `langfuse-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - Environment and SDK info
  - `logs.txt` - Recent redacted application logs
  - `npm-logs.txt` - npm debug logs
  - `config-redacted.txt` - Configuration (secrets removed)
  - `package-deps.txt` - Dependencies
  - `reproduction-steps.md` - Template for bug report

## Sensitive Data Handling

**ALWAYS REDACT:**
- API keys (pk-lf-*, sk-lf-*)
- Secret keys and tokens
- Passwords and credentials
- PII (emails, names, IDs)
- Internal URLs and IPs

**Safe to Include:**
- Error messages and stack traces
- SDK versions
- Configuration structure (not values)
- HTTP status codes
- Timing information

## Quick Debug Script

Save as `langfuse-debug.sh`:
```bash
#!/bin/bash
set -e

BUNDLE_DIR="langfuse-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

# Quick diagnostics
{
  echo "=== Langfuse Quick Debug ==="
  echo "Date: $(date)"
  echo ""
  echo "--- Environment ---"
  echo "Node: $(node --version 2>/dev/null || echo 'N/A')"
  echo "Python: $(python3 --version 2>/dev/null || echo 'N/A')"
  echo ""
  echo "--- SDK ---"
  npm list langfuse 2>/dev/null || echo "npm: not found"
  pip show langfuse 2>/dev/null | grep Version || echo "pip: not found"
  echo ""
  echo "--- Config ---"
  echo "Public Key: ${LANGFUSE_PUBLIC_KEY:+SET}"
  echo "Secret Key: ${LANGFUSE_SECRET_KEY:+SET}"
  echo "Host: ${LANGFUSE_HOST:-default}"
  echo ""
  echo "--- Connectivity ---"
  HOST="${LANGFUSE_HOST:-https://cloud.langfuse.com}"
  echo "Health: $(curl -s -o /dev/null -w '%{http_code}' $HOST/api/public/health)"
} > "$BUNDLE_DIR/summary.txt"

tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Created: $BUNDLE_DIR.tar.gz"
```

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| Environment versions | Compatibility check | Yes |
| SDK version | Version-specific bugs | Yes |
| Error logs (redacted) | Root cause analysis | Yes |
| Config (redacted) | Configuration issues | Yes |
| Network test | Connectivity issues | Yes |
| Reproduction template | Bug reporting | Yes |

## Submit to Support
1. Run debug script: `bash langfuse-debug.sh`
2. Review bundle for sensitive data
3. Fill in `reproduction-steps.md`
4. Open issue at [GitHub](https://github.com/langfuse/langfuse/issues)
5. Or post in [Discord](https://langfuse.com/discord)

## Resources
- [Langfuse GitHub Issues](https://github.com/langfuse/langfuse/issues)
- [Langfuse Discord](https://langfuse.com/discord)
- [Langfuse Status](https://status.langfuse.com)

## Next Steps
For rate limit issues, see `langfuse-rate-limits`.

## Examples

**Basic usage**: Apply langfuse debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize langfuse debug bundle for production environments with multiple constraints and team-specific requirements.