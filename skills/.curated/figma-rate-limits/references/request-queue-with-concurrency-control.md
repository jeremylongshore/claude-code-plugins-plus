# Step 3: Request Queue with Concurrency Control

Deep-dive reference for the `figma-rate-limits` skill — extracted from the 'Step 3: Request Queue with Concurrency Control' step of the workflow.

```typescript
import PQueue from 'p-queue';

// Limit concurrent requests to avoid bursting the bucket
const figmaQueue = new PQueue({
  concurrency: 3,       // max 3 parallel requests
  interval: 1000,       // per second
  intervalCap: 5,       // max 5 requests per second
});

async function queuedFigmaRequest<T>(
  path: string,
  token: string
): Promise<T> {
  return figmaQueue.add(() => figmaFetchWithRetry(path, token));
}

// Usage -- all requests are automatically queued and throttled
const [file, comments, images] = await Promise.all([
  queuedFigmaRequest(`/v1/files/${fileKey}`, token),
  queuedFigmaRequest(`/v1/files/${fileKey}/comments`, token),
  queuedFigmaRequest(`/v1/images/${fileKey}?ids=0:1&format=svg`, token),
]);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
