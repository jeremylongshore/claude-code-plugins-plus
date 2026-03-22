---
name: perplexity-debug-bundle
description: |
  Collect Perplexity debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Perplexity problems.
  Trigger with phrases like "perplexity debug", "perplexity support bundle",
  "collect perplexity logs", "perplexity diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, debugging]

---
# Perplexity Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`echo "PERPLEXITY_API_KEY: ${PERPLEXITY_API_KEY:+SET (${#PERPLEXITY_API_KEY} chars)}${PERPLEXITY_API_KEY:-NOT SET}"`

## Overview
Collect all diagnostic information needed to troubleshoot Perplexity Sonar API issues. Generates a redacted bundle safe for sharing with support or teammates.

## Prerequisites
- `PERPLEXITY_API_KEY` environment variable
- `curl` and `tar` available
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
set -euo pipefail
# perplexity-debug-bundle.sh

BUNDLE_DIR="perplexity-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Perplexity Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info
```bash
set -euo pipefail
cat >> "$BUNDLE_DIR/summary.txt" << 'EOF'
--- Environment ---
EOF

echo "Node: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "Python: $(python3 --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -sr)" >> "$BUNDLE_DIR/summary.txt"
echo "OpenAI SDK (npm): $(npm list openai 2>/dev/null | grep openai || echo 'not found')" >> "$BUNDLE_DIR/summary.txt"
echo "OpenAI SDK (pip): $(pip show openai 2>/dev/null | grep Version || echo 'not found')" >> "$BUNDLE_DIR/summary.txt"
echo "API Key: ${PERPLEXITY_API_KEY:+SET (prefix: ${PERPLEXITY_API_KEY:0:5}...)}${PERPLEXITY_API_KEY:-NOT SET}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Test API Connectivity
```bash
set -euo pipefail
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"

# DNS resolution
echo -n "DNS: " >> "$BUNDLE_DIR/summary.txt"
dig +short api.perplexity.ai >> "$BUNDLE_DIR/summary.txt" 2>&1

# API response test
echo -n "API Health: " >> "$BUNDLE_DIR/summary.txt"
curl -s -w "HTTP %{http_code} in %{time_total}s" \
  -o "$BUNDLE_DIR/api-response.json" \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Model test
echo -n "Model (sonar): " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

echo -n "Model (sonar-pro): " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar-pro","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Collect Redacted Config
```bash
set -euo pipefail
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Configuration (redacted) ---" >> "$BUNDLE_DIR/summary.txt"

# Env vars (redacted)
env | grep -i "PERPLEXITY\|PPLX" | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null

# .env file (redacted)
if [ -f .env ]; then
  cat .env | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt"
fi
```

### Step 5: Package Bundle
```bash
set -euo pipefail
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo ""
echo "REVIEW BEFORE SHARING — verify no secrets leaked"
```

## Output
- `perplexity-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` — Environment, SDK versions, API connectivity results
  - `api-response.json` — Raw API response (verify no sensitive query data)
  - `config-redacted.txt` — Configuration with values masked

## Sensitive Data Checklist
**ALWAYS REDACT:** API keys, tokens, passwords, PII, internal URLs.
**SAFE TO INCLUDE:** Error messages, HTTP status codes, SDK versions, latency measurements, model names.

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| SDK versions | Compatibility check | Yes |
| DNS resolution | Network routing | Yes |
| HTTP status codes | API availability | Yes |
| Response latency | Performance baseline | Yes |
| Model access | Key permissions | Yes |

## Resources
- [Perplexity Community Forum](https://community.perplexity.ai)
- [Perplexity API Docs](https://docs.perplexity.ai)

## Next Steps
For rate limit issues, see `perplexity-rate-limits`.
