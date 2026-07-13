# Step 3: Capacity Planning

Deep-dive reference for the `figma-load-scale` skill — extracted from the 'Step 3: Capacity Planning' step of the workflow.

```typescript
interface FigmaCapacityPlan {
  planTier: string;
  measuredLimitPerMinute: number;
  currentUsagePerMinute: number;
  headroomPercent: number;
  recommendation: string;
}

function planCapacity(
  measuredLimit: number,
  currentUsage: number,
  planTier: string
): FigmaCapacityPlan {
  const headroom = ((measuredLimit - currentUsage) / measuredLimit) * 100;

  let recommendation: string;
  if (headroom > 50) {
    recommendation = 'Adequate capacity. Monitor monthly.';
  } else if (headroom > 20) {
    recommendation = 'Approaching limits. Implement caching and batching.';
  } else {
    recommendation = 'Near capacity. Upgrade plan or reduce request volume.';
  }

  return {
    planTier,
    measuredLimitPerMinute: measuredLimit,
    currentUsagePerMinute: currentUsage,
    headroomPercent: Math.round(headroom),
    recommendation,
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
