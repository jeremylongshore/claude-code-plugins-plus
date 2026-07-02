# Step 3: Webhook-Driven Cache Invalidation

Deep-dive reference for the `figma-performance-tuning` skill — extracted from the 'Step 3: Webhook-Driven Cache Invalidation' step of the workflow.

```typescript
// Instead of polling, use webhooks to know when to re-fetch
// See figma-webhooks-events for full webhook setup

async function handleFileUpdate(fileKey: string) {
  // Invalidate cached data for this file
  fileCache.delete(fileKey);

  // Proactively re-fetch commonly accessed data
  const token = process.env.FIGMA_PAT!;
  await getCachedFile(fileKey, token);

  console.log(`Cache invalidated and refreshed for ${fileKey}`);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
