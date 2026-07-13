# Health Check Endpoint

Express health check that tests Shopify API connectivity and database availability, returning structured status with latency metrics.

```typescript
app.get("/health", async (req, res) => {
  const checks: Record<string, any> = {};

  // Test Shopify connectivity
  try {
    const start = Date.now();
    await client.request("{ shop { name } }");
    checks.shopify = { status: "ok", latencyMs: Date.now() - start };
  } catch (err) {
    checks.shopify = { status: "error", message: (err as Error).message };
  }

  // Test database
  try {
    await db.query("SELECT 1");
    checks.database = { status: "ok" };
  } catch (err) {
    checks.database = { status: "error" };
  }

  const allHealthy = Object.values(checks).every((c: any) => c.status === "ok");
  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? "healthy" : "degraded",
    checks,
    timestamp: new Date().toISOString(),
  });
});
```
