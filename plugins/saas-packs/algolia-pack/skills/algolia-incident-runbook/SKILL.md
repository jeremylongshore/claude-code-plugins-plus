---
name: algolia-incident-runbook
description: |
  Execute Algolia incident response: triage search failures, distinguish
  Algolia-side vs your-side issues, apply fallbacks, and run postmortems.
  Trigger: "algolia incident", "algolia outage", "algolia down",
  "algolia on-call", "algolia emergency", "algolia broken", "search is down".
allowed-tools: Read, Grep, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Incident Runbook

## Overview

Rapid incident response procedures for Algolia search failures. Algolia's infrastructure is distributed across multiple data centers with automatic failover, so true Algolia outages are rare. Most incidents are caused by API key issues, settings drift, or indexing pipeline failures on your side.

## Severity Classification

| Level | Definition | Response | Examples |
|-------|------------|----------|----------|
| P1 | Search completely down | < 15 min | 403/500 on all queries, Algolia unreachable |
| P2 | Degraded search | < 1 hour | High latency, partial results, stale data |
| P3 | Minor issue | < 4 hours | Analytics not updating, synonyms wrong |
| P4 | No user impact | Next day | Monitoring gap, test failures |

## Quick Triage (Run These First)

```bash
#!/bin/bash
echo "=== ALGOLIA TRIAGE ==="

# 1. Is Algolia's infrastructure up?
echo -n "Algolia Status: "
curl -s https://status.algolia.com/api/v2/status.json | jq -r '.status.description'

# 2. Can we reach our Algolia app?
echo -n "API Connectivity: "
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" \
  "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes" \
  -H "X-Algolia-Application-Id: ${ALGOLIA_APP_ID}" \
  -H "X-Algolia-API-Key: ${ALGOLIA_ADMIN_KEY}"
echo ""

# 3. Can we actually search?
echo -n "Search test: "
curl -s "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/products/query" \
  -H "X-Algolia-Application-Id: ${ALGOLIA_APP_ID}" \
  -H "X-Algolia-API-Key: ${ALGOLIA_SEARCH_KEY}" \
  -d '{"query":"test","hitsPerPage":1}' | jq '{nbHits, processingTimeMS}'

# 4. Check index health
echo "Index stats:"
curl -s "https://${ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes" \
  -H "X-Algolia-Application-Id: ${ALGOLIA_APP_ID}" \
  -H "X-Algolia-API-Key: ${ALGOLIA_ADMIN_KEY}" \
  | jq '.items[] | {name, entries, lastBuildTimeS}'
```

## Decision Tree

```
Search returning errors?
├── YES: What HTTP status?
│   ├── 403: API key issue
│   │   ├── Key expired/deleted → Rotate key (see below)
│   │   └── Wrong key type → Use admin key for writes, search key for reads
│   ├── 404: Index doesn't exist
│   │   ├── Typo in index name → Check INDICES config
│   │   └── Index accidentally deleted → Trigger full reindex
│   ├── 429: Rate limited
│   │   ├── Per-key limit → Increase maxQueriesPerIPPerHour
│   │   └── Server limit → Reduce indexing batch frequency
│   └── 5xx: Algolia-side error
│       ├── status.algolia.com shows incident → Wait + enable fallback
│       └── No incident shown → Contact Algolia support with request IDs
└── NO: Search returning wrong/stale results?
    ├── 0 results unexpectedly → Check searchableAttributes, synonyms
    ├── Stale data → Check indexing pipeline, look at last sync timestamp
    └── Wrong ranking → Review customRanking, check for conflicting rules
```

## Immediate Remediation by Error Type

### 403 — Rotate API Key

```typescript
import { algoliasearch } from 'algoliasearch';

// Emergency: create a new key with same permissions
const adminClient = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

const { key: emergencyKey } = await adminClient.addApiKey({
  apiKey: {
    acl: ['search'],
    description: `Emergency search key — ${new Date().toISOString()}`,
    indexes: ['products', 'articles'],
    maxQueriesPerIPPerHour: 50000,
  },
});

console.log(`Emergency key created: ...${emergencyKey.slice(-8)}`);
console.log('Update ALGOLIA_SEARCH_KEY and redeploy');
```

### 0 Results — Emergency Reindex

```typescript
// Check if index is empty
const { items } = await client.listIndices();
const target = items.find(i => i.name === 'products');
console.log(`products: ${target?.entries ?? 'NOT FOUND'} records`);

// If empty, trigger emergency reindex
if (!target || target.entries === 0) {
  console.log('Index is empty — triggering emergency reindex');
  // Import your reindex function
  await fullReindex();
}
```

### High Latency — Enable Fallback

```typescript
// Circuit breaker: switch to DB search if Algolia is slow
const TIMEOUT_MS = 2000;
const FAILURE_THRESHOLD = 5;
let failures = 0;

async function searchWithCircuitBreaker(query: string) {
  if (failures >= FAILURE_THRESHOLD) {
    console.warn('Circuit open: using database fallback');
    return databaseSearch(query);
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const result = await client.searchSingleIndex({
      indexName: 'products',
      searchParams: { query, hitsPerPage: 20 },
    });

    clearTimeout(timeout);
    failures = 0; // Reset on success
    return result;
  } catch (error) {
    failures++;
    console.error(`Algolia failure ${failures}/${FAILURE_THRESHOLD}:`, error);
    return databaseSearch(query);
  }
}
```

## Communication Templates

### Internal (Slack/PagerDuty)

```
P[1-4] INCIDENT: Algolia Search
Status: INVESTIGATING | IDENTIFIED | MONITORING | RESOLVED
Impact: [Users cannot search / Search is slow / Results are stale]
Root cause: [API key expired / Index empty / Algolia incident]
Mitigation: [Fallback enabled / Key rotated / Waiting for Algolia]
Next update: [Time]
Owner: @[name]
```

### Postmortem Template

```markdown
## Incident: Search [Outage/Degradation]
**Date:** YYYY-MM-DD HH:MM–HH:MM UTC
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Detection:** [Alert name / User report / Status page]

### Timeline
- HH:MM — First alert fired
- HH:MM — Triage started, identified [root cause]
- HH:MM — Mitigation applied: [action]
- HH:MM — Resolved, monitoring

### Root Cause
[Technical explanation: what broke and why]

### Impact
- Search availability: X% during incident
- Users affected: ~N

### Action Items
- [ ] [Fix] — Owner — Due date
- [ ] [Prevent] — Owner — Due date
- [ ] [Detect faster] — Owner — Due date
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status.algolia.com | Your network issue | Use mobile, VPN, or check @algloiastatus on Twitter |
| Triage script fails | Missing env vars | Set ALGOLIA_APP_ID, ALGOLIA_ADMIN_KEY, ALGOLIA_SEARCH_KEY |
| Fallback search slow | No DB index | Add database full-text index as backup |
| Key rotation breaks frontend | CDN cache | Purge CDN cache or wait for TTL |

## Resources

- [Algolia Status Page](https://status.algolia.com)
- [Algolia Support](https://support.algolia.com)
- [Algolia API Logs](https://dashboard.algolia.com) (Dashboard > Monitoring > API Logs)

## Next Steps

For data handling and privacy, see `algolia-data-handling`.
