---
name: deepgram-observability
description: |
  Set up comprehensive observability for Deepgram integrations.
  Use when implementing monitoring, setting up dashboards,
  or configuring alerting for Deepgram integration health.
  Trigger: "deepgram monitoring", "deepgram metrics", "deepgram observability",
  "monitor deepgram", "deepgram alerts", "deepgram dashboard".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, monitoring, observability, prometheus]

---
# Deepgram Observability

## Overview
Full observability stack for Deepgram: Prometheus metrics (request counts, latency histograms, audio processed, cost tracking), OpenTelemetry distributed tracing, structured JSON logging with Pino, Grafana dashboard JSON, and AlertManager rules.

## Four Pillars

| Pillar | Tool | What It Tracks |
|--------|------|----------------|
| Metrics | Prometheus | Request rate, latency, error rate, audio minutes, estimated cost |
| Traces | OpenTelemetry | End-to-end request flow, Deepgram API span timing |
| Logs | Pino (JSON) | Request details, errors, audit trail |
| Alerts | AlertManager | Error rate >5%, P95 latency >10s, rate limit hits |

## Instructions

### Step 1: Prometheus Metrics Definition

```typescript
import { Counter, Histogram, Gauge, Registry, collectDefaultMetrics } from 'prom-client';

const registry = new Registry();
collectDefaultMetrics({ register: registry });

// Request metrics
const requestsTotal = new Counter({
  name: 'deepgram_requests_total',
  help: 'Total Deepgram API requests',
  labelNames: ['method', 'model', 'status'] as const,
  registers: [registry],
});

const latencyHistogram = new Histogram({
  name: 'deepgram_request_duration_seconds',
  help: 'Deepgram API request duration',
  labelNames: ['method', 'model'] as const,
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60],
  registers: [registry],
});

// Usage metrics
const audioProcessedSeconds = new Counter({
  name: 'deepgram_audio_processed_seconds_total',
  help: 'Total audio seconds processed',
  labelNames: ['model'] as const,
  registers: [registry],
});

const estimatedCostDollars = new Counter({
  name: 'deepgram_estimated_cost_dollars_total',
  help: 'Estimated cost in USD',
  labelNames: ['model', 'method'] as const,
  registers: [registry],
});

// Operational metrics
const activeConnections = new Gauge({
  name: 'deepgram_active_websocket_connections',
  help: 'Currently active WebSocket connections',
  registers: [registry],
});

const rateLimitHits = new Counter({
  name: 'deepgram_rate_limit_hits_total',
  help: 'Number of 429 rate limit responses',
  registers: [registry],
});

export { registry, requestsTotal, latencyHistogram, audioProcessedSeconds,
         estimatedCostDollars, activeConnections, rateLimitHits };
```

### Step 2: Instrumented Deepgram Client

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';

class InstrumentedDeepgram {
  private client: DeepgramClient;
  private costPerMinute: Record<string, number> = {
    'nova-3': 0.0043, 'nova-2': 0.0043, 'base': 0.0048, 'whisper-large': 0.0048,
  };

  constructor(apiKey: string) {
    this.client = createClient(apiKey);
  }

  async transcribeUrl(url: string, options: Record<string, any> = {}) {
    const model = options.model ?? 'nova-3';
    const timer = latencyHistogram.startTimer({ method: 'prerecorded', model });

    try {
      const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
        { url }, { model, smart_format: true, ...options }
      );

      const status = error ? 'error' : 'success';
      timer();
      requestsTotal.inc({ method: 'prerecorded', model, status });

      if (error) {
        if ((error as any).status === 429) rateLimitHits.inc();
        throw error;
      }

      // Track usage
      const duration = result.metadata.duration;
      audioProcessedSeconds.inc({ model }, duration);
      estimatedCostDollars.inc(
        { model, method: 'prerecorded' },
        (duration / 60) * (this.costPerMinute[model] ?? 0.0043)
      );

      return result;
    } catch (err) {
      timer();
      requestsTotal.inc({ method: 'prerecorded', model, status: 'error' });
      throw err;
    }
  }

  // Live transcription with connection tracking
  connectLive(options: Record<string, any>) {
    const model = options.model ?? 'nova-3';
    activeConnections.inc();

    const connection = this.client.listen.live(options);

    const originalFinish = connection.finish.bind(connection);
    connection.finish = () => {
      activeConnections.dec();
      return originalFinish();
    };

    return connection;
  }
}
```

### Step 3: OpenTelemetry Tracing

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { Resource } from '@opentelemetry/resources';
import { SEMRESATTRS_SERVICE_NAME } from '@opentelemetry/semantic-conventions';
import { trace } from '@opentelemetry/api';

const sdk = new NodeSDK({
  resource: new Resource({
    [SEMRESATTRS_SERVICE_NAME]: 'deepgram-service',
    'deployment.environment': process.env.NODE_ENV ?? 'development',
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318/v1/traces',
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-http': {
        ignoreIncomingPaths: ['/health', '/metrics'],
      },
    }),
  ],
});

sdk.start();

// Add custom spans for Deepgram operations
const tracer = trace.getTracer('deepgram');

async function tracedTranscribe(url: string, model: string) {
  return tracer.startActiveSpan('deepgram.transcribe', async (span) => {
    span.setAttribute('deepgram.model', model);
    span.setAttribute('deepgram.audio_url', url.substring(0, 100));

    try {
      const instrumented = new InstrumentedDeepgram(process.env.DEEPGRAM_API_KEY!);
      const result = await instrumented.transcribeUrl(url, { model });

      span.setAttribute('deepgram.duration_seconds', result.metadata.duration);
      span.setAttribute('deepgram.request_id', result.metadata.request_id);
      span.setAttribute('deepgram.confidence',
        result.results.channels[0].alternatives[0].confidence);

      return result;
    } catch (err: any) {
      span.recordException(err);
      span.setStatus({ code: 2, message: err.message });
      throw err;
    } finally {
      span.end();
    }
  });
}
```

### Step 4: Structured Logging with Pino

```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  base: {
    service: 'deepgram-integration',
    env: process.env.NODE_ENV,
  },
});

// Child loggers per component
const transcriptionLog = logger.child({ component: 'transcription' });
const metricsLog = logger.child({ component: 'metrics' });

// Usage:
transcriptionLog.info({
  action: 'transcribe',
  model: 'nova-3',
  audioUrl: url.substring(0, 100),
  requestId: result.metadata.request_id,
  duration: result.metadata.duration,
  confidence: result.results.channels[0].alternatives[0].confidence,
}, 'Transcription completed');

transcriptionLog.error({
  action: 'transcribe',
  model: 'nova-3',
  error: err.message,
  statusCode: err.status,
}, 'Transcription failed');
```

### Step 5: Grafana Dashboard Panels

```json
{
  "title": "Deepgram Observability",
  "panels": [
    {
      "title": "Request Rate",
      "type": "timeseries",
      "targets": [{ "expr": "rate(deepgram_requests_total[5m])" }]
    },
    {
      "title": "P95 Latency",
      "type": "gauge",
      "targets": [{ "expr": "histogram_quantile(0.95, rate(deepgram_request_duration_seconds_bucket[5m]))" }]
    },
    {
      "title": "Error Rate %",
      "type": "stat",
      "targets": [{ "expr": "rate(deepgram_requests_total{status='error'}[5m]) / rate(deepgram_requests_total[5m]) * 100" }]
    },
    {
      "title": "Audio Processed (min/hr)",
      "type": "timeseries",
      "targets": [{ "expr": "rate(deepgram_audio_processed_seconds_total[1h]) / 60" }]
    },
    {
      "title": "Estimated Daily Cost",
      "type": "stat",
      "targets": [{ "expr": "increase(deepgram_estimated_cost_dollars_total[24h])" }]
    },
    {
      "title": "Active WebSocket Connections",
      "type": "gauge",
      "targets": [{ "expr": "deepgram_active_websocket_connections" }]
    }
  ]
}
```

### Step 6: AlertManager Rules

```yaml
groups:
  - name: deepgram-alerts
    rules:
      - alert: DeepgramHighErrorRate
        expr: >
          rate(deepgram_requests_total{status="error"}[5m])
          / rate(deepgram_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Deepgram error rate > 5% for 5 minutes"

      - alert: DeepgramHighLatency
        expr: >
          histogram_quantile(0.95,
            rate(deepgram_request_duration_seconds_bucket[5m])
          ) > 10
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Deepgram P95 latency > 10 seconds"

      - alert: DeepgramRateLimited
        expr: rate(deepgram_rate_limit_hits_total[1h]) > 10
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "Deepgram rate limit hits > 10/hour"

      - alert: DeepgramCostSpike
        expr: >
          increase(deepgram_estimated_cost_dollars_total[24h])
          > 2 * increase(deepgram_estimated_cost_dollars_total[24h] offset 1d)
        for: 30m
        labels: { severity: warning }
        annotations:
          summary: "Deepgram daily cost > 2x yesterday"

      - alert: DeepgramZeroRequests
        expr: rate(deepgram_requests_total[15m]) == 0
        for: 15m
        labels: { severity: warning }
        annotations:
          summary: "No Deepgram requests for 15 minutes"
```

## Metrics Endpoint

```typescript
import express from 'express';
const app = express();

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

## Output
- Prometheus metrics (6 metrics covering requests, latency, usage, cost)
- Instrumented Deepgram client with auto-tracking
- OpenTelemetry distributed tracing with custom spans
- Structured JSON logging (Pino)
- Grafana dashboard panel definitions
- AlertManager rules (5 alerts)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Metrics not appearing | Registry not exported | Check `/metrics` endpoint |
| High cardinality | Too many label values | Limit labels to known set |
| Alert storms | Thresholds too sensitive | Add `for:` duration, tune values |
| Missing traces | OTEL exporter not configured | Set `OTEL_EXPORTER_OTLP_ENDPOINT` |

## Resources
- [Prometheus Client](https://github.com/siimon/prom-client)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/languages/js/)
- [Pino Logger](https://getpino.io/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
