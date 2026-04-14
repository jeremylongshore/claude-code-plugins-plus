---
name: shopify-incident-runbook
description: |
  Execute Shopify incident response with triage using Shopify status page,
  API health checks, and rate limit diagnosis.
  Use when a Shopify integration is down, returning errors, or behaving unexpectedly in production.
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

Run the triage script to check Shopify status, API connectivity, REST rate limits, and GraphQL throttle state in one pass.

See [Triage Script](references/triage-script.md) for the complete diagnostic script.

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

Diagnostic commands and remediation for 401 (token expired), 429 (rate limited), and 5xx (Shopify internal errors). Always capture `X-Request-Id` headers for Shopify support.

See [Error Type Actions](references/error-type-actions.md) for complete commands per error type.

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
  "https://$SHOPIFY_STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/shop.json" \
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
