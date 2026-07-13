# Cost Estimation

## Cost Estimation

```typescript
interface UsageEstimate {
  requestsPerMonth: number;
  tier: string;
  estimatedCost: number;
  recommendation?: string;
}

function estimateVercelCost(requestsPerMonth: number): UsageEstimate {
  if (requestsPerMonth <= 1000) {
    return { requestsPerMonth, tier: 'Free', estimatedCost: 0 };
  }

  if (requestsPerMonth <= 100000) {
    return { requestsPerMonth, tier: 'Pro', estimatedCost: 20 };
  }

  const proOverage = (requestsPerMonth - 100000) * 0.001;
  const proCost = 20 + proOverage;

  return {
    requestsPerMonth,
    tier: 'Pro (with overage)',
    estimatedCost: proCost,
    recommendation: proCost > 500
      ? 'Consider Enterprise tier for volume discounts'
      : undefined,
  };
}
```
