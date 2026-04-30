---
name: lucidchart-debug-bundle
description: 'Debug Bundle for Lucidchart.

  Trigger: "lucidchart debug bundle".

  '
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart Debug Bundle

## Overview

This debug bundle collects diagnostic evidence from Lucidchart diagramming API integrations
for troubleshooting document access, shape rendering, data linking pipelines, and export
failures. It captures OAuth token validation, document listing, page metadata, data-linked
shape status, and export endpoint availability. The resulting tarball provides support
engineers the evidence to diagnose permission errors, stale data links, broken embeds,
and export timeouts without requiring direct Lucid account access.

## Prerequisites

- `curl`, `jq`, `tar` installed
- `LUCID_API_KEY` set (OAuth2 bearer token from Lucid developer portal)
- `LUCID_ACCOUNT_ID` optionally set for account-scoped queries

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-lucidchart-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Environment ===" > "$BUNDLE/environment.txt"
echo "API Key: ${LUCID_API_KEY:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Account ID: ${LUCID_ACCOUNT_ID:-NOT SET}" >> "$BUNDLE/environment.txt"
echo "Node: $(node -v 2>/dev/null || echo 'not installed')" >> "$BUNDLE/environment.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/environment.txt"

# API connectivity — user info
echo "=== API Health ===" > "$BUNDLE/api-health.txt"
curl -sf -o "$BUNDLE/api-health.txt" -w "HTTP %{http_code} in %{time_total}s\n" \
  -H "Authorization: Bearer ${LUCID_API_KEY}" \
  -H "Lucid-Api-Version: 1" \
  "https://api.lucid.co/users/me" 2>&1 || echo "UNREACHABLE" > "$BUNDLE/api-health.txt"

# Document listing (first 10)
echo "=== Documents ===" > "$BUNDLE/documents.json"
curl -sf -H "Authorization: Bearer ${LUCID_API_KEY}" \
  -H "Lucid-Api-Version: 1" \
  "https://api.lucid.co/documents?limit=10" \
  >> "$BUNDLE/documents.json" 2>&1 || echo '{"error":"FAILED"}' > "$BUNDLE/documents.json"

# Page metadata for first document
echo "=== Pages ===" > "$BUNDLE/pages.json"
DOC_ID=$(jq -r '.documents[0].documentId // empty' "$BUNDLE/documents.json" 2>/dev/null)
if [ -n "${DOC_ID:-}" ]; then
  curl -sf -H "Authorization: Bearer ${LUCID_API_KEY}" \
    -H "Lucid-Api-Version: 1" \
    "https://api.lucid.co/documents/${DOC_ID}/pages" \
    >> "$BUNDLE/pages.json" 2>&1
else
  echo '{"error":"No documents found"}' > "$BUNDLE/pages.json"
fi

# Data linking status
echo "=== Data Links ===" > "$BUNDLE/data-links.json"
if [ -n "${DOC_ID:-}" ]; then
  curl -sf -H "Authorization: Bearer ${LUCID_API_KEY}" \
    -H "Lucid-Api-Version: 1" \
    "https://api.lucid.co/documents/${DOC_ID}/dataSources" \
    >> "$BUNDLE/data-links.json" 2>&1 || echo '{"error":"DATA_LINKS_FAILED"}' > "$BUNDLE/data-links.json"
else
  echo '{"error":"Skipped — no document"}' > "$BUNDLE/data-links.json"
fi

# Recent logs
echo "=== Recent Logs ===" > "$BUNDLE/app-logs.txt"
tail -100 /var/log/lucid-integration/*.log >> "$BUNDLE/app-logs.txt" 2>/dev/null || echo "No integration logs found" >> "$BUNDLE/app-logs.txt"

# Rate limit status
echo "=== Rate Limits ===" > "$BUNDLE/rate-limits.txt"
curl -sI -H "Authorization: Bearer ${LUCID_API_KEY}" \
  -H "Lucid-Api-Version: 1" \
  "https://api.lucid.co/users/me" 2>/dev/null | grep -i "x-rate\|retry-after\|x-ratelimit" >> "$BUNDLE/rate-limits.txt" || echo "No rate limit headers" >> "$BUNDLE/rate-limits.txt"

# Package versions
echo "=== Dependencies ===" > "$BUNDLE/deps.txt"
npm ls 2>/dev/null | grep -i lucid >> "$BUNDLE/deps.txt" || echo "No Lucid npm packages found" >> "$BUNDLE/deps.txt"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-lucidchart-*.tar.gz
cat debug-lucidchart-*/environment.txt          # Verify API key is set
cat debug-lucidchart-*/api-health.txt           # Check HTTP status and latency
jq '.documents | length' debug-lucidchart-*/documents.json  # Count accessible docs
jq '.dataSources' debug-lucidchart-*/data-links.json        # Check linked data sources
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| 401 on all endpoints | `environment.txt` shows key NOT SET | Generate OAuth2 token in Lucid Developer Portal > API Tokens |
| 403 on document access | `documents.json` shows permission error | Token scope missing `lucidchart.document.content`; regenerate with correct scopes |
| Data links show stale values | `data-links.json` shows old `lastSynced` timestamp | Trigger manual data refresh via Lucidchart UI or PATCH datasource endpoint |
| Export returns 413 | App logs show payload too large | Document exceeds export size limit; split into multiple pages before exporting |
| Empty document list | `documents.json` returns empty array | Check `LUCID_ACCOUNT_ID` scope; token may be scoped to a different team folder |
| Shape IDs not resolving | `pages.json` missing expected shapes | Shapes on locked layers are excluded from API; unlock layers or use admin token |

## Automated Health Check

```typescript
async function checkLucidchartHealth(): Promise<{
  status: string;
  latencyMs: number;
  userOk: boolean;
  documentCount: number;
  dataLinkingAvailable: boolean;
}> {
  const apiKey = process.env.LUCID_API_KEY;
  const headers = {
    Authorization: `Bearer ${apiKey}`,
    "Lucid-Api-Version": "1",
  };
  const start = Date.now();

  const userRes = await fetch("https://api.lucid.co/users/me", { headers });
  const docsRes = await fetch("https://api.lucid.co/documents?limit=1", { headers });

  let documentCount = 0;
  let dataLinkingAvailable = false;
  if (docsRes.ok) {
    const data = await docsRes.json();
    documentCount = data.documents?.length ?? 0;
    if (documentCount > 0) {
      const docId = data.documents[0].documentId;
      const dlRes = await fetch(
        `https://api.lucid.co/documents/${docId}/dataSources`, { headers }
      );
      dataLinkingAvailable = dlRes.ok;
    }
  }

  return {
    status: userRes.ok ? "healthy" : "degraded",
    latencyMs: Date.now() - start,
    userOk: userRes.ok,
    documentCount,
    dataLinkingAvailable,
  };
}
```

## Resources

- [Lucid Developer Portal](https://developer.lucid.co/reference/overview)
- [Lucid Status Page](https://status.lucid.co)
- [Lucid API Changelog](https://developer.lucid.co/changelog)

## Next Steps

See `lucidchart-rate-limits`.
