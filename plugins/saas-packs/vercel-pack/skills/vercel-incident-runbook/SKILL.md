---
name: vercel-incident-runbook
description: |
  Execute Vercel incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Vercel-related outages, investigating errors,
  or running post-incident reviews for Vercel integration failures.
  Trigger with phrases like "vercel incident", "vercel outage",
  "vercel down", "vercel on-call", "vercel emergency", "vercel broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Incident Runbook

## Overview
Rapid incident response procedures for Vercel-related outages.

## Prerequisites
- Access to Vercel dashboard and status page
- kubectl access to production cluster
- Prometheus/Grafana access
- Communication channels (Slack, PagerDuty)

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | Vercel API unreachable |
| P2 | Degraded service | < 1 hour | High latency, partial failures |
| P3 | Minor impact | < 4 hours | Webhook delays, non-critical errors |
| P4 | No user impact | Next business day | Monitoring gaps |

## Quick Triage

```bash
# 1. Check Vercel status
curl -s https://www.vercel-status.com | jq

# 2. Check our integration health
curl -s https://api.yourapp.com/health | jq '.services.vercel'

# 3. Check error rate (last 5 min)
curl -s localhost:9090/api/v1/query?query=rate(vercel_errors_total[5m])

# 4. Recent error logs
kubectl logs -l app=vercel-integration --since=5m | grep -i error | tail -20
```

## Decision Tree

```
Vercel API returning errors?
├─ YES: Is status.vercel.com showing incident?
│   ├─ YES → Wait for Vercel to resolve. Enable fallback.
│   └─ NO → Our integration issue. Check credentials, config.
└─ NO: Is our service healthy?
    ├─ YES → Likely resolved or intermittent. Monitor.
    └─ NO → Our infrastructure issue. Check pods, memory, network.
```

## Immediate Actions by Error Type

### 401/403 - Authentication
```bash
# Verify API key is set
kubectl get secret vercel-secrets -o jsonpath='{.data.api-key}' | base64 -d

# Check if key was rotated
# → Verify in Vercel dashboard

# Remediation: Update secret and restart pods
kubectl create secret generic vercel-secrets --from-literal=api-key=NEW_KEY --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/vercel-integration
```

### 429 - Rate Limited
```bash
# Check rate limit headers
curl -v https://api.vercel.com 2>&1 | grep -i rate

# Enable request queuing
kubectl set env deployment/vercel-integration RATE_LIMIT_MODE=queue

# Long-term: Contact Vercel for limit increase
```

### 500/503 - Vercel Errors
```bash
# Enable graceful degradation
kubectl set env deployment/vercel-integration VERCEL_FALLBACK=true

# Notify users of degraded service
# Update status page

# Monitor Vercel status for resolution
```

## Communication Templates

### Internal (Slack)
```
🔴 P1 INCIDENT: Vercel Integration
Status: INVESTIGATING
Impact: [Describe user impact]
Current action: [What you're doing]
Next update: [Time]
Incident commander: @[name]
```

### External (Status Page)
```
Vercel Integration Issue

We're experiencing issues with our Vercel integration.
Some users may experience [specific impact].

We're actively investigating and will provide updates.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection
```bash
# Generate debug bundle
./scripts/vercel-debug-bundle.sh

# Export relevant logs
kubectl logs -l app=vercel-integration --since=1h > incident-logs.txt

# Capture metrics
curl "localhost:9090/api/v1/query_range?query=vercel_errors_total&start=2h" > metrics.json
```

### Postmortem Template
```markdown
## Incident: Vercel [Error Type]
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
Determine if the issue is Vercel-side or internal.

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
curl -sf https://api.yourapp.com/health | jq '.services.vercel.status' || echo "UNHEALTHY"
```

## Resources
- [Vercel Status Page](https://www.vercel-status.com)
- [Vercel Support](https://support.vercel.com)

## Next Steps
For data handling, see `vercel-data-handling`.