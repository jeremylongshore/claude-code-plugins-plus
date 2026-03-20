---
name: juicebox-prod-checklist
description: |
  Production deployment checklist for Juicebox.
  Use when preparing for production launch, validating deployment readiness,
  or performing pre-launch reviews.
  Trigger with phrases like "juicebox production", "deploy juicebox prod",
  "juicebox launch checklist", "juicebox go-live".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Production Checklist

## Overview
Systematic production readiness validation for Juicebox integrations. Covers security audit, error handling review, performance validation, monitoring setup, data compliance, and infrastructure checks. Includes a runnable validation script that tests API auth, search, enrichment, and webhook connectivity against the live Juicebox API (`Authorization: token {username}:{api_token}`).

## Prerequisites
- Juicebox integration deployed to staging (use `juicebox-deploy-integration` first)
- Production API credentials (username + token from https://juicebox.ai/settings)
- `curl` and `jq` available in the environment
- Monitoring infrastructure provisioned (Datadog, Grafana, or CloudWatch)

## Instructions

### Step 1: Security Checklist

Verify every security control before routing production traffic.

```markdown
## Security
- [ ] API token stored in a secret manager (AWS Secrets Manager, GCP Secret Manager, or Vault)
- [ ] No tokens in environment variables, `.env` files, or source control
- [ ] Token rotation schedule documented (recommended: 90 days)
- [ ] Backup API token generated and stored separately
- [ ] All Juicebox API calls use HTTPS (never HTTP)
- [ ] API token scoped to minimum required permissions
- [ ] Server-side proxy in place (client-side code never sees the token)
- [ ] Audit logging captures every Juicebox API call (who, what, when)
- [ ] PII from enriched profiles handled per GDPR/CCPA requirements
- [ ] Data retention policy defined for cached profile data
```

Verify no tokens are exposed in the codebase:

```bash
# Scan for leaked credentials
grep -rn "jb_tok_" . --include="*.ts" --include="*.js" --include="*.env" \
  --include="*.yaml" --include="*.yml" || echo "No hardcoded tokens found"

# Check .env files are gitignored
grep -q ".env" .gitignore && echo "OK: .env in .gitignore" || echo "FAIL: Add .env to .gitignore"

# Verify secrets are not in Docker image
docker history your-registry/juicebox-app:latest --no-trunc | grep -i "juicebox\|token\|secret" || echo "OK: No secrets in image layers"
```

### Step 2: Error Handling Checklist

```markdown
## Error Handling
- [ ] All Juicebox HTTP status codes handled (400, 401, 403, 404, 429, 500, 502, 503)
- [ ] Retry logic with exponential backoff for 429 and 5xx responses
- [ ] Circuit breaker trips after 5 consecutive failures, resets after 30s
- [ ] Fallback behavior defined when Juicebox is unreachable (cached results, graceful degradation)
- [ ] Error responses never expose internal details or API tokens to end users
- [ ] Structured error logging with request ID, status code, and latency
- [ ] Alerting configured for error rate > 5% over 5-minute window
```

Verify error handling is implemented:

```bash
# Test that your app handles a bad token gracefully
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token baduser:bad_token_000" \
  https://api.juicebox.ai/v1/me
# Expected: 401

# Verify your app returns a clean error, not a stack trace
curl -s http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"","limit":0}' | jq '.error'
# Expected: a user-friendly error message, not "TypeError" or raw stack
```

### Step 3: Performance Checklist

```markdown
## Performance
- [ ] Search response time < 3s at p95 under normal load
- [ ] Enrichment response time < 5s at p95
- [ ] Redis/Memcached cache layer in front of Juicebox API
- [ ] Cache TTL set (300s for search results, 3600s for enriched profiles)
- [ ] Connection pooling configured (keep-alive enabled)
- [ ] Request timeout set to 15s (prevents hung connections)
- [ ] Load test completed: 50 concurrent searches sustained for 5 minutes
- [ ] Rate limit headroom: current usage < 70% of Juicebox plan quota
```

### Step 4: Monitoring Checklist

```markdown
## Monitoring
- [ ] Health check endpoint `/health/ready` verifies Juicebox connectivity
- [ ] Metrics exported: request count, latency (p50/p95/p99), error rate, cache hit ratio
- [ ] Dashboard created with Juicebox-specific panels
- [ ] Alert: Juicebox API error rate > 5% for 5 minutes
- [ ] Alert: Juicebox API latency p95 > 5s for 5 minutes
- [ ] Alert: Health check failing for > 2 minutes
- [ ] On-call runbook links to `juicebox-incident-runbook`
- [ ] Juicebox status page bookmarked (https://status.juicebox.ai)
```

### Step 5: Data Handling Checklist

```markdown
## Data Handling
- [ ] Profile data stored with encryption at rest
- [ ] PII fields (email, phone, LinkedIn URL) access-controlled
- [ ] Data retention: enriched profiles auto-expire after defined period
- [ ] User consent captured before storing candidate data
- [ ] Export/delete capability for GDPR right-to-erasure requests
- [ ] Juicebox data not replicated to unauthorized systems
- [ ] ATS/CRM sync via Merge API uses separate credentials
```

### Step 6: Run Production Validation Script

This script tests API connectivity, search, enrichment, and webhook handling against the live Juicebox API.

```bash
#!/bin/bash
# scripts/validate-juicebox-prod.sh
set -euo pipefail

echo "============================================="
echo "  Juicebox Production Validation"
echo "============================================="

PASS=0
FAIL=0

check() {
  local name="$1" status="$2" expected="$3"
  if [ "$status" = "$expected" ]; then
    echo "  [PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] $name (got $status, expected $expected)"
    FAIL=$((FAIL + 1))
  fi
}

# Validate env vars
if [ -z "${JUICEBOX_USERNAME:-}" ] || [ -z "${JUICEBOX_API_TOKEN:-}" ]; then
  echo "ERROR: Set JUICEBOX_USERNAME and JUICEBOX_API_TOKEN"
  exit 1
fi

AUTH_HEADER="Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}"
API="https://api.juicebox.ai/v1"

echo ""
echo "--- Authentication ---"
AUTH_STATUS=$(curl -s -o /tmp/jb-auth.json -w "%{http_code}" \
  -H "$AUTH_HEADER" "${API}/me")
check "API authentication" "$AUTH_STATUS" "200"

ACCOUNT=$(jq -r '.username // empty' /tmp/jb-auth.json 2>/dev/null || true)
if [ -n "$ACCOUNT" ]; then
  echo "  Account: $ACCOUNT"
fi

echo ""
echo "--- Search ---"
SEARCH_STATUS=$(curl -s -o /tmp/jb-search.json -w "%{http_code}" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"query":"software engineer","limit":3}' \
  "${API}/search")
check "Search endpoint" "$SEARCH_STATUS" "200"

PROFILE_COUNT=$(jq '.profiles | length' /tmp/jb-search.json 2>/dev/null || echo 0)
echo "  Profiles returned: $PROFILE_COUNT"
if [ "$PROFILE_COUNT" -gt 0 ]; then
  FIRST_PROFILE_ID=$(jq -r '.profiles[0].id' /tmp/jb-search.json)
  echo "  First profile ID: $FIRST_PROFILE_ID"
fi

echo ""
echo "--- Enrichment ---"
if [ -n "${FIRST_PROFILE_ID:-}" ] && [ "$FIRST_PROFILE_ID" != "null" ]; then
  ENRICH_STATUS=$(curl -s -o /tmp/jb-enrich.json -w "%{http_code}" \
    -H "$AUTH_HEADER" \
    -X POST "${API}/profiles/${FIRST_PROFILE_ID}/enrich")
  check "Profile enrichment" "$ENRICH_STATUS" "200"

  HAS_EMAIL=$(jq 'has("email")' /tmp/jb-enrich.json 2>/dev/null || echo false)
  echo "  Has email: $HAS_EMAIL"
else
  echo "  [SKIP] No profile ID from search to test enrichment"
fi

echo ""
echo "--- Rate Limit Headers ---"
RATE_REMAINING=$(curl -s -D- -o /dev/null \
  -H "$AUTH_HEADER" "${API}/me" 2>/dev/null | grep -i "x-ratelimit-remaining" | tr -d '\r' || true)
if [ -n "$RATE_REMAINING" ]; then
  echo "  $RATE_REMAINING"
else
  echo "  Rate limit headers not available"
fi

echo ""
echo "============================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "============================================="

# Clean up
rm -f /tmp/jb-auth.json /tmp/jb-search.json /tmp/jb-enrich.json

if [ "$FAIL" -gt 0 ]; then
  echo "PRODUCTION VALIDATION FAILED"
  exit 1
fi
echo "PRODUCTION VALIDATION PASSED"
```

### Step 7: Implement Health Check

```typescript
// src/health.ts
import { buildAuthHeader } from './lib/secrets';

interface HealthReport {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, { ok: boolean; latencyMs: number; detail?: string }>;
  timestamp: string;
}

export async function runHealthCheck(): Promise<HealthReport> {
  const checks: HealthReport['checks'] = {};

  // Check 1: Juicebox auth
  const authStart = Date.now();
  try {
    const headers = await buildAuthHeader();
    const res = await fetch('https://api.juicebox.ai/v1/me', { headers });
    checks.auth = {
      ok: res.ok,
      latencyMs: Date.now() - authStart,
      detail: res.ok ? 'authenticated' : `HTTP ${res.status}`,
    };
  } catch (e) {
    checks.auth = {
      ok: false,
      latencyMs: Date.now() - authStart,
      detail: e instanceof Error ? e.message : 'unknown error',
    };
  }

  // Check 2: Search functionality
  const searchStart = Date.now();
  try {
    const headers = await buildAuthHeader();
    const res = await fetch('https://api.juicebox.ai/v1/search', {
      method: 'POST',
      headers,
      body: JSON.stringify({ query: 'test', limit: 1 }),
    });
    const body = await res.json();
    checks.search = {
      ok: res.ok && body.profiles?.length > 0,
      latencyMs: Date.now() - searchStart,
      detail: `${body.profiles?.length ?? 0} profiles returned`,
    };
  } catch (e) {
    checks.search = {
      ok: false,
      latencyMs: Date.now() - searchStart,
      detail: e instanceof Error ? e.message : 'unknown error',
    };
  }

  const allOk = Object.values(checks).every(c => c.ok);
  const someOk = Object.values(checks).some(c => c.ok);

  return {
    status: allOk ? 'healthy' : someOk ? 'degraded' : 'unhealthy',
    checks,
    timestamp: new Date().toISOString(),
  };
}
```

### Step 8: Go-Live Checklist

```markdown
## Go-Live

### T-24 Hours
- [ ] All checklist items above marked complete
- [ ] Production validation script passes (`./scripts/validate-juicebox-prod.sh`)
- [ ] Load test completed at 2x expected traffic
- [ ] Rollback procedure tested and documented
- [ ] On-call schedule confirmed for launch window

### T-1 Hour
- [ ] Monitoring dashboards open on shared screen
- [ ] On-call team in Slack channel
- [ ] Juicebox status page shows all systems operational
- [ ] Run validation script one final time

### Launch
- [ ] Enable feature flag / route traffic
- [ ] Watch error rate dashboard for 15 minutes
- [ ] Verify first real search completes successfully
- [ ] Confirm enrichment returns data for first candidate
- [ ] Check ATS/CRM sync delivers first candidate record

### T+1 Hour
- [ ] Error rate < 1%
- [ ] p95 latency within SLA
- [ ] No alerts fired
- [ ] Cache hit ratio > 50%
- [ ] Announce launch complete
```

## Output
- Completed security, error handling, performance, monitoring, and data handling checklists
- `scripts/validate-juicebox-prod.sh` — automated production validation script
- `src/health.ts` — programmatic health check with latency measurements
- Go-live timeline with pre-launch, launch, and post-launch gates

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Validation script returns `FAIL: API authentication` | Token expired or wrong credentials | Regenerate token at juicebox.ai/settings, update in secret manager |
| Search returns 0 profiles | Rate limit hit or query too narrow | Check `X-RateLimit-Remaining` header; try a broader query like "engineer" |
| Enrichment returns 402 | Enrichment credits exhausted | Check account balance at juicebox.ai/billing; purchase more credits |
| Health check reports `degraded` | Auth passes but search fails | Juicebox may be experiencing partial outage; check status.juicebox.ai |
| `jq: error` in validation script | Unexpected API response format | Run `curl` manually and inspect raw JSON; API version may have changed |
| Rate limit header missing | Juicebox doesn't return rate headers on all endpoints | Not a failure; rate limits are still enforced server-side |

## Examples

### Running the Validation Script
```bash
export JUICEBOX_USERNAME="your-username"
export JUICEBOX_API_TOKEN="jb_tok_prod_xxxxxxxxxxxx"

chmod +x scripts/validate-juicebox-prod.sh
./scripts/validate-juicebox-prod.sh
```

Expected output:
```
=============================================
  Juicebox Production Validation
=============================================

--- Authentication ---
  [PASS] API authentication
  Account: your-username

--- Search ---
  [PASS] Search endpoint
  Profiles returned: 3
  First profile ID: prf_abc123

--- Enrichment ---
  [PASS] Profile enrichment
  Has email: true

--- Rate Limit Headers ---
  x-ratelimit-remaining: 487

=============================================
  Results: 3 passed, 0 failed
=============================================
PRODUCTION VALIDATION PASSED
```

### Using Health Check in an Express App
```typescript
import express from 'express';
import { runHealthCheck } from './health';

const app = express();

app.get('/health/detailed', async (req, res) => {
  const report = await runHealthCheck();
  const statusCode = report.status === 'healthy' ? 200 :
                     report.status === 'degraded' ? 200 : 503;
  res.status(statusCode).json(report);
});
```

## Resources
- [Juicebox API Documentation](https://juicebox.ai/docs/api)
- [Juicebox Status Page](https://status.juicebox.ai)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GDPR Data Processing Guidelines](https://gdpr.eu/data-processing-agreement/)

## Next Steps
After completing the production checklist, use `juicebox-incident-runbook` for on-call procedures and `juicebox-upgrade-migration` for SDK updates.
