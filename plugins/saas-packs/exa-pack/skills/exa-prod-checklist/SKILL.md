---
name: exa-prod-checklist
description: |
  Execute Exa production deployment checklist with pre-flight, deploy, and rollback.
  Use when deploying Exa integrations to production, preparing for launch,
  or verifying production readiness.
  Trigger with phrases like "exa production", "deploy exa to prod",
  "exa go-live", "exa launch checklist", "exa production ready".
allowed-tools: Read, Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, deployment, production]

---
# Exa Production Checklist

## Overview
Complete checklist for deploying Exa search integrations to production. Covers API key management, error handling verification, performance baselines, monitoring, and rollback procedures.

## Pre-Deployment Checklist

### Security
- [ ] Production API key stored in secret manager (not env file)
- [ ] Different API keys for dev/staging/production
- [ ] `.env` files in `.gitignore`
- [ ] Git history scanned for accidentally committed keys
- [ ] API key has minimal scopes needed

### Code Quality
- [ ] All tests passing (unit + integration)
- [ ] No hardcoded API keys or URLs
- [ ] Error handling covers all Exa HTTP codes (400, 401, 402, 403, 429, 5xx)
- [ ] `requestId` captured from error responses
- [ ] Rate limiting/exponential backoff implemented
- [ ] Content moderation enabled (`moderation: true`) for user-facing search

### Performance
- [ ] Search type appropriate for latency SLO (`fast`/`auto`/`neural`)
- [ ] `numResults` minimized per use case (3-5 for most)
- [ ] `maxCharacters` set on text and highlights
- [ ] Result caching enabled (LRU or Redis)
- [ ] Request queue with concurrency limit (respect 10 QPS default)

### Monitoring
- [ ] Search latency histogram instrumented
- [ ] Error rate counter by status code
- [ ] Cache hit/miss rate tracked
- [ ] Daily search volume tracked (for budget)
- [ ] Alerts configured for latency > 3s, error rate > 5%

## Deploy Procedure

### Step 1: Pre-Flight Verification
```bash
set -euo pipefail
echo "=== Exa Pre-Flight ==="

# 1. Verify production API key works
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{"query":"pre-flight check","numResults":1}')
echo "API Status: $HTTP_CODE"
[ "$HTTP_CODE" = "200" ] || { echo "FAIL: API key invalid"; exit 1; }

# 2. Verify tests pass
npm test || { echo "FAIL: Tests failing"; exit 1; }

echo "Pre-flight PASSED"
```

### Step 2: Health Check Endpoint
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

app.get("/health/exa", async (_req, res) => {
  const start = performance.now();
  try {
    const result = await exa.search("health check", { numResults: 1 });
    const latencyMs = Math.round(performance.now() - start);
    res.json({
      status: "healthy",
      latencyMs,
      resultCount: result.results.length,
      timestamp: new Date().toISOString(),
    });
  } catch (err: any) {
    res.status(503).json({
      status: "unhealthy",
      error: err.message,
      errorCode: err.status,
      latencyMs: Math.round(performance.now() - start),
    });
  }
});
```

### Step 3: Gradual Rollout
```bash
set -euo pipefail
# Deploy canary (10% traffic)
kubectl apply -f k8s/production.yaml
kubectl rollout pause deployment/exa-service

echo "Canary deployed. Monitor for 10 minutes..."
echo "Check: /health/exa endpoint, error rates, latency"

# After monitoring, resume to full rollout
# kubectl rollout resume deployment/exa-service
```

## Post-Deployment Verification
```bash
set -euo pipefail
# Verify production endpoint
curl -sf https://your-app.com/health/exa | python3 -m json.tool

# Check error rates (if Prometheus available)
curl -s "localhost:9090/api/v1/query?query=rate(exa_search_error[5m])" 2>/dev/null
```

## Rollback Procedure
```bash
set -euo pipefail
# Immediate rollback
kubectl rollout undo deployment/exa-service
kubectl rollout status deployment/exa-service
echo "Rollback complete. Verify /health/exa endpoint."
```

## Alert Thresholds

| Alert | Condition | Severity |
|-------|-----------|----------|
| API Down | 5xx errors > 10/min | P1 |
| Auth Failure | 401/403 errors > 0 | P1 |
| Rate Limited | 429 errors > 5/min | P2 |
| High Latency | P95 > 5000ms | P2 |
| Budget Warning | Daily searches > 80% of limit | P3 |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Health check fails | API key not set in prod | Verify secret injection |
| Latency spike after deploy | Missing cache warm-up | Pre-populate cache |
| Rate limit on launch | Traffic spike | Enable request queue |
| Rollback needed | Error rate spike | `kubectl rollout undo` |

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)

## Next Steps
For version upgrades, see `exa-upgrade-migration`. For incident response, see `exa-incident-runbook`.
