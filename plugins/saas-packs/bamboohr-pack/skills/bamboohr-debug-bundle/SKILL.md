---
name: bamboohr-debug-bundle
description: |
  Collect BambooHR debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for BambooHR API problems.
  Trigger with phrases like "bamboohr debug", "bamboohr support bundle",
  "collect bamboohr logs", "bamboohr diagnostic", "bamboohr troubleshoot".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, debugging]
compatible-with: claude-code
---

# BambooHR Debug Bundle

## Overview

Collect all diagnostic information for BambooHR API troubleshooting or support tickets. Captures connectivity tests, API response details, environment info, and redacted configuration.

## Prerequisites

- BambooHR environment variables set
- `curl` available for API tests
- Permission to collect environment info

## Instructions

### Step 1: Complete Debug Bundle Script

```bash
#!/bin/bash
# bamboohr-debug-bundle.sh — Run this, then send the .tar.gz to support

set -euo pipefail

BUNDLE_DIR="bamboohr-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

DOMAIN="${BAMBOOHR_COMPANY_DOMAIN:?Set BAMBOOHR_COMPANY_DOMAIN}"
API_KEY="${BAMBOOHR_API_KEY:?Set BAMBOOHR_API_KEY}"
BASE="https://api.bamboohr.com/api/gateway.php/${DOMAIN}/v1"

exec > >(tee "$BUNDLE_DIR/summary.txt") 2>&1

echo "=== BambooHR Debug Bundle ==="
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Company Domain: ${DOMAIN}"
echo "API Key: ${API_KEY:0:4}****${API_KEY: -4}"
echo ""

# ── Environment ──────────────────────────────────────
echo "--- Runtime Environment ---"
echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')"
echo "Python: $(python3 --version 2>/dev/null || echo 'not installed')"
echo "curl: $(curl --version 2>/dev/null | head -1)"
echo "OS: $(uname -a)"
echo ""

# ── API Connectivity Test ────────────────────────────
echo "--- API Connectivity ---"
echo -n "Directory endpoint: "
curl -s -o "$BUNDLE_DIR/directory-response.json" \
  -w "HTTP %{http_code} | %{time_total}s | %{size_download} bytes\n" \
  -u "${API_KEY}:x" \
  -H "Accept: application/json" \
  "${BASE}/employees/directory"

echo -n "Employee endpoint: "
curl -s -o "$BUNDLE_DIR/employee-response.json" \
  -w "HTTP %{http_code} | %{time_total}s | %{size_download} bytes\n" \
  -u "${API_KEY}:x" \
  -H "Accept: application/json" \
  "${BASE}/employees/0/?fields=firstName"

echo -n "Time off types: "
curl -s -o "$BUNDLE_DIR/timeoff-types-response.json" \
  -w "HTTP %{http_code} | %{time_total}s\n" \
  -u "${API_KEY}:x" \
  -H "Accept: application/json" \
  "${BASE}/meta/time_off/types"

echo ""

# ── Response Headers (verbose for one endpoint) ─────
echo "--- Response Headers (directory) ---"
curl -s -I -u "${API_KEY}:x" \
  -H "Accept: application/json" \
  "${BASE}/employees/directory" \
  | grep -iE "^(x-bamboohr|content-type|retry-after|date|server)" \
  > "$BUNDLE_DIR/response-headers.txt"
cat "$BUNDLE_DIR/response-headers.txt"
echo ""

# ── Project Dependencies ─────────────────────────────
echo "--- Project Dependencies ---"
if [ -f package.json ]; then
  node -e "
    const pkg = require('./package.json');
    const deps = {...pkg.dependencies, ...pkg.devDependencies};
    const bamboo = Object.entries(deps).filter(([k]) => k.includes('bamboo'));
    const http = Object.entries(deps).filter(([k]) => ['axios','node-fetch','got','ky'].includes(k));
    console.log('BambooHR packages:', bamboo.length ? bamboo.map(([k,v]) => k+'@'+v).join(', ') : 'none (using fetch)');
    console.log('HTTP clients:', http.length ? http.map(([k,v]) => k+'@'+v).join(', ') : 'native fetch');
  " 2>/dev/null || echo "Could not parse package.json"
fi
echo ""

# ── Configuration (redacted) ─────────────────────────
echo "--- Configuration (redacted) ---"
if [ -f .env ]; then
  sed 's/=.*/=***REDACTED***/' .env > "$BUNDLE_DIR/config-redacted.txt"
  echo "Found .env with $(wc -l < .env) lines"
else
  echo "No .env file found"
fi

# ── Redact sensitive data from API responses ─────────
for f in "$BUNDLE_DIR"/*-response.json; do
  if [ -f "$f" ]; then
    # Remove email addresses and phone numbers from responses
    sed -i 's/[a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]*/***@redacted/g' "$f"
    sed -i 's/[0-9]\{3\}[-. ][0-9]\{3\}[-. ][0-9]\{4\}/***-***-****/g' "$f"
  fi
done

echo ""
echo "--- Bundle Complete ---"

# ── Package ──────────────────────────────────────────
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Created: $BUNDLE_DIR.tar.gz ($(du -h "$BUNDLE_DIR.tar.gz" | cut -f1))"
echo ""
echo "BEFORE SHARING: Review $BUNDLE_DIR/ for any remaining PII"
```

### Step 2: Programmatic Debug Info (TypeScript)

```typescript
import { BambooHRClient, BambooHRApiError } from './bamboohr/client';

interface DiagnosticResult {
  timestamp: string;
  environment: Record<string, string>;
  connectivity: {
    endpoint: string;
    status: number;
    latencyMs: number;
    error?: string;
  }[];
}

async function collectDiagnostics(client: BambooHRClient): Promise<DiagnosticResult> {
  const endpoints = [
    '/employees/directory',
    '/meta/time_off/types',
    '/meta/lists/',
  ];

  const connectivity = await Promise.all(
    endpoints.map(async (endpoint) => {
      const start = Date.now();
      try {
        await client.request('GET', endpoint);
        return { endpoint, status: 200, latencyMs: Date.now() - start };
      } catch (err) {
        const status = err instanceof BambooHRApiError ? err.status : 0;
        return {
          endpoint, status, latencyMs: Date.now() - start,
          error: (err as Error).message,
        };
      }
    }),
  );

  return {
    timestamp: new Date().toISOString(),
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      companyDomain: process.env.BAMBOOHR_COMPANY_DOMAIN || 'NOT SET',
      apiKeySet: process.env.BAMBOOHR_API_KEY ? 'yes' : 'NO',
    },
    connectivity,
  };
}
```

## Output

- `bamboohr-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` — Environment, connectivity, and dependency info
  - `directory-response.json` — Redacted API response sample
  - `response-headers.txt` — BambooHR-specific headers
  - `config-redacted.txt` — Environment config with secrets removed

## Sensitive Data Handling

**Always redact before sharing:**
- API keys and tokens
- Employee emails, phone numbers, SSNs
- Home addresses and personal info
- Salary and compensation data

**Safe to include:**
- HTTP status codes and error messages
- Response latencies and sizes
- `X-BambooHR-Error-Message` header values
- SDK/runtime versions

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| curl not found | Not installed | Install curl or use Node.js version |
| Permission denied | Script not executable | `chmod +x bamboohr-debug-bundle.sh` |
| Empty response files | Auth failure | Check API key before running |
| Large bundle size | Too many response files | Reduce to key endpoints only |

## Resources

- [BambooHR Support](https://www.bamboohr.com/contact-support/)
- [BambooHR Status Page](https://status.bamboohr.com)

## Next Steps

For rate limit issues, see `bamboohr-rate-limits`.
