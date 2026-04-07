---
name: glean-debug-bundle
description: |
  Collect Glean diagnostic information for support including datasource config, indexing status, and search quality metrics.
  Trigger: "glean debug", "glean support", "glean diagnostic".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Debug Bundle

## Overview

This debug bundle collects diagnostic evidence from Glean enterprise search integrations
for troubleshooting datasource configuration, document indexing pipelines, and search
quality issues. It captures indexing token validation, datasource configuration state,
crawl status, search query test results, and permission model health. The resulting
tarball provides the evidence needed to diagnose connector failures, stale index problems,
missing document results, and permission-based search gaps without requiring admin console access.

## Prerequisites

- `curl`, `jq`, `tar` installed
- `GLEAN_DOMAIN` set to your Glean instance (e.g., `your-company-be.glean.com`)
- `GLEAN_INDEXING_TOKEN` for datasource/indexing endpoints
- `GLEAN_CLIENT_TOKEN` for search API endpoints

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-glean-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Environment ===" > "$BUNDLE/environment.txt"
echo "Glean Domain: ${GLEAN_DOMAIN:-NOT SET}" >> "$BUNDLE/environment.txt"
echo "Indexing Token: ${GLEAN_INDEXING_TOKEN:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Client Token: ${GLEAN_CLIENT_TOKEN:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Node: $(node -v 2>/dev/null || echo 'not installed')" >> "$BUNDLE/environment.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/environment.txt"

# Datasource configuration
echo "=== Datasource Config ===" > "$BUNDLE/datasource-config.json"
curl -sf -X POST "https://${GLEAN_DOMAIN}/api/index/v1/getdatasourceconfig" \
  -H "Authorization: Bearer ${GLEAN_INDEXING_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"datasource\":\"${GLEAN_DATASOURCE:-custom}\"}" \
  >> "$BUNDLE/datasource-config.json" 2>&1 || echo '{"error":"UNREACHABLE"}' > "$BUNDLE/datasource-config.json"

# Indexing status check
echo "=== Indexing Status ===" > "$BUNDLE/indexing-status.json"
curl -sf -X POST "https://${GLEAN_DOMAIN}/api/index/v1/getstatus" \
  -H "Authorization: Bearer ${GLEAN_INDEXING_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"datasource\":\"${GLEAN_DATASOURCE:-custom}\"}" \
  >> "$BUNDLE/indexing-status.json" 2>&1 || echo '{"error":"FAILED"}' > "$BUNDLE/indexing-status.json"

# Search quality test
echo "=== Search Test ===" > "$BUNDLE/search-test.json"
curl -sf -X POST "https://${GLEAN_DOMAIN}/api/client/v1/search" \
  -H "Authorization: Bearer ${GLEAN_CLIENT_TOKEN}" \
  -H "X-Glean-Auth-Type: BEARER" \
  -H "Content-Type: application/json" \
  -d '{"query":"test","pageSize":3}' \
  >> "$BUNDLE/search-test.json" 2>&1 || echo '{"error":"SEARCH_FAILED"}' > "$BUNDLE/search-test.json"

# Recent indexing logs
echo "=== Recent Logs ===" > "$BUNDLE/app-logs.txt"
tail -100 /var/log/glean-connector/*.log >> "$BUNDLE/app-logs.txt" 2>/dev/null || echo "No connector logs found" >> "$BUNDLE/app-logs.txt"

# Rate limit status
echo "=== Rate Limits ===" > "$BUNDLE/rate-limits.txt"
curl -sI -X POST "https://${GLEAN_DOMAIN}/api/index/v1/getdatasourceconfig" \
  -H "Authorization: Bearer ${GLEAN_INDEXING_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null | grep -i "x-rate\|retry-after\|x-ratelimit" >> "$BUNDLE/rate-limits.txt" || echo "No rate limit headers" >> "$BUNDLE/rate-limits.txt"

# Package versions
echo "=== Dependencies ===" > "$BUNDLE/deps.txt"
npm ls 2>/dev/null | grep -i glean >> "$BUNDLE/deps.txt" || echo "No Glean npm packages found" >> "$BUNDLE/deps.txt"
pip list 2>/dev/null | grep -i glean >> "$BUNDLE/deps.txt" || echo "No Glean pip packages found" >> "$BUNDLE/deps.txt"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-glean-*.tar.gz
cat debug-glean-*/environment.txt               # Verify tokens are set
jq '.objectType' debug-glean-*/datasource-config.json  # Check datasource type
jq '.status' debug-glean-*/indexing-status.json  # Verify crawl state
jq '.results | length' debug-glean-*/search-test.json  # Count search results
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| 401 on indexing API | `environment.txt` shows token NOT SET | Generate new indexing token in Glean admin under Datasources > API |
| Datasource config returns empty | `datasource-config.json` has no fields | Set `GLEAN_DATASOURCE` env var to match your registered datasource name |
| Search returns 0 results | `search-test.json` results array is empty | Check `indexing-status.json` for crawl completion; new datasources take 15-60 min to index |
| 403 on search endpoint | `search-test.json` shows permission error | Client token needs search scope; regenerate with correct permissions in admin |
| Stale documents in results | `indexing-status.json` shows old `lastCrawlTime` | Trigger a re-crawl via admin UI or POST to `/api/index/v1/bulkindexdocuments` |
| Rate limited during bulk indexing | `rate-limits.txt` shows retry-after header | Batch documents in groups of 100; respect 10 req/sec indexing limit |

## Automated Health Check

```typescript
async function checkGleanHealth(): Promise<{
  status: string;
  latencyMs: number;
  indexing: boolean;
  searchWorking: boolean;
}> {
  const domain = process.env.GLEAN_DOMAIN;
  const indexToken = process.env.GLEAN_INDEXING_TOKEN;
  const clientToken = process.env.GLEAN_CLIENT_TOKEN;
  const start = Date.now();

  const indexRes = await fetch(`https://${domain}/api/index/v1/getdatasourceconfig`, {
    method: "POST",
    headers: { Authorization: `Bearer ${indexToken}`, "Content-Type": "application/json" },
    body: JSON.stringify({ datasource: process.env.GLEAN_DATASOURCE || "custom" }),
  });

  const searchRes = await fetch(`https://${domain}/api/client/v1/search`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${clientToken}`,
      "X-Glean-Auth-Type": "BEARER",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: "test", pageSize: 1 }),
  });

  return {
    status: indexRes.ok && searchRes.ok ? "healthy" : "degraded",
    latencyMs: Date.now() - start,
    indexing: indexRes.ok,
    searchWorking: searchRes.ok,
  };
}
```

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Glean Status Page](https://status.glean.com)
- [Glean Indexing API Reference](https://developers.glean.com/indexing-api/)

## Next Steps

See `glean-rate-limits`.
