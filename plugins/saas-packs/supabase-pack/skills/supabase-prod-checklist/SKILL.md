---
name: supabase-prod-checklist
description: |
  Supabase production deployment checklist and rollback procedures.
  Trigger phrases: "supabase production", "deploy supabase",
  "supabase go-live", "supabase launch checklist".
allowed-tools: Read, Bash, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Production Checklist

## Overview
Complete checklist for deploying Supabase integrations to production.

## Pre-Deployment Checklist

### Configuration
- [ ] Production API keys in secure vault (not .env files)
- [ ] Environment variables set in deployment platform
- [ ] API key scopes are minimal (least privilege)
- [ ] Webhook endpoints configured with HTTPS
- [ ] Webhook secrets stored securely

### Code Quality
- [ ] All tests passing (`npm test`)
- [ ] No hardcoded credentials
- [ ] Error handling covers all Supabase error types
- [ ] Rate limiting/backoff implemented
- [ ] Logging is production-appropriate (no sensitive data)

### Infrastructure
- [ ] Health check endpoint includes Supabase connectivity
- [ ] Monitoring/alerting configured for Supabase errors
- [ ] Circuit breaker pattern for external API calls
- [ ] Graceful degradation if Supabase is unavailable

### Documentation
- [ ] Runbook for Supabase-related incidents
- [ ] On-call knows how to check Supabase status
- [ ] API key rotation procedure documented

## Health Check Implementation

```typescript
async function healthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  supabase: { connected: boolean; latencyMs: number };
}> {
  const start = Date.now();
  try {
    await supabaseClient.ping();
    return {
      status: 'healthy',
      supabase: { connected: true, latencyMs: Date.now() - start },
    };
  } catch (error) {
    return {
      status: 'degraded',
      supabase: { connected: false, latencyMs: Date.now() - start },
    };
  }
}
```

## Deployment Procedure

### 1. Pre-flight Checks
```bash
# Verify staging environment works
curl -f https://staging.example.com/health

# Check Supabase API status
curl -s https://status.supabase.com
```

### 2. Deploy
```bash
# Deploy with feature flag disabled
kubectl apply -f k8s/production.yaml

# Verify pods are healthy
kubectl get pods -l app=supabase-integration

# Enable feature flag gradually (10% → 50% → 100%)
```

### 3. Validation
```bash
# Check logs for Supabase errors
kubectl logs -l app=supabase-integration --since=5m | grep -i error

# Verify metrics
curl localhost:9090/metrics | grep supabase
```

## Rollback Procedure

### Immediate Rollback
```bash
# 1. Disable feature flag
curl -X POST https://api.featureflags.com/disable/supabase-integration

# 2. Revert to previous deployment
kubectl rollout undo deployment/supabase-integration

# 3. Verify rollback
kubectl rollout status deployment/supabase-integration
```

### Post-Mortem Requirements
- [ ] Timeline of events
- [ ] Root cause identified
- [ ] Supabase API logs/request IDs collected
- [ ] Action items to prevent recurrence

## Monitoring Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| Supabase API Down | 5xx errors > 10/min | P1 |
| High Latency | p99 > 5000ms | P2 |
| Rate Limited | 429 errors > 5/min | P2 |
| Auth Failures | 401/403 errors > 0 | P1 |

## Next Steps
For version upgrades, see `supabase-upgrade-migration`.