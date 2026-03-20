---
name: maintainx-prod-checklist
description: |
  Production deployment checklist for MaintainX integrations.
  Use when preparing to deploy a MaintainX integration to production,
  verifying production readiness, or auditing existing deployments.
  Trigger with phrases like "maintainx production", "deploy maintainx",
  "maintainx go-live", "maintainx production checklist", "maintainx launch".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Production Checklist

## Overview
Comprehensive pre-deployment and post-deployment checklist for MaintainX integrations covering security, reliability, observability, and data integrity.

## Prerequisites
- MaintainX integration developed and tested
- Production MaintainX account with API access
- Deployment infrastructure ready (Cloud Run, K8s, or similar)

## Instructions

### Step 1: Authentication & Security

```bash
# Verify production API key works
curl -s -o /dev/null -w "HTTP %{http_code}" \
  https://api.getmaintainx.com/v1/users?limit=1 \
  -H "Authorization: Bearer $MAINTAINX_API_KEY_PROD"

# Verify no secrets in codebase
npx gitleaks detect --source . --no-git
```

- [ ] API key stored in secret manager (not env file or code)
- [ ] `.env` and `*.key` files in `.gitignore`
- [ ] Pre-commit hook blocking secret commits
- [ ] API key rotation schedule set (every 90 days)
- [ ] Input validation on all user-provided data (Zod or similar)

### Step 2: Error Handling & Resilience

- [ ] Retry logic with exponential backoff for 429 and 5xx errors
- [ ] `Retry-After` header honored on 429 responses
- [ ] Circuit breaker for cascading failure prevention
- [ ] Graceful degradation when MaintainX API is down
- [ ] Request timeout set (30 seconds recommended)

```typescript
// Verify retry logic is configured
const client = axios.create({
  baseURL: 'https://api.getmaintainx.com/v1',
  timeout: 30_000,  // 30 second timeout
  headers: { Authorization: `Bearer ${apiKey}` },
});
```

### Step 3: Data Integrity

- [ ] Cursor-based pagination handles all list endpoints
- [ ] Idempotency keys on webhook handlers (prevent duplicate processing)
- [ ] Data sync state persisted (survives restarts)
- [ ] Reconciliation job runs daily to detect drift
- [ ] Work order status transitions follow valid paths only

### Step 4: Observability

- [ ] Structured JSON logging (not console.log in production)
- [ ] API request metrics (count, latency, error rate)
- [ ] Health check endpoint (`/health`) returning API connectivity status
- [ ] Readiness probe (`/ready`) for container orchestration
- [ ] Alerting configured for error rate > 5%, latency > 5s, sync lag > 15min

### Step 5: Performance

- [ ] Connection pooling with keep-alive enabled
- [ ] Response caching for static resources (users, locations, teams)
- [ ] Max page size (100) used for pagination
- [ ] Webhook-driven updates instead of polling where possible
- [ ] Rate limiting to stay within API quotas

### Step 6: Deployment

- [ ] Multi-stage Docker build (small production image)
- [ ] Non-root user in container
- [ ] Resource limits set (CPU, memory)
- [ ] Auto-scaling configured (min 1 instance for webhooks)
- [ ] Rollback procedure documented and tested

## Post-Deployment Verification

```bash
#!/bin/bash
echo "=== Post-Deployment Verification ==="

# 1. Health check
echo -n "Health check: "
curl -s http://YOUR_SERVICE_URL/health | jq -r '.status'

# 2. API connectivity
echo -n "MaintainX API: "
curl -s -o /dev/null -w "%{http_code}" \
  https://api.getmaintainx.com/v1/users?limit=1 \
  -H "Authorization: Bearer $MAINTAINX_API_KEY_PROD"
echo ""

# 3. Create test work order
echo "Creating test work order..."
WO=$(curl -s -X POST https://api.getmaintainx.com/v1/workorders \
  -H "Authorization: Bearer $MAINTAINX_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{"title":"Post-deploy verification test","priority":"LOW"}')
WO_ID=$(echo $WO | jq -r '.id')
echo "  Created: #$WO_ID"

# 4. Verify retrieval
echo -n "Retrieve test: "
curl -s "https://api.getmaintainx.com/v1/workorders/$WO_ID" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY_PROD" | jq -r '.status'

# 5. Clean up
curl -s -X PATCH "https://api.getmaintainx.com/v1/workorders/$WO_ID" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{"status":"CLOSED"}' > /dev/null
echo "  Cleaned up test work order #$WO_ID"

# 6. Check metrics endpoint
echo -n "Metrics endpoint: "
curl -s -o /dev/null -w "%{http_code}" http://YOUR_SERVICE_URL/metrics
echo ""

echo "=== Verification complete ==="
```

## Go-Live Readiness Summary

| Category | Requirement | Priority |
|----------|------------|----------|
| Auth | Secret manager, no hardcoded keys | P0 |
| Errors | Retry + backoff for 429/5xx | P0 |
| Data | Pagination, idempotency, sync state | P0 |
| Observability | Logging, metrics, health check | P0 |
| Performance | Connection pooling, caching | P1 |
| Security | Input validation, audit logging | P1 |
| Deployment | Docker, non-root, resource limits | P1 |
| Recovery | Rollback procedure, reconciliation | P2 |

## Output
- All P0 checklist items verified before go-live
- Post-deployment verification script run successfully
- Test work order created and cleaned up in production
- Health check and metrics endpoints responding
- Go-live readiness documented

## Error Handling
| Issue | Check | Solution |
|-------|-------|----------|
| Health check fails post-deploy | `curl /health` | Check API key is mounted, restart pod |
| Test work order creation fails | Check HTTP status | Verify API key permissions and plan tier |
| Metrics endpoint 404 | Check route config | Ensure metrics server started on correct port |
| High error rate after deploy | Check logs | Roll back, investigate, fix, redeploy |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [MaintainX Status Page](https://status.getmaintainx.com)
- [12-Factor App](https://12factor.net/)

## Next Steps
For API version migrations, see `maintainx-upgrade-migration`.

## Examples

**Automated pre-deploy gate in CI**:

```yaml
# .github/workflows/deploy.yml
jobs:
  pre-deploy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx gitleaks detect --source . --no-git
      - run: npm run test -- --coverage --coverageThreshold='{"global":{"branches":80}}'
      - run: npm run lint
      - run: npm run typecheck
```
