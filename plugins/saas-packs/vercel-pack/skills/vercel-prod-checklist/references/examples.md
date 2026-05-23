## Examples

### Health Check Implementation

```typescript
async function healthCheck(): Promise<{ status: string; vercel: any }> {
  const start = Date.now();
  try {
    await vercelClient.ping();
    return { status: 'healthy', vercel: { connected: true, latencyMs: Date.now() - start } };
  } catch (error) {
    return { status: 'degraded', vercel: { connected: false, latencyMs: Date.now() - start } };
  }
}
```

### Immediate Rollback

```bash
kubectl rollout undo deployment/vercel-integration
kubectl rollout status deployment/vercel-integration
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
