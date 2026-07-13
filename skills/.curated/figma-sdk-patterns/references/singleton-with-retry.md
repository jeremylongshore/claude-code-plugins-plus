# Step 5: Singleton with Retry

Deep-dive reference for the `figma-sdk-patterns` skill — extracted from the 'Step 5: Singleton with Retry' step of the workflow.

```typescript
// Singleton instance with automatic retry on transient errors
let client: FigmaClient | null = null;

export function getFigmaClient(): FigmaClient {
  if (!client) {
    client = new FigmaClient(process.env.FIGMA_PAT!);
  }
  return client;
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (err instanceof FigmaRateLimitError) {
        await new Promise(r => setTimeout(r, err.retryAfterSeconds * 1000));
        continue;
      }
      if (attempt === maxRetries) throw err;
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
    }
  }
  throw new Error('Unreachable');
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
