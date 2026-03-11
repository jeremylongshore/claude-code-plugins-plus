# OpenEvidence Observability - Implementation Details

## Prometheus Metrics
Full metric definitions: requestCounter, requestDuration, errorCounter, cacheHits, cacheMisses, rateLimitRemaining, deepConsultActive, deepConsultDuration, confidenceScore.

## Instrumented Client Wrapper
```typescript
export class InstrumentedOpenEvidenceClient {
  async query(request: ClinicalQueryRequest): Promise<ClinicalQueryResponse> {
    return tracer.startActiveSpan('openevidence.query', async (span) => {
      const timer = requestDuration.startTimer({ method: 'query', specialty: request.context.specialty });
      // Check cache, make API request, update metrics, record confidence
      // ...
    });
  }
}
```

## Distributed Tracing (OpenTelemetry)
```typescript
export function initTracing(): void {
  const sdk = new NodeSDK({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'clinical-evidence-api',
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV,
    }),
    traceExporter: new TraceExporter(),
    instrumentations: [new HttpInstrumentation(), new ExpressInstrumentation()],
  });
  sdk.start();
}
```

## Structured Logging
```typescript
export const logger = pino({
  name: 'clinical-evidence-api',
  redact: { paths: ['patient.*', 'patientId', 'mrn', '*.ssn'], censor: '[REDACTED]' },
});
```

## Alert Rules (Prometheus)
- OpenEvidenceHighErrorRate: > 5% error rate for 5m
- OpenEvidenceCriticalErrorRate: > 20% error rate for 2m
- OpenEvidenceHighLatency: P95 > 15s for 5m
- OpenEvidenceLowCacheHitRate: < 50% for 30m
- OpenEvidenceRateLimitWarning: < 10 remaining for 1m
- OpenEvidenceDown: no health checks for 1m

## Grafana Dashboard
Panels: Request Rate, Error Rate gauge, Latency heatmap, Cache Hit Rate timeseries, Rate Limit Usage gauge, Confidence Score histogram.
