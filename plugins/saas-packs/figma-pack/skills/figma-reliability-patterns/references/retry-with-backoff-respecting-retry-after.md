# Step 3: Retry with Backoff (Respecting Retry-After)

Deep-dive reference for the `figma-reliability-patterns` skill — extracted from the 'Step 3: Retry with Backoff (Respecting Retry-After)' step of the workflow.

```typescript
async function figmaRetry<T>(
  fn: () => Promise<Response>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fn();

    if (res.ok) return res.json();

    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      if (attempt < maxRetries) {
        console.warn(`429 -- waiting ${retryAfter}s (attempt ${attempt + 1}/${maxRetries})`);
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        continue;
      }
    }

    if (res.status >= 500 && attempt < maxRetries) {
      const delay = Math.min(1000 * Math.pow(2, attempt), 30_000);
      const jitter = Math.random() * 1000;
      await new Promise(r => setTimeout(r, delay + jitter));
      continue;
    }

    throw new FigmaApiError(res.status, await res.text());
  }
  throw new Error('Max retries exceeded');
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
