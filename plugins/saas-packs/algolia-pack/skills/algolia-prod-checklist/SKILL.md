---
name: algolia-prod-checklist
description: |
  Execute Algolia production readiness checklist: index settings, key security,
  replica configuration, monitoring, and rollback procedures.
  Trigger: "algolia production", "deploy algolia", "algolia go-live",
  "algolia launch checklist", "algolia production ready".
allowed-tools: Read, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Production Checklist

## Overview

Complete checklist for deploying Algolia search to production. Covers index configuration, API key security, replica setup, monitoring, and rollback procedures.

## Pre-Production Checklist

### Index Configuration

- [ ] `searchableAttributes` ordered by priority (first = highest)
- [ ] `attributesForFaceting` set for all filterable attributes
- [ ] `customRanking` configured (business metrics as tie-breakers)
- [ ] `unretrievableAttributes` set for fields that should be searchable but not returned
- [ ] `attributesToRetrieve` limited to fields needed by the UI
- [ ] `typoTolerance` tested (default: enabled, min 4 chars for 1 typo, min 8 for 2)
- [ ] `removeStopWords` configured for your language(s)
- [ ] `distinct` set if deduplication needed (e.g., one result per product group)

```typescript
// Verify production settings
const settings = await client.getSettings({ indexName: 'products' });
console.log(JSON.stringify(settings, null, 2));
```

### API Key Security

- [ ] Admin key in backend env vars only (never frontend)
- [ ] Search-Only key used in frontend with `referers` restriction
- [ ] `maxQueriesPerIPPerHour` set on all public keys
- [ ] `maxHitsPerQuery` limited on search keys
- [ ] Secured API keys used for multi-tenant data isolation
- [ ] Keys restricted to specific `indexes` where possible

### Replicas (Alternate Sorting)

```typescript
// Replicas give users alternate sort orders
await client.setSettings({
  indexName: 'products',
  indexSettings: {
    // Standard replicas: share parent's data, use their own relevance settings
    replicas: [
      'products_price_asc',    // Sort by price ascending
      'products_price_desc',   // Sort by price descending
      'products_newest',       // Sort by newest first
    ],
  },
});

// Configure each replica's ranking
await client.setSettings({
  indexName: 'products_price_asc',
  indexSettings: {
    ranking: [
      'asc(price)',    // Primary: price ascending
      'typo', 'geo', 'words', 'filters', 'proximity', 'attribute', 'exact', 'custom',
    ],
  },
});
```

### Monitoring

- [ ] Health check endpoint tests Algolia connectivity
- [ ] Alert on error rate > 1% over 5 minutes
- [ ] Alert on P95 latency > 200ms (Algolia is typically < 50ms)
- [ ] Dashboard shows queries/sec, latency, error rate
- [ ] [status.algolia.com](https://status.algolia.com) RSS/webhook configured

```typescript
// Health check endpoint
async function algoliaHealthCheck() {
  const start = Date.now();
  try {
    const { items } = await client.listIndices();
    const latencyMs = Date.now() - start;
    return {
      status: 'healthy',
      latencyMs,
      indexCount: items.length,
      totalRecords: items.reduce((sum, i) => sum + (i.entries || 0), 0),
    };
  } catch (error) {
    return { status: 'unhealthy', error: String(error), latencyMs: Date.now() - start };
  }
}
```

### Graceful Degradation

```typescript
// If Algolia is down, fall back to database search
async function searchWithFallback(query: string) {
  try {
    const { hits } = await client.searchSingleIndex({
      indexName: 'products',
      searchParams: { query, hitsPerPage: 20 },
    });
    return { source: 'algolia', results: hits };
  } catch (error) {
    console.error('Algolia unavailable, falling back to DB', error);
    const dbResults = await db.products.find({
      name: { $regex: query, $options: 'i' },
    }).limit(20);
    return { source: 'database', results: dbResults };
  }
}
```

### Pre-Deploy Verification Script

```bash
#!/bin/bash
echo "=== Algolia Production Pre-Flight ==="

# 1. Verify connectivity
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes" \
  -H "X-Algolia-Application-Id: ${ALGOLIA_APP_ID}" \
  -H "X-Algolia-API-Key: ${ALGOLIA_ADMIN_KEY}")
echo "API connectivity: HTTP $HTTP_CODE"
[ "$HTTP_CODE" != "200" ] && echo "FAIL: Cannot reach Algolia" && exit 1

# 2. Check Algolia service status
STATUS=$(curl -s https://status.algolia.com/api/v2/status.json | jq -r '.status.indicator')
echo "Algolia status: $STATUS"
[ "$STATUS" != "none" ] && echo "WARNING: Algolia reporting issues"

# 3. Verify index has data
RECORDS=$(curl -s "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/products" \
  -H "X-Algolia-Application-Id: ${ALGOLIA_APP_ID}" \
  -H "X-Algolia-API-Key: ${ALGOLIA_ADMIN_KEY}" | jq '.entries')
echo "Products index: $RECORDS records"
[ "$RECORDS" -lt 1 ] && echo "FAIL: Index is empty" && exit 1

echo ""
echo "All checks passed. Ready to deploy."
```

## Error Handling

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Search errors | 5xx or 403 errors > 5/min | P1 | Check API keys, Algolia status |
| High latency | P95 > 200ms for 5+ min | P2 | Check index size, network |
| Rate limited | 429 errors > 10/min | P2 | Reduce request rate, check key limits |
| Index stale | Last updated > 1 hour ago | P3 | Check sync pipeline |

## Resources

- [Algolia Dashboard](https://dashboard.algolia.com)
- [Algolia Status](https://status.algolia.com)
- [Index Settings Reference](https://www.algolia.com/doc/api-reference/settings-api-parameters/)

## Next Steps

For version upgrades, see `algolia-upgrade-migration`.
