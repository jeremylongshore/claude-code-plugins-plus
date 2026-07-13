# Step 2: Implement Exponential Backoff

Deep-dive reference for the `figma-rate-limits` skill — extracted from the 'Step 2: Implement Exponential Backoff' step of the workflow.

```typescript
async function figmaFetchWithRetry(
  path: string,
  token: string,
  maxRetries = 5
): Promise<any> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fetch(`https://api.figma.com${path}`, {
      headers: { 'X-Figma-Token': token },
    });

    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      const limitType = res.headers.get('X-Figma-Rate-Limit-Type') || 'unknown';

      if (attempt === maxRetries) {
        throw new Error(`Rate limited after ${maxRetries} retries (${limitType})`);
      }

      // Use the Retry-After header -- Figma tells you exactly how long to wait
      const jitter = Math.random() * 1000;
      const delay = retryAfter * 1000 + jitter;
      console.warn(`429 (${limitType}). Waiting ${(delay/1000).toFixed(1)}s (attempt ${attempt + 1})`);
      await new Promise(r => setTimeout(r, delay));
      continue;
    }

    if (res.status >= 500 && attempt < maxRetries) {
      // Server errors: exponential backoff without Retry-After
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
      await new Promise(r => setTimeout(r, delay));
      continue;
    }

    if (!res.ok) {
      throw new Error(`Figma API error: ${res.status} ${await res.text()}`);
    }

    return res.json();
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
