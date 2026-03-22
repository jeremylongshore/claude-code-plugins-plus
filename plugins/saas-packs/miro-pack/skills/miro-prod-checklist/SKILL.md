---
name: miro-prod-checklist
description: |
  Execute Miro production deployment checklist and rollback procedures.
  Use when deploying Miro integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "miro production", "deploy miro",
  "miro go-live", "miro launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, miro]
---

# Miro Production Checklist

## Overview
Complete checklist for deploying Miro integrations to production.

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
- [ ] Error handling covers all Miro error types
- [ ] Rate limiting/backoff implemented
- [ ] Logging is production-appropriate

### Step 3: Infrastructure Setup
- [ ] Health check endpoint includes Miro connectivity
- [ ] Monitoring/alerting configured
- [ ] Circuit breaker pattern implemented
- [ ] Graceful degradation configured

### Step 4: Documentation Requirements
- [ ] Incident runbook created
- [ ] Key rotation procedure documented
- [ ] Rollback procedure documented
- [ ] On-call escalation path defined

### Step 5: Deploy with Gradual Rollout
```bash
# Pre-flight checks
curl -f https://staging.example.com/health
curl -s https://status.miro.com

# Gradual rollout - start with canary (10%)
kubectl apply -f k8s/production.yaml
kubectl set image deployment/miro-integration app=image:new --record
kubectl rollout pause deployment/miro-integration

# Monitor canary traffic for 10 minutes
sleep 600
# Check error rates and latency before continuing

# If healthy, continue rollout to 50%
kubectl rollout resume deployment/miro-integration
kubectl rollout pause deployment/miro-integration
sleep 300

# Complete rollout to 100%
kubectl rollout resume deployment/miro-integration
kubectl rollout status deployment/miro-integration
```

## Output
- Deployed Miro integration
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
async function healthCheck(): Promise<{ status: string; miro: any }> {
  const start = Date.now();
  try {
    await miroClient.ping();
    return { status: 'healthy', miro: { connected: true, latencyMs: Date.now() - start } };
  } catch (error) {
    return { status: 'degraded', miro: { connected: false, latencyMs: Date.now() - start } };
  }
}
```

### Immediate Rollback
```bash
kubectl rollout undo deployment/miro-integration
kubectl rollout status deployment/miro-integration
```

## Resources
- [Miro Status](https://status.miro.com)
- [Miro Support](https://docs.miro.com/support)

## Next Steps
For version upgrades, see `miro-upgrade-migration`.