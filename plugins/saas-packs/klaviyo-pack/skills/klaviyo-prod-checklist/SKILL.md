---
name: klaviyo-prod-checklist
description: 'Execute Klaviyo production deployment checklist and validation procedures.

  Use when deploying Klaviyo integrations to production, preparing for launch,

  or implementing go-live procedures for email/SMS marketing.

  Trigger with phrases like "klaviyo production", "deploy klaviyo",

  "klaviyo go-live", "klaviyo launch checklist", "klaviyo prod ready".

  '
allowed-tools: Read, Bash(curl:*), Bash(npm:*), Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Production Checklist

## Overview

Complete checklist for deploying Klaviyo integrations to production, with health
checks, rollback procedures, and validation against real Klaviyo API endpoints.
Work the pre-deployment checklist below, run the pre-flight script, then verify
the live health endpoint before declaring the deploy done.

## Prerequisites

- Staging environment tested and verified
- Production API key with correct scopes (`pk_*`)
- Webhook signing secret configured
- Monitoring and alerting ready

## Instructions

Follow these steps in order. Steps 1–2 are read-only audits of the codebase and
config; steps 3–5 exercise the live API and health surface.

1. **Audit secrets and code.** Confirm the production key lives in a secret
   manager and no keys are hardcoded — run `Grep`/`grep -r "pk_" src/` to catch
   leaks, and `Read` the deployment manifest to verify scopes. See the
   Pre-Deployment Checklist below.
2. **Audit the integration, resilience, and webhooks.** Walk the remaining
   checklist sections (API integration, error handling, webhook security,
   monitoring).
3. **Run the pre-flight script** (`scripts/preflight-klaviyo.sh`) to validate the
   status page, API auth, rate-limit headroom, and pinned SDK version.
4. **Deploy**, then **verify the health endpoint** returns `healthy`.
5. **Keep the rollback path ready** (feature flag first) in case metrics regress.

Health check, pre-flight script, and rollback code are in
[references/implementation.md](references/implementation.md).

### Pre-Deployment Checklist

#### Authentication & Secrets

- [ ] Production `KLAVIYO_PRIVATE_KEY` stored in secret manager (not env file)
- [ ] Key has minimal scopes (only what the app needs)
- [ ] Webhook signing secret (`KLAVIYO_WEBHOOK_SIGNING_SECRET`) configured
- [ ] Public key (`KLAVIYO_PUBLIC_KEY`) set for client-side tracking (if used)
- [ ] No hardcoded keys in codebase (`grep -r "pk_" src/`)

#### API Integration

- [ ] All API calls use `klaviyo-api` SDK (not raw HTTP)
- [ ] SDK version pinned in `package.json` (not `^` or `*`)
- [ ] `revision` header set to `2024-10-15` (or current supported revision)
- [ ] All profile creates use `createOrUpdateProfile` (upsert, not create)
- [ ] Events include `uniqueId` for deduplication where applicable
- [ ] Phone numbers validated as E.164 format (`+15551234567`)

#### Error Handling & Resilience

- [ ] 429 retry logic honors `Retry-After` header
- [ ] 5xx errors retried with exponential backoff
- [ ] 401/403 errors logged with alert (key rotation needed)
- [ ] Circuit breaker or graceful degradation when Klaviyo is down
- [ ] Request queue prevents exceeding 75 req/s burst limit

#### Webhook Security

- [ ] Webhook endpoint uses HTTPS only
- [ ] HMAC-SHA256 signature verification enabled
- [ ] Idempotency handling (dedup by event ID)
- [ ] Webhook endpoint returns 200 within 30 seconds

#### Monitoring

- [ ] Health check endpoint includes Klaviyo connectivity test
- [ ] Alert on 429 rate (>5/min = P2)
- [ ] Alert on 401/403 errors (any = P1)
- [ ] Alert on 5xx errors (>10/min = P1)
- [ ] API latency tracked (P95 > 5s = P2)
- [ ] Klaviyo status page monitored ([status.klaviyo.com](https://status.klaviyo.com))

## Output

Working through this skill produces:

- A completed pre-deployment checklist (every box ticked, or a documented
  exception).
- A pre-flight run that exits `0` with all four gates green (status page, API
  auth `200`, rate-limit headroom, pinned SDK version) — see
  [references/examples.md](references/examples.md).
- A live `/health` endpoint that returns `healthy` with sub-500ms latency and
  the resolved `accountId`.
- A rehearsed rollback path (feature flag → git revert → `kubectl rollout undo`).

A go-live is "prod ready" only when the checklist is complete, pre-flight is
green, and the health endpoint reports `healthy`.

## Error Handling

Map each failure to the correct severity and response. Full alert-threshold
table:

| Alert | Condition | Severity |
|-------|-----------|----------|
| API Auth Failure | Any 401/403 | P1 -- key may be revoked |
| API Unreachable | 5xx > 10/min | P1 -- check status page |
| Rate Limited | 429 > 5/min | P2 -- reduce request volume |
| High Latency | P95 > 5s | P2 -- check network/Klaviyo load |
| Webhook Signature Invalid | Any rejection | P2 -- verify signing secret |

- **Pre-flight fails auth (`403`/`401`):** the key is revoked or under-scoped.
  Rotate/repair before deploying — do not proceed (see Example 2 in
  [references/examples.md](references/examples.md)).
- **Health endpoint `degraded`:** Klaviyo returned `429`. Back off; honor
  `Retry-After` and confirm the request queue caps at 75 req/s.
- **Health endpoint `down`:** Klaviyo unreachable (5xx) — check
  [status.klaviyo.com](https://status.klaviyo.com) and trip the circuit breaker.
- **Metrics regress post-deploy:** execute the rollback procedure, feature flag
  first, from [references/implementation.md](references/implementation.md).

## Examples

Read the full endpoint on a live integration to confirm health before sign-off:

```bash
curl -s localhost:3000/health | python3 -m json.tool
# → { "status": "healthy", "services": { "klaviyo": { "status": "healthy", "latencyMs": 142, ... } } }
```

Four worked runs — green pre-flight, a blocked `403`, reading the health
endpoint, and an instant feature-flag rollback — are in
[references/examples.md](references/examples.md).

## Resources

- [Klaviyo Status Page](https://status.klaviyo.com)
- [API Versioning Policy](https://developers.klaviyo.com/en/docs/api_versioning_and_deprecation_policy)
- [Rate Limits](https://developers.klaviyo.com/en/docs/rate_limits_and_error_handling)
- [Implementation code](references/implementation.md) — health check, pre-flight script, rollback
- [Worked examples](references/examples.md) — green/failed pre-flight, health reads, rollback

## Next Steps

For version upgrades, see `klaviyo-upgrade-migration`.
