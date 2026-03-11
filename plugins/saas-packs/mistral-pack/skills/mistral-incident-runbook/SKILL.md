---
name: mistral-incident-runbook
description: |
  Execute Mistral AI incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Mistral AI-related outages, investigating errors,
  or running post-incident reviews for Mistral AI integration failures.
  Trigger with phrases like "mistral incident", "mistral outage",
  "mistral down", "mistral on-call", "mistral emergency", "mistral broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Incident Runbook

## Overview
Rapid incident response procedures for Mistral AI-related outages.

## Prerequisites
- Access to Mistral AI console
- kubectl access to production cluster (if applicable)
- Prometheus/Grafana access
- Communication channels (Slack, PagerDuty)

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | Mistral API unreachable, all requests failing |
| P2 | Degraded service | < 1 hour | High latency, partial failures, rate limiting |
| P3 | Minor impact | < 4 hours | Occasional errors, non-critical feature down |
| P4 | No user impact | Next business day | Monitoring gaps, documentation issues |

## Quick Triage

```bash
#!/bin/bash
set -euo pipefail
# mistral-triage.sh

echo "=== Mistral AI Quick Triage ==="
echo "Timestamp: $(date)"
echo ""

# 1. Check Mistral API health
echo "1. Checking Mistral API..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models)
echo "   API Status: $HTTP_STATUS"

# 2. Check our health endpoint
echo ""
echo "2. Checking our service health..."
curl -s https://api.yourapp.com/health | jq '.services.mistral' 2>/dev/null || echo "   Health check failed"

# 3. Check recent error rate
echo ""
echo "3. Recent errors (if Prometheus available)..."
curl -s "localhost:9090/api/v1/query?query=rate(mistral_errors_total[5m])" | jq '.data.result' 2>/dev/null || echo "   Prometheus not available"  # 9090: Prometheus port

# 4. Check recent logs
echo ""
echo "4. Recent error logs..."
kubectl logs -l app=mistral-service --since=5m 2>/dev/null | grep -i error | tail -10 || echo "   kubectl not available"
```

## Decision Tree

```
Mistral API returning errors?
├─ YES: Check api.mistral.ai/v1/models with curl
│   ├─ 401 → API key issue (see Auth section)  # HTTP 401 Unauthorized
│   ├─ 429 → Rate limited (see Rate Limit section)  # HTTP 429 Too Many Requests
│   ├─ 5xx → Mistral service issue (wait & monitor)
│   └─ Timeout → Network issue (check connectivity)
└─ NO: Our service returning errors?
    ├─ YES → Check our logs & config
    └─ NO → Likely resolved, continue monitoring
```

## Immediate Actions by Error Type

### 401 Unauthorized - Authentication Failed

```bash
set -euo pipefail
# 1. Verify API key is set
echo "API Key length: ${#MISTRAL_API_KEY}"
echo "API Key prefix: ${MISTRAL_API_KEY:0:10}..."

# 2. Test API key directly
curl -v -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models

# 3. Check if key was rotated
# → Verify in Mistral console: console.mistral.ai

# 4. Update key if needed
kubectl create secret generic mistral-secrets \
  --from-literal=api-key="$NEW_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. Restart pods
kubectl rollout restart deployment/mistral-service
```

### 429 Rate Limited

```bash
set -euo pipefail
# 1. Check current rate limit status
curl -v -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models 2>&1 | grep -i "rate\|retry"

# 2. Enable request queuing (if supported)
kubectl set env deployment/mistral-service RATE_LIMIT_MODE=queue

# 3. Reduce request concurrency
kubectl set env deployment/mistral-service MAX_CONCURRENT_REQUESTS=5

# 4. Long-term: Contact Mistral for limit increase
# → console.mistral.ai or support@mistral.ai
```

### 500/503 Service Error

```bash
set -euo pipefail
# 1. Check Mistral status (if available)
echo "Checking Mistral status..."

# 2. Enable graceful degradation
kubectl set env deployment/mistral-service MISTRAL_FALLBACK=true

# 3. Notify users
# → Update status page

# 4. Monitor for recovery
watch -n 30 'curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${MISTRAL_API_KEY}" https://api.mistral.ai/v1/models'
```

### Timeout/Network Error

```bash
set -euo pipefail
# 1. Test connectivity
curl -v --connect-timeout 5 https://api.mistral.ai/v1/models

# 2. Check DNS resolution
nslookup api.mistral.ai

# 3. Increase timeout
kubectl set env deployment/mistral-service MISTRAL_TIMEOUT=60000  # 60000: 1 minute in ms

# 4. Check egress rules
kubectl get networkpolicy
```

## Communication Templates

### Internal (Slack)
```
:red_circle: P1 INCIDENT: Mistral AI Integration
**Status**: INVESTIGATING
**Impact**: [Users cannot use AI features / Degraded AI responses]
**Current action**: [What you're doing]
**Next update**: [Time - typically every 15-30 min for P1]
**Incident commander**: @[name]
```

### External (Status Page)
```
AI Feature Degradation

We're experiencing issues with our AI-powered features.
Some users may experience slower responses or temporary unavailability.

Our team is actively investigating and working with our AI provider to resolve this.

Affected services:
- [List affected features]

Workaround: [If available]

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection

```bash
#!/bin/bash
set -euo pipefail
# collect-evidence.sh

INCIDENT_DIR="incident-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$INCIDENT_DIR"

# Collect logs
kubectl logs -l app=mistral-service --since=1h > "$INCIDENT_DIR/logs.txt"

# Export metrics
curl "localhost:9090/api/v1/query_range?query=mistral_errors_total&start=$(date -d '2 hours ago' +%s)&end=$(date +%s)&step=60" \  # 9090: Prometheus port
  > "$INCIDENT_DIR/metrics.json"

# Collect config (redacted)
kubectl get deployment mistral-service -o yaml | grep -v "api-key" > "$INCIDENT_DIR/deployment.yaml"

# Create bundle
tar -czf "$INCIDENT_DIR.tar.gz" "$INCIDENT_DIR"
echo "Evidence bundle: $INCIDENT_DIR.tar.gz"
```

### Postmortem Template

```markdown
## Incident: Mistral AI [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Incident Commander:** [Name]

### Summary
[1-2 sentence description of what happened]

### Timeline (UTC)
| Time | Event |
|------|-------|
| HH:MM | First alert triggered |
| HH:MM | Incident declared |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Service restored |

### Root Cause
[Technical explanation of what went wrong]

### Impact
- Users affected: [Number or percentage]
- Duration of impact: [Time]
- Requests failed: [Number]
- Revenue impact: [If applicable]

### Detection
How was the incident detected?
- [ ] Automated alerting
- [ ] Customer report
- [ ] Internal testing
- [ ] Other: ___

### Resolution
[What was done to fix the issue]

### Action Items
| Priority | Action | Owner | Due Date | Status |
|----------|--------|-------|----------|--------|
| P1 | [Immediate fix] | @name | YYYY-MM-DD | [ ] |
| P2 | [Preventive measure] | @name | YYYY-MM-DD | [ ] |
| P3 | [Improvement] | @name | YYYY-MM-DD | [ ] |

### Lessons Learned
- What went well:
- What could be improved:
- What we got lucky with:
```

## Output
- Issue identified and categorized
- Mitigation applied
- Stakeholders notified
- Evidence collected for postmortem

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| kubectl fails | Auth expired | Re-authenticate with cloud provider |
| Metrics unavailable | Prometheus down | Check backup metrics or logs |
| Secret rotation fails | Permission denied | Escalate to admin |
| Fallback not working | Not implemented | Use cached responses or error page |

## Examples

### One-Line Health Check
```bash
set -euo pipefail
curl -sf -H "Authorization: Bearer ${MISTRAL_API_KEY}" https://api.mistral.ai/v1/models | jq '.data[0].id' || echo "UNHEALTHY"
```

### Quick Rollback
```bash
set -euo pipefail
kubectl rollout undo deployment/mistral-service && \
kubectl rollout status deployment/mistral-service
```

## Resources
- [Mistral AI Console](https://console.mistral.ai/)
- [Mistral AI Documentation](https://docs.mistral.ai/)

## Next Steps
For data handling, see `mistral-data-handling`.

## Instructions

1. Assess the current state of the Mistral configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference