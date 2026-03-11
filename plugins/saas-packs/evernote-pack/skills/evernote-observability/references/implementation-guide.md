# Evernote Observability - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Metrics Collection

```javascript
// monitoring/metrics.js
const prometheus = require('prom-client');

// Initialize default metrics
prometheus.collectDefaultMetrics({ prefix: 'evernote_' });

// API call metrics
const apiCallCounter = new prometheus.Counter({
  name: 'evernote_api_calls_total',
  help: 'Total number of Evernote API calls',
  labelNames: ['operation', 'status', 'sandbox']
});

const apiCallDuration = new prometheus.Histogram({
  name: 'evernote_api_call_duration_seconds',
  help: 'Duration of Evernote API calls',
  labelNames: ['operation'],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10]
});

// Rate limit metrics
const rateLimitCounter = new prometheus.Counter({
  name: 'evernote_rate_limits_total',
  help: 'Total number of rate limit hits'
});

const rateLimitWaitGauge = new prometheus.Gauge({
  name: 'evernote_rate_limit_wait_seconds',
  help: 'Current rate limit wait time'
});

// Cache metrics
const cacheHitCounter = new prometheus.Counter({
  name: 'evernote_cache_hits_total',
  help: 'Total cache hits',
  labelNames: ['operation']
});

const cacheMissCounter = new prometheus.Counter({
  name: 'evernote_cache_misses_total',
  help: 'Total cache misses',
  labelNames: ['operation']
});

// Auth metrics
const authCounter = new prometheus.Counter({
  name: 'evernote_auth_total',
  help: 'Total authentication attempts',
  labelNames: ['status', 'type']
});

const activeTokensGauge = new prometheus.Gauge({
  name: 'evernote_active_tokens',
  help: 'Number of active user tokens'
});

// Quota metrics
const quotaUsageGauge = new prometheus.Gauge({
  name: 'evernote_quota_usage_bytes',
  help: 'Current quota usage in bytes',
  labelNames: ['user_id']
});

// Export metrics
module.exports = {
  apiCallCounter,
  apiCallDuration,
  rateLimitCounter,
  rateLimitWaitGauge,
  cacheHitCounter,
  cacheMissCounter,
  authCounter,
  activeTokensGauge,
  quotaUsageGauge,
  register: prometheus.register
};
```

### Step 2: Instrumented Client

```javascript
// services/instrumented-client.js
const Evernote = require('evernote');
const metrics = require('../monitoring/metrics');
const logger = require('../logging/logger');

class InstrumentedEvernoteClient {
  constructor(accessToken, options = {}) {
    this.client = new Evernote.Client({
      token: accessToken,
      sandbox: options.sandbox || false
    });
    this.userId = options.userId;
    this.sandbox = options.sandbox;
    this._noteStore = null;
  }

  get noteStore() {
    if (!this._noteStore) {
      this._noteStore = this.wrapStore(
        this.client.getNoteStore(),
        'NoteStore'
      );
    }
    return this._noteStore;
  }

  wrapStore(store, storeName) {
    const self = this;

    return new Proxy(store, {
      get(target, prop) {
        const original = target[prop];

        if (typeof original !== 'function') {
          return original;
        }

        return async (...args) => {
          const operation = `${storeName}.${prop}`;
          const startTime = Date.now();

          // Start timer
          const endTimer = metrics.apiCallDuration.startTimer({ operation });

          try {
            const result = await original.apply(target, args);

            // Record success
            const duration = (Date.now() - startTime) / 1000;
            metrics.apiCallCounter.inc({
              operation,
              status: 'success',
              sandbox: String(self.sandbox)
            });

            logger.debug('Evernote API call', {
              operation,
              duration,
              userId: self.userId
            });

            return result;
          } catch (error) {
            // Record error
            metrics.apiCallCounter.inc({
              operation,
              status: error.errorCode ? `error_${error.errorCode}` : 'error',
              sandbox: String(self.sandbox)
            });

            // Rate limit tracking
            if (error.errorCode === 19) {
              metrics.rateLimitCounter.inc();
              metrics.rateLimitWaitGauge.set(error.rateLimitDuration || 0);

              logger.warn('Rate limit hit', {
                operation,
                userId: self.userId,
                waitTime: error.rateLimitDuration
              });
            } else {
              logger.error('Evernote API error', {
                operation,
                errorCode: error.errorCode,
                parameter: error.parameter,
                userId: self.userId
              });
            }

            throw error;
          } finally {
            endTimer();
          }
        };
      }
    });
  }
}

module.exports = InstrumentedEvernoteClient;
```

### Step 3: Structured Logging

```javascript
// logging/logger.js
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'evernote-integration',
    environment: process.env.NODE_ENV
  },
  transports: [
    new winston.transports.Console({
      format: process.env.NODE_ENV === 'development'
        ? winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        : winston.format.json()
    })
  ]
});

// Add file transport in production
if (process.env.NODE_ENV === 'production') {
  logger.add(new winston.transports.File({
    filename: 'logs/error.log',
    level: 'error',
    maxsize: 10 * 1024 * 1024,
    maxFiles: 5
  }));

  logger.add(new winston.transports.File({
    filename: 'logs/combined.log',
    maxsize: 10 * 1024 * 1024,
    maxFiles: 5
  }));
}

// Redact sensitive data
const redactPatterns = [
  /S=s\d+:U=[^:]+:[^:]+:[a-f0-9]+/gi, // Evernote tokens
  /bearer\s+[^\s]+/gi,
  /api[_-]?key[=:]\s*[^\s,}]+/gi
];

function redact(message) {
  if (typeof message !== 'string') return message;

  let redacted = message;
  for (const pattern of redactPatterns) {
    redacted = redacted.replace(pattern, '[REDACTED]');
  }
  return redacted;
}

// Wrap logger methods
const originalLog = logger.log.bind(logger);
logger.log = function(level, message, meta = {}) {
  if (typeof message === 'string') {
    message = redact(message);
  }
  if (meta && typeof meta === 'object') {
    meta = JSON.parse(redact(JSON.stringify(meta)));
  }
  return originalLog(level, message, meta);
};

module.exports = logger;
```

### Step 4: Distributed Tracing

```javascript
// tracing/tracer.js
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { trace, context, SpanKind } = require('@opentelemetry/api');

// Initialize tracer
const provider = new NodeTracerProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'evernote-integration'
  })
});

// Configure exporter
if (process.env.JAEGER_ENDPOINT) {
  const exporter = new JaegerExporter({
    endpoint: process.env.JAEGER_ENDPOINT
  });
  provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
}

provider.register();

const tracer = trace.getTracer('evernote-integration');

// Traced client wrapper
function traceOperation(operation, fn) {
  return async (...args) => {
    const span = tracer.startSpan(`evernote.${operation}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        'evernote.operation': operation
      }
    });

    try {
      const result = await context.with(
        trace.setSpan(context.active(), span),
        () => fn(...args)
      );

      span.setStatus({ code: 0 }); // OK
      return result;
    } catch (error) {
      span.setStatus({
        code: 2, // ERROR
        message: error.message
      });

      span.recordException(error);
      span.setAttribute('evernote.error_code', error.errorCode);
      throw error;
    } finally {
      span.end();
    }
  };
}

module.exports = { tracer, traceOperation };
```

### Step 5: Health and Readiness Endpoints

```javascript
// routes/health.js
const express = require('express');
const metrics = require('../monitoring/metrics');

const router = express.Router();

// Liveness probe
router.get('/health/live', (req, res) => {
  res.status(200).json({ status: 'alive' });
});

// Readiness probe
router.get('/health/ready', async (req, res) => {
  const checks = await runHealthChecks();
  const allHealthy = checks.every(c => c.status === 'healthy');

  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? 'ready' : 'not_ready',
    checks
  });
});

// Detailed health status
router.get('/health/detailed', async (req, res) => {
  const checks = await runHealthChecks();

  res.json({
    status: checks.every(c => c.status === 'healthy') ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    checks
  });
});

// Prometheus metrics endpoint
router.get('/metrics', async (req, res) => {
  res.set('Content-Type', metrics.register.contentType);
  res.end(await metrics.register.metrics());
});

async function runHealthChecks() {
  const checks = [];

  // Database check
  try {
    await db.query('SELECT 1');
    checks.push({ name: 'database', status: 'healthy' });
  } catch (error) {
    checks.push({ name: 'database', status: 'unhealthy', error: error.message });
  }

  // Redis check
  try {
    await redis.ping();
    checks.push({ name: 'redis', status: 'healthy' });
  } catch (error) {
    checks.push({ name: 'redis', status: 'unhealthy', error: error.message });
  }

  // Memory check
  const memUsage = process.memoryUsage();
  const heapPercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
  checks.push({
    name: 'memory',
    status: heapPercent < 90 ? 'healthy' : 'warning',
    heapUsedPercent: heapPercent.toFixed(1)
  });

  return checks;
}

module.exports = router;
```

### Step 6: Alert Rules

```yaml
groups:
  - name: evernote-alerts
    rules:
      # High error rate
      - alert: EvernoteHighErrorRate
        expr: |
          sum(rate(evernote_api_calls_total{status=~"error.*"}[5m])) /
          sum(rate(evernote_api_calls_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High Evernote API error rate
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Rate limiting
      - alert: EvernoteRateLimited
        expr: rate(evernote_rate_limits_total[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: Evernote rate limit detected
          description: "Rate limits are being hit"

      # High latency
      - alert: EvernoteHighLatency
        expr: |
          histogram_quantile(0.95, rate(evernote_api_call_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High Evernote API latency
          description: "P95 latency is {{ $value }}s"

      # Auth failures
      - alert: EvernoteAuthFailures
        expr: rate(evernote_auth_total{status="failure"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High authentication failure rate
          description: "Auth failures: {{ $value }} per second"

      # Low cache hit rate
      - alert: EvernoteLowCacheHitRate
        expr: |
          sum(rate(evernote_cache_hits_total[5m])) /
          (sum(rate(evernote_cache_hits_total[5m])) +
           sum(rate(evernote_cache_misses_total[5m]))) < 0.5
        for: 15m
        labels:
          severity: info
        annotations:
          summary: Low cache hit rate
          description: "Cache hit rate is {{ $value | humanizePercentage }}"
```

### Step 7: Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Evernote Integration",
    "panels": [
      {
        "title": "API Calls Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(evernote_api_calls_total[5m])) by (operation)",
            "legendFormat": "{{operation}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(evernote_api_calls_total{status=~\"error.*\"}[5m])) / sum(rate(evernote_api_calls_total[5m])) * 100",
            "legendFormat": "Error %"
          }
        ]
      },
      {
        "title": "API Latency (P50/P95/P99)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(evernote_api_call_duration_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(evernote_api_call_duration_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(evernote_api_call_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "Rate Limits",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(evernote_rate_limits_total[1h]))",
            "legendFormat": "Rate Limits (1h)"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(rate(evernote_cache_hits_total[5m])) / (sum(rate(evernote_cache_hits_total[5m])) + sum(rate(evernote_cache_misses_total[5m]))) * 100"
          }
        ]
      }
    ]
  }
}
```


## Key Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| api_calls_total | Counter | Track API usage |
| api_call_duration_seconds | Histogram | Latency monitoring |
| rate_limits_total | Counter | Rate limit tracking |
| cache_hits_total | Counter | Cache effectiveness |
| auth_total | Counter | Auth success/failure |
