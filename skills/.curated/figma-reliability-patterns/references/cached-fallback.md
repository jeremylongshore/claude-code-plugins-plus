# Step 2: Cached Fallback

Deep-dive reference for the `figma-reliability-patterns` skill — extracted from the 'Step 2: Cached Fallback' step of the workflow.

```typescript
import { readFileSync, writeFileSync, existsSync } from 'fs';

// Serve cached data when Figma is unavailable
class FigmaFallbackCache {
  constructor(private cacheDir = '.figma-cache') {}

  private getPath(key: string) {
    return `${this.cacheDir}/${key.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
  }

  save(key: string, data: any) {
    const { mkdirSync } = require('fs');
    mkdirSync(this.cacheDir, { recursive: true });
    writeFileSync(this.getPath(key), JSON.stringify({
      data,
      cachedAt: new Date().toISOString(),
    }));
  }

  load(key: string): { data: any; cachedAt: string } | null {
    const path = this.getPath(key);
    if (!existsSync(path)) return null;
    return JSON.parse(readFileSync(path, 'utf-8'));
  }
}

const fallbackCache = new FigmaFallbackCache();

async function fetchWithFallback<T>(
  cacheKey: string,
  fetcher: () => Promise<T>
): Promise<{ data: T; fromCache: boolean; cachedAt?: string }> {
  try {
    const data = await safeFigmaCall(fetcher);
    // Update cache with fresh data
    fallbackCache.save(cacheKey, data);
    return { data, fromCache: false };
  } catch (error) {
    console.warn(`Figma unavailable, loading cached ${cacheKey}`);
    const cached = fallbackCache.load(cacheKey);
    if (cached) {
      return { data: cached.data as T, fromCache: true, cachedAt: cached.cachedAt };
    }
    throw new Error(`Figma unavailable and no cached data for ${cacheKey}`);
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
