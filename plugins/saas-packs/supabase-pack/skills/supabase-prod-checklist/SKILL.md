---
name: supabase-prod-checklist
description: |
  Deploy Supabase integrations to production with confidence.
  Use when preparing for production deployment or go-live.
  Trigger with phrases like "supabase production", "deploy supabase",
  "supabase go-live", "supabase launch checklist".
allowed-tools: Read, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Production Checklist

## Overview
Complete checklist for deploying Supabase integrations to production.

## Prerequisites
- All development and testing complete
- supabase-security-basics implemented
- Access to production environment
- Rollback plan documented

## Instructions

### Step 1: Configuration Verification
- [ ] Production API keys in secure vault (not .env files)
- [ ] Environment variables set in deployment platform
- [ ] API key scopes are minimal (least privilege)
- [ ] Webhook endpoints configured with HTTPS
- [ ] Webhook secrets stored securely

### Step 2: Code Quality Verification
- [ ] All tests passing (`npm test`)
- [ ] No hardcoded credentials
- [ ] Error handling covers all Supabase error types
- [ ] Rate limiting/backoff implemented
- [ ] Logging is production-appropriate (no sensitive data)

### Step 3: Infrastructure Verification
- [ ] Health check endpoint includes Supabase connectivity
- [ ] Monitoring/alerting configured for Supabase errors
- [ ] Circuit breaker pattern for external API calls
- [ ] Graceful degradation if Supabase is unavailable

### Step 4: Deploy and Validate
```bash
# Pre-flight checks
curl -f https://staging.example.com/health
curl -s https://status.supabase.com

# Deploy
kubectl apply -f k8s/production.yaml
kubectl get pods -l app=supabase-integration

# Validate
kubectl logs -l app=supabase-integration --since=5m | grep -i error
```

## Output
- Production deployment completed successfully
- Health check endpoint reporting healthy
- Monitoring alerts configured and tested
- Rollback procedure documented and tested

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Health check failed | Supabase connectivity | Check API status, verify credentials |
| Pod crash loop | Missing environment variables | Verify all required env vars are set |
| 5xx errors after deploy | Code regression | Execute rollback procedure |
| Alert storms | Monitoring misconfigured | Tune alert thresholds |

## Examples

### Health Check Implementation
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

### Rollback Procedure
```bash
# 1. Disable feature flag
curl -X POST https://api.featureflags.com/disable/supabase-integration

# 2. Revert to previous deployment
kubectl rollout undo deployment/supabase-integration

# 3. Verify rollback
kubectl rollout status deployment/supabase-integration
```

### Monitoring Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| Supabase API Down | 5xx errors > 10/min | P1 |
| High Latency | p99 > 5000ms | P2 |
| Rate Limited | 429 errors > 5/min | P2 |
| Auth Failures | 401/403 errors > 0 | P1 |

## Resources
- [Supabase Status Page](https://status.supabase.com)
- [Deployment Best Practices](https://supabase.com/docs/deployment)
- [Incident Response Guide](https://supabase.com/docs/incidents)

## Next Steps
For version upgrades, see `supabase-upgrade-migration`.