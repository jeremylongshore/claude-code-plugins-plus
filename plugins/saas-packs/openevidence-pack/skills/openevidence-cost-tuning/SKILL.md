---
name: openevidence-cost-tuning
description: |
  Cost Tuning for OpenEvidence.
  Trigger: "openevidence cost tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Cost Tuning

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
  console.log(`OpenEvidence API calls today: ${totalCalls}`);
  return fn();
}
```

## Resources
- [OpenEvidence Pricing](https://www.openevidence.com)

## Next Steps
See `openevidence-reference-architecture`.
