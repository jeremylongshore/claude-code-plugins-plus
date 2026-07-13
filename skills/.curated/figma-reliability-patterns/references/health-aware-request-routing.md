# Step 5: Health-Aware Request Routing

Deep-dive reference for the `figma-reliability-patterns` skill — extracted from the 'Step 5: Health-Aware Request Routing' step of the workflow.

```typescript
// Only make non-critical Figma calls when the API is healthy
class FigmaHealthTracker {
  private healthy = true;
  private lastCheck = 0;
  private checkIntervalMs = 30_000;

  async isHealthy(token: string): Promise<boolean> {
    if (Date.now() - this.lastCheck < this.checkIntervalMs) {
      return this.healthy;
    }

    try {
      const res = await figmaFetchWithTimeout('/v1/me', token, 5000);
      this.healthy = res.ok;
    } catch {
      this.healthy = false;
    }
    this.lastCheck = Date.now();
    return this.healthy;
  }
}

const healthTracker = new FigmaHealthTracker();

async function conditionalFigmaCall<T>(
  token: string,
  critical: boolean,
  fn: () => Promise<T>,
  fallback: () => Promise<T>
): Promise<T> {
  const healthy = await healthTracker.isHealthy(token);

  if (!healthy && !critical) {
    console.log('Figma unhealthy, using fallback for non-critical call');
    return fallback();
  }

  return fetchWithFallback('default', fn).then(r => r.data);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
