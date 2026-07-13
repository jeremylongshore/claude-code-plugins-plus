# API Monitoring Dashboard Examples

## Prometheus Metrics Middleware

```javascript
const client = require('prom-client');

const httpDuration = new client.Histogram({
  name: 'http_request_duration_seconds', help: 'Request duration',
  labelNames: ['method', 'path', 'status'],
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
});
const httpTotal = new client.Counter({
  name: 'http_requests_total', help: 'Total requests',
  labelNames: ['method', 'path', 'status'],
});
const httpInFlight = new client.Gauge({
  name: 'http_requests_in_flight', help: 'In-flight requests',
});

function metricsMiddleware(req, res, next) {
  httpInFlight.inc();
  const start = process.hrtime.bigint();
  res.on('finish', () => {
    const duration = Number(process.hrtime.bigint() - start) / 1e9;
    const path = req.route?.path || req.path;
    const labels = { method: req.method, path, status: res.statusCode };
    httpDuration.observe(labels, duration);
    httpTotal.inc(labels);
    httpInFlight.dec();
  });
  next();
}

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});
```

## Health Check Endpoint

```javascript
app.get('/health', async (req, res) => {
  const checks = {};
  try { const s = Date.now(); await db.query('SELECT 1'); checks.database = { status: 'healthy', latencyMs: Date.now() - s }; }
  catch (e) { checks.database = { status: 'unhealthy', error: e.message }; }

  try { const s = Date.now(); await redis.ping(); checks.redis = { status: 'healthy', latencyMs: Date.now() - s }; }
  catch (e) { checks.redis = { status: 'unhealthy', error: e.message }; }

  const allHealthy = Object.values(checks).every(c => c.status === 'healthy');
  const anyUnhealthy = Object.values(checks).some(c => c.status === 'unhealthy');
  const overall = allHealthy ? 'healthy' : anyUnhealthy ? 'unhealthy' : 'degraded';

  res.status(overall === 'unhealthy' ? 503 : 200).json({
    status: overall, uptime: process.uptime(), checks,
  });
});

let isReady = false;
app.get('/ready', (req, res) => {
  res.status(isReady ? 200 : 503).json({ status: isReady ? 'ready' : 'not ready' });
});
```

## Grafana Dashboard (PromQL)

```json
{
  "panels": [
    { "title": "Request Rate", "expr": "sum(rate(http_requests_total[5m]))" },
    { "title": "Error Rate %", "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100" },
    { "title": "p50 Latency", "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))" },
    { "title": "p95 Latency", "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))" },
    { "title": "p99 Latency", "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))" },
    { "title": "In-Flight", "expr": "http_requests_in_flight" }
  ]
}
```

## Alerting Rules

```yaml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations: { summary: "Error rate > 5% for 5 minutes" }

      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels: { severity: warning }

      - alert: HealthCheckFailing
        expr: probe_success == 0
        for: 3m
        labels: { severity: critical }

      - alert: ErrorBudgetBurning
        expr: (1 - (sum(rate(http_requests_total{status!~"5.."}[1h])) / sum(rate(http_requests_total[1h])))) / (1 - 0.999) > 14.4
        for: 5m
        labels: { severity: critical }
```

## SLO Configuration

```yaml
slos:
  - name: api-availability
    target: 0.999
    window: 30d
    indicator:
      good: 'sum(rate(http_requests_total{status!~"5.."}[5m]))'
      total: 'sum(rate(http_requests_total[5m]))'
  - name: api-latency
    target: 0.95
    window: 30d
    indicator:
      good: 'sum(rate(http_request_duration_seconds_bucket{le="0.5"}[5m]))'
      total: 'sum(rate(http_request_duration_seconds_count[5m]))'
```

## Synthetic Monitoring Probe

```javascript
const endpoints = [
  { name: 'health', url: 'https://api.example.com/health', timeout: 5000 },
  { name: 'users', url: 'https://api.example.com/users?limit=1', timeout: 3000 },
];

async function runProbes() {
  for (const ep of endpoints) {
    const start = Date.now();
    try {
      const resp = await fetch(ep.url, { signal: AbortSignal.timeout(ep.timeout) });
      console.log(JSON.stringify({ probe: ep.name, status: resp.ok ? 'up' : 'degraded', latencyMs: Date.now() - start }));
    } catch (err) {
      console.log(JSON.stringify({ probe: ep.name, status: 'down', error: err.message }));
    }
  }
}
setInterval(runProbes, 30000);
```

## curl: Monitoring Endpoints

```bash
curl -s http://localhost:3000/health | jq .
# {"status":"healthy","uptime":86400,"checks":{"database":{"status":"healthy","latencyMs":2},...}}

curl -s http://localhost:3000/metrics | head -10
# http_request_duration_seconds_bucket{method="GET",path="/users",status="200",le="0.1"} 4523
# http_requests_total{method="GET",path="/users",status="200"} 5012
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
