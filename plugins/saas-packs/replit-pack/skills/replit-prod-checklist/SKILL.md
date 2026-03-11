---
name: replit-prod-checklist
description: |
  Execute Replit production deployment checklist and rollback procedures.
  Use when deploying Replit integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "replit production", "deploy replit",
  "replit go-live", "replit launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Production Checklist

## Overview
Complete checklist for deploying Replit integrations to production.

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
- [ ] Error handling covers all Replit error types
- [ ] Rate limiting/backoff implemented
- [ ] Logging is production-appropriate

### Step 3: Infrastructure Setup
- [ ] Health check endpoint includes Replit connectivity
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
set -euo pipefail
# Pre-flight checks
curl -f https://staging.example.com/health
curl -s https://status.replit.com

# Gradual rollout - start with canary (10%)
kubectl apply -f k8s/production.yaml
kubectl set image deployment/replit-integration app=image:new --record
kubectl rollout pause deployment/replit-integration

# Monitor canary traffic for 10 minutes
sleep 600  # 600: timeout: 10 minutes
# Check error rates and latency before continuing

# If healthy, continue rollout to 50%
kubectl rollout resume deployment/replit-integration
kubectl rollout pause deployment/replit-integration
sleep 300  # 300: timeout: 5 minutes

# Complete rollout to 100%
kubectl rollout resume deployment/replit-integration
kubectl rollout status deployment/replit-integration
```

## Output
- Deployed Replit integration
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
async function healthCheck(): Promise<{ status: string; replit: any }> {
  const start = Date.now();
  try {
    await replitClient.ping();
    return { status: 'healthy', replit: { connected: true, latencyMs: Date.now() - start } };
  } catch (error) {
    return { status: 'degraded', replit: { connected: false, latencyMs: Date.now() - start } };
  }
}
```

### Immediate Rollback
```bash
set -euo pipefail
kubectl rollout undo deployment/replit-integration
kubectl rollout status deployment/replit-integration
```

## Resources
- [Replit Status](https://status.replit.com)
- [Replit Support](https://docs.replit.com/support)

## Next Steps
For version upgrades, see `replit-upgrade-migration`.