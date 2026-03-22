---
name: palantir-prod-checklist
description: |
  Execute Palantir Foundry production deployment checklist and rollback procedures.
  Use when deploying Foundry integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "palantir production", "deploy foundry",
  "palantir go-live", "foundry launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, production, deployment]
compatible-with: claude-code, codex, openclaw
---

# Palantir Production Checklist

## Overview
Complete go-live checklist for deploying Foundry-integrated applications to production. Covers credential management, health checks, monitoring, and rollback procedures.

## Prerequisites
- Staging environment tested and verified
- Production OAuth2 credentials from Developer Console
- Deployment pipeline configured
- Monitoring infrastructure ready

## Instructions

### Pre-Deployment: Credentials & Config
- [ ] OAuth2 client credentials in secrets manager (not personal tokens)
- [ ] Scopes are minimal: only what the app actually needs
- [ ] `FOUNDRY_HOSTNAME` points to production enrollment
- [ ] Separate credentials from staging (not shared)
- [ ] Credential rotation schedule documented (90-day max)

### Code Quality
- [ ] All tests passing including Foundry integration tests
- [ ] No hardcoded hostnames, tokens, or RIDs
- [ ] Error handling covers all Foundry `ApiError` status codes
- [ ] Rate limiting with exponential backoff implemented
- [ ] Logging uses structured format (JSON) with request IDs

### Infrastructure
- [ ] Health check endpoint verifies Foundry connectivity
```python
@app.get("/health")
async def health():
    try:
        client.ontologies.Ontology.list()
        return {"status": "healthy", "foundry": "connected"}
    except foundry.ApiError as e:
        return {"status": "degraded", "foundry": f"error_{e.status_code}"}
```
- [ ] Circuit breaker pattern for Foundry API calls
- [ ] Graceful degradation when Foundry is unreachable
- [ ] Timeout configuration: 30s for reads, 60s for writes
- [ ] Connection pooling configured

### Monitoring & Alerting
- [ ] Metrics: request count, latency p50/p99, error rate by status code
- [ ] Alert: 5xx error rate > 5% for 5 minutes → P1
- [ ] Alert: p99 latency > 10s for 10 minutes → P2
- [ ] Alert: 429 rate > 10/min → P2 (tune rate limiter)
- [ ] Alert: 401/403 errors → P1 (credential issue)
- [ ] Dashboard with Foundry API health summary

### Documentation
- [ ] Incident runbook: `palantir-incident-runbook`
- [ ] Credential rotation procedure documented
- [ ] Rollback procedure documented and tested
- [ ] On-call escalation path defined
- [ ] Foundry support contact info available

### Deploy
```bash
set -euo pipefail
# Pre-flight
curl -sf "https://$FOUNDRY_HOSTNAME/api/v2/ontologies" \
  -H "Authorization: Bearer $FOUNDRY_TOKEN" > /dev/null \
  && echo "Foundry API reachable" || echo "BLOCKED: Foundry unreachable"

# Deploy with canary
kubectl set image deployment/my-app app=myimage:v2.0.0 --record
kubectl rollout status deployment/my-app --timeout=300s
```

### Rollback
```bash
kubectl rollout undo deployment/my-app
kubectl rollout status deployment/my-app
```

## Output
- Production deployment with verified Foundry connectivity
- Health checks passing
- Monitoring and alerting active
- Rollback procedure tested

## Error Handling
| Alert | Condition | Severity |
|-------|-----------|----------|
| Foundry Unreachable | Health check fails 3x | P1 |
| Auth Failure | Any 401/403 | P1 |
| Rate Limited | 429 > 10/min | P2 |
| High Latency | p99 > 10s | P2 |

## Resources
- [Foundry API Reference](https://www.palantir.com/docs/foundry/api/general/overview/introduction)
- [Foundry Documentation](https://www.palantir.com/docs/foundry)

## Next Steps
For version upgrades, see `palantir-upgrade-migration`.
