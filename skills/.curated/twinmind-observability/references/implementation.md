# TwinMind Observability - Detailed Implementation

## Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

export const transcriptionCounter = new Counter({
  name: 'twinmind_transcriptions_total',
  help: 'Total TwinMind transcription requests',
  labelNames: ['status', 'model', 'language'],
  registers: [registry],
});

export const transcriptionDuration = new Histogram({
  name: 'twinmind_transcription_duration_seconds',
  help: 'TwinMind transcription processing duration',
  labelNames: ['model'],
  buckets: [1, 5, 10, 30, 60, 120, 300, 600],
  registers: [registry],
});

export const apiLatency = new Histogram({
  name: 'twinmind_api_latency_seconds',
  help: 'TwinMind API request latency',
  labelNames: ['method', 'endpoint'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

export const errorCounter = new Counter({
  name: 'twinmind_errors_total',
  help: 'TwinMind errors by type',
  labelNames: ['error_type', 'operation'],
  registers: [registry],
});

export const rateLimitRemaining = new Gauge({
  name: 'twinmind_rate_limit_remaining',
  help: 'Remaining rate limit quota',
  labelNames: ['endpoint'],
  registers: [registry],
});

export const aiTokensUsed = new Counter({
  name: 'twinmind_ai_tokens_used',
  help: 'AI tokens consumed',
  labelNames: ['operation'],
  registers: [registry],
});

export { registry };
```

## Instrumented Client

```typescript
export class InstrumentedTwinMindClient {
  private client: TwinMindClient;

  async transcribe(audioUrl: string, options?: TranscriptionOptions): Promise<Transcript> {
    const timer = transcriptionDuration.startTimer({ model: options?.model || 'ear-3' });
    try {
      const result = await this.client.transcribe(audioUrl, options);
      transcriptionCounter.inc({ status: 'success', model: options?.model || 'ear-3', language: result.language });
      audioHoursProcessed.inc({ model: options?.model || 'ear-3' }, result.duration_seconds / 3600);
      return result;
    } catch (error: any) {
      transcriptionCounter.inc({ status: 'error', model: options?.model || 'ear-3', language: 'unknown' });
      errorCounter.inc({ error_type: error.code || 'unknown', operation: 'transcribe' });
      throw error;
    } finally {
      timer();
    }
  }
}
```

## OpenTelemetry Tracing

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';

const sdk = new NodeSDK({
  resource: new Resource({
    'service.name': 'twinmind-integration',
    'service.version': process.env.npm_package_version,
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces',
  }),
});
sdk.start();

export const tracer = trace.getTracer('twinmind-client');

export async function tracedOperation<T>(
  operationName: string,
  operation: () => Promise<T>,
  attributes?: Record<string, string | number>
): Promise<T> {
  return tracer.startActiveSpan(
    `twinmind.${operationName}`,
    { kind: SpanKind.CLIENT, attributes },
    async (span) => {
      try {
        const result = await operation();
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error: any) {
        span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
        span.recordException(error);
        throw error;
      } finally {
        span.end();
      }
    }
  );
}
```

## Structured Logging

```typescript
import pino from 'pino';

export const logger = pino({
  name: 'twinmind',
  level: process.env.LOG_LEVEL || 'info',
  redact: ['apiKey', 'authorization', 'password'],
});

export function logTwinMindOperation(operation: string, data: Record<string, any>, duration?: number): void {
  logger.info({ service: 'twinmind', operation, duration_ms: duration, ...data });
}

export function logTwinMindError(operation: string, error: Error, context?: Record<string, any>): void {
  logger.error({ service: 'twinmind', operation, error: { name: error.name, message: error.message, stack: error.stack }, ...context });
}
```

## AlertManager Rules

```yaml
groups:
  - name: twinmind_alerts
    rules:
      - alert: TwinMindHighErrorRate
        expr: rate(twinmind_errors_total[5m]) / rate(twinmind_api_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: warning, service: twinmind }
        annotations: { summary: "TwinMind error rate > 5%" }

      - alert: TwinMindHighLatency
        expr: histogram_quantile(0.95, rate(twinmind_api_latency_seconds_bucket[5m])) > 5
        for: 5m
        labels: { severity: warning, service: twinmind }
        annotations: { summary: "TwinMind P95 latency > 5s" }

      - alert: TwinMindRateLimitApproaching
        expr: twinmind_rate_limit_remaining < 10
        for: 1m
        labels: { severity: warning, service: twinmind }
        annotations: { summary: "TwinMind rate limit approaching" }

      - alert: TwinMindAPIDown
        expr: up{job="twinmind"} == 0
        for: 1m
        labels: { severity: critical, service: twinmind }
        annotations: { summary: "TwinMind integration is down" }

      - alert: TwinMindHighTokenUsage
        expr: increase(twinmind_ai_tokens_used[24h]) > 1500000
        for: 5m
        labels: { severity: warning, service: twinmind }
        annotations: { summary: "High TwinMind token usage (>1.5M in 24h)" }
```

## Grafana Dashboard

```json
{
  "dashboard": {
    "title": "TwinMind Integration",
    "panels": [
      { "title": "Transcription Rate", "type": "graph", "targets": [{ "expr": "rate(twinmind_transcriptions_total[5m])", "legendFormat": "{{status}}" }] },
      { "title": "API Latency (P50/P95/P99)", "type": "graph", "targets": [
        { "expr": "histogram_quantile(0.5, rate(twinmind_api_latency_seconds_bucket[5m]))", "legendFormat": "P50" },
        { "expr": "histogram_quantile(0.95, rate(twinmind_api_latency_seconds_bucket[5m]))", "legendFormat": "P95" },
        { "expr": "histogram_quantile(0.99, rate(twinmind_api_latency_seconds_bucket[5m]))", "legendFormat": "P99" }
      ]},
      { "title": "Error Rate", "type": "graph", "targets": [{ "expr": "rate(twinmind_errors_total[5m])", "legendFormat": "{{error_type}}" }] },
      { "title": "Rate Limit Remaining", "type": "gauge", "targets": [{ "expr": "twinmind_rate_limit_remaining" }] },
      { "title": "AI Tokens Used (24h)", "type": "stat", "targets": [{ "expr": "increase(twinmind_ai_tokens_used[24h])" }] }
    ]
  }
}
```

## Metrics Endpoint

```typescript
import express from 'express';
import { registry } from '../observability/metrics';

const router = express.Router();
router.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
export default router;
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
