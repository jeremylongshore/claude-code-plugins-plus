# Deepgram Production Checklist - Implementation Details

## Production Client

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';
import { getSecret } from './secrets';

interface ProductionConfig {
  timeout: number;
  retries: number;
  model: string;
}

const config: ProductionConfig = { timeout: 30000, retries: 3, model: 'nova-2' };
let client: DeepgramClient | null = null;

export async function getProductionClient(): Promise<DeepgramClient> {
  if (client) return client;
  const apiKey = await getSecret('DEEPGRAM_API_KEY');
  client = createClient(apiKey, { global: { fetch: { options: { timeout: config.timeout } } } });
  return client;
}

export async function transcribeProduction(audioUrl: string, options: { language?: string; callback?: string } = {}) {
  const startTime = Date.now();
  const requestId = crypto.randomUUID();
  logger.info('Starting transcription', { requestId, audioUrl: sanitize(audioUrl) });

  try {
    const deepgram = await getProductionClient();
    const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
      { url: audioUrl },
      { model: config.model, language: options.language || 'en', smart_format: true, punctuate: true, callback: options.callback }
    );

    const duration = Date.now() - startTime;
    metrics.histogram('deepgram.transcription.duration', duration);
    if (error) { metrics.increment('deepgram.transcription.error'); throw new Error(error.message); }
    metrics.increment('deepgram.transcription.success');
    logger.info('Transcription complete', { requestId, deepgramRequestId: result.metadata?.request_id, duration });
    return result;
  } catch (err) {
    metrics.increment('deepgram.transcription.exception');
    throw err;
  }
}

function sanitize(url: string): string {
  try { const parsed = new URL(url); return `${parsed.protocol}//${parsed.host}${parsed.pathname}`; }
  catch { return '[invalid-url]'; }
}
```

## Health Check Endpoint

```typescript
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: { deepgram: { status: 'pass' | 'fail'; latency?: number; message?: string } };
}

export async function healthCheck(): Promise<HealthStatus> {
  const checks: HealthStatus['checks'] = { deepgram: { status: 'fail' } };
  const startTime = Date.now();
  try {
    const client = await getProductionClient();
    const { error } = await client.manage.getProjects();
    checks.deepgram = { status: error ? 'fail' : 'pass', latency: Date.now() - startTime, message: error?.message };
  } catch (err) {
    checks.deepgram = { status: 'fail', latency: Date.now() - startTime, message: err instanceof Error ? err.message : 'Unknown' };
  }
  const allPassing = Object.values(checks).every(c => c.status === 'pass');
  return { status: allPassing ? 'healthy' : 'unhealthy', timestamp: new Date().toISOString(), checks };
}
```

## Production Metrics

```typescript
import { Counter, Histogram, Registry } from 'prom-client';

export const registry = new Registry();

export const transcriptionDuration = new Histogram({
  name: 'deepgram_transcription_duration_seconds', help: 'Duration of transcription requests',
  labelNames: ['status', 'model'], buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60], registers: [registry],
});

export const transcriptionTotal = new Counter({
  name: 'deepgram_transcription_total', help: 'Total number of transcription requests',
  labelNames: ['status', 'error_code'], registers: [registry],
});

export const audioProcessedSeconds = new Counter({
  name: 'deepgram_audio_processed_seconds_total', help: 'Total seconds of audio processed', registers: [registry],
});

export const rateLimitHits = new Counter({
  name: 'deepgram_rate_limit_hits_total', help: 'Number of rate limit errors', registers: [registry],
});
```

## Alerting Configuration

```yaml
groups:
  - name: deepgram
    rules:
      - alert: DeepgramHighErrorRate
        expr: sum(rate(deepgram_transcription_total{status="error"}[5m])) / sum(rate(deepgram_transcription_total[5m])) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: High Deepgram error rate
          description: Error rate is above 5% for the last 5 minutes

      - alert: DeepgramHighLatency
        expr: histogram_quantile(0.95, sum(rate(deepgram_transcription_duration_seconds_bucket[5m])) by (le)) > 10
        for: 5m
        labels: { severity: warning }

      - alert: DeepgramRateLimiting
        expr: increase(deepgram_rate_limit_hits_total[1h]) > 10
        for: 0m
        labels: { severity: warning }

      - alert: DeepgramDown
        expr: up{job="deepgram-health"} == 0
        for: 2m
        labels: { severity: critical }
```

## Go-Live Checklist Template

```markdown
## Pre-Launch (D-7)
- [ ] Load testing completed
- [ ] Security review passed
- [ ] Documentation finalized
- [ ] Team trained on runbooks

## Launch Day (D-0)
- [ ] Final smoke test passed
- [ ] Monitoring dashboards open
- [ ] On-call rotation confirmed
- [ ] Rollback plan ready

## Post-Launch (D+1)
- [ ] No critical alerts
- [ ] Error rate within SLA
- [ ] Performance metrics acceptable
- [ ] Customer feedback collected
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
