# Step 2: Response Caching

Deep-dive reference for the `figma-performance-tuning` skill — extracted from the 'Step 2: Response Caching' step of the workflow.

```typescript
import { LRUCache } from 'lru-cache';

// File metadata changes rarely -- cache for 5 minutes
const fileCache = new LRUCache<string, any>({
  max: 100,
  ttl: 5 * 60 * 1000, // 5 minutes
});

async function getCachedFile(fileKey: string, token: string) {
  const cached = fileCache.get(fileKey);
  if (cached) return cached;

  const file = await fetch(
    `https://api.figma.com/v1/files/${fileKey}?depth=1`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());

  fileCache.set(fileKey, file);
  return file;
}

// Image URLs expire after 30 days -- cache them but with a shorter TTL
const imageUrlCache = new LRUCache<string, string>({
  max: 1000,
  ttl: 24 * 60 * 60 * 1000, // 1 day (well within 30-day expiry)
});

async function getCachedImageUrl(
  fileKey: string, nodeId: string, format: string, token: string
): Promise<string | null> {
  const cacheKey = `${fileKey}:${nodeId}:${format}`;
  const cached = imageUrlCache.get(cacheKey);
  if (cached) return cached;

  const data = await fetch(
    `https://api.figma.com/v1/images/${fileKey}?ids=${nodeId}&format=${format}`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());

  const url = data.images[nodeId];
  if (url) imageUrlCache.set(cacheKey, url);
  return url;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
