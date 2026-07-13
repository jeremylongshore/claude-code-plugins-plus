# Scaling Patterns

## Scaling Patterns

### Horizontal Scaling

```yaml
# kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: supabase-integration-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: supabase-integration
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
          name: supabase_queue_depth
        target:
          type: AverageValue
          averageValue: 100
```

### Connection Pooling

```typescript
import { Pool } from 'generic-pool';

const supabasePool = Pool.create({
  create: async () => {
    return new SupabaseClient({
      apiKey: process.env.SUPABASE_API_KEY!,
    });
  },
  destroy: async (client) => {
    await client.close();
  },
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

async function withSupabaseClient<T>(
  fn: (client: SupabaseClient) => Promise<T>
): Promise<T> {
  const client = await supabasePool.acquire();
  try {
    return await fn(client);
  } finally {
    supabasePool.release(client);
  }
}
```
