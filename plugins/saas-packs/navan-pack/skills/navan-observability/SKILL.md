---
name: navan-observability
description: |
  Observability for Navan.
  Trigger: "navan observability".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Observability

## Key Metrics
| Metric | Alert |
|--------|-------|
| API latency p99 | > 5s |
| Error rate | > 5% |
| Daily API calls | > 80% quota |

## Logging
```typescript
async function tracked(fn: () => Promise<any>) {
  const start = Date.now();
  const result = await fn();
  logger.info({ event: 'navan.api', ms: Date.now() - start });
  return result;
}
```

## Resources
- [Navan Docs](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-incident-runbook`.
