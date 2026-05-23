# Capacity Planning

## Capacity Planning

### Metrics to Monitor

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Utilization | > 70% | > 85% |
| Memory Usage | > 75% | > 90% |
| Request Queue Depth | > 100 | > 500 |
| Error Rate | > 1% | > 5% |
| P95 Latency | > 500ms | > 2000ms |

### Capacity Calculation

```typescript
interface CapacityEstimate {
  currentRPS: number;
  maxRPS: number;
  headroom: number;
  scaleRecommendation: string;
}

function estimateSupabaseCapacity(
  metrics: SystemMetrics
): CapacityEstimate {
  const currentRPS = metrics.requestsPerSecond;
  const avgLatency = metrics.p50Latency;
  const cpuUtilization = metrics.cpuPercent;

  // Estimate max RPS based on current performance
  const maxRPS = currentRPS / (cpuUtilization / 100) * 0.7; // 70% target
  const headroom = ((maxRPS - currentRPS) / currentRPS) * 100;

  return {
    currentRPS,
    maxRPS: Math.floor(maxRPS),
    headroom: Math.round(headroom),
    scaleRecommendation: headroom < 30
      ? 'Scale up soon'
      : headroom < 50
      ? 'Monitor closely'
      : 'Adequate capacity',
  };
}
```
