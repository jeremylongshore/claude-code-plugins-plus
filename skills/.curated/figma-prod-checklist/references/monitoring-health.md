# Step 4: Monitoring & Health

Deep-dive reference for the `figma-prod-checklist` skill — extracted from the 'Step 4: Monitoring & Health' step of the workflow.

```typescript
// Health check endpoint
async function figmaHealthCheck() {
  const start = Date.now();
  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
      signal: AbortSignal.timeout(5000),
    });
    return {
      status: res.ok ? 'healthy' : 'degraded',
      latencyMs: Date.now() - start,
      httpStatus: res.status,
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      latencyMs: Date.now() - start,
      error: error instanceof Error ? error.message : 'Unknown',
    };
  }
}
```

- [ ] Health endpoint includes Figma connectivity check
- [ ] Alerts on sustained 429 errors (>5/min)
- [ ] Alerts on 403 errors (token expiry)
- [ ] Alerts on response latency >5s (P95)
- [ ] Dashboard tracks requests/min, error rate, latency

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
