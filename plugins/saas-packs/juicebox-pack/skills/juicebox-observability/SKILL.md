---
name: juicebox-observability
description: |
  Set up Juicebox monitoring.
  Trigger: "juicebox monitoring", "juicebox metrics".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Observability

## Metrics
| Metric | Alert |
|--------|-------|
| Search latency p99 | > 5s |
| Error rate | > 5% |
| Quota usage | > 80% |

## Logging
```typescript
async function trackedSearch(query: string) {
  const start = Date.now();
  const result = await client.search({ query });
  logger.info({ event: 'jb.search', query, total: result.total, ms: Date.now() - start });
  return result;
}
```

## Resources
- [Dashboard](https://app.juicebox.ai/analytics)

## Next Steps
See `juicebox-incident-runbook`.
