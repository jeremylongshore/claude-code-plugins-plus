---
name: juicebox-debug-bundle
description: |
  Collect Juicebox debug evidence.
  Trigger: "juicebox debug", "juicebox support ticket".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Debug Bundle

## Overview

Collect Juicebox API connectivity status, dataset health, analysis quota usage, and rate limit state into a single diagnostic archive. This bundle helps troubleshoot failed dataset uploads, stalled AI analysis runs, quota exhaustion, and API authentication problems.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-juicebox-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Juicebox Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "JUICEBOX_API_KEY: ${JUICEBOX_API_KEY:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity — health endpoint
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${JUICEBOX_API_KEY}" \
  https://api.juicebox.ai/v1/health 2>/dev/null || echo "000")
echo "API Status: HTTP $HTTP" >> "$BUNDLE/summary.txt"

# Account quota
curl -s -H "Authorization: Bearer ${JUICEBOX_API_KEY}" \
  "https://api.juicebox.ai/v1/account/quota" \
  > "$BUNDLE/quota.json" 2>&1 || true

# Datasets and recent analyses
curl -s -H "Authorization: Bearer ${JUICEBOX_API_KEY}" \
  "https://api.juicebox.ai/v1/datasets?limit=10" > "$BUNDLE/datasets.json" 2>&1 || true
curl -s -H "Authorization: Bearer ${JUICEBOX_API_KEY}" \
  "https://api.juicebox.ai/v1/analyses?limit=5" > "$BUNDLE/recent-analyses.json" 2>&1 || true

# Rate limit headers
curl -s -D "$BUNDLE/rate-headers.txt" -o /dev/null \
  -H "Authorization: Bearer ${JUICEBOX_API_KEY}" https://api.juicebox.ai/v1/health 2>/dev/null || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-juicebox-*.tar.gz
cat debug-juicebox-*/summary.txt                    # Auth + API health
jq '{used, limit, remaining}' debug-juicebox-*/quota.json        # Quota usage
jq '.[] | {id, name, row_count}' debug-juicebox-*/datasets.json  # Dataset inventory
jq '.[] | {id, status, created_at}' debug-juicebox-*/recent-analyses.json
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| API returns 401 | `summary.txt` shows HTTP 401 | Regenerate API key in Juicebox Settings > API Keys |
| Dataset upload stuck | `datasets.json` shows processing status for >10 min | Check file format (CSV/JSON required); reduce file size below 100MB |
| Analysis quota exhausted | `quota.json` shows remaining at 0 | Upgrade plan or wait for monthly quota reset |
| Analysis run failed | `recent-analyses.json` shows error status | Check dataset has required columns; verify data types match analysis type |
| Rate limited (429) | `rate-headers.txt` shows Retry-After | Implement exponential backoff; batch dataset queries |

## Automated Health Check

```typescript
async function checkJuicebox(): Promise<void> {
  const key = process.env.JUICEBOX_API_KEY;
  if (!key) { console.error("[FAIL] JUICEBOX_API_KEY not set"); return; }

  const res = await fetch("https://api.juicebox.ai/v1/health", {
    headers: { Authorization: `Bearer ${key}` },
  });
  console.log(`[${res.ok ? "OK" : "FAIL"}] API: HTTP ${res.status}`);

  if (res.ok) {
    const quota = await fetch("https://api.juicebox.ai/v1/account/quota", {
      headers: { Authorization: `Bearer ${key}` },
    });
    if (quota.ok) {
      const data = await quota.json();
      console.log(`[INFO] Quota remaining: ${data.remaining ?? "unknown"}`);
    }
  }
}
checkJuicebox();
```

## Resources

- [Juicebox Status](https://status.juicebox.ai)

## Next Steps

See `juicebox-common-errors`.
