---
name: openevidence-observability
description: |
  Observability for OpenEvidence.
  Trigger: "openevidence observability".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Observability

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
  logger.info({ event: 'openevidence.api', ms: Date.now() - start });
  return result;
}
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-incident-runbook`.
