---
name: groq-debug-bundle
description: |
  Collect Groq debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Groq problems.
  Trigger with phrases like "groq debug", "groq support bundle",
  "collect groq logs", "groq diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, debugging]

---
# Groq Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`npm list groq-sdk 2>/dev/null | grep groq-sdk || echo 'groq-sdk not installed'`

## Overview
Collect all diagnostic information needed to resolve Groq API issues. Produces a redacted support bundle with environment info, SDK version, connectivity test results, and rate limit status.

## Prerequisites
- `GROQ_API_KEY` set in environment
- `curl` and `jq` available
- Access to application logs

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
set -euo pipefail

BUNDLE_DIR="groq-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"
echo "Collecting Groq debug bundle..."

# === Environment ===
cat > "$BUNDLE_DIR/environment.txt" <<ENVEOF
=== Groq Debug Bundle ===
Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Hostname: $(hostname)
OS: $(uname -sr)
Node.js: $(node --version 2>/dev/null || echo 'not installed')
Python: $(python3 --version 2>/dev/null || echo 'not installed')
npm groq-sdk: $(npm list groq-sdk 2>/dev/null | grep groq-sdk || echo 'not installed')
pip groq: $(pip show groq 2>/dev/null | grep Version || echo 'not installed')
GROQ_API_KEY: ${GROQ_API_KEY:+SET (${#GROQ_API_KEY} chars, prefix: ${GROQ_API_KEY:0:4}...)}${GROQ_API_KEY:-NOT SET}
ENVEOF
```

### Step 2: API Connectivity Test
```bash
# Test API endpoint and capture headers
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/connectivity.txt"

# Models endpoint (lightweight, confirms auth)
curl -s -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  | jq '.data | length' >> "$BUNDLE_DIR/connectivity.txt" 2>&1

echo "Models available: $(curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | jq -r '.data[].id' | wc -l)" \
  >> "$BUNDLE_DIR/connectivity.txt"
```

### Step 3: Rate Limit Status
```bash
# Make a minimal request and capture rate limit headers
echo "--- Rate Limit Status ---" >> "$BUNDLE_DIR/rate-limits.txt"

curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -iE "^(x-ratelimit|retry-after|x-request-id)" \
  >> "$BUNDLE_DIR/rate-limits.txt"
```

### Step 4: Latency Benchmark
```bash
# Quick latency test across models
echo "--- Latency Benchmark ---" >> "$BUNDLE_DIR/latency.txt"

for model in "llama-3.1-8b-instant" "llama-3.3-70b-versatile"; do
  latency=$(curl -s -w "%{time_total}" -o /dev/null \
    https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $GROQ_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":5}" \
    2>/dev/null)
  echo "$model: ${latency}s" >> "$BUNDLE_DIR/latency.txt"
done
```

### Step 5: Application Log Extraction
```bash
# Capture recent Groq-related errors from application logs (redacted)
echo "--- Application Logs (redacted) ---" >> "$BUNDLE_DIR/app-logs.txt"

# Node.js logs
if [ -d "logs" ]; then
  grep -i "groq\|rate.limit\|429\|api.error" logs/*.log 2>/dev/null | \
    tail -50 | \
    sed 's/gsk_[a-zA-Z0-9]*/gsk_***REDACTED***/g' \
    >> "$BUNDLE_DIR/app-logs.txt"
fi

# Config (redacted)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/config-redacted.txt"
if [ -f ".env" ]; then
  sed 's/=.*/=***REDACTED***/' .env >> "$BUNDLE_DIR/config-redacted.txt"
fi
```

### Step 6: Package Bundle
```bash
# Create tarball
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review before sharing -- ensure no secrets are included."
```

## Programmatic Debug Check (TypeScript)
```typescript
import Groq from "groq-sdk";

async function groqDiagnostic() {
  const groq = new Groq();
  const report: Record<string, any> = {};

  // Test auth
  try {
    const models = await groq.models.list();
    report.auth = "OK";
    report.modelsAvailable = models.data.map((m) => m.id);
  } catch (err) {
    report.auth = `FAILED: ${(err as Error).message}`;
    return report;
  }

  // Test completion
  try {
    const start = performance.now();
    const completion = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "Reply: OK" }],
      max_tokens: 5,
      temperature: 0,
    });
    report.completion = "OK";
    report.latencyMs = Math.round(performance.now() - start);
    report.model = completion.model;
    report.usage = completion.usage;
  } catch (err: any) {
    report.completion = `FAILED: ${err.status} ${err.message}`;
  }

  return report;
}

groqDiagnostic().then((r) => console.log(JSON.stringify(r, null, 2)));
```

## Bundle Contents
| File | Purpose | Sensitive? |
|------|---------|-----------|
| `environment.txt` | Node/Python versions, SDK version | Key prefix only |
| `connectivity.txt` | API reachability, model count | No |
| `rate-limits.txt` | Current rate limit headers | No |
| `latency.txt` | Response times per model | No |
| `app-logs.txt` | Recent error logs (redacted) | Redacted |
| `config-redacted.txt` | Config keys only (values masked) | Redacted |

## ALWAYS Redact Before Sharing
- API keys (anything starting with `gsk_`)
- Bearer tokens
- PII (emails, names, IDs)
- Internal hostnames and IPs

## Resources
- [Groq Error Codes](https://console.groq.com/docs/errors)
- [Groq Status Page](https://status.groq.com)

## Next Steps
For rate limit issues, see `groq-rate-limits`.
