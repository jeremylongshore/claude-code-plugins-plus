# Step 5: Usage Dashboard Query

Deep-dive reference for the `figma-cost-tuning` skill — extracted from the 'Step 5: Usage Dashboard Query' step of the workflow.

```typescript
// Log API calls to a database for analysis
interface ApiCallLog {
  timestamp: Date;
  endpoint: string;
  fileKey: string;
  status: number;
  latencyMs: number;
  cached: boolean;
}

// Monthly usage summary
function getMonthlyReport(logs: ApiCallLog[]) {
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const monthLogs = logs.filter(l => l.timestamp >= monthStart);

  return {
    totalRequests: monthLogs.length,
    uniqueFiles: new Set(monthLogs.map(l => l.fileKey)).size,
    cacheHitRate: monthLogs.filter(l => l.cached).length / monthLogs.length,
    errorRate: monthLogs.filter(l => l.status >= 400).length / monthLogs.length,
    topEndpoints: Object.entries(
      monthLogs.reduce((acc, l) => {
        acc[l.endpoint] = (acc[l.endpoint] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    ).sort(([,a], [,b]) => b - a).slice(0, 5),
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
