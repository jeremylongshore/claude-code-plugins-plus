---
name: mindtickle-cost-tuning
description: |
  Cost Tuning for MindTickle.
  Trigger: "mindtickle cost tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Cost Tuning

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
  console.log(`MindTickle API calls today: ${totalCalls}`);
  return fn();
}
```

## Resources
- [MindTickle Pricing](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-reference-architecture`.
