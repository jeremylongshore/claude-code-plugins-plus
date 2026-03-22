---
name: algolia-debug-bundle
description: |
  Collect Algolia debug evidence: index stats, API key ACLs, query logs,
  and network diagnostics for support tickets.
  Trigger: "algolia debug", "algolia support bundle", "collect algolia logs",
  "algolia diagnostic", "algolia troubleshoot".
allowed-tools: Read, Bash(curl:*), Bash(npm:*), Bash(tar:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Debug Bundle

## Overview

Collect all necessary diagnostic information for Algolia support tickets or internal troubleshooting. Uses real Algolia API endpoints to gather index stats, key permissions, and query performance data.

## Prerequisites

- `ALGOLIA_APP_ID` and `ALGOLIA_ADMIN_KEY` environment variables set
- `curl` and `jq` available
- Permission to read API key ACLs and index settings

## Instructions

### Step 1: Create the Debug Bundle Script

```bash
#!/bin/bash
# algolia-debug-bundle.sh
set -euo pipefail

APP_ID="${ALGOLIA_APP_ID:?Set ALGOLIA_APP_ID}"
API_KEY="${ALGOLIA_ADMIN_KEY:?Set ALGOLIA_ADMIN_KEY}"
BUNDLE_DIR="algolia-debug-$(date +%Y%m%d-%H%M%S)"
BASE_URL="https://${APP_ID}-dsn.algolia.net"
HEADERS=(-H "X-Algolia-Application-Id: ${APP_ID}" -H "X-Algolia-API-Key: ${API_KEY}")

mkdir -p "$BUNDLE_DIR"

echo "=== Algolia Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$BUNDLE_DIR/summary.txt"
echo "App ID: $APP_ID" | tee -a "$BUNDLE_DIR/summary.txt"

# 1. List all indices with record counts
echo "--- Indices ---" >> "$BUNDLE_DIR/summary.txt"
curl -s "${BASE_URL}/1/indexes" "${HEADERS[@]}" \
  | jq '.items[] | {name, entries, dataSize, lastBuildTimeS}' \
  > "$BUNDLE_DIR/indices.json" 2>/dev/null
echo "Indices saved" >> "$BUNDLE_DIR/summary.txt"

# 2. Check API key permissions (redacted key)
echo "--- API Key ACL ---" >> "$BUNDLE_DIR/summary.txt"
curl -s "${BASE_URL}/1/keys" "${HEADERS[@]}" \
  | jq '.keys[] | {description, acl, indexes, maxQueriesPerIPPerHour, validity}' \
  > "$BUNDLE_DIR/api-keys-acl.json" 2>/dev/null
echo "Key ACLs saved (keys redacted)" >> "$BUNDLE_DIR/summary.txt"

# 3. Get recent query logs (last 1000)
echo "--- Query Logs ---" >> "$BUNDLE_DIR/summary.txt"
curl -s "${BASE_URL}/1/logs?length=100&type=all" "${HEADERS[@]}" \
  | jq '.logs[] | {timestamp, method, url, answer_code, processing_time_ms, query_nb_hits}' \
  > "$BUNDLE_DIR/query-logs.json" 2>/dev/null
echo "Last 100 log entries saved" >> "$BUNDLE_DIR/summary.txt"

# 4. Network connectivity test
echo "--- Network Diagnostics ---" >> "$BUNDLE_DIR/summary.txt"
for host in "${APP_ID}-dsn.algolia.net" "${APP_ID}-1.algolianet.com" "${APP_ID}-2.algolianet.com"; do
  RESULT=$(curl -s -o /dev/null -w "%{http_code},%{time_total}" "https://${host}/1/indexes" "${HEADERS[@]}" 2>/dev/null || echo "FAILED")
  echo "  ${host}: ${RESULT}" >> "$BUNDLE_DIR/summary.txt"
done

# 5. SDK version
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "node: not found" >> "$BUNDLE_DIR/summary.txt"
npm list algoliasearch 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "algoliasearch: not installed" >> "$BUNDLE_DIR/summary.txt"

# 6. Algolia service status
echo "--- Algolia Status ---" >> "$BUNDLE_DIR/summary.txt"
curl -s https://status.algolia.com/api/v2/status.json \
  | jq -r '.status.description' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null

# Package (API keys already excluded from raw responses)
tar -czf "${BUNDLE_DIR}.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo ""
echo "Bundle created: ${BUNDLE_DIR}.tar.gz"
```

### Step 2: Programmatic Debug Data Collection

```typescript
import { algoliasearch } from 'algoliasearch';

async function collectDebugInfo() {
  const client = algoliasearch(
    process.env.ALGOLIA_APP_ID!,
    process.env.ALGOLIA_ADMIN_KEY!
  );

  const debug: Record<string, any> = {};

  // Index list and stats
  const { items } = await client.listIndices();
  debug.indices = items.map(i => ({
    name: i.name,
    entries: i.entries,
    dataSize: i.dataSize,
    lastBuildTimeS: i.lastBuildTimeS,
  }));

  // Per-index settings for problematic index
  const indexName = 'products'; // Target index
  try {
    debug.settings = await client.getSettings({ indexName });
  } catch (e) {
    debug.settings = `Failed: ${e}`;
  }

  // Recent logs
  const { logs } = await client.getLogs({
    indexName,
    length: 50,
    type: 'error',  // 'all' | 'query' | 'build' | 'error'
  });
  debug.recentErrors = logs.map(l => ({
    timestamp: l.timestamp,
    method: l.method,
    answerCode: l.answer_code,
    processingTimeMs: l.processing_time_ms,
  }));

  // API key used (check its ACL)
  try {
    const keyInfo = await client.getApiKey({
      key: process.env.ALGOLIA_ADMIN_KEY!,
    });
    debug.currentKeyAcl = keyInfo.acl;
  } catch (e) {
    debug.currentKeyAcl = 'Unable to read key ACL';
  }

  return debug;
}
```

## Sensitive Data Handling

**ALWAYS REDACT before sharing:**
- Full API keys (only share last 4 chars)
- User PII in query logs
- Internal hostnames or IPs

**Safe to include:**
- App ID (it's in every frontend bundle)
- Error codes and status codes
- Index names and record counts
- SDK and Node.js versions
- Processing times and latencies

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `getLogs` returns empty | Logs retention is 7 days (Grow) or 30 days (Premium) | Run sooner after incident |
| `getApiKey` 403 | Non-admin key can only read its own info | Use Admin key |
| curl returns `000` | DNS or firewall blocking | Check outbound HTTPS to `*.algolia.net` |
| No `jq` available | Not installed | `apt install jq` or parse JSON differently |

## Resources

- [Algolia Logs API](https://www.algolia.com/doc/api-reference/api-methods/get-logs/)
- [Algolia Status Page](https://status.algolia.com)
- [Algolia Support](https://support.algolia.com)

## Next Steps

For rate limit issues, see `algolia-rate-limits`.
