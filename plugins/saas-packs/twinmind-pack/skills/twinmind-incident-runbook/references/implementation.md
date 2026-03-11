# TwinMind Incident Runbook - Detailed Implementation

## Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| P1 - Critical | Complete service outage | 15 minutes | All transcriptions failing |
| P2 - High | Major feature degraded | 1 hour | Summaries not generating |
| P3 - Medium | Minor functionality impacted | 4 hours | Slow transcription |
| P4 - Low | Cosmetic or edge case | 24 hours | Occasional timeout |

## Diagnostic Commands

### Check TwinMind API Status

```bash
# Quick health check
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health

# Detailed health check
curl -s -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health | jq

# Check status page API
curl -s https://status.twinmind.com/api/v2/status.json | jq '.status'
```

### Check Our Service Health

```bash
curl -s http://localhost:8080/health | jq
curl -s http://localhost:8080/health/twinmind | jq
kubectl logs -l app=twinmind-service --tail=100 | grep -i error
curl -s http://localhost:8080/metrics | grep twinmind_errors
```

### Check Rate Limits

```bash
curl -I -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health 2>/dev/null | grep -i ratelimit
curl -s http://localhost:8080/metrics | grep rate_limit
```

## Scenario 1: All Transcriptions Failing

**Symptoms:** 100% error rate, `twinmind_transcriptions_total{status="error"}` spiking

**Diagnosis:**
```bash
curl -v -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health

kubectl logs -l app=twinmind-service --tail=200 | \
  grep -E "(error|Error|ERROR)" | awk '{print $NF}' | sort | uniq -c | sort -rn
```

**Resolution:**
1. TwinMind API down: Update status page, notify users, monitor status.twinmind.com
2. Invalid API key: Check expiration, regenerate, update secrets, restart services
3. Network issue: Check DNS, firewall rules, egress connectivity

## Scenario 2: High Latency

**Symptoms:** P95 > 5s, `twinmind_api_latency_seconds` high values

**Resolution:**
1. TwinMind slow: Check status page, switch to faster model (ear-2), queue non-urgent
2. Service overloaded: Scale up replicas, increase rate limiting
3. Network latency: Check regional connectivity, cache DNS

## Scenario 3: Rate Limiting

**Symptoms:** 429 errors, `twinmind_errors_total{error_type="RATE_LIMITED"}` > 0

**Resolution:**
1. Immediate: Enable request queue, reject non-critical requests
2. Short-term: Request limit increase, upgrade tier
3. Long-term: Implement caching, batch requests

## Scenario 4: Authentication Failures

**Symptoms:** 401 errors, "Invalid API key" messages

**Resolution:**
1. Key expired: Generate new key, update secrets manager, restart services
2. Key leaked: Immediately revoke, generate new, audit logs, update security practices

## Escalation Path

```
Level 1: On-Call Engineer (0-15 min)
   -> Level 2: Team Lead (15-30 min)
   -> Level 3: Engineering Manager (30-60 min)
   -> Level 4: VP Engineering (60+ min)
```

## TwinMind Support Contacts
- **Email:** support@twinmind.com
- **Enterprise:** enterprise-support@twinmind.com
- **Status:** https://status.twinmind.com

## Incident Report Template

```markdown
# Incident Report: [TITLE]

**Date:** YYYY-MM-DD
**Duration:** HH:MM - HH:MM
**Severity:** P1/P2/P3/P4
**Impact:** [Affected users/requests]

## Summary
[Brief description]

## Timeline
- HH:MM - Alert triggered
- HH:MM - On-call acknowledged
- HH:MM - Issue resolved

## Root Cause
[Detailed explanation]

## Resolution
[How fixed]

## Action Items
- [ ] [Preventive measure]
- [ ] [Monitoring improvement]
```

## Post-Incident Checklist

### Immediate (Within 24 hours)
- [ ] Confirm issue fully resolved
- [ ] Update status page to resolved
- [ ] Notify stakeholders
- [ ] Document timeline

### Follow-up (Within 1 week)
- [ ] Schedule post-mortem meeting
- [ ] Write incident report
- [ ] Identify root cause
- [ ] Create action items
