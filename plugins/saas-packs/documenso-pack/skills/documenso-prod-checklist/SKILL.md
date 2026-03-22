---
name: documenso-prod-checklist
description: |
  Execute Documenso production deployment checklist and rollback procedures.
  Use when deploying Documenso integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "documenso production", "deploy documenso",
  "documenso go-live", "documenso launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, deployment]

---
# Documenso Production Checklist

## Overview

Complete checklist for deploying Documenso integrations to production, covering security, reliability, monitoring, and compliance readiness.

## Prerequisites

- Staging environment tested and verified
- Production API keys available
- Deployment pipeline configured (see `documenso-ci-integration`)
- Monitoring ready (see `documenso-observability`)

## Production Checklist

### 1. Authentication & Secrets
- [ ] Production API key generated (not staging key)
- [ ] API key stored in secret manager (Vault, AWS Secrets Manager, not `.env`)
- [ ] Webhook secret configured and verified
- [ ] Key rotation procedure documented
- [ ] Old/unused keys revoked
- [ ] Self-hosted: secrets generated with `openssl rand -hex 32`
- [ ] Self-hosted: signing certificate from trusted CA mounted

### 2. Error Handling
- [ ] All API calls wrapped in try/catch with typed errors
- [ ] Exponential backoff for 429/5xx responses
- [ ] Circuit breaker for Documenso outages
- [ ] User-friendly error messages (no raw API errors exposed)
- [ ] Error tracking integration (Sentry, Datadog, etc.)

### 3. Performance
- [ ] Singleton client pattern (not creating new client per request)
- [ ] Templates used for repetitive document creation
- [ ] Bulk operations use concurrency control (p-queue)
- [ ] Background processing for non-critical operations (Bull/BullMQ)
- [ ] Document metadata cached (completed documents immutable)

### 4. Monitoring & Alerting
- [ ] Health check endpoint: `GET /health/documenso`
- [ ] API error rate alerting (> 5% for 5 minutes)
- [ ] Latency monitoring (p95 > 5s)
- [ ] Webhook delivery success rate tracking
- [ ] Structured logging with sanitized PII

### 5. Webhooks
- [ ] HTTPS endpoint configured (HTTP rejected by Documenso)
- [ ] Webhook secret verification using constant-time comparison
- [ ] Idempotent event processing (handle duplicates)
- [ ] Async processing (respond 200 immediately, process in background)
- [ ] Dead letter queue for failed webhook processing

### 6. Data & Compliance
- [ ] PII sanitized in all logs (emails, names)
- [ ] Data retention policy implemented
- [ ] GDPR access/erasure request process documented
- [ ] Signed PDFs archived to durable storage
- [ ] Self-hosted: document storage strategy defined

### 7. Self-Hosted Production (if applicable)
- [ ] PostgreSQL with automated backups
- [ ] HTTPS via reverse proxy (nginx, Caddy, Traefik)
- [ ] Signing certificate from trusted CA (not self-signed)
- [ ] SMTP configured and tested (emails actually deliver)
- [ ] Container runs as non-root user (UID 1001)
- [ ] Resource limits set (CPU, memory)
- [ ] Automated container restarts (restart: unless-stopped)

## Pre-Deployment Verification Script

```bash
#!/bin/bash
set -euo pipefail
echo "=== Documenso Production Verification ==="

# Check API key
if [ -z "${DOCUMENSO_API_KEY:-}" ]; then
  echo "FAIL: DOCUMENSO_API_KEY not set"; exit 1
fi
echo "OK: API key configured"

# Test connection
BASE="${DOCUMENSO_BASE_URL:-https://app.documenso.com/api/v1}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  "$BASE/documents?page=1&perPage=1")
[ "$STATUS" = "200" ] && echo "OK: API connection ($STATUS)" || echo "FAIL: API connection ($STATUS)"

# Test webhook endpoint
WEBHOOK_URL="${DOCUMENSO_WEBHOOK_URL:-}"
if [ -n "$WEBHOOK_URL" ]; then
  WH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$WEBHOOK_URL")
  echo "Webhook endpoint: $WH_STATUS"
fi

# Check health endpoint
HEALTH_URL="${APP_URL:-http://localhost:3000}/health/documenso"
HEALTH=$(curl -s "$HEALTH_URL" 2>/dev/null | jq -r '.status' 2>/dev/null || echo "unreachable")
echo "Health check: $HEALTH"

echo "=== Verification Complete ==="
```

## Rollback Procedure

```text
If issues occur after deployment:

1. Immediate: revert to previous container image / deployment
   kubectl rollout undo deployment/signing-service
   # or: vercel rollback

2. Verify rollback:
   curl -s $APP_URL/health/documenso | jq '.status'

3. Investigate:
   - Check deployment diff (what changed?)
   - Review error logs for the deployment window
   - Test the failed version in staging

4. Fix and re-deploy:
   - Fix the root cause on a feature branch
   - Test in staging
   - Deploy with monitoring active
```

## Go-Live Day Checklist

- [ ] All checklist items above verified
- [ ] Staging smoke test passed within last 24 hours
- [ ] Team notified of deployment window
- [ ] Monitoring dashboards open during deployment
- [ ] Rollback procedure documented and accessible
- [ ] Support contact for Documenso available (Discord or email)
- [ ] First production document created and verified end-to-end

## Error Handling

| Alert | Condition | Response |
|-------|-----------|----------|
| Deploy failed | CI/CD error | Check logs, fix, retry |
| Health check failed | Documenso unreachable | Verify API key, check status page |
| Error spike post-deploy | Breaking change | Execute rollback procedure |
| Webhook delivery stopped | Endpoint misconfigured | Check HTTPS URL, secret, event subscriptions |

## Resources

- [Documenso Status](https://status.documenso.com)
- [Self-Hosting Tips](https://docs.documenso.com/docs/self-hosting/getting-started/tips)
- [Documenso Discord](https://documenso.com/discord)

## Next Steps

For version upgrades, see `documenso-upgrade-migration`.
