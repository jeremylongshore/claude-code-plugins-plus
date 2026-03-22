---
name: shopify-incident-runbook
description: |
  Execute Shopify incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Shopify-related outages, investigating errors,
  or running post-incident reviews for Shopify integration failures.
  Trigger with phrases like "shopify incident", "shopify outage",
  "shopify down", "shopify on-call", "shopify emergency", "shopify broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, shopify]
---

# Shopify Incident Runbook

## Overview
Rapid incident response procedures for Shopify-related outages.

## Prerequisites
- Access to Shopify dashboard and status page
- kubectl access to production cluster
- Prometheus/Grafana access
- Communication channels (Slack, PagerDuty)

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | Shopify API unreachable |
| P2 | Degraded service | < 1 hour | High latency, partial failures |
| P3 | Minor impact | < 4 hours | Webhook delays, non-critical errors |
| P4 | No user impact | Next business day | Monitoring gaps |

## Quick Triage

```bash
# 1. Check Shopify status
curl -s https://status.shopify.com | jq

# 2. Check our integration health
curl -s https://api.yourapp.com/health | jq '.services.shopify'

# 3. Check error rate (last 5 min)
curl -s localhost:9090/api/v1/query?query=rate(shopify_errors_total[5m])

# 4. Recent error logs
kubectl logs -l app=shopify-integration --since=5m | grep -i error | tail -20
```

## Decision Tree

```
Shopify API returning errors?
├─ YES: Is status.shopify.com showing incident?
│   ├─ YES → Wait for Shopify to resolve. Enable fallback.
│   └─ NO → Our integration issue. Check credentials, config.
└─ NO: Is our service healthy?
    ├─ YES → Likely resolved or intermittent. Monitor.
    └─ NO → Our infrastructure issue. Check pods, memory, network.
```

## Immediate Actions by Error Type

### 401/403 - Authentication
```bash
# Verify API key is set
kubectl get secret shopify-secrets -o jsonpath='{.data.api-key}' | base64 -d

# Check if key was rotated
# → Verify in Shopify dashboard

# Remediation: Update secret and restart pods
kubectl create secret generic shopify-secrets --from-literal=api-key=NEW_KEY --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/shopify-integration
```

### 429 - Rate Limited
```bash
# Check rate limit headers
curl -v https://api.shopify.com 2>&1 | grep -i rate

# Enable request queuing
kubectl set env deployment/shopify-integration RATE_LIMIT_MODE=queue

# Long-term: Contact Shopify for limit increase
```

### 500/503 - Shopify Errors
```bash
# Enable graceful degradation
kubectl set env deployment/shopify-integration SHOPIFY_FALLBACK=true

# Notify users of degraded service
# Update status page

# Monitor Shopify status for resolution
```

## Communication Templates

### Internal (Slack)
```
🔴 P1 INCIDENT: Shopify Integration
Status: INVESTIGATING
Impact: [Describe user impact]
Current action: [What you're doing]
Next update: [Time]
Incident commander: @[name]
```

### External (Status Page)
```
Shopify Integration Issue

We're experiencing issues with our Shopify integration.
Some users may experience [specific impact].

We're actively investigating and will provide updates.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection
```bash
# Generate debug bundle
./scripts/shopify-debug-bundle.sh

# Export relevant logs
kubectl logs -l app=shopify-integration --since=1h > incident-logs.txt

# Capture metrics
curl "localhost:9090/api/v1/query_range?query=shopify_errors_total&start=2h" > metrics.json
```

### Postmortem Template
```markdown
## Incident: Shopify [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]

### Summary
[1-2 sentence description]

### Timeline
- HH:MM - [Event]
- HH:MM - [Event]

### Root Cause
[Technical explanation]

### Impact
- Users affected: N
- Revenue impact: $X

### Action Items
- [ ] [Preventive measure] - Owner - Due date
```

## Instructions

### Step 1: Quick Triage
Run the triage commands to identify the issue source.

### Step 2: Follow Decision Tree
Determine if the issue is Shopify-side or internal.

### Step 3: Execute Immediate Actions
Apply the appropriate remediation for the error type.

### Step 4: Communicate Status
Update internal and external stakeholders.

## Output
- Issue identified and categorized
- Remediation applied
- Stakeholders notified
- Evidence collected for postmortem

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status page | Network issue | Use mobile or VPN |
| kubectl fails | Auth expired | Re-authenticate |
| Metrics unavailable | Prometheus down | Check backup metrics |
| Secret rotation fails | Permission denied | Escalate to admin |

## Examples

### One-Line Health Check
```bash
curl -sf https://api.yourapp.com/health | jq '.services.shopify.status' || echo "UNHEALTHY"
```

## Resources
- [Shopify Status Page](https://status.shopify.com)
- [Shopify Support](https://support.shopify.com)

## Next Steps
For data handling, see `shopify-data-handling`.