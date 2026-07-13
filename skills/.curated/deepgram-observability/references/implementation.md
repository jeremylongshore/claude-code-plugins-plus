# Deepgram Observability - Implementation Details

## Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge, collectDefaultMetrics } from 'prom-client';

export const registry = new Registry();
collectDefaultMetrics({ register: registry });

export const transcriptionRequests = new Counter({
  name: 'deepgram_transcription_requests_total', help: 'Total transcription requests',
  labelNames: ['status', 'model', 'type'], registers: [registry],
});

export const transcriptionLatency = new Histogram({
  name: 'deepgram_transcription_latency_seconds', help: 'Transcription latency',
  labelNames: ['model', 'type'], buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60, 120], registers: [registry],
});

export const audioProcessed = new Counter({
  name: 'deepgram_audio_processed_seconds_total', help: 'Total audio processed',
  labelNames: ['model'], registers: [registry],
});

export const activeConnections = new Gauge({
  name: 'deepgram_active_connections', help: 'Active Deepgram connections',
  labelNames: ['type'], registers: [registry],
});

export const rateLimitHits = new Counter({
  name: 'deepgram_rate_limit_hits_total', help: 'Rate limit responses', registers: [registry],
});

export const estimatedCost = new Counter({
  name: 'deepgram_estimated_cost_dollars', help: 'Estimated cost in dollars',
  labelNames: ['model'], registers: [registry],
});
```

## Instrumented Transcription Client

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('deepgram-client');
const modelCosts: Record<string, number> = { 'nova-2': 0.0043, 'nova': 0.0043, 'base': 0.0048 };

export class InstrumentedDeepgramClient {
  private client: DeepgramClient;
  constructor(apiKey: string) { this.client = createClient(apiKey); }

  async transcribeUrl(url: string, options: { model?: string } = {}) {
    const model = options.model || 'nova-2';
    const startTime = Date.now();

    return tracer.startActiveSpan('deepgram.transcribe', async (span) => {
      span.setAttribute('deepgram.model', model);
      span.setAttribute('deepgram.audio_url', url);
      try {
        const { result, error } = await this.client.listen.prerecorded.transcribeUrl({ url }, { model, smart_format: true });
        const duration = (Date.now() - startTime) / 1000;

        if (error) {
          transcriptionRequests.labels('error', model, 'prerecorded').inc();
          span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
          throw error;
        }

        transcriptionRequests.labels('success', model, 'prerecorded').inc();
        transcriptionLatency.labels(model, 'prerecorded').observe(duration);
        const audioDuration = result.metadata.duration;
        audioProcessed.labels(model).inc(audioDuration);
        const cost = (audioDuration / 60) * (modelCosts[model] || 0.0043);
        estimatedCost.labels(model).inc(cost);
        span.setAttribute('deepgram.request_id', result.metadata.request_id);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (err) {
        transcriptionRequests.labels('exception', model, 'prerecorded').inc();
        span.setStatus({ code: SpanStatusCode.ERROR, message: err instanceof Error ? err.message : 'Unknown' });
        throw err;
      } finally { span.end(); }
    });
  }
}
```

## OpenTelemetry Configuration

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'deepgram-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.VERSION || '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV || 'development',
  }),
  traceExporter: new OTLPTraceExporter({ url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317' }),
  instrumentations: [getNodeAutoInstrumentations({ '@opentelemetry/instrumentation-http': { ignoreIncomingPaths: ['/health', '/metrics'] } })],
});

export function initTracing(): void {
  sdk.start();
  process.on('SIGTERM', () => { sdk.shutdown().finally(() => process.exit(0)); });
}
```

## Structured Logging

```typescript
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: { level: (label) => ({ level: label }) },
  base: { service: 'deepgram-service', version: process.env.VERSION || '1.0.0', environment: process.env.NODE_ENV || 'development' },
  timestamp: pino.stdTimeFunctions.isoTime,
});

export const transcriptionLogger = logger.child({ component: 'transcription' });
export const metricsLogger = logger.child({ component: 'metrics' });
```

## Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Deepgram Transcription Service",
    "panels": [
      { "title": "Request Rate", "expr": "sum(rate(deepgram_transcription_requests_total[5m])) by (status)" },
      { "title": "Latency P95", "expr": "histogram_quantile(0.95, sum(rate(deepgram_transcription_latency_seconds_bucket[5m])) by (le, model))" },
      { "title": "Audio Processed/hr", "expr": "sum(increase(deepgram_audio_processed_seconds_total[1h]))/60" },
      { "title": "Error Rate", "expr": "sum(rate(deepgram_transcription_requests_total{status='error'}[5m])) / sum(rate(deepgram_transcription_requests_total[5m])) * 100" },
      { "title": "Estimated Cost Today", "expr": "sum(increase(deepgram_estimated_cost_dollars[24h]))" },
      { "title": "Active Connections", "expr": "deepgram_active_connections" }
    ]
  }
}
```

## AlertManager Rules

```yaml
groups:
  - name: deepgram-alerts
    rules:
      - alert: DeepgramHighErrorRate
        expr: sum(rate(deepgram_transcription_requests_total{status="error"}[5m])) / sum(rate(deepgram_transcription_requests_total[5m])) > 0.05
        for: 5m
        labels: { severity: critical }
      - alert: DeepgramHighLatency
        expr: histogram_quantile(0.95, sum(rate(deepgram_transcription_latency_seconds_bucket[5m])) by (le)) > 30
        for: 5m
        labels: { severity: warning }
      - alert: DeepgramRateLimited
        expr: increase(deepgram_rate_limit_hits_total[1h]) > 10
        labels: { severity: warning }
      - alert: DeepgramCostSpike
        expr: sum(increase(deepgram_estimated_cost_dollars[1h])) > sum(increase(deepgram_estimated_cost_dollars[1h] offset 1d)) * 2
        for: 30m
        labels: { severity: warning }
      - alert: DeepgramNoRequests
        expr: sum(rate(deepgram_transcription_requests_total[15m])) == 0 and sum(deepgram_transcription_requests_total) > 0
        for: 15m
        labels: { severity: warning }
```

## Health Check Endpoint

```typescript
import express from 'express';

const router = express.Router();

router.get('/health', async (req, res) => {
  const health = { status: 'healthy' as const, timestamp: new Date().toISOString(), checks: {} as Record<string, any> };
  const startTime = Date.now();
  try {
    const client = createClient(process.env.DEEPGRAM_API_KEY!);
    const { error } = await client.manage.getProjects();
    health.checks.deepgram = { status: error ? 'fail' : 'pass', latency: Date.now() - startTime, message: error?.message };
  } catch (err) {
    health.checks.deepgram = { status: 'fail', latency: Date.now() - startTime };
  }
  const failedChecks = Object.values(health.checks).filter((c: any) => c.status === 'fail');
  const statusCode = failedChecks.length > 0 ? 503 : 200;
  res.status(statusCode).json(health);
});

router.get('/metrics', async (req, res) => { res.set('Content-Type', 'text/plain'); res.send(await registry.metrics()); });
export default router;
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
