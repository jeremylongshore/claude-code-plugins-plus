---
name: oraclecloud-cost-tuning
description: |
  Cost Tuning for Oracle Cloud.
  Trigger: "oraclecloud cost tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Cost Tuning

## Optimization Strategies
1. Cache frequent API calls
2. Batch requests where possible
3. Use appropriate API tier
4. Monitor usage dashboards

## Usage Tracking
```typescript
let totalCalls = 0;
async function tracked(fn: () => Promise<any>) {
  totalCalls++;
  console.log(`Oracle Cloud API calls today: ${totalCalls}`);
  return fn();
}
```

## Resources
- [Oracle Cloud Pricing](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-reference-architecture`.
