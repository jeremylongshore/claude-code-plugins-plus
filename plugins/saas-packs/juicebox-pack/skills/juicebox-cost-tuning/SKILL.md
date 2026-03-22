---
name: juicebox-cost-tuning
description: |
  Optimize Juicebox costs.
  Trigger: "juicebox cost", "juicebox billing", "juicebox budget".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Cost Tuning

## Cost Factors
| Feature | Cost Driver |
|---------|-------------|
| Search | Per query |
| Enrichment | Per profile |
| Contact data | Per lookup |
| Outreach | Per message |

## Reduction Strategies
1. Cache search results (avoid duplicate queries)
2. Use filters (fewer wasted enrichments)
3. Only enrich top-scored candidates
4. Only get contacts for final candidates

## Quota Monitoring
```typescript
const quota = await client.account.getQuota();
console.log(`Searches: ${quota.searches.used}/${quota.searches.limit}`);
if (quota.searches.used > quota.searches.limit * 0.8) console.warn('80% quota used');
```

## Resources
- [Pricing](https://juicebox.ai/pricing)

## Next Steps
See `juicebox-reference-architecture`.
