---
name: mistral-incident-runbook
description: |
  Execute Mistral AI incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Mistral AI-related outages, investigating errors,
  or running post-incident reviews.
  Trigger with phrases like "mistral incident", "mistral outage",
  "mistral down", "mistral on-call", "mistral emergency".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, incident-response]

---
# Mistral AI Incident Runbook

## Overview
Rapid incident response procedures for Mistral AI integration failures. Covers severity classification, quick triage script, decision tree, per-error mitigations, communication templates, and postmortem process.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | Complete outage | < 15 min | All Mistral requests failing |
| P2 | Degraded service | < 1 hour | High latency, partial 429s |
| P3 | Minor impact | < 4 hours | Occasional errors, non-critical feature |
| P4 | No user impact | Next business day | Monitoring gaps, docs |

## Quick Triage Script

```bash
#!/bin/bash
set -euo pipefail
echo "=== Mistral AI Quick Triage ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. API health
echo -e "\n1. Mistral API status:"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models 2>/dev/null)
echo "   HTTP: $HTTP"
case $HTTP in
  200) echo "   OK — API is reachable" ;;
  401) echo "   AUTH FAILURE — API key invalid or revoked" ;;
  429) echo "   RATE LIMITED — check workspace limits" ;;
  5*) echo "   SERVER ERROR — Mistral service issue" ;;
  000) echo "   NETWORK ERROR — cannot reach api.mistral.ai" ;;
esac

# 2. Our service health
echo -e "\n2. App health endpoint:"
curl -sf https://yourapp.com/health 2>/dev/null | jq '.services.mistral' || echo "   UNREACHABLE"

# 3. Error rate (if Prometheus available)
echo -e "\n3. Error rate (last 5m):"
curl -sf "localhost:9090/api/v1/query?query=rate(mistral_errors_total[5m])" 2>/dev/null \
  | jq -r '.data.result[] | "\(.metric.model): \(.value[1])/s"' || echo "   Prometheus unavailable"
```

## Decision Tree

```
API returning errors?
|-- YES: curl -H "Authorization: Bearer $KEY" https://api.mistral.ai/v1/models
|   |-- 401 → API key issue (Step 1 below)
|   |-- 429 → Rate limited (Step 2 below)
|   |-- 5xx → Mistral service issue (Step 3 below)
|   +-- Timeout → Network issue (Step 4 below)
+-- NO: Our service returning errors?
    |-- YES → Check app logs and config
    +-- NO → Resolved, continue monitoring
```

## Immediate Actions

### Step 1: 401 — Authentication Failure (P1)

```bash
set -euo pipefail
# Verify key
echo "Key length: ${#MISTRAL_API_KEY}"
echo "Key prefix: ${MISTRAL_API_KEY:0:8}..."

# Test directly
curl -v -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models

# If invalid: rotate key at console.mistral.ai
# Then update in your secret manager:
# GCP: gcloud secrets versions add mistral-api-key --data-file=-
# AWS: aws secretsmanager put-secret-value --secret-id mistral/api-key
# K8s: kubectl create secret generic mistral --from-literal=api-key="$NEW_KEY" --dry-run=client -o yaml | kubectl apply -f -
```

### Step 2: 429 — Rate Limited (P2)

```bash
set -euo pipefail
# Check headers for limit info
curl -v -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models 2>&1 | grep -i "ratelimit\|retry"

# Immediate mitigation: reduce concurrency
kubectl set env deployment/app MAX_CONCURRENT_MISTRAL=3

# Check workspace limits: https://admin.mistral.ai/plateforme/limits
# Long-term: Contact Mistral to increase limits
```

### Step 3: 5xx — Mistral Service Error (P1/P2)

```bash
set -euo pipefail
# Check Mistral status page
echo "Check: https://status.mistral.ai/"

# Enable fallback/degradation
kubectl set env deployment/app MISTRAL_FALLBACK=true

# Monitor recovery (check every 30s)
watch -n 30 'curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models'
```

### Step 4: Network/Timeout Error (P2)

```bash
set -euo pipefail
# Test DNS
nslookup api.mistral.ai

# Test connectivity
curl -v --connect-timeout 5 https://api.mistral.ai/v1/models

# Check egress policies
kubectl get networkpolicy -A | grep mistral

# Increase timeout if latency issue
kubectl set env deployment/app MISTRAL_TIMEOUT_MS=120000
```

## Communication Templates

### Internal (Slack)
```
:red_circle: P[1-4] INCIDENT: Mistral AI Integration
**Status**: INVESTIGATING | MITIGATING | RESOLVED
**Impact**: [Description of user-facing impact]
**Action**: [Current action being taken]
**Next update**: [HH:MM UTC]
**IC**: @[name]
```

### External (Status Page)
```
AI Feature Degradation

We are experiencing issues with our AI-powered features.
Some users may see slower responses or temporary unavailability.

Our team is investigating with our AI provider.

Affected: [list features]
Workaround: [if any]
Updated: [timestamp UTC]
```

## Post-Incident

### Evidence Collection

```bash
#!/bin/bash
set -euo pipefail
DIR="incident-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DIR"

kubectl logs -l app=mistral-service --since=2h > "$DIR/app-logs.txt" 2>/dev/null || true
kubectl get events --sort-by=.lastTimestamp > "$DIR/k8s-events.txt" 2>/dev/null || true
kubectl get deployment mistral-service -o yaml | grep -v api-key > "$DIR/deployment.yaml" 2>/dev/null || true

tar -czf "$DIR.tar.gz" "$DIR" && rm -rf "$DIR"
echo "Evidence: $DIR.tar.gz"
```

### Postmortem Template

```markdown
## Incident: Mistral AI [Error Type]
**Date:** YYYY-MM-DD  |  **Duration:** Xh Ym  |  **Severity:** P[1-4]

### Summary
[1-2 sentence description]

### Timeline (UTC)
| Time | Event |
|------|-------|
| HH:MM | Alert fired |
| HH:MM | IC assigned |
| HH:MM | Root cause identified |
| HH:MM | Mitigated |
| HH:MM | Resolved |

### Root Cause
[Technical explanation]

### Impact
- Users affected: [N]
- Failed requests: [N]
- Duration: [time]

### Action Items
| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| P1 | [Fix] | @name | date |
| P2 | [Prevent] | @name | date |
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| kubectl auth expired | Token expired | Re-authenticate with cloud provider |
| Metrics unavailable | Prometheus down | Fall back to app logs |
| Secret rotation fails | IAM permissions | Escalate to admin |
| Fallback not working | Not implemented | Return cached responses or error page |

## Resources
- [Mistral AI Status](https://status.mistral.ai/)
- [Mistral Console](https://console.mistral.ai/)
- [Discord Community](https://discord.gg/mistralai)

## Output
- Issue identified and severity classified
- Mitigation applied per error type
- Stakeholders notified with status updates
- Evidence collected for postmortem
- Action items documented
