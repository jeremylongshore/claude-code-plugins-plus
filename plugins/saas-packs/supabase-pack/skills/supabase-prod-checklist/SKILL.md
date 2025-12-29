---
name: supabase-prod-checklist
description: |
  Execute Supabase production deployment checklist and rollback procedures.
  Use when deploying Supabase integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "supabase production", "deploy supabase",
  "supabase go-live", "supabase launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Production Checklist

## Overview
Complete checklist for deploying Supabase integrations to production.

## Prerequisites
- Staging environment tested and verified
- Production API keys available
- Deployment pipeline configured
- Monitoring and alerting ready

## Instructions

### Step 1: Pre-Deployment Configuration
- [ ] Production API keys in secure vault
- [ ] Environment variables set in deployment platform
- [ ] API key scopes are minimal (least privilege)
- [ ] Webhook endpoints configured with HTTPS
- [ ] Webhook secrets stored securely

### Step 2: Code Quality Verification
- [ ] All tests passing (`npm test`)
- [ ] No hardcoded credentials
- [ ] Error handling covers all Supabase error types
- [ ] Rate limiting/backoff implemented
- [ ] Logging is production-appropriate

### Step 3: Infrastructure Setup
- [ ] Health check endpoint includes Supabase connectivity
- [ ] Monitoring/alerting configured
- [ ] Circuit breaker pattern implemented
- [ ] Graceful degradation configured

### Step 4: Deploy and Validate
```bash
# Pre-flight checks
curl -f https://staging.example.com/health
curl -s https://status.supabase.com

# Deploy and verify
kubectl apply -f k8s/production.yaml
kubectl get pods -l app=supabase-integration
```

## Output
- Deployed Supabase integration
- Health checks passing
- Monitoring active
- Rollback procedure documented

## Error Handling
| Alert | Condition | Severity |
|-------|-----------|----------|
| API Down | 5xx errors > 10/min | P1 |
| High Latency | p99 > 5000ms | P2 |
| Rate Limited | 429 errors > 5/min | P2 |
| Auth Failures | 401/403 errors > 0 | P1 |

## Examples

### Health Check Implementation
```typescript
async function healthCheck(): Promise<{ status: string; supabase: any }> {
  const start = Date.now();
  try {
    await supabaseClient.ping();
    return { status: 'healthy', supabase: { connected: true, latencyMs: Date.now() - start } };
  } catch (error) {
    return { status: 'degraded', supabase: { connected: false, latencyMs: Date.now() - start } };
  }
}
```

### Immediate Rollback
```bash
kubectl rollout undo deployment/supabase-integration
kubectl rollout status deployment/supabase-integration
```

## Resources
- [Supabase Status](https://status.supabase.com)
- [Supabase Support](https://supabase.com/docs/support)

## Next Steps
For version upgrades, see `supabase-upgrade-migration`.