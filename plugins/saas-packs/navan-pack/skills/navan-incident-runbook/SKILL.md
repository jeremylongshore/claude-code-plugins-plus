---
name: navan-incident-runbook
description: "Use when responding to Navan platform incidents \u2014 flight cancellations,\
  \ booking API failures, expense sync outages, or OAuth authentication errors.\n\
  Trigger with \"navan incident runbook\" or \"navan outage response\".\n"
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
# Navan Incident Runbook

## Overview

Structured incident response for Navan travel platform disruptions. Navan uses raw REST APIs with OAuth 2.0 — there is no SDK and no sandbox. All diagnostic commands run against production.

## Prerequisites

- Access to Navan admin console (Admin > Travel admin)
- OAuth credentials (`client_id`, `client_secret`) stored in your secret manager
- Familiarity with Navan's Ava AI assistant (in-app chat, first-line support)
- `curl` and `jq` for API health probing

## Instructions

### Step 1 — Classify Severity

| Severity | Condition | Response Time | Escalation |
|----------|-----------|---------------|------------|
| **P1 — Critical** | API fully down, all bookings failing | Immediate | Navan support + Ava AI + internal exec |
| **P2 — High** | Degraded performance, partial failures | 15 minutes | Navan support + internal travel admin |
| **P3 — Medium** | Intermittent errors, expense sync delays | 1 hour | Internal triage, monitor |
| **P4 — Low** | Cosmetic issues, non-blocking warnings | Next business day | Internal backlog |

### Step 2 — Triage with Ava AI

Before manual debugging, use Navan's built-in AI assistant:

1. Open the Navan app or visit [app.navan.com](https://app.navan.com)
2. Click the Ava chat icon (bottom-right)
3. Describe the issue — Ava can check booking status, rebook flights, and surface known outages
4. If Ava cannot resolve, proceed to API health checks

### Step 3 — API Health Check

```bash
# Test OAuth authentication
AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET")

HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -1)
BODY=$(echo "$AUTH_RESPONSE" | sed '$d')

echo "Auth endpoint: HTTP $HTTP_CODE"
echo "$BODY" | jq '{token_present: (.access_token != null), error: .error}' 2>/dev/null
```

```bash
# Test booking retrieval (requires valid token)
TOKEN=$(echo "$BODY" | jq -r '.access_token')
curl -s -w "\nHTTP %{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/bookings?page=0&size=50" | tail -1
```

### Step 4 — Incident-Specific Playbooks

**Booking API Failure (P1/P2):**
1. Confirm via API health check above — look for HTTP 500/503
2. Check if the issue is flight-specific or hotel-specific by testing both trip types
3. Direct travelers to Navan mobile app or phone support as fallback
4. Queue failed booking requests for retry with exponential backoff

**OAuth Token Failure (P1):**
1. Test with `curl` against `/ta-auth/oauth/token` — expect HTTP 200 with `access_token` field
2. If HTTP 401: credentials may be rotated; check Admin > Integrations
3. If HTTP 403: API access may be revoked; contact Navan admin
4. Re-request a token via `POST /ta-auth/oauth/token` with `grant_type=client_credentials`

**Expense Sync Failure (P2/P3):**
1. Check the Expense Transaction API status — this endpoint requires separate enablement
2. Verify your Fivetran/Airbyte connector status if using a data pipeline
3. Check TRANSACTION table freshness — incremental sync may be lagging
4. Validate that expense categories map correctly to your ERP

**Flight Cancellation / Disruption (P2):**
1. Use Ava AI to check rebooking options — Ava handles most rebookings automatically
2. Verify traveler's profile has correct loyalty program numbers
3. Check `/v1/bookings` for the affected booking UUID
4. Coordinate with travel admin for policy exception approvals if rebooking exceeds budget

### Step 5 — Escalation Path

| Level | Contact | When |
|-------|---------|------|
| **L1** | Ava AI assistant | Always start here |
| **L2** | Navan Help Center | Ava cannot resolve; [app.navan.com/app/helpcenter](https://app.navan.com/app/helpcenter) |
| **L3** | Navan account manager | P1/P2 unresolved after 30 minutes |
| **L4** | Internal executive sponsor | Business-critical travel disruption |

### Step 6 — Post-Incident Review

After resolution, create a post-incident record:

```bash
cat > "incident-$(date +%Y%m%d-%H%M%S).md" <<'INCEOF'
## Incident Report
- **Severity**: P?
- **Duration**: Start — End
- **Impact**: Number of affected travelers/bookings
- **Root Cause**: (API outage / credential issue / sync failure / ...)
- **Resolution**: Steps taken
- **Prevention**: Changes to avoid recurrence
INCEOF
```

## Output

- Severity classification for the incident
- API health check results confirming platform vs local issue
- Executed playbook steps with outcomes
- Escalation actions taken with timestamps
- Post-incident report document

## Error Handling

| HTTP Code | Meaning | Runbook Action |
|-----------|---------|----------------|
| 401 | Authentication failed | Check credential rotation; re-authenticate |
| 403 | Access denied | Verify API integration is enabled in admin |
| 429 | Rate limited | Back off; check `Retry-After` header value |
| 500 | Server error | Navan-side issue; escalate to L2/L3 |
| 502/503 | Service unavailable | Platform outage; escalate immediately |

## Examples

Quick API status check during an incident:

```bash
# One-liner health probe
curl -s -o /dev/null -w "Auth: %{http_code} (%{time_total}s)\n" \
  -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET"
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Support portal and known issues
- [Navan Security](https://navan.com/security) — Infrastructure and compliance details
- [Navan Integrations](https://navan.com/integrations) — Connector status and documentation

## Next Steps

- Use `navan-debug-bundle` to collect full diagnostic data for support tickets
- Use `navan-prod-checklist` to harden your integration against future incidents
- Use `navan-common-errors` for detailed error code interpretation
