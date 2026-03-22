---
name: deepgram-prod-checklist
description: |
  Execute Deepgram production deployment checklist.
  Use when preparing for production launch, auditing production readiness,
  or verifying deployment configurations.
  Trigger: "deepgram production", "deploy deepgram", "deepgram prod checklist",
  "deepgram go-live", "production ready deepgram".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, deployment, production]

---
# Deepgram Production Checklist

## Overview
Comprehensive go-live checklist for Deepgram integrations. Covers singleton client, health checks, Prometheus metrics, alert rules, error handling, and a phased go-live timeline.

## Production Readiness Matrix

| Category | Item | Status |
|----------|------|--------|
| **Auth** | Production API key with scoped permissions | [ ] |
| **Auth** | Key stored in secret manager (not env file) | [ ] |
| **Auth** | Key rotation schedule (90-day) configured | [ ] |
| **Auth** | Fallback key provisioned and tested | [ ] |
| **Resilience** | Retry with exponential backoff on 429/5xx | [ ] |
| **Resilience** | Circuit breaker for cascade failure prevention | [ ] |
| **Resilience** | Request timeout set (30s pre-recorded, 10s TTS) | [ ] |
| **Resilience** | Graceful degradation when API unavailable | [ ] |
| **Performance** | Singleton client (not creating per-request) | [ ] |
| **Performance** | Concurrency limited (50-80% of plan limit) | [ ] |
| **Performance** | Audio preprocessed (16kHz mono for best results) | [ ] |
| **Performance** | Large files use callback URL (async) | [ ] |
| **Monitoring** | Health check endpoint testing Deepgram API | [ ] |
| **Monitoring** | Prometheus metrics: latency, error rate, usage | [ ] |
| **Monitoring** | Alerts: error rate >5%, latency >10s, circuit open | [ ] |
| **Security** | PII redaction enabled if handling sensitive audio | [ ] |
| **Security** | Audio URLs validated (HTTPS, no private IPs) | [ ] |
| **Security** | Audit logging on all operations | [ ] |

## Instructions

### Step 1: Production Singleton Client

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';

class ProductionDeepgram {
  private static client: DeepgramClient | null = null;

  static getClient(): DeepgramClient {
    if (!this.client) {
      const key = process.env.DEEPGRAM_API_KEY;
      if (!key) throw new Error('DEEPGRAM_API_KEY required for production');
      this.client = createClient(key);
    }
    return this.client;
  }

  // Force re-init (for key rotation)
  static reset() { this.client = null; }
}
```

### Step 2: Health Check Endpoint

```typescript
import express from 'express';
import { createClient } from '@deepgram/sdk';

const app = express();
const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

app.get('/health', async (req, res) => {
  const start = Date.now();
  try {
    // Test API connectivity by listing projects
    const { error } = await deepgram.manage.getProjects();
    const latency = Date.now() - start;

    if (error) {
      return res.status(503).json({
        status: 'unhealthy',
        deepgram: 'error',
        error: error.message,
        latency_ms: latency,
      });
    }

    res.json({
      status: 'healthy',
      deepgram: 'connected',
      latency_ms: latency,
      timestamp: new Date().toISOString(),
    });
  } catch (err: any) {
    res.status(503).json({
      status: 'unhealthy',
      deepgram: 'unreachable',
      error: err.message,
      latency_ms: Date.now() - start,
    });
  }
});
```

### Step 3: Prometheus Metrics

```typescript
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const registry = new Registry();

const transcriptionRequests = new Counter({
  name: 'deepgram_requests_total',
  help: 'Total Deepgram API requests',
  labelNames: ['method', 'model', 'status'],
  registers: [registry],
});

const transcriptionLatency = new Histogram({
  name: 'deepgram_latency_seconds',
  help: 'Deepgram API request latency',
  labelNames: ['method', 'model'],
  buckets: [0.5, 1, 2, 5, 10, 30],
  registers: [registry],
});

const audioProcessed = new Counter({
  name: 'deepgram_audio_seconds_total',
  help: 'Total audio seconds processed',
  labelNames: ['model'],
  registers: [registry],
});

const activeConnections = new Gauge({
  name: 'deepgram_active_connections',
  help: 'Active WebSocket connections',
  registers: [registry],
});

// Instrumented transcription
async function instrumentedTranscribe(url: string, model = 'nova-3') {
  const timer = transcriptionLatency.startTimer({ method: 'prerecorded', model });
  try {
    const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
      { url }, { model, smart_format: true }
    );
    timer();
    transcriptionRequests.inc({ method: 'prerecorded', model, status: error ? 'error' : 'ok' });
    if (result?.metadata?.duration) {
      audioProcessed.inc({ model }, result.metadata.duration);
    }
    if (error) throw error;
    return result;
  } catch (err) {
    timer();
    transcriptionRequests.inc({ method: 'prerecorded', model, status: 'error' });
    throw err;
  }
}

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

### Step 4: Alert Rules (Prometheus/AlertManager)

```yaml
groups:
  - name: deepgram
    rules:
      - alert: DeepgramHighErrorRate
        expr: rate(deepgram_requests_total{status="error"}[5m]) / rate(deepgram_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Deepgram error rate > 5%"

      - alert: DeepgramHighLatency
        expr: histogram_quantile(0.95, rate(deepgram_latency_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Deepgram P95 latency > 10s"

      - alert: DeepgramHealthCheckFailed
        expr: up{job="deepgram-service"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Deepgram health check failed for 2+ minutes"
```

### Step 5: Error Handling Wrapper

```typescript
async function safeTranscribe(url: string, options: Record<string, any> = {}) {
  const timeout = options.timeout ?? 30000;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const result = await Promise.race([
      instrumentedTranscribe(url, options.model ?? 'nova-3'),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Transcription timeout')), timeout)
      ),
    ]);
    clearTimeout(timeoutId);
    return result;
  } catch (err: any) {
    clearTimeout(timeoutId);
    // Log structured error
    console.error(JSON.stringify({
      level: 'error',
      service: 'deepgram',
      message: err.message,
      url: url.substring(0, 100),
      timestamp: new Date().toISOString(),
    }));
    throw err;
  }
}
```

### Step 6: Go-Live Timeline

| Phase | When | Actions |
|-------|------|---------|
| D-7 | 1 week before | Load test at 2x expected volume, security review |
| D-3 | 3 days before | Smoke test with production key, verify all alerts fire |
| D-1 | Day before | Confirm on-call rotation, validate dashboards |
| D-0 | Launch | Shadow mode (10% traffic), monitoring open |
| D+1 | Day after | Review error rate, latency, verify no anomalies |
| D+7 | 1 week after | Full traffic, tune alert thresholds based on baselines |

## Output
- Singleton client with reset capability
- Health check endpoint with latency reporting
- Prometheus metrics (requests, latency, audio, connections)
- AlertManager rules for error rate, latency, availability
- Timeout-safe transcription wrapper
- Phased go-live timeline

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Health check 503 | API key expired | Rotate key, check secret manager |
| Metrics not scraped | Wrong port/path | Verify Prometheus target config |
| Alert storms | Thresholds too tight | Add `for:` duration, tune values |
| Timeout on large files | Sync mode too slow | Switch to `callback` URL pattern |

## Resources
- [Deepgram Production Guide](https://developers.deepgram.com/docs/production-guide)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Deepgram SLA](https://deepgram.com/sla)
