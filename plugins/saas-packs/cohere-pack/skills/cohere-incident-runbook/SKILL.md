---
name: cohere-incident-runbook
description: |
  Execute Cohere incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Cohere API outages, investigating errors,
  or running post-incident reviews for Cohere integration failures.
  Trigger with phrases like "cohere incident", "cohere outage",
  "cohere down", "cohere on-call", "cohere emergency", "cohere broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Incident Runbook

## Overview
Rapid incident response procedures for Cohere API v2 outages. Covers triage, mitigation, communication, and postmortem for Chat, Embed, Rerank, and Classify endpoints.

## Prerequisites
- Access to [status.cohere.com](https://status.cohere.com)
- kubectl access to production cluster
- Prometheus/Grafana access
- PagerDuty/Slack communication channels

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | All Cohere endpoints down | < 15 min | API returning 5xx globally |
| P2 | Degraded (rate limits, high latency) | < 1 hour | 429 errors, P95 > 10s |
| P3 | Single endpoint affected | < 4 hours | Embed works, Chat fails |
| P4 | Non-blocking issue | Next business day | Slow response, minor errors |

## Quick Triage (Run These First)

```bash
# 1. Check Cohere service status
curl -s https://status.cohere.com/api/v2/status.json | jq '.status.description'

# 2. Test each endpoint directly
echo "--- Chat ---"
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.cohere.com/v2/chat \
  -H "Authorization: Bearer $CO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"command-r7b-12-2024","messages":[{"role":"user","content":"ping"}]}'

echo -e "\n--- Embed ---"
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.cohere.com/v2/embed \
  -H "Authorization: Bearer $CO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"embed-v4.0","texts":["test"],"input_type":"search_document","embedding_types":["float"]}'

echo -e "\n--- Rerank ---"
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.cohere.com/v2/rerank \
  -H "Authorization: Bearer $CO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"rerank-v3.5","query":"test","documents":["a","b"]}'

# 3. Check our app health
curl -sf https://api.yourapp.com/api/health | jq '.cohere'

# 4. Check error rate (last 5 min)
curl -s "localhost:9090/api/v1/query?query=rate(cohere_errors_total[5m])" | jq '.data.result'
```

## Decision Tree

```
Cohere API returning errors?
├─ YES: Is status.cohere.com showing incident?
│   ├─ YES → Cohere-side outage. Enable fallback. Monitor status page.
│   └─ NO → Check our API key and configuration.
│       ├─ 401 → API key revoked or wrong. Check CO_API_KEY.
│       ├─ 429 → Rate limited. Check if trial key in prod.
│       ├─ 400 → Bad request. Check request format (v1 vs v2?).
│       └─ 5xx → Cohere server issue. Retry with backoff.
└─ NO: Is our app healthy?
    ├─ YES → Intermittent. Monitor.
    └─ NO → Our infrastructure. Check pods, memory, network.
```

## Immediate Actions by Error Type

### 401 — Authentication Failure

```bash
# Verify API key is set
kubectl get secret cohere-secrets -o jsonpath='{.data.CO_API_KEY}' | base64 -d | head -c4
echo "..."

# Test key directly
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $(kubectl get secret cohere-secrets -o jsonpath='{.data.CO_API_KEY}' | base64 -d)" \
  -H "Content-Type: application/json" \
  https://api.cohere.com/v2/chat \
  -d '{"model":"command-r7b-12-2024","messages":[{"role":"user","content":"test"}]}'

# If key is invalid: rotate
# 1. Generate new key at dashboard.cohere.com
# 2. Update secret
kubectl create secret generic cohere-secrets \
  --from-literal=CO_API_KEY=NEW_KEY \
  --dry-run=client -o yaml | kubectl apply -f -
# 3. Restart pods
kubectl rollout restart deployment/app
```

### 429 — Rate Limited

```bash
# Check if using trial key in production (trial = 20 calls/min)
KEY_LEN=$(kubectl get secret cohere-secrets -o jsonpath='{.data.CO_API_KEY}' | base64 -d | wc -c)
echo "Key length: $KEY_LEN chars"

# If trial key: upgrade to production key at dashboard.cohere.com

# If production key: reduce concurrency
kubectl set env deployment/app COHERE_MAX_CONCURRENT=5

# Enable request queuing
kubectl set env deployment/app COHERE_QUEUE_ENABLED=true
```

### 5xx — Cohere Server Errors

```bash
# Enable graceful degradation
kubectl set env deployment/app COHERE_FALLBACK_ENABLED=true

# If using RAG: fall back to rerank-only (skip chat)
# If using agents: fall back to cached responses

# Monitor Cohere status page for resolution
watch -n 30 'curl -s https://status.cohere.com/api/v2/status.json | jq .status.description'
```

## Graceful Degradation Pattern

```typescript
import { CohereError, CohereTimeoutError } from 'cohere-ai';

async function resilientChat(message: string): Promise<string> {
  try {
    const response = await cohere.chat({
      model: 'command-a-03-2025',
      messages: [{ role: 'user', content: message }],
    });
    return response.message?.content?.[0]?.text ?? '';
  } catch (err) {
    if (err instanceof CohereError && err.statusCode === 429) {
      // Fallback to cheaper model (may have separate rate limit)
      const fallback = await cohere.chat({
        model: 'command-r7b-12-2024',
        messages: [{ role: 'user', content: message }],
        maxTokens: 200,
      });
      return fallback.message?.content?.[0]?.text ?? '';
    }

    if (err instanceof CohereError && (err.statusCode ?? 0) >= 500) {
      return 'Cohere is temporarily unavailable. Please try again shortly.';
    }

    throw err;
  }
}
```

## Communication Templates

### Internal (Slack)
```
P[1-4] INCIDENT: Cohere Integration
Status: INVESTIGATING / MITIGATED / RESOLVED
Impact: [e.g., "RAG answers unavailable, chat degraded to cached responses"]
Root cause: [e.g., "Cohere API returning 503 — confirmed on status.cohere.com"]
Current action: [e.g., "Enabled fallback mode, monitoring for recovery"]
Next update: [time]
```

### External (Status Page)
```
Cohere Integration — Degraded Performance

Some AI-powered features may be slower than usual or temporarily unavailable.
We are monitoring the situation and will provide updates as available.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection

```bash
# Export error logs from incident window
kubectl logs -l app=my-cohere-app --since=1h | grep -i "cohere\|CohereError" > incident-logs.txt

# Export metrics
curl "localhost:9090/api/v1/query_range?query=cohere_errors_total&start=$(date -d '2 hours ago' +%s)&end=$(date +%s)&step=60" > metrics.json

# Cohere status history
curl -s https://status.cohere.com/api/v2/incidents.json | jq '.incidents[:3]'
```

### Postmortem Template

```markdown
## Incident: Cohere [endpoint] [error type]
**Date:** YYYY-MM-DD HH:MM - HH:MM UTC
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Detection:** [Alert name / user report / health check]

### Summary
[1-2 sentences]

### Timeline
- HH:MM — Alert fired: cohere_errors_total spike
- HH:MM — On-call acknowledged, began triage
- HH:MM — Root cause identified: [cause]
- HH:MM — Mitigation applied: [action]
- HH:MM — Service restored

### Root Cause
[Was it Cohere-side (status page incident) or our configuration?]

### Action Items
- [ ] Add circuit breaker for [endpoint] — @owner — due date
- [ ] Improve fallback for [scenario] — @owner — due date
- [ ] Add alert for [missed signal] — @owner — due date
```

## Output
- Triage completed with endpoint-level diagnosis
- Immediate mitigation applied (fallback, key rotation, etc.)
- Stakeholders notified via templates
- Evidence collected for postmortem

## Resources
- [Cohere Status Page](https://status.cohere.com)
- [Cohere Error Codes](https://docs.cohere.com/reference/errors)
- [Cohere Support](https://support.cohere.com)

## Next Steps
For data handling, see `cohere-data-handling`.
