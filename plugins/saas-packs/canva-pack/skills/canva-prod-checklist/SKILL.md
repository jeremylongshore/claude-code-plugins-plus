---
name: canva-prod-checklist
description: |
  Execute Canva Connect API production deployment checklist and go-live procedures.
  Use when deploying Canva integrations to production, preparing for launch,
  or validating production readiness.
  Trigger with phrases like "canva production", "deploy canva",
  "canva go-live", "canva launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Production Checklist

## Overview

Complete checklist for deploying Canva Connect API integrations to production, covering OAuth configuration, security, error handling, monitoring, and Canva's integration review process.

## Pre-Deployment

### OAuth & Security
- [ ] Client ID and secret stored in secret manager (not env files)
- [ ] Redirect URIs use HTTPS and match production domains
- [ ] Only required OAuth scopes requested (least privilege)
- [ ] Access tokens stored encrypted at rest
- [ ] Refresh token rotation handled (single-use tokens)
- [ ] Token revocation implemented for user disconnect
- [ ] No client secrets in frontend code

### API Integration
- [ ] All API calls use `api.canva.com/rest/v1/*` endpoints
- [ ] Rate limits respected with exponential backoff (see `canva-rate-limits`)
- [ ] Export polling implemented with timeout (don't poll forever)
- [ ] 429 responses handled with `Retry-After` header
- [ ] 401 responses trigger automatic token refresh
- [ ] Error responses parsed and logged (without tokens)
- [ ] Blank designs auto-delete warning handled (7-day window)
- [ ] Export download URLs consumed within 24-hour window

### Webhook Security
- [ ] Webhook endpoint uses HTTPS
- [ ] JWK signature verification implemented (see `canva-webhooks-events`)
- [ ] Webhook handler returns 200 immediately
- [ ] Heavy processing done asynchronously
- [ ] Idempotency keys prevent duplicate processing

### Data Handling
- [ ] No access tokens in log output
- [ ] User design metadata treated as sensitive
- [ ] Temporary URLs (thumbnails, exports) not cached beyond expiry
- [ ] Thumbnail URLs expire in 15 minutes — refresh as needed
- [ ] Edit/view URLs expire in 30 days — regenerate via API

## Production Readiness Verification

```bash
#!/bin/bash
# canva-prod-verify.sh

echo "=== Canva Production Readiness ==="

# 1. Verify API connectivity from production
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $CANVA_ACCESS_TOKEN" \
  "https://api.canva.com/rest/v1/users/me")
echo "[$([ $HTTP_CODE = 200 ] && echo 'PASS' || echo 'FAIL')] API connectivity: HTTP $HTTP_CODE"

# 2. Test design creation
DESIGN=$(curl -s -X POST "https://api.canva.com/rest/v1/designs" \
  -H "Authorization: Bearer $CANVA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"design_type":{"type":"custom","width":100,"height":100},"title":"Prod Test"}')
DESIGN_ID=$(echo "$DESIGN" | python3 -c "import sys,json; print(json.load(sys.stdin)['design']['id'])" 2>/dev/null)
echo "[$([ -n "$DESIGN_ID" ] && echo 'PASS' || echo 'FAIL')] Design creation: $DESIGN_ID"

# 3. Test export
if [ -n "$DESIGN_ID" ]; then
  EXPORT=$(curl -s -X POST "https://api.canva.com/rest/v1/exports" \
    -H "Authorization: Bearer $CANVA_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"design_id\":\"$DESIGN_ID\",\"format\":{\"type\":\"png\"}}")
  EXPORT_ID=$(echo "$EXPORT" | python3 -c "import sys,json; print(json.load(sys.stdin)['job']['id'])" 2>/dev/null)
  echo "[$([ -n "$EXPORT_ID" ] && echo 'PASS' || echo 'FAIL')] Export job: $EXPORT_ID"
fi

echo ""
echo "=== Done ==="
```

## Canva Integration Review

For **public integrations** (available to all Canva users), you must pass Canva's review:

1. Submit your integration for review in the Canva developer portal
2. Canva reviews security, OAuth implementation, and UX
3. Preview features (e.g., webhooks) are **not allowed** in public integrations
4. Fix any issues and resubmit

**Private integrations** (your organization only) do not require review.

## Health Check Endpoint

```typescript
app.get('/health', async (req, res) => {
  const start = Date.now();
  let canvaStatus = 'unknown';

  try {
    const me = await fetch('https://api.canva.com/rest/v1/users/me', {
      headers: { 'Authorization': `Bearer ${getServiceToken()}` },
      signal: AbortSignal.timeout(5000),
    });
    canvaStatus = me.ok ? 'healthy' : `error:${me.status}`;
  } catch {
    canvaStatus = 'unreachable';
  }

  res.json({
    status: canvaStatus === 'healthy' ? 'healthy' : 'degraded',
    services: { canva: { status: canvaStatus, latencyMs: Date.now() - start } },
    timestamp: new Date().toISOString(),
  });
});
```

## Monitoring Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| Auth failures | 401 errors > 0 | P1 |
| Rate limited | 429 errors > 5/min | P2 |
| Export failures | `license_required` or `internal_failure` | P3 |
| API unreachable | Connection timeout | P1 |
| Token refresh fails | Refresh returns error | P1 |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Token refresh loop | Revoked refresh token | Re-authorize user |
| Export stuck `in_progress` | Backend delay | Timeout after 120s, retry |
| Webhook URL rejected | HTTP not HTTPS | Use HTTPS endpoint |
| Review rejection | Using preview features | Remove preview-only features |

## Resources

- [Canva Connect Quickstart](https://www.canva.dev/docs/connect/quickstart/)
- [Creating Integrations](https://www.canva.dev/docs/connect/creating-integrations/)
- [Canva Changelog](https://www.canva.dev/docs/connect/changelog/)

## Next Steps

For version upgrades, see `canva-upgrade-migration`.
