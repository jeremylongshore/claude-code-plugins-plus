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
tags: [saas, langfuse, debugging]

---
# Langfuse Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`npm list langfuse @langfuse/client @langfuse/tracing 2>/dev/null | head -5 || echo 'No langfuse packages'`

## Overview
Collect all diagnostic information needed for Langfuse support tickets: environment versions, SDK config, API connectivity, redacted logs, and a reproduction template.

## Prerequisites
- Langfuse SDK installed
- Access to application logs
- Bash shell available

## Instructions

### Step 1: Run the Full Debug Bundle Script

Save this as `langfuse-debug.sh` and run it:

```bash
#!/bin/bash
set -euo pipefail

BUNDLE_DIR="langfuse-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Langfuse Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" | tee -a "$BUNDLE_DIR/summary.txt"

# --- Environment ---
{
  echo ""
  echo "--- Environment ---"
  echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')"
  echo "Python: $(python3 --version 2>/dev/null || echo 'not installed')"
  echo "npm: $(npm --version 2>/dev/null || echo 'not installed')"
  echo "OS: $(uname -srm)"
} >> "$BUNDLE_DIR/summary.txt"

# --- SDK Versions ---
{
  echo ""
  echo "--- SDK Versions ---"
  npm list langfuse @langfuse/client @langfuse/tracing @langfuse/otel @langfuse/openai @langfuse/langchain 2>/dev/null || echo "npm: no langfuse packages"
  pip show langfuse 2>/dev/null | grep -E "Name|Version" || echo "pip: langfuse not found"
} >> "$BUNDLE_DIR/summary.txt"

# --- Config (redacted) ---
{
  echo ""
  echo "--- Langfuse Config ---"
  echo "LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY:+SET (${LANGFUSE_PUBLIC_KEY:0:12}...)}"
  echo "LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY:+SET}"
  echo "LANGFUSE_BASE_URL: ${LANGFUSE_BASE_URL:-NOT SET}"
  echo "LANGFUSE_HOST: ${LANGFUSE_HOST:-NOT SET}"
} >> "$BUNDLE_DIR/summary.txt"

# --- Network Connectivity ---
{
  echo ""
  echo "--- Network Test ---"
  HOST="${LANGFUSE_BASE_URL:-${LANGFUSE_HOST:-https://cloud.langfuse.com}}"
  echo "Target host: $HOST"
  echo -n "Health endpoint: "
  curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" "$HOST/api/public/health" 2>/dev/null || echo "FAILED"
  echo ""

  if [ -n "${LANGFUSE_PUBLIC_KEY:-}" ] && [ -n "${LANGFUSE_SECRET_KEY:-}" ]; then
    AUTH=$(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)
    echo -n "Auth test: "
    curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: Basic $AUTH" \
      "$HOST/api/public/traces?limit=1" 2>/dev/null || echo "FAILED"
    echo ""
  fi
} >> "$BUNDLE_DIR/summary.txt"

# --- Application Logs (redacted) ---
if [ -d "logs" ]; then
  grep -i "langfuse\|trace\|generation\|flush" logs/*.log 2>/dev/null | \
    tail -100 | \
    sed 's/sk-lf-[a-zA-Z0-9]*/sk-lf-***REDACTED***/g' | \
    sed 's/pk-lf-[a-zA-Z0-9]*/pk-lf-***REDACTED***/g' \
    > "$BUNDLE_DIR/app-logs-redacted.txt" 2>/dev/null || true
fi

# --- Package Dependencies ---
if [ -f "package.json" ]; then
  grep -A 100 '"dependencies"' package.json | head -60 > "$BUNDLE_DIR/package-deps.txt" 2>/dev/null || true
fi

# --- Reproduction Template ---
cat > "$BUNDLE_DIR/reproduction-steps.md" << 'REPRO'
# Bug Report

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
Paste error output here
```

## Relevant Code
```typescript
// Paste minimal reproduction here
```
REPRO

# --- Package ---
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR" 2>/dev/null
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Contents:"
ls -la "$BUNDLE_DIR/"
```

### Step 2: Review Before Sharing

**Always redact before submitting:**

| Include | Redact |
|---------|--------|
| Error messages and stack traces | API keys (`pk-lf-*`, `sk-lf-*`) |
| SDK versions and config structure | Secret keys and passwords |
| HTTP status codes | PII (emails, user IDs) |
| Timing and latency data | Internal URLs and IPs |
| OS and runtime versions | Database connection strings |

### Step 3: Submit to Support

1. Run: `bash langfuse-debug.sh`
2. Review bundle contents for leaked secrets
3. Fill in `reproduction-steps.md`
4. Submit via:
   - [GitHub Issues](https://github.com/langfuse/langfuse/issues) (public)
   - [Discord](https://langfuse.com/discord) (community)
   - Email support (enterprise customers)

### Step 4: Quick Inline Diagnostic (No File)

For a fast check without creating files:

```bash
set -euo pipefail
echo "=== Quick Langfuse Check ==="
echo "Node: $(node --version 2>/dev/null || echo N/A)"
npm list langfuse @langfuse/client 2>/dev/null | head -5
echo ""
echo "Public Key: ${LANGFUSE_PUBLIC_KEY:+SET} | Secret Key: ${LANGFUSE_SECRET_KEY:+SET}"
HOST="${LANGFUSE_BASE_URL:-${LANGFUSE_HOST:-https://cloud.langfuse.com}}"
echo "Health: $(curl -s -o /dev/null -w '%{http_code}' $HOST/api/public/health)"
```

## Error Handling

| Collected Item | Why It Matters |
|----------------|---------------|
| SDK version | Version-specific bugs, breaking changes between v3/v4/v5 |
| Environment versions | Node 18+ required, Python 3.9+ |
| Network test | Firewall, DNS, self-hosted connectivity |
| Auth test | Key validity, project mismatch |
| Redacted logs | Trace errors, flush failures, rate limits |
| Package deps | Conflicting versions, missing peer deps |

## Resources
- [GitHub Issues](https://github.com/langfuse/langfuse/issues)
- [Discord Community](https://langfuse.com/discord)
- [Langfuse Status](https://status.langfuse.com)
- [Self-Hosting Troubleshooting](https://langfuse.com/self-hosting/configuration)
