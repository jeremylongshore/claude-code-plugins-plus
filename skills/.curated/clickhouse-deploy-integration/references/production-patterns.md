# Production Patterns — Health Checks & Graceful Shutdown

Runtime hardening that applies to every platform. The health endpoint drives
Fly.io / Cloud Run readiness probes; graceful shutdown prevents dropped inserts
when a container is recycled or a machine is auto-stopped.

## Health Check Endpoint

```typescript
// Works on all platforms
app.get('/health', async (req, res) => {
  const start = Date.now();
  try {
    const client = getClickHouse();
    const { success } = await client.ping();
    const latencyMs = Date.now() - start;

    res.json({
      status: success ? 'healthy' : 'degraded',
      clickhouse: { connected: success, latencyMs },
      version: process.env.npm_package_version,
    });
  } catch (err) {
    res.status(503).json({
      status: 'unhealthy',
      clickhouse: { connected: false, error: (err as Error).message },
    });
  }
});
```

## Graceful Shutdown

```typescript
// Critical: flush pending inserts on shutdown
async function gracefulShutdown() {
  console.log('Shutting down...');
  const client = getClickHouse();
  await client.close();    // Waits for pending operations to complete
  process.exit(0);
}

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);
```
