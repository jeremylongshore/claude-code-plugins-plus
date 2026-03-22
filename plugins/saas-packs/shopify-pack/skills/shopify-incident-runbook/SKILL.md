---
name: shopify-incident-runbook
description: |
  Execute Shopify incident response with triage using Shopify status page,
  API health checks, and rate limit diagnosis.
  Trigger with phrases like "shopify incident", "shopify outage",
  "shopify down", "shopify on-call", "shopify emergency", "shopify not responding".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Incident Runbook

## Overview

Rapid incident response for Shopify API outages, authentication failures, and rate limit emergencies. Distinguish between Shopify-side issues and your app's integration issues.

## Prerequisites

- Access to Shopify admin and status page
- Application logs and metrics
- Communication channels (Slack, PagerDuty)

## Instructions

### Step 1: Quick Triage (First 5 Minutes)

```bash
#!/bin/bash
echo "=== SHOPIFY INCIDENT TRIAGE ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Is Shopify itself down?
echo ""
echo "--- Shopify Status ---"
echo "Check: https://www.shopifystatus.com"
echo "API Status: https://www.shopifystatus.com/api/v2/status.json"
curl -sf "https://www.shopifystatus.com/api/v2/status.json" 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Overall: {d[\"status\"][\"description\"]}')" \
  2>/dev/null || echo "Could not reach status page"

# 2. Can we reach the Shopify API?
echo ""
echo "--- API Connectivity ---"
echo -n "Admin API: "
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_STORE/admin/api/2024-10/shop.json" 2>/dev/null)
echo "$HTTP_CODE"

# 3. Rate limit state
echo ""
echo "--- Rate Limit State ---"
curl -sI -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_STORE/admin/api/2024-10/shop.json" 2>/dev/null \
  | grep -i "x-shopify-shop-api-call-limit"

# 4. GraphQL rate limit
echo ""
echo "--- GraphQL Throttle ---"
curl -sf -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' \
  "https://$SHOPIFY_STORE/admin/api/2024-10/graphql.json" 2>/dev/null \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
t=d.get('extensions',{}).get('cost',{}).get('throttleStatus',{})
print(f'Available: {t.get(\"currentlyAvailable\",\"?\")}/{t.get(\"maximumAvailable\",\"?\")}')
print(f'Restore rate: {t.get(\"restoreRate\",\"?\")}/sec')
" 2>/dev/null || echo "Could not query"
```

### Step 2: Decision Tree

```
Is Shopifystatus.com showing an incident?
├── YES → Shopify-side outage
│   ├── Enable graceful degradation / cached responses
│   ├── Notify stakeholders: "Shopify is experiencing issues"
│   └── Monitor status page for resolution
│
└── NO → Likely your integration
    ├── HTTP 401? → Token expired or revoked
    │   └── Check: Was app reinstalled? Rotate token.
    ├── HTTP 403? → Scope missing
    │   └── Check: Were scopes changed? Re-run OAuth.
    ├── HTTP 429 / THROTTLED? → Rate limit exceeded
    │   └── Check: Runaway loop? Reduce query frequency.
    ├── HTTP 5xx? → Intermittent Shopify issue
    │   └── Retry with backoff, monitor for pattern.
    └── Network timeout? → Infrastructure issue
        └── Check: DNS, firewall, TLS certificates.
```

### Step 3: Immediate Actions by Error Type

**401 — Token Expired/Revoked:**
```bash
# Verify the token is still valid
curl -sf -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_STORE/admin/api/2024-10/shop.json" | jq '.shop.name'

# If 401: merchant may have uninstalled and reinstalled
# → Trigger re-authentication flow
# → Check APP_UNINSTALLED webhook logs
```

**429 — Rate Limited:**
```bash
# Check if you have a runaway loop
# Look for rapid sequential API calls in your logs

# Immediate mitigation: pause all non-critical API calls
# Check GraphQL query costs — are any queries > 500 points?

# For REST: check the bucket header
curl -sI -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/2024-10/shop.json" \
  | grep "x-shopify-shop-api-call-limit"
# If "40/40" — bucket is full, wait 20 seconds (40 / 2 per second)
```

**5xx — Shopify Internal Error:**
```bash
# Capture the X-Request-Id for support
curl -sI -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/2024-10/shop.json" \
  | grep -i "x-request-id"
# Include this ID when contacting Shopify Partner Support
```

### Step 4: Communication Templates

**Internal (Slack):**
```
INCIDENT: Shopify Integration Issue
Severity: P[1/2/3]
Status: INVESTIGATING
Impact: [What users/merchants are affected]
Root cause: [Shopify outage / Our auth issue / Rate limiting]
Action: [What we're doing now]
Next update: [Time]
Responder: @[name]
```

**External (Merchant-facing):**
```
We're currently experiencing issues with some Shopify-connected features.
[Order sync / Product updates / etc.] may be delayed.
We're actively working on resolution and will update shortly.
All data is safe — no orders or products have been lost.
```

## Output

- Triage completed within 5 minutes
- Root cause identified (Shopify vs. integration)
- Immediate mitigation applied
- Stakeholders notified

## Error Handling

| Scenario | Response Time | Escalation |
|----------|--------------|------------|
| Shopify API fully down | Monitor status page | Nothing to fix on our side |
| Auth token revoked | < 15 min | Trigger re-auth, notify merchant |
| Rate limit exhaustion | < 30 min | Reduce query frequency, optimize costs |
| Webhook delivery failures | < 1 hour | Check endpoint health, review HMAC |
| Data sync stalled | < 4 hours | Run manual sync after resolution |

## Examples

### One-Liner Health Check

```bash
curl -sf -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_STORE/admin/api/2024-10/shop.json" \
  | jq '{name: .shop.name, plan: .shop.plan_name}' \
  && echo "SHOPIFY: HEALTHY" || echo "SHOPIFY: UNREACHABLE"
```

### Post-Incident Checklist

- [ ] Timeline documented with UTC timestamps
- [ ] Root cause identified
- [ ] `X-Request-Id` values collected (for Shopify support)
- [ ] Customer impact assessed
- [ ] Prevention action items created
- [ ] Monitoring/alerting gaps identified

## Resources

- [Shopify Status Page](https://www.shopifystatus.com)
- [Shopify Partner Support](https://help.shopify.com/en/partners)
- [Shopify Community Forums](https://community.shopify.dev)

## Next Steps

For data handling and GDPR, see `shopify-data-handling`.
