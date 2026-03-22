---
name: palantir-debug-bundle
description: |
  Collect Palantir Foundry debug evidence for support tickets and troubleshooting.
  Use when encountering persistent Foundry issues, preparing support tickets,
  or collecting diagnostic information for Foundry problems.
  Trigger with phrases like "palantir debug", "foundry support bundle",
  "collect palantir logs", "foundry diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, debugging, diagnostics]
compatible-with: claude-code, codex, openclaw
---

# Palantir Debug Bundle

## Overview
Collect all diagnostic information needed for Foundry support tickets: SDK version, auth status, API connectivity, build logs, and environment details. Secrets are automatically redacted.

## Prerequisites
- `foundry-platform-sdk` installed
- Access to application logs and Foundry build logs
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
set -euo pipefail
BUNDLE_DIR="foundry-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Foundry Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"

# Python environment
echo -e "\n--- Python Environment ---" >> "$BUNDLE_DIR/summary.txt"
python --version >> "$BUNDLE_DIR/summary.txt" 2>&1
pip show foundry-platform-sdk 2>/dev/null | grep -E "^(Name|Version)" >> "$BUNDLE_DIR/summary.txt"
pip show palantir-sdk 2>/dev/null | grep -E "^(Name|Version)" >> "$BUNDLE_DIR/summary.txt"

# Environment variables (redacted)
echo -e "\n--- Environment (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
echo "FOUNDRY_HOSTNAME: ${FOUNDRY_HOSTNAME:-NOT SET}" >> "$BUNDLE_DIR/summary.txt"
echo "FOUNDRY_TOKEN: ${FOUNDRY_TOKEN:+[SET, length=${#FOUNDRY_TOKEN}]}" >> "$BUNDLE_DIR/summary.txt"
echo "FOUNDRY_CLIENT_ID: ${FOUNDRY_CLIENT_ID:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "FOUNDRY_CLIENT_SECRET: ${FOUNDRY_CLIENT_SECRET:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Test API Connectivity
```bash
# API connectivity test
echo -e "\n--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "${FOUNDRY_HOSTNAME:-}" ] && [ -n "${FOUNDRY_TOKEN:-}" ]; then
  HTTP_CODE=$(curl -s -o "$BUNDLE_DIR/api-response.json" -w "%{http_code}" \
    -H "Authorization: Bearer $FOUNDRY_TOKEN" \
    "https://$FOUNDRY_HOSTNAME/api/v2/ontologies" 2>/dev/null || echo "FAILED")
  echo "Ontology API: HTTP $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"
else
  echo "Skipped: FOUNDRY_HOSTNAME or FOUNDRY_TOKEN not set" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 3: Collect Build Logs and Error Context
```bash
# Collect recent Python errors
echo -e "\n--- Recent Errors ---" >> "$BUNDLE_DIR/summary.txt"
grep -rn "foundry\.\|ApiError\|Traceback" *.log 2>/dev/null | tail -30 >> "$BUNDLE_DIR/errors.txt" || true

# Collect .env (redacted)
if [ -f .env ]; then
  sed 's/=.*/=***REDACTED***/' .env > "$BUNDLE_DIR/config-redacted.txt"
fi
```

### Step 4: Package and Verify
```bash
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle: $BUNDLE_DIR.tar.gz ($(du -h "$BUNDLE_DIR.tar.gz" | cut -f1))"
rm -rf "$BUNDLE_DIR"
```

## Output
- `foundry-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` — SDK versions, env vars (redacted), API status
  - `api-response.json` — raw API response for diagnosis
  - `errors.txt` — recent error logs
  - `config-redacted.txt` — configuration with secrets masked

## Error Handling
| Item | Purpose | Sensitive? |
|------|---------|------------|
| SDK versions | Compatibility check | No |
| API HTTP code | Connectivity diagnosis | No |
| Error logs | Root cause analysis | Review before sharing |
| Config (redacted) | Configuration issues | Auto-redacted |
| Bearer tokens | Auth diagnosis | NEVER include raw values |

## Examples

### Submit to Palantir Support
1. Run: `bash foundry-debug-bundle.sh`
2. Review the tarball for any leaked secrets
3. Open a support ticket in Palantir's support portal
4. Attach the bundle with a description of the issue

## Resources
- [Foundry Documentation](https://www.palantir.com/docs/foundry)
- [Foundry API Reference](https://www.palantir.com/docs/foundry/api/general/overview/introduction)

## Next Steps
For rate limit issues, see `palantir-rate-limits`.
