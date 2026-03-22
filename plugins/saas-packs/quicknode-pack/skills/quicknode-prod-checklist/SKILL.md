---
name: quicknode-prod-checklist
description: |
  Execute QuickNode production deployment checklist and rollback procedures.
  Use when deploying QuickNode integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "quicknode production", "deploy quicknode",
  "quicknode go-live", "quicknode launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, quicknode]
---

# QuickNode Production Checklist

## Overview
Complete checklist for deploying QuickNode integrations to production.

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
- [ ] Error handling covers all QuickNode error types
- [ ] Rate limiting/backoff implemented
- [ ] Logging is production-appropriate

### Step 3: Infrastructure Setup
- [ ] Health check endpoint includes QuickNode connectivity
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
curl -s https://status.quicknode.com

# Gradual rollout - start with canary (10%)
kubectl apply -f k8s/production.yaml
kubectl set image deployment/quicknode-integration app=image:new --record
kubectl rollout pause deployment/quicknode-integration

# Monitor canary traffic for 10 minutes
sleep 600
# Check error rates and latency before continuing

# If healthy, continue rollout to 50%
kubectl rollout resume deployment/quicknode-integration
kubectl rollout pause deployment/quicknode-integration
sleep 300

# Complete rollout to 100%
kubectl rollout resume deployment/quicknode-integration
kubectl rollout status deployment/quicknode-integration
```

## Output
- Deployed QuickNode integration
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
async function healthCheck(): Promise<{ status: string; quicknode: any }> {
  const start = Date.now();
  try {
    await quicknodeClient.ping();
    return { status: 'healthy', quicknode: { connected: true, latencyMs: Date.now() - start } };
  } catch (error) {
    return { status: 'degraded', quicknode: { connected: false, latencyMs: Date.now() - start } };
  }
}
```

### Immediate Rollback
```bash
kubectl rollout undo deployment/quicknode-integration
kubectl rollout status deployment/quicknode-integration
```

## Resources
- [QuickNode Status](https://status.quicknode.com)
- [QuickNode Support](https://docs.quicknode.com/support)

## Next Steps
For version upgrades, see `quicknode-upgrade-migration`.