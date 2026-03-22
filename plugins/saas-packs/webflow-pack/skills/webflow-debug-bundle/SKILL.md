---
name: webflow-debug-bundle
description: |
  Collect Webflow debug evidence for support tickets and troubleshooting.
  Gathers SDK version, token validation, rate limit status, site connectivity,
  CMS health, and error logs into a single diagnostic bundle.
  Trigger with phrases like "webflow debug", "webflow support bundle",
  "collect webflow logs", "webflow diagnostic", "webflow troubleshoot".
allowed-tools: Read, Bash(npm:*), Bash(npx:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Debug Bundle

## Overview

Collect comprehensive diagnostic information for Webflow integration troubleshooting.
Generates a support-ready bundle with SDK version, token status, rate limits, site
health, and redacted configuration.

## Prerequisites

- `webflow-api` SDK installed
- Access to application logs
- Permission to run diagnostic commands

## Instructions

### Step 1: Debug Bundle Script

```bash
#!/bin/bash
# webflow-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="webflow-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Webflow Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- Environment ---
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node.js: $(node --version 2>/dev/null || echo 'not found')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not found')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -s) $(uname -r)" >> "$BUNDLE_DIR/summary.txt"
echo "WEBFLOW_API_TOKEN: ${WEBFLOW_API_TOKEN:+[SET]}${WEBFLOW_API_TOKEN:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "WEBFLOW_SITE_ID: ${WEBFLOW_SITE_ID:+[SET]}${WEBFLOW_SITE_ID:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"

# --- SDK Version ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- SDK Version ---" >> "$BUNDLE_DIR/summary.txt"
npm list webflow-api 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "webflow-api: not installed" >> "$BUNDLE_DIR/summary.txt"
echo "Latest available: $(npm view webflow-api version 2>/dev/null || echo 'unknown')" >> "$BUNDLE_DIR/summary.txt"

# --- API Connectivity ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"

if [ -n "${WEBFLOW_API_TOKEN:-}" ]; then
  # Token validation (list sites)
  HTTP_CODE=$(curl -s -o "$BUNDLE_DIR/sites-response.json" -w "%{http_code}" \
    -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
    https://api.webflow.com/v2/sites 2>/dev/null)
  echo "Sites endpoint: HTTP $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"

  if [ "$HTTP_CODE" = "200" ]; then
    SITE_COUNT=$(cat "$BUNDLE_DIR/sites-response.json" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('sites',[])))" 2>/dev/null || echo "parse error")
    echo "Accessible sites: $SITE_COUNT" >> "$BUNDLE_DIR/summary.txt"
  fi

  # Rate limit headers
  echo "" >> "$BUNDLE_DIR/summary.txt"
  echo "--- Rate Limit Status ---" >> "$BUNDLE_DIR/summary.txt"
  curl -s -I -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
    https://api.webflow.com/v2/sites 2>/dev/null | \
    grep -i "x-ratelimit\|retry-after\|content-type" >> "$BUNDLE_DIR/summary.txt" || echo "Could not read headers" >> "$BUNDLE_DIR/summary.txt"
else
  echo "Skipped (no WEBFLOW_API_TOKEN set)" >> "$BUNDLE_DIR/summary.txt"
fi

# --- Webflow Platform Status ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Webflow Platform Status ---" >> "$BUNDLE_DIR/summary.txt"
curl -s https://status.webflow.com/api/v2/status.json 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Status: {d['status']['description']}\")" 2>/dev/null \
  >> "$BUNDLE_DIR/summary.txt" || echo "Could not reach status page" >> "$BUNDLE_DIR/summary.txt"

# --- Configuration (redacted) ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
for envfile in .env .env.local .env.production; do
  if [ -f "$envfile" ]; then
    echo "[$envfile]" >> "$BUNDLE_DIR/config-redacted.txt"
    sed 's/=.*/=***REDACTED***/' "$envfile" >> "$BUNDLE_DIR/config-redacted.txt"
    echo "" >> "$BUNDLE_DIR/config-redacted.txt"
  fi
done
[ -f "$BUNDLE_DIR/config-redacted.txt" ] && echo "See config-redacted.txt" >> "$BUNDLE_DIR/summary.txt" || echo "No .env files found" >> "$BUNDLE_DIR/summary.txt"

# --- Recent Error Logs ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Recent Errors ---" >> "$BUNDLE_DIR/summary.txt"
if [ -d "logs" ]; then
  grep -ri "webflow\|429\|401\|403\|500" logs/ 2>/dev/null | tail -50 >> "$BUNDLE_DIR/errors.txt" || true
  echo "See errors.txt" >> "$BUNDLE_DIR/summary.txt"
else
  echo "No logs/ directory found" >> "$BUNDLE_DIR/summary.txt"
fi

# --- Package Bundle ---
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review for sensitive data before sharing."
```

### Step 2: TypeScript Diagnostic Script

For deeper programmatic diagnostics:

```typescript
// webflow-diagnostics.ts
import { WebflowClient } from "webflow-api";

interface DiagnosticReport {
  timestamp: string;
  sdk: { version: string; installed: boolean };
  auth: { valid: boolean; error?: string };
  sites: Array<{ id: string; name: string; lastPublished: string | null }>;
  collections: Array<{ siteId: string; id: string; name: string; itemCount: number }>;
  rateLimits: { note: string };
  platformStatus: string;
}

async function runDiagnostics(): Promise<DiagnosticReport> {
  const report: DiagnosticReport = {
    timestamp: new Date().toISOString(),
    sdk: { version: "unknown", installed: false },
    auth: { valid: false },
    sites: [],
    collections: [],
    rateLimits: { note: "Check response headers for X-RateLimit-Remaining" },
    platformStatus: "unknown",
  };

  // 1. SDK Version
  try {
    const pkg = await import("webflow-api/package.json", { assert: { type: "json" } });
    report.sdk = { version: pkg.default.version, installed: true };
  } catch {
    report.sdk = { version: "unknown", installed: true };
  }

  // 2. Auth Check
  const webflow = new WebflowClient({
    accessToken: process.env.WEBFLOW_API_TOKEN!,
  });

  try {
    const { sites } = await webflow.sites.list();
    report.auth = { valid: true };
    report.sites = (sites || []).map(s => ({
      id: s.id!,
      name: s.displayName!,
      lastPublished: s.lastPublished || null,
    }));

    // 3. Collections for each site
    for (const site of sites || []) {
      const { collections } = await webflow.collections.list(site.id!);
      for (const col of collections || []) {
        report.collections.push({
          siteId: site.id!,
          id: col.id!,
          name: col.displayName!,
          itemCount: col.itemCount || 0,
        });
      }
    }
  } catch (err: any) {
    report.auth = { valid: false, error: `${err.statusCode}: ${err.message}` };
  }

  // 4. Platform Status
  try {
    const res = await fetch("https://status.webflow.com/api/v2/status.json");
    const data = await res.json();
    report.platformStatus = data.status?.description || "unknown";
  } catch {
    report.platformStatus = "unreachable";
  }

  return report;
}

runDiagnostics().then(report => {
  console.log(JSON.stringify(report, null, 2));
}).catch(console.error);
```

### Step 3: Run Diagnostics

```bash
# Bash bundle
chmod +x webflow-debug-bundle.sh
./webflow-debug-bundle.sh

# TypeScript diagnostics
npx tsx webflow-diagnostics.ts
```

## Sensitive Data Handling

**ALWAYS REDACT before sharing:**
- API tokens and OAuth secrets
- Customer emails and PII from form submissions
- Webhook secrets

**Safe to include:**
- HTTP status codes and error messages
- SDK/Node.js versions
- Site IDs and collection IDs (not sensitive)
- Rate limit headers
- Platform status

## Output

- `webflow-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` — Environment, SDK version, connectivity, rate limits
  - `sites-response.json` — API response (if token valid)
  - `config-redacted.txt` — Environment files with values masked
  - `errors.txt` — Recent error logs

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `curl: command not found` | curl not installed | `apt install curl` or use TypeScript diagnostics |
| Sites endpoint 401 | Token expired | Generate new token |
| Status page unreachable | Network issue | Check DNS/firewall |
| Empty error logs | No logs/ directory | Check app logging configuration |

## Resources

- [Webflow Status Page](https://status.webflow.com)
- [Webflow Support](https://support.webflow.com)
- [API Reference](https://developers.webflow.com/data/reference/rest-introduction)

## Next Steps

For rate limit issues, see `webflow-rate-limits`.
