---
name: juicebox-debug-bundle
description: |
  Collect Juicebox debug evidence for support.
  Use when creating support tickets, gathering diagnostic info,
  or preparing error reports for Juicebox support team.
  Trigger with phrases like "juicebox debug info", "juicebox support bundle",
  "collect juicebox diagnostics", "juicebox troubleshooting".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview

Collect environment info, test API connectivity, gather error logs, and package everything into a redacted support bundle (`juicebox-debug-TIMESTAMP.tar.gz`). The bundle omits full API tokens and credentials, keeping only masked prefixes for identification. Juicebox support accepts this format for accelerated ticket triage.

## Prerequisites

- `JUICEBOX_USERNAME` and `JUICEBOX_API_TOKEN` environment variables set
- Access to application log files (default: `./logs/`)
- `curl` and `tar` available in PATH

## Instructions

### Step 1: Collect Environment Info

```bash
#!/bin/bash
# juicebox-debug-bundle.sh
# Collects diagnostic info and packages a redacted support bundle

set -euo pipefail
TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)
BUNDLE_DIR="juicebox-debug-${TIMESTAMP}"
mkdir -p "${BUNDLE_DIR}"

echo "=== Juicebox Debug Bundle ===" | tee "${BUNDLE_DIR}/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "" | tee -a "${BUNDLE_DIR}/summary.txt"

# Environment
echo "--- Environment ---" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'not installed')" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "Python: $(python3 --version 2>/dev/null || echo 'not installed')" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "OS: $(uname -srm)" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "" | tee -a "${BUNDLE_DIR}/summary.txt"

# SDK version
echo "--- Juicebox SDK ---" | tee -a "${BUNDLE_DIR}/summary.txt"
npm list @juicebox/sdk 2>/dev/null | tee -a "${BUNDLE_DIR}/summary.txt" || echo "SDK not found in node_modules" | tee -a "${BUNDLE_DIR}/summary.txt"
pip show juicebox-sdk 2>/dev/null | tee -a "${BUNDLE_DIR}/summary.txt" || echo "Python SDK not found" | tee -a "${BUNDLE_DIR}/summary.txt"

# Redacted config
echo "" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "--- Auth (redacted) ---" | tee -a "${BUNDLE_DIR}/summary.txt"
if [ -n "${JUICEBOX_API_TOKEN:-}" ]; then
  echo "Token: ${JUICEBOX_API_TOKEN:0:8}...${JUICEBOX_API_TOKEN: -4}" | tee -a "${BUNDLE_DIR}/summary.txt"
  echo "Username: ${JUICEBOX_USERNAME:-'NOT SET'}" | tee -a "${BUNDLE_DIR}/summary.txt"
else
  echo "JUICEBOX_API_TOKEN: NOT SET" | tee -a "${BUNDLE_DIR}/summary.txt"
fi
```

### Step 2: Test API Connectivity

```bash
# Append to juicebox-debug-bundle.sh

echo "" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "--- API Connectivity ---" | tee -a "${BUNDLE_DIR}/summary.txt"

# Health check (no auth required)
echo "Health check:" | tee -a "${BUNDLE_DIR}/summary.txt"
curl -s -w "\n  HTTP: %{http_code} | DNS: %{time_namelookup}s | Connect: %{time_connect}s | Total: %{time_total}s\n" \
  --connect-timeout 10 \
  https://api.juicebox.ai/v1/health | tee -a "${BUNDLE_DIR}/summary.txt"

# Auth check (requires token)
echo "" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "Auth test:" | tee -a "${BUNDLE_DIR}/summary.txt"
AUTH_RESULT=$(curl -s -w "\n  HTTP: %{http_code}" \
  --connect-timeout 10 \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  https://api.juicebox.ai/v1/auth/me 2>&1)
# Redact any tokens in the response
echo "$AUTH_RESULT" | sed "s/${JUICEBOX_API_TOKEN}/[REDACTED]/g" | tee -a "${BUNDLE_DIR}/summary.txt"

# Rate limit status
echo "" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "Rate limit headers:" | tee -a "${BUNDLE_DIR}/summary.txt"
curl -s -D - -o /dev/null \
  --connect-timeout 10 \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  https://api.juicebox.ai/v1/usage 2>&1 | grep -i "x-ratelimit" | tee -a "${BUNDLE_DIR}/summary.txt"
```

### Step 3: Gather Error Logs

```bash
# Append to juicebox-debug-bundle.sh

echo "" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "--- Recent Errors (last 24h) ---" | tee -a "${BUNDLE_DIR}/summary.txt"

LOG_DIR="${LOG_PATH:-./logs}"

if [ -d "$LOG_DIR" ]; then
  # Grep for Juicebox-related errors, redact tokens
  grep -rih "juicebox\|peoplegpt\|api\.juicebox" "$LOG_DIR"/*.log 2>/dev/null \
    | grep -i "error\|fail\|timeout\|429\|401\|500" \
    | tail -100 \
    | sed "s/${JUICEBOX_API_TOKEN:-PLACEHOLDER}/[REDACTED]/g" \
    > "${BUNDLE_DIR}/errors.log"

  ERROR_COUNT=$(wc -l < "${BUNDLE_DIR}/errors.log")
  echo "Found ${ERROR_COUNT} error lines" | tee -a "${BUNDLE_DIR}/summary.txt"
else
  echo "Log directory not found at ${LOG_DIR}" | tee -a "${BUNDLE_DIR}/summary.txt"
  touch "${BUNDLE_DIR}/errors.log"
fi

# Also capture stderr from a test search
echo "" | tee -a "${BUNDLE_DIR}/summary.txt"
echo "--- Test Search ---" | tee -a "${BUNDLE_DIR}/summary.txt"
curl -s -w "\n  HTTP: %{http_code} | Time: %{time_total}s" \
  --connect-timeout 10 \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}' \
  https://api.juicebox.ai/v1/search 2>&1 \
  | sed "s/${JUICEBOX_API_TOKEN}/[REDACTED]/g" \
  | tee -a "${BUNDLE_DIR}/summary.txt"
```

### Step 4: Package the Support Bundle

```bash
# Append to juicebox-debug-bundle.sh

echo ""
echo "--- Packaging Bundle ---"

# Final redaction pass on all files
for f in "${BUNDLE_DIR}"/*; do
  if [ -f "$f" ]; then
    sed -i "s/${JUICEBOX_API_TOKEN:-PLACEHOLDER}/[REDACTED]/g" "$f" 2>/dev/null || true
  fi
done

# Create tarball
tar -czf "${BUNDLE_DIR}.tar.gz" "${BUNDLE_DIR}/"
rm -rf "${BUNDLE_DIR}"

BUNDLE_SIZE=$(du -h "${BUNDLE_DIR}.tar.gz" | cut -f1)
echo ""
echo "Bundle created: ${BUNDLE_DIR}.tar.gz (${BUNDLE_SIZE})"
echo "Attach this file to your Juicebox support ticket."
```

### Complete Script

Save all four steps above into a single `juicebox-debug-bundle.sh` file and run:

```bash
chmod +x juicebox-debug-bundle.sh
./juicebox-debug-bundle.sh
```

## Output

- `juicebox-debug-TIMESTAMP.tar.gz` containing:
  - `summary.txt` -- environment, SDK version, redacted auth status, connectivity results
  - `errors.log` -- filtered Juicebox-related error lines from the last 24 hours
- All API tokens and credentials are automatically redacted before packaging

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `curl: (7) Failed to connect` | DNS or firewall blocking `api.juicebox.ai` | Check DNS with `nslookup api.juicebox.ai`; verify outbound HTTPS is allowed |
| `JUICEBOX_API_TOKEN: NOT SET` | Environment variable missing | Export the variable: `export JUICEBOX_API_TOKEN="your_token"` |
| `grep: ./logs/*.log: No such file` | Log directory path differs | Set `LOG_PATH=/path/to/logs` before running the script |
| Bundle is empty (0 error lines) | Logs rotated or different format | Check log rotation config; adjust grep patterns for your log format |
| `tar: Cannot open: Permission denied` | No write access to current directory | Run from a writable directory or set `BUNDLE_DIR` to `/tmp/` |

## Examples

**Quick one-liner to test connectivity only:**

```bash
curl -s -w "\nHTTP: %{http_code} | Total: %{time_total}s\n" \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  https://api.juicebox.ai/v1/health
```

**Collect bundle with custom log path:**

```bash
LOG_PATH=/var/log/myapp ./juicebox-debug-bundle.sh
```

**Attach to a support ticket via email:**

```bash
# After generating the bundle
echo "Please find the debug bundle attached." | \
  mail -s "Juicebox Support: [ISSUE DESCRIPTION]" \
  -a juicebox-debug-*.tar.gz \
  support@juicebox.ai
```

## Resources

- [Juicebox Support Portal](https://juicebox.ai/support)
- [Juicebox API Status](https://status.juicebox.ai)
- [Juicebox API Documentation](https://juicebox.ai/docs/api)

## Next Steps

After collecting the bundle, attach it to your support ticket. If the issue is rate-limit related, see `juicebox-rate-limits`. For ongoing incidents, follow `juicebox-incident-runbook`.
