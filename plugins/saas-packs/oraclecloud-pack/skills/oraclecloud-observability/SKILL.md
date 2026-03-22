---
name: oraclecloud-observability
description: |
  Observability for Oracle Cloud.
  Trigger: "oraclecloud observability".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Observability

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
  logger.info({ event: 'oraclecloud.api', ms: Date.now() - start });
  return result;
}
```

## Resources
- [Oracle Cloud Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-incident-runbook`.
