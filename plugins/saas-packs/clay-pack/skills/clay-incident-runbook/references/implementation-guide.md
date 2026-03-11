# Clay Incident Runbook — Implementation Guide

## Quick Triage Commands

```bash
# 1. Check Clay status
curl -s https://status.clay.com | jq

# 2. Check our integration health
curl -s https://api.yourapp.com/health | jq '.services.clay'

# 3. Check error rate (last 5 min)
curl -s localhost:9090/api/v1/query?query=rate(clay_errors_total[5m])

# 4. Recent error logs
kubectl logs -l app=clay-integration --since=5m | grep -i error | tail -20
```

## Decision Tree

```
Clay API returning errors?
├─ YES: Is status.clay.com showing incident?
│   ├─ YES -> Wait for Clay to resolve. Enable fallback.
│   └─ NO -> Our integration issue. Check credentials, config.
└─ NO: Is our service healthy?
    ├─ YES -> Likely resolved or intermittent. Monitor.
    └─ NO -> Our infrastructure issue. Check pods, memory, network.
```

## 401/403 Authentication Remediation

```bash
# Verify API key is set
kubectl get secret clay-secrets -o jsonpath='{.data.api-key}' | base64 -d

# Remediation: Update secret and restart pods
kubectl create secret generic clay-secrets --from-literal=api-key=NEW_KEY --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/clay-integration
```

## 429 Rate Limited Remediation

```bash
# Check rate limit headers
curl -v https://api.clay.com 2>&1 | grep -i rate

# Enable request queuing
kubectl set env deployment/clay-integration RATE_LIMIT_MODE=queue
```

## 500/503 Clay Errors Remediation

```bash
# Enable graceful degradation
kubectl set env deployment/clay-integration CLAY_FALLBACK=true

# Monitor Clay status for resolution
```

## Communication Templates

### Internal (Slack)
```
P1 INCIDENT: Clay Integration
Status: INVESTIGATING
Impact: [Describe user impact]
Current action: [What you're doing]
Next update: [Time]
Incident commander: @[name]
```

### External (Status Page)
```
Clay Integration Issue

We're experiencing issues with our Clay integration.
Some users may experience [specific impact].

We're actively investigating and will provide updates.

Last updated: [timestamp]
```

## Post-Incident Evidence Collection

```bash
# Generate debug bundle
./scripts/clay-debug-bundle.sh

# Export relevant logs
kubectl logs -l app=clay-integration --since=1h > incident-logs.txt

# Capture metrics
curl "localhost:9090/api/v1/query_range?query=clay_errors_total&start=2h" > metrics.json
```

## Postmortem Template

```markdown
## Incident: Clay [Error Type]
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
