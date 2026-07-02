# Step 4: Data Retention

Deep-dive reference for the `figma-data-handling` skill — extracted from the 'Step 4: Data Retention' step of the workflow.

```typescript
// Figma image export URLs expire after 30 days
// Plan data retention accordingly

interface CachedFigmaData {
  data: any;
  fetchedAt: Date;
  expiresAt: Date;
}

function createCacheEntry(data: any, ttlMs: number): CachedFigmaData {
  const now = new Date();
  return {
    data,
    fetchedAt: now,
    expiresAt: new Date(now.getTime() + ttlMs),
  };
}

// Cleanup expired entries
async function cleanupExpiredData(db: any) {
  const now = new Date();
  const deleted = await db.figmaCache.deleteMany({
    expiresAt: { $lt: now },
  });
  console.log(`Cleaned up ${deleted.count} expired Figma cache entries`);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
