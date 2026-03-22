---
name: navan-cost-tuning
description: |
  Cost Tuning for Navan.
  Trigger: "navan cost tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Cost Tuning

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
  console.log(`Navan API calls today: ${totalCalls}`);
  return fn();
}
```

## Resources
- [Navan Pricing](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-reference-architecture`.
