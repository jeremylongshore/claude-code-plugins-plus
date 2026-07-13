# Step 4: Request Timeout

Deep-dive reference for the `figma-reliability-patterns` skill — extracted from the 'Step 4: Request Timeout' step of the workflow.

```typescript
// Prevent requests from hanging indefinitely
async function figmaFetchWithTimeout(
  path: string,
  token: string,
  timeoutMs = 15_000
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(`https://api.figma.com${path}`, {
      headers: { 'X-Figma-Token': token },
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`Figma request timed out after ${timeoutMs}ms: ${path}`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
