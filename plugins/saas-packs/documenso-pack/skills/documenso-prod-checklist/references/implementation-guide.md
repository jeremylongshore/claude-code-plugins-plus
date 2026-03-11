# Documenso Production Checklist - Implementation Guide

## Pre-Deployment Checklist

### Configuration
- [ ] Production API key generated (separate from staging)
- [ ] API key stored in secure vault (not in code)
- [ ] Environment variables configured in deployment platform
- [ ] Webhook endpoint URL uses HTTPS
- [ ] Webhook secret configured
- [ ] Base URL correct for environment

### Code Quality
- [ ] All tests passing (`npm test`)
- [ ] No hardcoded credentials or API keys
- [ ] Error handling covers all Documenso error types
- [ ] Rate limiting/backoff implemented
- [ ] Logging is production-appropriate (no sensitive data)
- [ ] TypeScript strict mode enabled

### Security
- [ ] API keys have minimal required permissions
- [ ] Webhook signature verification implemented
- [ ] Input validation on all user inputs
- [ ] File upload validation (type, size)
- [ ] Signing URLs not exposed in logs
- [ ] Audit logging enabled

### Infrastructure
- [ ] Health check endpoint includes Documenso connectivity
- [ ] Monitoring/alerting configured for errors
- [ ] Circuit breaker pattern implemented
- [ ] Graceful degradation for Documenso outages

### Documentation
- [ ] Incident runbook created
- [ ] API key rotation procedure documented
- [ ] Rollback procedure documented
- [ ] On-call escalation path defined

## Deployment Procedure

### Step 1: Pre-flight Checks

```bash
# Verify staging health
curl -f https://staging.yourapp.com/health

# Verify Documenso API status
curl -s https://status.documenso.com/api/v2/status.json | jq '.status'

# Run final test suite
npm run test:integration
```

### Step 2: Deploy with Gradual Rollout

```bash
# Deploy to production (canary - 10%)
kubectl apply -f k8s/production.yaml
kubectl set image deployment/signing-service app=image:new --record
kubectl rollout pause deployment/signing-service

# Monitor canary for 10 minutes
echo "Monitoring canary deployment..."
sleep 600

# Check error rates
kubectl logs -l app=signing-service --since=10m | grep -c "ERROR"

# If healthy, continue to 50%
kubectl rollout resume deployment/signing-service
kubectl rollout pause deployment/signing-service
sleep 300

# Complete rollout to 100%
kubectl rollout resume deployment/signing-service
kubectl rollout status deployment/signing-service
```

### Step 3: Health Check Implementation

```typescript
// src/health.ts
import { getDocumensoClient } from "./documenso/client";

interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  checks: {
    documenso: {
      connected: boolean;
      latencyMs: number;
      error?: string;
    };
    database?: {
      connected: boolean;
      latencyMs: number;
    };
  };
  version: string;
}

export async function healthCheck(): Promise<HealthStatus> {
  const checks: HealthStatus["checks"] = {
    documenso: { connected: false, latencyMs: 0 },
  };

  // Test Documenso connectivity
  const docStart = Date.now();
  try {
    const client = getDocumensoClient();
    await client.documents.findV0({ perPage: 1 });
    checks.documenso = {
      connected: true,
      latencyMs: Date.now() - docStart,
    };
  } catch (error: any) {
    checks.documenso = {
      connected: false,
      latencyMs: Date.now() - docStart,
      error: error.message,
    };
  }

  // Determine overall status
  const allHealthy = checks.documenso.connected;
  const anyFailed = !checks.documenso.connected;

  return {
    status: allHealthy ? "healthy" : anyFailed ? "unhealthy" : "degraded",
    checks,
    version: process.env.APP_VERSION ?? "unknown",
  };
}

// Express endpoint
app.get("/health", async (req, res) => {
  const health = await healthCheck();
  const statusCode = health.status === "unhealthy" ? 503 : 200;
  res.status(statusCode).json(health);
});
```

### Step 4: Monitoring Setup

```typescript
// Monitor key metrics
interface DocumensoMetrics {
  requestsTotal: number;
  errorsTotal: number;
  latencyP50Ms: number;
  latencyP99Ms: number;
  rateLimitHits: number;
}

class MetricsCollector {
  private latencies: number[] = [];
  private errors = 0;
  private requests = 0;
  private rateLimits = 0;

  recordRequest(latencyMs: number, success: boolean): void {
    this.requests++;
    this.latencies.push(latencyMs);
    if (!success) this.errors++;

    // Keep last 1000 latencies
    if (this.latencies.length > 1000) {
      this.latencies = this.latencies.slice(-1000);
    }
  }

  recordRateLimit(): void {
    this.rateLimits++;
  }

  getMetrics(): DocumensoMetrics {
    const sorted = [...this.latencies].sort((a, b) => a - b);
    return {
      requestsTotal: this.requests,
      errorsTotal: this.errors,
      latencyP50Ms: sorted[Math.floor(sorted.length * 0.5)] ?? 0,
      latencyP99Ms: sorted[Math.floor(sorted.length * 0.99)] ?? 0,
      rateLimitHits: this.rateLimits,
    };
  }
}

// Export to Prometheus/Datadog/etc
app.get("/metrics", (req, res) => {
  const metrics = metricsCollector.getMetrics();
  res.json(metrics);
});
```

### Step 5: Alert Configuration

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| API Down | 5xx errors > 10/min | P1 | Page on-call |
| High Latency | p99 > 5000ms | P2 | Investigate |
| Rate Limited | 429 errors > 5/min | P2 | Reduce throughput |
| Auth Failures | 401/403 errors > 0 | P1 | Check API key |
| Webhook Failures | 4xx/5xx on webhook | P2 | Check endpoint |

```yaml
# Example Datadog alert config
alerts:
  - name: documenso_api_errors
    query: sum(last_5m):sum:documenso.errors{env:production} > 10
    message: "High Documenso API error rate"
    priority: P1

  - name: documenso_high_latency
    query: avg(last_5m):avg:documenso.latency.p99{env:production} > 5000
    message: "Documenso API latency elevated"
    priority: P2

  - name: documenso_rate_limits
    query: sum(last_5m):sum:documenso.rate_limits{env:production} > 5
    message: "Hitting Documenso rate limits"
    priority: P2
```

## Rollback Procedure

### Immediate Rollback

```bash
# Kubernetes rollback
kubectl rollout undo deployment/signing-service
kubectl rollout status deployment/signing-service

# Verify rollback
kubectl get pods -l app=signing-service
curl -f https://yourapp.com/health
```

### Feature Flag Rollback

```typescript
// Use feature flags to disable Documenso features
const documensoEnabled = await featureFlags.isEnabled("documenso_signing");

if (!documensoEnabled) {
  throw new Error("Document signing temporarily unavailable");
}
```

## Post-Deployment Verification

```bash
# Run smoke tests
npm run test:smoke

# Verify document creation
curl -X POST https://yourapp.com/api/documents \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Document"}'

# Verify webhook delivery
# Check webhook logs in Documenso dashboard

# Monitor for 30 minutes
watch -n 30 'curl -s https://yourapp.com/health | jq'
```
