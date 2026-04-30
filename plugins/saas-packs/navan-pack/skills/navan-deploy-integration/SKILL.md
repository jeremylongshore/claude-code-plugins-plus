---
name: navan-deploy-integration
description: 'Use when deploying Navan integrations with ERP systems (NetSuite, Sage
  Intacct, Xero), HRIS platforms (Workday, BambooHR), or identity providers (Okta,
  Azure AD).

  Trigger with "navan deploy integration" or "navan erp setup" or "navan sso deployment".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Deploy Integration

## Overview

Navan connects to enterprise systems through multiple integration methods: direct REST API with OAuth 2.0, SCIM for user provisioning, SFTP for batch file exchange, SAML/OIDC for SSO, and webhooks for real-time events. There is no SDK — all integrations use Navan's REST endpoints or admin console configuration. This skill provides deployment checklists for the three most common integration categories: ERP expense sync, HRIS user provisioning, and identity provider SSO.

## Prerequisites

- **Navan Admin** account with integration management permissions
- **OAuth 2.0 credentials** — `client_id` and `client_secret` from Admin > API Settings
- **Target system admin access** — NetSuite/Sage Intacct/Xero admin, Workday/BambooHR admin, or Okta/Azure AD admin
- API base URL: `https://api.navan.com/v1`

## Instructions

### Category A — ERP Expense Sync (NetSuite, Sage Intacct, Xero, QuickBooks)

**Deployment Checklist:**

1. **Create OAuth credentials** in Navan Admin > API Settings
2. **Configure GL code mappings** — Map Navan expense categories to your chart of accounts
3. **Set cost center mappings** — Align Navan departments with ERP cost centers
4. **Enable expense export** via REST API:

```bash
# Fetch approved expenses ready for ERP sync
curl -s -X GET "https://api.navan.com/v1/expenses?status=approved&limit=50" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json"

# Response includes fields for ERP mapping:
# {
#   "uuid": "exp_abc123",
#   "amount": 245.50,
#   "currency": "USD",
#   "category": "meals_entertainment",
#   "cost_center": "engineering",
#   "gl_code": "6200",
#   "receipt_url": "https://api.navan.com/v1/receipts/exp_abc123",
#   "approved_at": "2026-03-20T14:30:00Z"
# }
```

5. **Set up sync schedule** — Navan supports daily or real-time export via webhooks
6. **Validate with test expenses** — Submit 3-5 test expenses through the full approval flow
7. **Enable in production** — Switch from sandbox to production OAuth credentials

### Category B — HRIS User Provisioning (Workday, BambooHR, ADP)

**SCIM Provisioning Setup:**

1. **Enable SCIM** in Navan Admin > Integrations > User Provisioning
2. **Configure SCIM endpoint** in your HRIS:
   - SCIM Base URL: `https://api.navan.com/scim/v2`
   - Authentication: OAuth 2.0 Bearer Token
3. **Map user attributes:**

| HRIS Field | Navan SCIM Attribute | Required |
|------------|---------------------|----------|
| Email | `userName` | Yes |
| First Name | `name.givenName` | Yes |
| Last Name | `name.familyName` | Yes |
| Department | `urn:navan:department` | Recommended |
| Manager | `urn:navan:manager_email` | Recommended |
| Cost Center | `urn:navan:cost_center` | Optional |

4. **Test provisioning** — Create a test user in HRIS and verify they appear in Navan within 15 minutes
5. **Test deprovisioning** — Deactivate the test user and confirm Navan access is revoked
6. **Verify via API:**

```bash
# Check provisioned users
curl -s "https://api.navan.com/v1/users?provisioning_source=scim&limit=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq '.[] | {email, status, provisioned_at}'
```

### Category C — SSO Deployment (Okta, Azure AD)

**SAML Configuration:**

1. **Create SAML application** in your IdP (Okta or Azure AD)
2. **Configure Navan SAML settings** in Admin > Security > SSO:
   - Entity ID: `https://app.navan.com/saml/metadata`
   - ACS URL: `https://app.navan.com/saml/acs`
   - Name ID Format: `emailAddress`
3. **Map SAML attributes:**

```
email       → user.email        (Required)
firstName   → user.firstName    (Required)
lastName    → user.lastName     (Required)
department  → user.department   (Optional — enables policy routing)
```

4. **Upload IdP metadata XML** to Navan Admin console
5. **Enable JIT provisioning** (optional) — Auto-create Navan accounts on first SSO login
6. **Test with a pilot group** — Assign 5-10 users before org-wide rollout
7. **Enforce SSO** — After pilot validation, enable "SSO Required" to disable password login

## Output

Each integration deployment produces:
- **Connection validation** confirming data flows between systems
- **Field mapping documentation** for ongoing maintenance
- **Test results** from pilot user group
- **Rollback instructions** if issues arise post-deployment

## Error Handling

| HTTP Code | Meaning | Resolution |
|-----------|---------|------------|
| `400` | Invalid field mapping or malformed request | Review GL code / attribute mappings |
| `401` | OAuth token expired or invalid | Rotate credentials in Navan Admin |
| `403` | Integration not enabled for your plan | Verify Navan plan includes this integration (Enterprise required for some) |
| `409` | Duplicate user in SCIM provisioning | Check for existing user with same email |
| `422` | Validation error on expense export | Verify required fields (amount, currency, category) are present |
| `429` | Rate limited | Reduce sync frequency or implement exponential backoff |

## Examples

**Automated daily expense export to NetSuite:**

```bash
#!/usr/bin/env bash
# scripts/navan-netsuite-sync.sh
set -euo pipefail

# Authenticate
TOKEN=$(curl -sf -X POST https://api.navan.com/ta-auth/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${NAVAN_CLIENT_ID}&client_secret=${NAVAN_CLIENT_SECRET}" \
  | jq -r '.access_token')

# Fetch yesterday's approved expenses
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
curl -s "https://api.navan.com/v1/expenses?status=approved&approved_after=${YESTERDAY}T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN" \
  -o /tmp/navan-expenses.json

EXPENSE_COUNT=$(jq length /tmp/navan-expenses.json)
echo "Exporting $EXPENSE_COUNT expenses to NetSuite"
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Integration setup guides
- [Navan Integrations Directory](https://navan.com/integrations) — Full list of supported connectors
- [SCIM Protocol Spec (RFC 7644)](https://datatracker.ietf.org/doc/html/rfc7644) — SCIM provisioning standard
- [Navan Pricing](https://navan.com/pricing) — Plan comparison for integration availability

## Next Steps

- Add `navan-observability` to monitor integration health post-deployment
- Add `navan-webhooks-events` for real-time event-driven sync instead of polling
- See `navan-security-basics` for credential rotation and access control
