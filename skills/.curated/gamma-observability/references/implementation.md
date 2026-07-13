# Gamma Observability - Implementation Details

## Metrics (Prometheus)

```typescript
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'gamma_requests_total', help: 'Total Gamma API requests',
  labelNames: ['method', 'endpoint', 'status'], registers: [registry],
});

const requestDuration = new Histogram({
  name: 'gamma_request_duration_seconds', help: 'Gamma API request duration',
  labelNames: ['method', 'endpoint'], buckets: [0.1, 0.5, 1, 2, 5, 10, 30], registers: [registry],
});

const presentationsCreated = new Counter({
  name: 'gamma_presentations_created_total', help: 'Total presentations created',
  labelNames: ['style', 'user_tier'], registers: [registry],
});

const rateLimitRemaining = new Gauge({
  name: 'gamma_rate_limit_remaining', help: 'Remaining API calls',
  registers: [registry],
});

export function createInstrumentedClient() {
  return new GammaClient({
    apiKey: process.env.GAMMA_API_KEY,
    interceptors: {
      request: (config) => { config._startTime = Date.now(); return config; },
      response: (response, config) => {
        const duration = (Date.now() - config._startTime) / 1000;
        requestCounter.inc({ method: config.method, endpoint: config.path.split('/')[1], status: response.status });
        requestDuration.observe({ method: config.method, endpoint: config.path.split('/')[1] }, duration);
        const remaining = response.headers['x-ratelimit-remaining'];
        if (remaining) rateLimitRemaining.set(parseInt(remaining, 10));
        return response;
      },
    },
  });
}
```

## Structured Logging (Winston)

```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  defaultMeta: { service: 'gamma-integration' },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'gamma-error.log', level: 'error' }),
    new winston.transports.File({ filename: 'gamma-combined.log' }),
  ],
});

export function logGammaRequest(operation, params) {
  logger.info('Gamma API request', { operation, params: sanitizeParams(params) });
}

export function logGammaError(operation, error, context) {
  logger.error('Gamma API error', { operation, error: error.message, stack: error.stack, context });
}
```

## Distributed Tracing (OpenTelemetry)

```typescript
import { trace, SpanKind, SpanStatusCode } from '@opentelemetry/api';
const tracer = trace.getTracer('gamma-integration');

export async function traceGammaCall<T>(operationName: string, fn: () => Promise<T>): Promise<T> {
  return tracer.startActiveSpan(`gamma.${operationName}`, { kind: SpanKind.CLIENT }, async (span) => {
    try {
      const result = await fn();
      span.setAttributes({ 'gamma.operation': operationName, 'gamma.success': true });
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      span.recordException(error);
      throw error;
    } finally { span.end(); }
  });
}
```

## Grafana Dashboard

```json
{
  "title": "Gamma Integration",
  "panels": [
    { "title": "Request Rate", "targets": [{ "expr": "rate(gamma_requests_total[5m])" }] },
    { "title": "Latency P95", "targets": [{ "expr": "histogram_quantile(0.95, rate(gamma_request_duration_seconds_bucket[5m]))" }] },
    { "title": "Error Rate", "targets": [{ "expr": "rate(gamma_requests_total{status=~'5..'}[5m]) / rate(gamma_requests_total[5m])" }] },
    { "title": "Rate Limit", "targets": [{ "expr": "gamma_rate_limit_remaining" }] }
  ]
}
```

## Alert Rules

```yaml
groups:
  - name: gamma
    rules:
      - alert: GammaHighErrorRate
        expr: rate(gamma_requests_total{status=~"5.."}[5m]) / rate(gamma_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: warning }
      - alert: GammaRateLimitLow
        expr: gamma_rate_limit_remaining < 10
        for: 1m
        labels: { severity: critical }
      - alert: GammaHighLatency
        expr: histogram_quantile(0.95, rate(gamma_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels: { severity: warning }
```

## Health Check Endpoint

```typescript
app.get('/health/gamma', async (req, res) => {
  const health = { status: 'unknown', latency: 0, rateLimit: { remaining: 0, limit: 0 } };
  try {
    const start = Date.now();
    const response = await gamma.ping();
    health.latency = Date.now() - start;
    health.status = response.ok ? 'healthy' : 'degraded';
    health.rateLimit = { remaining: response.rateLimit.remaining, limit: response.rateLimit.limit };
  } catch { health.status = 'unhealthy'; }
  res.status(health.status === 'healthy' ? 200 : 503).json(health);
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
