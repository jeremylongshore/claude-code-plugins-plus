---
name: cohere-prod-checklist
description: |
  Execute Cohere production deployment checklist and rollback procedures.
  Use when deploying Cohere integrations to production, preparing for launch,
  or implementing go-live procedures for Cohere-powered apps.
  Trigger with phrases like "cohere production", "deploy cohere",
  "cohere go-live", "cohere launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Production Checklist

## Overview
Complete go-live checklist for deploying Cohere API v2 integrations to production with safety gates, health checks, and rollback procedures.

## Prerequisites
- Staging environment tested and verified
- Production API key (not trial) from [dashboard.cohere.com](https://dashboard.cohere.com)
- Deployment pipeline configured
- Monitoring and alerting ready

## Checklist

### API & Authentication
- [ ] Using **production** API key (not trial — trial is rate-limited to 20 calls/min)
- [ ] `CO_API_KEY` stored in secret manager (Vault, AWS Secrets Manager, GCP Secret Manager)
- [ ] Key rotation procedure documented and tested
- [ ] Billing alerts configured at dashboard.cohere.com
- [ ] Using API v2 endpoints (`CohereClientV2`, not `CohereClient`)

### Code Quality
- [ ] All API calls specify `model` parameter explicitly
- [ ] `embeddingTypes` set for all Embed calls (required for v3+)
- [ ] `inputType` set for all Embed calls (required for v3+)
- [ ] Error handling catches `CohereError` and `CohereTimeoutError`
- [ ] Retry logic with exponential backoff for 429 and 5xx
- [ ] No hardcoded API keys in source code
- [ ] Request/response logging excludes API keys and PII

### Model Selection
- [ ] Correct model IDs used (not deprecated names):

| Use Case | Recommended Model | Fallback |
|----------|------------------|----------|
| Chat/generation | `command-a-03-2025` | `command-r-plus-08-2024` |
| Lightweight chat | `command-r7b-12-2024` | `command-r-08-2024` |
| Embeddings | `embed-v4.0` | `embed-english-v3.0` |
| Reranking | `rerank-v3.5` | `rerank-english-v3.0` |

### Performance
- [ ] Embed calls batched (up to 96 texts per request)
- [ ] Rerank calls limited to 1000 documents per request
- [ ] Streaming enabled for user-facing chat (`chatStream`)
- [ ] Connection pooling / keep-alive configured
- [ ] Response caching for repeated embed/rerank queries
- [ ] `maxTokens` set to prevent runaway generation costs

### Health Check Endpoint

```typescript
// /api/health
import { CohereClientV2, CohereError } from 'cohere-ai';

const cohere = new CohereClientV2();

export async function GET() {
  const start = Date.now();
  let cohereStatus: 'healthy' | 'degraded' | 'down' = 'down';

  try {
    // Cheapest possible health check — minimal chat
    await cohere.chat({
      model: 'command-r7b-12-2024',
      messages: [{ role: 'user', content: 'ping' }],
      maxTokens: 1,
    });
    cohereStatus = 'healthy';
  } catch (err) {
    if (err instanceof CohereError && err.statusCode === 429) {
      cohereStatus = 'degraded'; // Rate limited but reachable
    }
  }

  return Response.json({
    status: cohereStatus === 'healthy' ? 'ok' : 'degraded',
    cohere: {
      status: cohereStatus,
      latencyMs: Date.now() - start,
    },
    timestamp: new Date().toISOString(),
  });
}
```

### Circuit Breaker

```typescript
class CohereCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private threshold = 5,
    private resetMs = 60_000
  ) {}

  async call<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetMs) {
        this.state = 'half-open';
      } else if (fallback) {
        return fallback();
      } else {
        throw new Error('Cohere circuit breaker is open');
      }
    }

    try {
      const result = await fn();
      this.failures = 0;
      this.state = 'closed';
      return result;
    } catch (err) {
      this.failures++;
      this.lastFailure = Date.now();

      if (this.failures >= this.threshold) {
        this.state = 'open';
        console.error(`Cohere circuit breaker OPEN after ${this.failures} failures`);
      }
      throw err;
    }
  }
}

const breaker = new CohereCircuitBreaker();
```

### Gradual Rollout

```bash
# Pre-flight
curl -sf https://staging.example.com/api/health | jq '.cohere'
curl -s https://status.cohere.com/api/v2/status.json | jq '.status'

# Deploy with canary (10% traffic)
kubectl apply -f k8s/production.yaml
kubectl rollout pause deployment/app

# Monitor for 10 minutes: error rate, latency, 429s
# Check: No increase in CohereError rate
# Check: P95 latency < 5s for chat, < 500ms for embed/rerank

# Proceed to 100%
kubectl rollout resume deployment/app
kubectl rollout status deployment/app
```

### Monitoring Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| Cohere unreachable | Health check fails 3x | P1 |
| High error rate | 5xx > 5% of requests/5min | P1 |
| Rate limited | 429 > 10/min | P2 |
| High latency | Chat P95 > 10s | P2 |
| Auth failure | Any 401 response | P1 |
| Budget exceeded | Daily token cost > threshold | P2 |

### Rollback

```bash
# Immediate rollback
kubectl rollout undo deployment/app
kubectl rollout status deployment/app

# Verify rollback
curl -sf https://api.example.com/api/health | jq '.cohere'
```

## Output
- Production-ready Cohere integration with health checks
- Circuit breaker preventing cascade failures
- Monitoring alerts for Cohere-specific error conditions
- Documented rollback procedure

## Resources
- [Cohere Going Live Guide](https://docs.cohere.com/docs/going-live)
- [Cohere Status Page](https://status.cohere.com)
- [Cohere Pricing](https://cohere.com/pricing)

## Next Steps
For version upgrades, see `cohere-upgrade-migration`.
