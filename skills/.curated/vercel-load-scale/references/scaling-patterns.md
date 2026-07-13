# Scaling Patterns

## Scaling Patterns

### Horizontal Scaling

```yaml
# kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vercel-integration-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vercel-integration
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: vercel_queue_depth
        target:
          type: AverageValue
          averageValue: 100
```

### Connection Pooling

```typescript
import { Pool } from 'generic-pool';

const vercelPool = Pool.create({
  create: async () => {
    return new VercelClient({
      apiKey: process.env.VERCEL_API_KEY!,
    });
  },
  destroy: async (client) => {
    await client.close();
  },
  max: None,
  min: None,
  idleTimeoutMillis: 30000,
});

async function withVercelClient<T>(
  fn: (client: VercelClient) => Promise<T>
): Promise<T> {
  const client = await vercelPool.acquire();
  try {
    return await fn(client);
  } finally {
    vercelPool.release(client);
  }
}
```
