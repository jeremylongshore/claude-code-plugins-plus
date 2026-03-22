---
name: mistral-prod-checklist
description: |
  Execute Mistral AI production deployment checklist and rollback procedures.
  Use when deploying Mistral AI integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "mistral production", "deploy mistral",
  "mistral go-live", "mistral launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, deployment]

---
# Mistral AI Production Checklist

## Overview
Complete checklist for deploying Mistral AI integrations to production. Covers credential management, code quality gates, health endpoints, circuit breaker resilience, gradual rollout, and rollback procedures.

## Prerequisites
- Staging environment tested and verified
- Production API keys from La Plateforme
- Deployment pipeline (CI/CD) configured
- Monitoring and alerting ready (see `mistral-observability`)

## Instructions

### Step 1: Pre-Deployment Verification

**Credentials**
- [ ] Production API key stored in secret manager (never in env files or code)
- [ ] Key tested with `curl -H "Authorization: Bearer $KEY" https://api.mistral.ai/v1/models`
- [ ] Key has appropriate model access scope
- [ ] Fallback key available for rotation

**Code Quality**
- [ ] `npm run typecheck` passes
- [ ] `npm test` passes (unit + integration)
- [ ] No hardcoded keys: `grep -r "MISTRAL_API_KEY\|sk-" src/ --include="*.ts"`
- [ ] Error handling covers 401, 429, 500+ status codes
- [ ] Rate limiting/backoff implemented
- [ ] Logging excludes message content and API keys

**Model Configuration**
- [ ] Using versioned model IDs or `-latest` aliases intentionally
- [ ] `maxTokens` set to prevent runaway costs
- [ ] `temperature` set appropriately (0 for deterministic, 0.7 for creative)
- [ ] Token budget alerts configured

### Step 2: Health Check Endpoint

```typescript
import { Mistral } from '@mistralai/mistralai';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  provider: 'mistral';
  latencyMs: number;
  model?: string;
  error?: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  const start = performance.now();
  try {
    const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });
    const models = await client.models.list();
    const latencyMs = Math.round(performance.now() - start);

    return {
      status: latencyMs > 5000 ? 'degraded' : 'healthy',
      provider: 'mistral',
      latencyMs,
      model: models.data?.[0]?.id,
    };
  } catch (error: any) {
    return {
      status: 'unhealthy',
      provider: 'mistral',
      latencyMs: Math.round(performance.now() - start),
      error: error.message,
    };
  }
}

// Express route
app.get('/health', async (req, res) => {
  const health = await checkHealth();
  res.status(health.status === 'unhealthy' ? 503 : 200).json(health);
});
```

### Step 3: Circuit Breaker

```typescript
class MistralCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private readonly threshold = 5;
  private readonly resetMs = 60_000;

  async execute<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetMs) {
        this.state = 'half-open';
      } else if (fallback) {
        return fallback();
      } else {
        throw new Error('Circuit breaker open — Mistral unavailable');
      }
    }

    try {
      const result = await fn();
      if (this.state === 'half-open') {
        this.state = 'closed';
        this.failures = 0;
      }
      return result;
    } catch (error: any) {
      if (error.status >= 500 || error.status === 429) {
        this.failures++;
        this.lastFailure = Date.now();
        if (this.failures >= this.threshold) {
          this.state = 'open';
        }
      }
      throw error;
    }
  }
}
```

### Step 4: Gradual Rollout

```bash
set -euo pipefail
# Deploy to canary (10% traffic)
kubectl set image deployment/mistral-app app=mistral-app:v2
kubectl rollout pause deployment/mistral-app

# Monitor for 10 minutes
echo "Monitoring canary..."
for i in $(seq 1 10); do
  curl -sf https://yourapp.com/health | jq '.services.mistral'
  sleep 60
done

# If healthy, resume rollout
kubectl rollout resume deployment/mistral-app
kubectl rollout status deployment/mistral-app
```

### Step 5: Post-Deployment Verification

```bash
set -euo pipefail
# 1. Health check
curl -sf https://yourapp.com/health | jq '.'

# 2. Smoke test
curl -X POST https://yourapp.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"ping"}]}' | jq '.choices[0].message.content'

# 3. Check error rate in monitoring
echo "Check Grafana/Datadog for mistral_errors_total"
```

### Step 6: Emergency Rollback

```bash
set -euo pipefail
# Immediate rollback
kubectl rollout undo deployment/mistral-app
kubectl rollout status deployment/mistral-app

# Verify
curl -sf https://yourapp.com/health | jq '.'
```

## Alert Configuration

| Alert | Condition | Severity |
|-------|-----------|----------|
| API Down | 5xx errors > 10/min | P1 |
| High Latency | p95 > 5000ms for 5min | P2 |
| Rate Limited | 429 errors > 5/min | P2 |
| Auth Failure | Any 401 error | P1 |
| Circuit Open | Breaker triggered | P2 |
| Cost Spike | Spend > $10/hour | P3 |

## Documentation Requirements
- [ ] Incident runbook created (see `mistral-incident-runbook`)
- [ ] Key rotation procedure documented
- [ ] Rollback procedure tested
- [ ] On-call escalation path defined
- [ ] API usage limits documented

## Output
- Production deployment with verified credentials
- Health check endpoint with latency monitoring
- Circuit breaker for graceful degradation
- Gradual rollout procedure
- Emergency rollback tested

## Error Handling
| Issue | Detection | Resolution |
|-------|-----------|------------|
| Deploy failure | `kubectl rollout status` | `kubectl rollout undo` |
| Health check 503 | Alert triggered | Check Mistral status, verify credentials |
| Circuit open | Metrics alert | Investigate availability, wait for reset |
| High error rate | Monitoring alert | Check logs, consider rollback |

## Resources
- [Mistral AI Status](https://status.mistral.ai/)
- [Mistral AI Console](https://console.mistral.ai/)
- [Rate Limits](https://docs.mistral.ai/deployment/ai-studio/tier/)
