---
name: hubspot-incident-runbook
description: |
  Execute HubSpot incident response with triage, mitigation, and postmortem.
  Use when responding to HubSpot API outages, investigating CRM errors,
  or running post-incident reviews for HubSpot integration failures.
  Trigger with phrases like "hubspot incident", "hubspot outage",
  "hubspot down", "hubspot on-call", "hubspot emergency", "hubspot broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Incident Runbook

## Overview

Rapid incident response procedures for HubSpot CRM integration failures, including triage, mitigation, and postmortem templates.

## Prerequisites

- Access to application logs and metrics
- `HUBSPOT_ACCESS_TOKEN` available for manual testing
- Communication channels (Slack, PagerDuty)

## Instructions

### Step 1: Quick Triage (< 2 minutes)

```bash
#!/bin/bash
# hubspot-triage.sh -- Run this first during any incident

echo "=== HubSpot Quick Triage ==="
echo "Time: $(date -u)"

# 1. Is HubSpot itself down?
echo ""
echo "--- HubSpot Platform Status ---"
curl -s https://status.hubspot.com/api/v2/summary.json | jq '{
  status: .status.description,
  active_incidents: [.incidents[] | {name, status, updated_at}]
}'

# 2. Can we reach the API?
echo ""
echo "--- API Connectivity ---"
STATUS=$(curl -so /dev/null -w "%{http_code}" \
  https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN")
echo "API Status: HTTP $STATUS"

# 3. Rate limit state
echo ""
echo "--- Rate Limits ---"
curl -sI https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i "ratelimit\|retry-after"

# 4. Check our health endpoint
echo ""
echo "--- Our Health Check ---"
curl -sf https://your-app.com/health | jq '.services.hubspot' || echo "Health check failed"
```

### Step 2: Decision Tree

```
Is HubSpot status page showing an incident?
├── YES → HubSpot-side outage
│   ├── Enable fallback/degraded mode
│   ├── Notify stakeholders: "HubSpot platform issue"
│   └── Monitor status page for resolution
└── NO → Our integration issue
    ├── Is the error 401/403?
    │   ├── YES → Token revoked or regenerated
    │   │   └── Get new token from Settings > Private Apps
    │   └── NO → Continue diagnosis
    ├── Is the error 429?
    │   ├── YES → Rate limit exceeded
    │   │   ├── Check if another app is consuming quota
    │   │   └── Reduce request volume or wait for reset
    │   └── NO → Continue diagnosis
    ├── Is the error 5xx?
    │   ├── YES → HubSpot transient error (not on status page)
    │   │   └── SDK retries should handle this (numberOfApiCallRetries)
    │   └── NO → Application bug
    └── Check application logs for the real error
```

### Step 3: Common Incident Responses

#### Token Revoked (401)

```bash
# Verify current token
curl -s https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" | jq .category
# If "INVALID_AUTHENTICATION":

# 1. Go to HubSpot Settings > Integrations > Private Apps
# 2. Regenerate the access token
# 3. Update in your secret manager:
aws secretsmanager update-secret --secret-id hubspot/production \
  --secret-string '{"access_token":"pat-na1-NEW_TOKEN"}'

# 4. Restart/redeploy application
# 5. Verify connectivity
```

#### Rate Limit Exceeded (429)

```bash
# Check remaining quota
curl -sI https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i "daily-remaining"

# If daily limit is exhausted:
# 1. Wait for midnight UTC reset (check Retry-After header)
# 2. Identify the source of excessive calls in logs
# 3. Emergency: request limit increase from HubSpot support
```

#### HubSpot Platform Outage (5xx)

```bash
# Enable degraded mode if you have one
# export HUBSPOT_FALLBACK=true

# Typical HubSpot incident resolution: 15 min to 2 hours
# Monitor: https://status.hubspot.com
# Subscribe to updates via email/SMS on status page
```

### Step 4: Communication Templates

**Internal (Slack):**
```
:red_circle: P1 INCIDENT: HubSpot CRM Integration
Status: INVESTIGATING
Impact: [e.g., "Contact syncing is delayed", "Deal creation failing"]
Cause: [e.g., "HubSpot API returning 429", "Access token expired"]
ETA: Monitoring / [time estimate]
Next update: [time]
Thread: [link to incident channel thread]
```

**Status Page:**
```
HubSpot Integration Degraded

We are experiencing issues with our HubSpot CRM integration.
[Specific user impact: e.g., "New lead capture is delayed."]

Our team is actively working on resolution.
Last updated: [ISO timestamp]
```

### Step 5: Postmortem Template

```markdown
## Incident: HubSpot [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Correlation IDs:** [list from error responses]

### Summary
[1-2 sentence description of what happened]

### Timeline (UTC)
- HH:MM - Alert fired: [description]
- HH:MM - On-call acknowledged
- HH:MM - Root cause identified: [cause]
- HH:MM - Mitigation applied: [action]
- HH:MM - Full recovery confirmed

### Root Cause
[Technical explanation with HubSpot API details]

### Impact
- CRM operations affected: [contacts/deals/tickets]
- Duration: [X minutes/hours]
- Data impact: [any missed webhooks, delayed syncs]

### Action Items
- [ ] [Preventive measure] - Owner - Due date
- [ ] [Monitoring improvement] - Owner - Due date
```

## Output

- Triage script identifying issue source in < 2 minutes
- Decision tree guiding response based on error code
- Specific remediation for 401, 429, and 5xx scenarios
- Communication templates for internal and external updates
- Postmortem template with timeline and action items

## Error Handling

| Scenario | First Action | Escalation |
|----------|-------------|------------|
| 401 Auth failure | Regenerate token | Contact HubSpot if tokens keep expiring |
| 429 Rate limit | Reduce volume, wait for reset | Request limit increase |
| 5xx Platform error | Enable fallback mode | Monitor status.hubspot.com |
| Webhook delivery failure | Check endpoint logs | Verify URL and signature |

## Resources

- [HubSpot Status Page](https://status.hubspot.com)
- [HubSpot Support](https://help.hubspot.com/)
- [Error Handling Guide](https://developers.hubspot.com/docs/api-reference/error-handling)

## Next Steps

For data handling and GDPR compliance, see `hubspot-data-handling`.
