## Examples

### Quick k6 Test

```bash
k6 run --vus 10 --duration 30s supabase-load-test.js
```

### Check Current Capacity

```typescript
const metrics = await getSystemMetrics();
const capacity = estimateSupabaseCapacity(metrics);
console.log('Headroom:', capacity.headroom + '%');
console.log('Recommendation:', capacity.scaleRecommendation);
```

### Scale HPA Manually

```bash
kubectl scale deployment supabase-integration --replicas=5
kubectl get hpa supabase-integration-hpa
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
