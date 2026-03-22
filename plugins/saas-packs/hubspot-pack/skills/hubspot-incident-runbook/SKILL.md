---
name: hubspot-incident-runbook
description: |
  Execute HubSpot incident response procedures with triage, mitigation, and postmortem.
  Use when responding to HubSpot-related outages, investigating errors,
  or running post-incident reviews for HubSpot integration failures.
  Trigger with phrases like "hubspot incident", "hubspot outage",
  "hubspot down", "hubspot on-call", "hubspot emergency", "hubspot broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hubspot]
---

# HubSpot Incident Runbook

## Overview
Rapid incident response procedures for HubSpot-related outages.

## Prerequisites
- Access to HubSpot dashboard and status page
- kubectl access to production cluster
- Prometheus/Grafana access
- Communication channels (Slack, PagerDuty)

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | HubSpot API unreachable |
| P2 | Degraded service | < 1 hour | High latency, partial failures |
| P3 | Minor impact | < 4 hours | Webhook delays, non-critical errors |
| P4 | No user impact | Next business day | Monitoring gaps |

## Quick Triage

```bash
# 1. Check HubSpot status
curl -s https://status.hubspot.com | jq

# 2. Check our integration health
curl -s https://api.yourapp.com/health | jq '.services.hubspot'

# 3. Check error rate (last 5 min)
curl -s localhost:9090/api/v1/query?query=rate(hubspot_errors_total[5m])

# 4. Recent error logs
kubectl logs -l app=hubspot-integration --since=5m | grep -i error | tail -20
```

## Decision Tree

```
HubSpot API returning errors?
├─ YES: Is status.hubspot.com showing incident?
│   ├─ YES → Wait for HubSpot to resolve. Enable fallback.
│   └─ NO → Our integration issue. Check credentials, config.
└─ NO: Is our service healthy?
    ├─ YES → Likely resolved or intermittent. Monitor.
    └─ NO → Our infrastructure issue. Check pods, memory, network.
```

## Immediate Actions by Error Type

### 401/403 - Authentication
```bash
# Verify API key is set
kubectl get secret hubspot-secrets -o jsonpath='{.data.api-key}' | base64 -d

# Check if key was rotated
# → Verify in HubSpot dashboard

# Remediation: Update secret and restart pods
kubectl create secret generic hubspot-secrets --from-literal=api-key=NEW_KEY --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/hubspot-integration
```

### 429 - Rate Limited
```bash
# Check rate limit headers
curl -v https://api.hubspot.com 2>&1 | grep -i rate

# Enable request queuing
kubectl set env deployment/hubspot-integration RATE_LIMIT_MODE=queue

# Long-term: Contact HubSpot for limit increase
```

### 500/503 - HubSpot Errors
```bash
# Enable graceful degradation
kubectl set env deployment/hubspot-integration HUBSPOT_FALLBACK=true

# Notify users of degraded service
# Update status page

# Monitor HubSpot status for resolution
```

## Communication Templates

### Internal (Slack)
```
🔴 P1 INCIDENT: HubSpot Integration
Status: INVESTIGATING
Impact: [Describe user impact]
Current action: [What you're doing]
Next update: [Time]
Incident commander: @[name]
```

### External (Status Page)
```
HubSpot Integration Issue

We're experiencing issues with our HubSpot integration.
Some users may experience [specific impact].

We're actively investigating and will provide updates.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection
```bash
# Generate debug bundle
./scripts/hubspot-debug-bundle.sh

# Export relevant logs
kubectl logs -l app=hubspot-integration --since=1h > incident-logs.txt

# Capture metrics
curl "localhost:9090/api/v1/query_range?query=hubspot_errors_total&start=2h" > metrics.json
```

### Postmortem Template
```markdown
## Incident: HubSpot [Error Type]
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
Determine if the issue is HubSpot-side or internal.

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
curl -sf https://api.yourapp.com/health | jq '.services.hubspot.status' || echo "UNHEALTHY"
```

## Resources
- [HubSpot Status Page](https://status.hubspot.com)
- [HubSpot Support](https://support.hubspot.com)

## Next Steps
For data handling, see `hubspot-data-handling`.