# Step 4: Health Check Endpoint

Deep-dive reference for the `figma-deploy-integration` skill — extracted from the 'Step 4: Health Check Endpoint' step of the workflow.

```typescript
// src/health.ts -- works on any platform
import { figmaFetch } from './figma-client';

export async function healthHandler(req: Request): Promise<Response> {
  const start = Date.now();

  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
      signal: AbortSignal.timeout(5000),
    });

    return Response.json({
      status: res.ok ? 'healthy' : 'degraded',
      figma: {
        authenticated: res.ok,
        latencyMs: Date.now() - start,
      },
      timestamp: new Date().toISOString(),
    });
  } catch {
    return Response.json({
      status: 'unhealthy',
      figma: { authenticated: false, latencyMs: Date.now() - start },
    }, { status: 503 });
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
