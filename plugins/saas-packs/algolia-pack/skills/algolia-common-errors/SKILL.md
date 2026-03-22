---
name: algolia-common-errors
description: |
  Diagnose and fix the top Algolia API errors: 400, 403, 404, 429, ApiError,
  RetryError, and indexing failures.
  Trigger: "algolia error", "fix algolia", "algolia not working",
  "debug algolia", "algolia 429", "algolia 403".
allowed-tools: Read, Grep, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Common Errors

## Overview

Quick reference for the most common Algolia errors, their root causes, and fixes. All examples use `algoliasearch` v5 client error types.

## Error Reference

### 1. Invalid Application-ID or API key (403)

```
ApiError: Invalid Application-ID or API key
```

**Cause:** App ID or API key is wrong, expired, or deleted.

**Fix:**
```bash
# Verify your env vars are set
echo "APP_ID: $ALGOLIA_APP_ID"
echo "KEY set: ${ALGOLIA_ADMIN_KEY:+yes}"

# Test with curl
curl -s "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes" \
  -H "X-Algolia-Application-Id: ${ALGOLIA_APP_ID}" \
  -H "X-Algolia-API-Key: ${ALGOLIA_ADMIN_KEY}" | head -c 200
```

Get fresh keys: dashboard.algolia.com > Settings > API Keys.

---

### 2. Method not allowed with this API key (403)

```
ApiError: Method not allowed with this API key
```

**Cause:** Using a Search-Only key for a write operation (saveObjects, setSettings, etc.).

**Fix:** Use the Admin API key for write operations. Search-Only keys only permit `search` ACL.

```typescript
// Wrong: search-only key for indexing
const client = algoliasearch(appId, searchOnlyKey);
await client.saveObjects({ ... }); // 403

// Right: admin key for indexing
const client = algoliasearch(appId, adminKey);
await client.saveObjects({ ... }); // Works
```

---

### 3. Index does not exist (404)

```
ApiError: Index products_staging does not exist
```

**Cause:** Searching an index that hasn't been created yet. Algolia creates indices lazily on first `saveObjects`.

**Fix:** Index some data first, or check the index name for typos:
```bash
# List all indices in your app
curl -s "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes" \
  -H "X-Algolia-Application-Id: ${ALGOLIA_APP_ID}" \
  -H "X-Algolia-API-Key: ${ALGOLIA_ADMIN_KEY}" | jq '.items[].name'
```

---

### 4. Rate limit exceeded (429)

```
ApiError: Too Many Requests
```

**Cause:** API key's `maxQueriesPerIPPerHour` exceeded, or server-side indexing rate limit hit.

**Fix:**
```typescript
// Algolia's built-in retry handles transient 429s.
// For sustained rate limits:

// 1. Reduce batch frequency
const BATCH_SIZE = 500;  // Down from 1000

// 2. Add delay between batches
for (const batch of chunks) {
  await client.saveObjects({ indexName: 'products', objects: batch });
  await new Promise(r => setTimeout(r, 200)); // 200ms pause between batches
}

// 3. Check/increase key rate limit
// Dashboard > Settings > API Keys > Edit key > Rate limit
```

---

### 5. Record is too big (400)

```
ApiError: Record at the position 0 is too big size=15234 bytes. Contact us if you need a higher quota.
```

**Cause:** Single record exceeds 10KB (free/Build plan) or 100KB (paid plans).

**Fix:**
```typescript
// Strip unnecessary fields before indexing
function trimForAlgolia(record: any) {
  const { full_html, raw_content, internal_notes, ...searchable } = record;
  return searchable;
}

// Or split long text into chunks
function truncateDescription(record: any, maxChars = 5000) {
  return {
    ...record,
    description: record.description?.substring(0, maxChars),
  };
}
```

---

### 6. Attribute not valid for filtering (400)

```
ApiError: Attribute "price" is not in attributesForFaceting
```

**Cause:** Using `filters` or `facetFilters` on an attribute not configured for faceting.

**Fix:**
```typescript
await client.setSettings({
  indexName: 'products',
  indexSettings: {
    attributesForFaceting: ['category', 'brand', 'filterOnly(price)', 'filterOnly(in_stock)'],
  },
});
// Wait for settings to propagate
```

---

### 7. RetryError: Unreachable hosts

```
RetryError: Unreachable hosts - yourass might not be connected to the internet
```

**Cause:** Network/DNS issue. Can't reach `*.algolia.net` or `*.algolianet.com`.

**Fix:**
```bash
# Test DNS resolution
nslookup ${ALGOLIA_APP_ID}-dsn.algolia.net

# Test HTTPS connectivity
curl -v "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes" 2>&1 | grep "Connected to"

# Check firewall — Algolia needs outbound HTTPS (443) to:
# ${APP_ID}.algolia.net
# ${APP_ID}-1.algolianet.com
# ${APP_ID}-2.algolianet.com
# ${APP_ID}-3.algolianet.com
```

---

### 8. Invalid filter syntax (400)

```
ApiError: Invalid syntax for filter: 'price > AND < 100'
```

**Fix:** Algolia filter syntax reference:
```
# Correct syntax
price > 50 AND price < 100        # Numeric range
category:shoes                     # String equality
NOT category:sandals               # Negation
(brand:Nike OR brand:Adidas)       # Grouped OR
in_stock = true                    # Boolean (stored as 0/1)
_tags:featured                     # Tag filter
```

## Quick Diagnostic Script

```bash
#!/bin/bash
echo "=== Algolia Diagnostics ==="
echo "App ID: ${ALGOLIA_APP_ID:-NOT SET}"
echo "Admin key: ${ALGOLIA_ADMIN_KEY:+SET (${#ALGOLIA_ADMIN_KEY} chars)}"
echo ""

echo "=== Connectivity ==="
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
  "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes" \
  -H "X-Algolia-Application-Id: ${ALGOLIA_APP_ID}" \
  -H "X-Algolia-API-Key: ${ALGOLIA_ADMIN_KEY}"
echo ""

echo "=== SDK Version ==="
npm list algoliasearch 2>/dev/null || echo "Not installed"

echo "=== Algolia Status ==="
curl -s https://status.algolia.com/api/v2/status.json | jq -r '.status.description' 2>/dev/null
```

## Escalation Path

1. Check [status.algolia.com](https://status.algolia.com) first
2. Collect debug info with `algolia-debug-bundle` skill
3. Search [Algolia Support](https://support.algolia.com) articles
4. Open support ticket with request ID from error response

## Resources

- [Algolia Status Page](https://status.algolia.com)
- [API Key Restrictions](https://www.algolia.com/doc/guides/security/api-keys/in-depth/api-key-restrictions/)
- [Troubleshooting FAQ](https://support.algolia.com/hc/en-us/categories/4406981828753)

## Next Steps

For comprehensive debugging, see `algolia-debug-bundle`.
