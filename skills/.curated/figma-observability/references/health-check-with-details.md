# Step 4: Health Check with Details

Deep-dive reference for the `figma-observability` skill — extracted from the 'Step 4: Health Check with Details' step of the workflow.

```typescript
async function figmaHealthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: Record<string, any>;
}> {
  const start = Date.now();

  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
      signal: AbortSignal.timeout(5000),
    });

    const latencyMs = Date.now() - start;
    const remaining = res.headers.get('X-RateLimit-Remaining');

    return {
      status: res.ok ? (latencyMs > 3000 ? 'degraded' : 'healthy') : 'degraded',
      details: {
        authenticated: res.ok,
        latencyMs,
        rateLimitRemaining: remaining ? parseInt(remaining) : null,
        planTier: res.headers.get('X-Figma-Plan-Tier'),
      },
    };
  } catch {
    return {
      status: 'unhealthy',
      details: { authenticated: false, latencyMs: Date.now() - start },
    };
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
