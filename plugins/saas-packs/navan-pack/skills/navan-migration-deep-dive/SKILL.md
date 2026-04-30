---
name: navan-migration-deep-dive
description: "Use when planning or executing a migration from SAP Concur or legacy\
  \ TMC to Navan \u2014 data migration, user provisioning, policy recreation, and\
  \ cutover planning.\nTrigger with \"navan migration deep dive\" or \"migrate to\
  \ navan from concur\".\n"
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
# Navan Migration Deep Dive

## Overview

End-to-end migration playbook for moving from SAP Concur or legacy travel management systems to Navan. Navan uses REST APIs with OAuth 2.0 — there is no SDK, no automated migration tool, and no sandbox for testing.

## Prerequisites

- Admin access to both source system (SAP Concur, legacy TMC) and Navan
- Navan OAuth credentials from Admin > Travel admin > Settings > Integrations
- Data export from source system (expense reports, itineraries, user directory)
- SSO identity provider (Okta, Azure AD, Google Workspace) for user provisioning
- Executive sponsor and travel program manager identified

## Instructions

### Phase 1 — Discovery and Planning (Weeks 1-2)

**Inventory current state:**

| Data Category | SAP Concur Source | Navan Target | Migration Method |
|---------------|-------------------|--------------|-----------------|
| User profiles | Concur user export (CSV) | SCIM provisioning or `/get_users` API | IdP-driven |
| Travel policies | Concur policy rules | Navan admin console | Manual recreation |
| Expense categories | Concur expense types | Navan expense categories | Mapping table |
| Historical bookings | Concur trip export | Archive only (not imported) | Export + cold storage |
| Historical expenses | Concur expense reports | Archive only (not imported) | Export + cold storage |
| Approval workflows | Concur approval chains | Navan approval policies | Manual recreation |
| Corporate card feeds | Concur card integrations | Navan card program or integration | New setup |

**Key decision: historical data strategy.** Navan does not support importing historical booking or expense data. Export source system data to a data warehouse or archive storage for reference. Future Navan data starts fresh from migration day.

### Phase 2 — User Provisioning (Weeks 2-3)

**Option A — SCIM provisioning (recommended):**
1. Configure SCIM connector in your IdP (Okta, Azure AD)
2. Map IdP groups to Navan roles: traveler, travel arranger, approver, admin
3. Enable provisioning — users are created in Navan automatically
4. Test with a pilot group (10-20 users) before full rollout

**Option B — CSV bulk upload:**
1. Export user directory from source system
2. Format per Navan's CSV template (available in Admin > User Management)
3. Upload via Navan admin console
4. Manually verify role assignments

**Verify provisioned users via API:**

```bash
TOKEN=$(curl -s -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | jq -r '.access_token')

# Count provisioned users
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/users" \
  | jq '{total: (.data | length), sample: [.data[:3][] | {email, status}]}'
```

### Phase 3 — Policy Recreation (Weeks 3-4)

Recreate travel policies in Navan admin console. Key policy areas:

1. **Booking policies**: Flight class limits (economy/business by route length), hotel rate caps by city, advance booking requirements
2. **Approval workflows**: Auto-approve under threshold, manager approval above, VP approval for international
3. **Expense policies**: Per diem rates, receipt requirements, out-of-policy flagging
4. **Preferred vendors**: Airline/hotel preferences, negotiated corporate rates, loyalty program linkage
5. **Traveler profiles**: Default seat preferences, meal requirements, loyalty numbers, passport info

**SAP Concur policy mapping pitfalls:**
- Concur's "travel rules" do not map 1:1 to Navan's policy engine — expect manual translation
- Concur custom fields require mapping to Navan's cost center / department / project structure
- Concur delegation rules differ from Navan's travel arranger model

### Phase 4 — Parallel Running (Weeks 4-6)

Run both systems simultaneously to validate the migration:

| Activity | Source System | Navan | Duration |
|----------|-------------|-------|----------|
| New bookings | Disabled for pilot group | Active for pilot group | 2 weeks |
| Expense submission | Active (all users) | Active (pilot group) | 2 weeks |
| Approval workflows | Active | Tested with pilot | 2 weeks |
| Reporting | Primary | Validated against source | 2 weeks |

```bash
# Monitor booking volume in Navan during parallel run
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/bookings?page=0&size=50&createdFrom=$(date -d '7 days ago' +%Y-%m-%d)" \
  | jq '{total_bookings: (.data | length)}'
```

**Reconciliation checks:**
- Compare booking counts between systems weekly
- Validate expense report totals match between systems
- Verify approval chains produce consistent outcomes
- Test edge cases: international travel, group bookings, last-minute changes

### Phase 5 — Cutover (Week 6-7)

**Go/no-go checklist (all must pass):**

- [ ] All users provisioned and can log in via SSO
- [ ] Travel policies match source system intent (reviewed by travel manager)
- [ ] Pilot group has booked 20+ trips without issues
- [ ] Expense submission and approval tested end-to-end
- [ ] Corporate card feeds connected (if applicable)
- [ ] Navan API integration healthy (auth + data endpoints return 200)
- [ ] Fivetran/Airbyte data sync running for BOOKING and TRANSACTION tables
- [ ] Rollback procedure documented and tested
- [ ] User training materials distributed
- [ ] IT support team briefed on Navan admin and Ava AI assistant
- [ ] Source system read-only access preserved for historical lookups

**Cutover steps:**
1. Send company-wide communication (24 hours before)
2. Disable new bookings in source system
3. Enable Navan SSO for all users
4. Activate all Navan travel policies
5. Switch corporate card feeds to Navan
6. Verify first production bookings succeed
7. Monitor error rates for 48 hours

### Phase 6 — Post-Migration (Weeks 7-10)

- Monitor Navan API health daily for first two weeks
- Track user adoption metrics (login rate, booking volume, Ava usage)
- Collect feedback from frequent travelers and approvers
- Maintain source system in read-only mode for 90 days (historical reference)
- Decommission source system after retention period

## Output

- Migration project plan with phase timelines and owners
- Data mapping document (source fields to Navan structure)
- User provisioning report showing successful account creation
- Parallel running reconciliation results
- Go/no-go checklist with sign-offs
- Post-migration adoption metrics

## Error Handling

| Issue | Impact | Resolution |
|-------|--------|------------|
| SCIM provisioning fails | Users cannot access Navan | Fall back to CSV upload; check IdP connector logs |
| SSO login fails | Users locked out | Verify SAML metadata; test with Navan admin account |
| Policy mismatch | Out-of-policy bookings approved | Audit first 50 bookings; adjust policy rules |
| API returns 403 on `/get_users` | Cannot verify provisioning | Confirm API integration enabled in Admin > Integrations |
| Data sync not running | No reporting data | Check Fivetran/Airbyte connector status and credentials |

## Examples

Quick migration readiness assessment:

```bash
# Verify Navan API access and user count
echo "=== Migration Readiness Check ==="
TOKEN=$(curl -s -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | jq -r '.access_token')

echo "API Auth: $([ -n "$TOKEN" ] && echo 'OK' || echo 'FAILED')"
USERS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/users" | jq '.data | length')
echo "Provisioned users: $USERS"
BOOKINGS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/bookings?page=0&size=50" | jq '.data | length')
echo "Total bookings: $BOOKINGS"
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Admin setup guides and migration support
- [Navan Integrations](https://navan.com/integrations) — ERP and data connector options
- [Navan Security](https://navan.com/security) — SOC 2, ISO 27001, GDPR compliance for vendor evaluation

## Next Steps

- Use `navan-install-auth` to set up OAuth credentials for the migration
- Use `navan-prod-checklist` before cutover to validate production readiness
- Use `navan-data-sync` to configure Fivetran/Airbyte data pipelines
