---
name: intercom-prod-checklist
description: 'Execute Intercom production readiness checklist and rollback procedures.

  Use when deploying Intercom integrations to production, preparing for launch,

  or implementing go-live validation.

  Trigger with phrases like "intercom production", "deploy intercom",

  "intercom go-live", "intercom launch checklist", "intercom production readiness".

  '
allowed-tools: Read, Bash(curl:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Production Checklist

## Overview

Complete checklist for deploying Intercom integrations to production, covering
authentication, error handling, rate limits, webhooks, and monitoring. Work the
pre-deployment checklist below section by section, run the pre-flight script as
the go-live gate, and keep the rollback procedure ready before you launch.

## Prerequisites

- A production Intercom workspace with an access token issued from the Developer Hub.
- `$INTERCOM_ACCESS_TOKEN` exported in the environment where you run the checks.
- `curl` and `jq` available for the pre-flight and status probes.
- The integration deployed behind a feature flag so it can be disabled without a redeploy.
- (Optional) `$WEBHOOK_URL` set if the integration receives Intercom webhooks.

## Instructions

Work through the checklist in order. Each group gates a distinct failure class —
do not skip a group because "it probably works."

### Authentication and secrets

- [ ] Production access token stored in secret manager (not env files)
- [ ] Token has minimal required OAuth scopes
- [ ] Token rotation procedure documented and tested
- [ ] Separate tokens for dev/staging/production workspaces
- [ ] No hardcoded tokens in source code (verified with `grep -r "dG9r" .`)

### API integration quality

- [ ] All API calls wrapped in error handling (`try/catch` with `IntercomError`)
- [ ] 429 rate limit retry with exponential backoff implemented
- [ ] 5xx server error retry implemented
- [ ] Request timeouts configured (recommended: 30s)
- [ ] Pagination handles cursor-based iteration correctly
- [ ] Contact search uses compound queries efficiently

### Webhook endpoints

- [ ] Webhook URL uses HTTPS (Intercom requires it)
- [ ] `X-Hub-Signature` verification implemented (HMAC-SHA1)
- [ ] Webhook handler responds within 5 seconds (Intercom timeout)
- [ ] Idempotency: duplicate webhooks handled gracefully
- [ ] Failed webhook retry handled (Intercom retries once after 1 min)

### Data handling

- [ ] PII redacted from logs (emails, names, phone numbers)
- [ ] Contact data cached with appropriate TTL
- [ ] GDPR deletion handler implemented for contact data
- [ ] Custom attributes validated before sending to API

### Monitoring and alerting

- [ ] Health check endpoint includes Intercom connectivity test
- [ ] Error rate alerting configured (threshold: 5% over 5 min)
- [ ] Rate limit usage tracked (alert at 80% of limit)
- [ ] Latency monitoring (alert if P95 > 2 seconds)
- [ ] Intercom status page monitored (https://status.intercom.com)

### Health check and go-live

- [ ] Production health endpoint returns `503` when Intercom is unhealthy —
  skeleton below, full implementation in
  [references/implementation.md](references/implementation.md).
- [ ] Pre-flight verification script passes against the production token —
  full script in [references/examples.md](references/examples.md).
- [ ] Rollback procedure rehearsed — see
  [references/examples.md](references/examples.md).

Minimal health-check skeleton (the full module classifies degraded-vs-unhealthy
from the `IntercomError` status code and wires an Express `/health` route — see
[the full walkthrough](references/implementation.md)):

```typescript
async function checkIntercomHealth(client: IntercomClient) {
  const start = Date.now();
  try {
    await client.admins.list();
    return { status: "healthy", latencyMs: Date.now() - start };
  } catch (err) {
    // 429 → degraded, 401 → unhealthy + unauthenticated, else unhealthy
    return { status: "unhealthy", latencyMs: Date.now() - start };
  }
}
```

## Output

- A completed checklist where every applicable box is checked before launch.
- A pre-flight run that prints `Auth: PASS`, current rate-limit headroom, the
  Intercom status indicator (`none` = clear), and the webhook endpoint HTTP code.
  A non-`200` auth code exits non-zero and blocks the go-live.
- A `/health` endpoint returning `200` when Intercom is healthy and `503` when it
  is degraded or unhealthy, with the classification reason in the JSON body.

## Error Handling

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| API unreachable | 5xx > 10/min | P1 | Enable fallback, check status page |
| Auth failure | Any 401 | P1 | Rotate token, verify in Developer Hub |
| Rate limited | 429 > 5/min | P2 | Reduce request volume, add queuing |
| High latency | P95 > 3s | P2 | Check Intercom status, enable caching |
| Webhook failures | Delivery errors | P3 | Check endpoint health, verify signature |

If the integration is failing in production, run the rollback procedure in
[references/examples.md](references/examples.md): flip the feature flag off first,
then roll back the deployment, verify `/health`, and disable webhooks in the
Developer Hub to stop queued deliveries reaching an unhealthy endpoint.

## Examples

- **Production health check** — a full TypeScript module plus Express `/health`
  endpoint with status classification: [references/implementation.md](references/implementation.md).
- **Pre-flight verification script** — a `set -euo pipefail` bash gate that
  checks auth, rate-limit headroom, platform status, and webhook reachability,
  with expected output: [references/examples.md](references/examples.md).
- **Rollback procedure** — feature-flag disable, `kubectl rollout undo`, health
  verification, and webhook teardown: [references/examples.md](references/examples.md).

## Resources

- [Intercom Status](https://status.intercom.com)
- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)
- [Webhook Setup](https://developers.intercom.com/docs/webhooks/setting-up-webhooks)
- Production health check + monitoring detail: [references/implementation.md](references/implementation.md)
- Pre-flight + rollback scripts: [references/examples.md](references/examples.md)

## Next Steps

For version upgrades, see the `intercom-upgrade-migration` skill in this pack,
which covers breaking-change migration and dependency bumps.
