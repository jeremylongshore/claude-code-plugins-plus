---
name: hex-debug-bundle
description: |
  Collect Hex debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Hex problems.
  Trigger with phrases like "hex debug", "hex support bundle",
  "collect hex logs", "hex diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Debug Bundle

## Overview

Collect Hex API connectivity status, project listing, run history, data connection health, and rate limit state into a single diagnostic archive. This bundle helps troubleshoot failed notebook runs, stale data connections, scheduled run failures, and API authentication issues.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-hex-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Hex Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "HEX_API_KEY: ${HEX_API_KEY:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${HEX_API_KEY}" \
  https://app.hex.tech/api/v1/projects 2>/dev/null || echo "000")
echo "API Status: HTTP $HTTP" >> "$BUNDLE/summary.txt"

# Project listing
curl -s -H "Authorization: Bearer ${HEX_API_KEY}" \
  "https://app.hex.tech/api/v1/projects" \
  > "$BUNDLE/projects.json" 2>&1 || true

# Recent runs (across projects)
curl -s -H "Authorization: Bearer ${HEX_API_KEY}" \
  "https://app.hex.tech/api/v1/runs?limit=10" \
  > "$BUNDLE/recent-runs.json" 2>&1 || true

# Data connections and rate limit headers
curl -s -D "$BUNDLE/rate-headers.txt" -H "Authorization: Bearer ${HEX_API_KEY}" \
  "https://app.hex.tech/api/v1/connections" > "$BUNDLE/connections.json" 2>&1 || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-hex-*.tar.gz
cat debug-hex-*/summary.txt                       # Auth + connectivity
jq '.[] | {id, title, status}' debug-hex-*/projects.json   # Project inventory
jq '.[] | {id, status, started_at}' debug-hex-*/recent-runs.json  # Run history
jq '.[] | {name, type, status}' debug-hex-*/connections.json      # Data source health
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| API returns 401 | `summary.txt` shows HTTP 401 | Regenerate API token in Hex workspace Settings > API |
| Run stuck in pending | `recent-runs.json` shows pending status for >5 min | Check compute quota; cancel and re-trigger the run |
| Data connection failed | `connections.json` shows error on a source | Re-authenticate the connection; verify DB credentials haven't expired |
| Scheduled run not firing | `recent-runs.json` missing expected scheduled entries | Check project schedule in Hex UI; verify project is published |
| Rate limited (429) | `rate-headers.txt` shows Retry-After | Reduce API polling; batch project queries where possible |

## Automated Health Check

```typescript
async function checkHex(): Promise<void> {
  const key = process.env.HEX_API_KEY;
  if (!key) { console.error("[FAIL] HEX_API_KEY not set"); return; }

  const res = await fetch("https://app.hex.tech/api/v1/projects", {
    headers: { Authorization: `Bearer ${key}` },
  });
  console.log(`[${res.ok ? "OK" : "FAIL"}] API: HTTP ${res.status}`);

  if (res.ok) {
    const data = await res.json();
    console.log(`[INFO] Projects accessible: ${Array.isArray(data) ? data.length : 0}`);
  }
}
checkHex();
```

## Resources

- [Hex Status](https://status.hex.tech)

## Next Steps

See `hex-common-errors`.
