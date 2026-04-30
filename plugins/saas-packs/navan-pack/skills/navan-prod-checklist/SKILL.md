---
name: navan-prod-checklist
description: "Use when validating production readiness for a Navan API integration\
  \ \u2014 credential rotation, alerting, rate limits, SSO, SCIM, and compliance audit\
  \ trails.\nTrigger with \"navan prod checklist\" or \"navan production readiness\"\
  .\n"
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Production Checklist

## Overview

Gated production readiness verification for Navan REST API integrations. Navan has no SDK and no sandbox — production is the only environment, making this checklist critical.

## Prerequisites

- Navan admin access (Admin > Travel admin > Settings)
- OAuth credentials stored in a secret manager (credentials are viewable only once)
- SSO identity provider configured (Okta, Azure AD, or Google Workspace)
- `curl` and `jq` for verification commands

## Instructions

### Domain 1 — Credential Security

- [ ] **Secret storage**: OAuth `client_id` and `client_secret` stored in a secret manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault) — never in environment variables, config files, or source control
- [ ] **Rotation plan documented**: Schedule for rotating credentials (recommend 90-day cycle)
- [ ] **Zero-downtime rotation tested**: Dual-credential swap procedure validated

```bash
# Verify current credentials work
curl -s -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | jq '{authenticated: (.access_token != null), error: .error}'
```

**Rotation procedure:**
1. Generate new credentials in Admin > Integrations (old ones remain valid)
2. Deploy new credentials to secret manager
3. Update application configuration to reference new secret version
4. Verify new credentials with `/ta-auth/oauth/token`
5. Revoke old credentials in Admin > Integrations
6. Confirm old credentials return HTTP 401

### Domain 2 — Error Handling and Alerting

- [ ] **All HTTP error codes handled**: 400, 401, 403, 404, 429, 500, 502, 503
- [ ] **Retry logic with exponential backoff**: For 429 and 5xx responses
- [ ] **Alert thresholds configured**: Error rate > 5% over 5 minutes triggers alert
- [ ] **Dead letter queue**: Failed API requests stored for retry or manual review

```bash
# Health check endpoint pattern
health_check() {
  RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/navan-health.json \
    -X POST "https://api.navan.com/ta-auth/oauth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET")

  if [ "$RESPONSE" = "200" ]; then
    echo '{"status":"healthy","navan_api":"reachable"}'
  elif [ "$RESPONSE" = "429" ]; then
    echo '{"status":"degraded","reason":"rate_limited"}'
  else
    echo "{\"status\":\"unhealthy\",\"http_code\":\"$RESPONSE\"}"
  fi
}
```

### Domain 3 — Rate Limiting

- [ ] **Client-side rate limiter**: Token bucket or sliding window before API calls
- [ ] **429 response handling**: Parse `Retry-After` header and honor wait time
- [ ] **Request queuing**: Burst requests queued rather than dropped
- [ ] **Rate limit monitoring**: Dashboard showing API call volume and 429 frequency

### Domain 4 — Data Pipeline

- [ ] **BOOKING table sync**: Weekly full refresh configured (Fivetran, Airbyte, or custom)
- [ ] **TRANSACTION table sync**: Incremental sync with deduplication by transaction UUID
- [ ] **Data backup strategy**: Export snapshots stored in cloud storage with retention policy
- [ ] **Reconciliation checks**: Automated comparison between Navan data and ERP records

### Domain 5 — SSO and User Provisioning

- [ ] **SAML SSO verified**: Login flow tested end-to-end through identity provider

```bash
# Verify users are synced via API
TOKEN=$(curl -s -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | jq -r '.access_token')

curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/users" \
  | jq '{total_users: (.data | length), sample: .data[0] | {id, email, status}}'
```

- [ ] **SCIM provisioning active**: User create/update/deactivate syncing from IdP
- [ ] **Deprovisioning tested**: Terminated employees removed from Navan within 24 hours
- [ ] **Role mapping documented**: IdP groups mapped to Navan roles (traveler, approver, admin)

### Domain 6 — Compliance and Audit

- [ ] **API access logging**: All Navan API calls logged with timestamp, endpoint, response code, and user context
- [ ] **Audit trail retention**: Logs retained per your compliance requirements (SOC 2: 1 year minimum)
- [ ] **Data classification**: Navan data (PII, payment info) classified and handled per PCI DSS L1
- [ ] **Compliance certifications verified**: Confirm Navan's SOC 1/2 Type II, ISO 27001, PCI DSS L1, GDPR status at [navan.com/security](https://navan.com/security)

## Output

A completed checklist with:
- Pass/fail status for each domain
- Verification command output proving each check
- Identified gaps with remediation plan and owner
- Sign-off from security and operations leads

## Error Handling

| Check Failure | Impact | Remediation |
|---------------|--------|-------------|
| Credentials in plaintext | Critical — security breach risk | Move to secret manager immediately |
| No retry logic on 429 | High — cascading failures under load | Implement exponential backoff |
| SCIM not configured | Medium — manual user management overhead | Enable SCIM in IdP and Navan admin |
| No audit logging | High — compliance violation | Add structured logging to API client |

## Examples

Run a quick pre-launch validation:

```bash
# Rapid smoke test — auth + user count + timing
echo "=== Navan Production Smoke Test ==="
curl -s -w "Auth: %{http_code} (%{time_total}s)\n" -o /tmp/navan-auth.json \
  -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET"

TOKEN=$(jq -r '.access_token' /tmp/navan-auth.json)
curl -s -w "Users: %{http_code} (%{time_total}s)\n" -o /tmp/navan-users.json \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/users"
echo "User count: $(jq '.data | length' /tmp/navan-users.json)"
```

## Resources

- [Navan Security](https://navan.com/security) — SOC 2, ISO 27001, PCI DSS certifications
- [Navan Integrations](https://navan.com/integrations) — Connector catalog and setup guides
- [Navan Help Center](https://app.navan.com/app/helpcenter) — Admin documentation

## Next Steps

- Use `navan-upgrade-migration` for ongoing API change management
- Use `navan-observability` for monitoring stack setup
- Use `navan-incident-runbook` if production issues arise post-launch
