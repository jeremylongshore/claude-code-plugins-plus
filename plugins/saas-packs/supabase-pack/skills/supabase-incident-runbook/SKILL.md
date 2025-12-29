---
name: supabase-incident-runbook
description: |
  Detect and respond to Supabase incidents with triage, mitigation, and postmortem.
  Use when responding to Supabase outages or service degradation.
  Trigger with phrases like "supabase incident", "supabase outage",
  "supabase down", "supabase on-call".
allowed-tools: Read, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Incident Runbook

## Overview
Rapid incident response procedures for Supabase-related outages.

## Prerequisites
- supabase-install-auth completed
- Access to Kubernetes/infrastructure
- Monitoring dashboards available
- On-call escalation contacts

## Instructions

### Step 1: Assess Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | Supabase API unreachable |
| P2 | Degraded service | < 1 hour | High latency, partial failures |
| P3 | Minor impact | < 4 hours | Webhook delays, non-critical errors |
| P4 | No user impact | Next business day | Monitoring gaps |

## Quick Triage

```bash
# 1. Check Supabase status
curl -s https://status.supabase.com | jq

# 2. Check our integration health
curl -s https://api.yourapp.com/health | jq '.services.supabase'

# 3. Check error rate (last 5 min)
curl -s localhost:9090/api/v1/query?query=rate(supabase_errors_total[5m])

# 4. Recent error logs
kubectl logs -l app=supabase-integration --since=5m | grep -i error | tail -20
```

## Decision Tree

```
Supabase API returning errors?
├─ YES: Is status.supabase.com showing incident?
│   ├─ YES → Wait for Supabase to resolve. Enable fallback.
│   └─ NO → Our integration issue. Check credentials, config.
└─ NO: Is our service healthy?
    ├─ YES → Likely resolved or intermittent. Monitor.
    └─ NO → Our infrastructure issue. Check pods, memory, network.
```

## Immediate Actions by Error Type

### 401/403 - Authentication
```bash
# Verify API key is set
kubectl get secret supabase-secrets -o jsonpath='{.data.api-key}' | base64 -d

# Check if key was rotated
# → Verify in Supabase dashboard

# Remediation: Update secret and restart pods
kubectl create secret generic supabase-secrets --from-literal=api-key=NEW_KEY --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/supabase-integration
```

### 429 - Rate Limited
```bash
# Check rate limit headers
curl -v https://api.supabase.com 2>&1 | grep -i rate

# Enable request queuing
kubectl set env deployment/supabase-integration RATE_LIMIT_MODE=queue

# Long-term: Contact Supabase for limit increase
```

### 500/503 - Supabase Errors
```bash
# Enable graceful degradation
kubectl set env deployment/supabase-integration SUPABASE_FALLBACK=true

# Notify users of degraded service
# Update status page

# Monitor Supabase status for resolution
```

## Communication Templates

### Internal (Slack)
```
🔴 P1 INCIDENT: Supabase Integration
Status: INVESTIGATING
Impact: [Describe user impact]
Current action: [What you're doing]
Next update: [Time]
Incident commander: @[name]
```

### External (Status Page)
```
Supabase Integration Issue

We're experiencing issues with our Supabase integration.
Some users may experience [specific impact].

We're actively investigating and will provide updates.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection
```bash
# Generate debug bundle
./scripts/supabase-debug-bundle.sh

# Export relevant logs
kubectl logs -l app=supabase-integration --since=1h > incident-logs.txt

# Capture metrics
curl "localhost:9090/api/v1/query_range?query=supabase_errors_total&start=2h" > metrics.json
```

### Postmortem Template
```markdown
## Incident: Supabase [Error Type]
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

## Output
- Incident triaged and severity assigned
- Root cause identified or escalated
- Mitigation applied and verified
- Postmortem documented with action items

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Can't access logs | RBAC permissions | Use break-glass access or escalate |
| Status page disagrees | Stale status or different issue | Check multiple sources, trust metrics |
| Rollback failed | Bad previous version | Deploy known-good version manually |
| Unable to reach Supabase | Network/DNS issue | Try alternative endpoints, check DNS |

## Examples

### PagerDuty Automation

```yaml
# Automatic Supabase incident creation
on_call:
  service: supabase-integration
  escalation_policy: engineering-on-call
  severity_mapping:
    P1: critical
    P2: high
    P3: warning
    P4: info
```

## Resources
- [Supabase Status Page](https://status.supabase.com)
- [Incident Response Best Practices](https://supabase.com/docs/incident-response)
- [Support Contact](https://supabase.com/docs/support)

## Next Steps
For data handling, see `supabase-data-handling`.