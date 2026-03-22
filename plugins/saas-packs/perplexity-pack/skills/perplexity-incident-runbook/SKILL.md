---
name: perplexity-incident-runbook
description: |
  Execute Perplexity incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Perplexity API outages, investigating search failures,
  or running post-incident reviews for Perplexity integration issues.
  Trigger with phrases like "perplexity incident", "perplexity outage",
  "perplexity down", "perplexity on-call", "perplexity emergency".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, incident-response]

---
# Perplexity Incident Runbook

## Overview
Rapid incident response for Perplexity Sonar API issues. Perplexity-specific: the API depends on live web search, so outages can be partial (search degraded but API responding), model-specific (sonar-pro down but sonar working), or citation-related (answers returned but no sources).

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|-----------|--------------|---------|
| P1 | Complete API failure | < 15 min | All requests returning 500/503 |
| P2 | Degraded service | < 1 hour | High latency, 429 rate limits, no citations |
| P3 | Minor impact | < 4 hours | Single model unavailable, sporadic errors |
| P4 | No user impact | Next business day | Monitoring gap, stale cache |

## Quick Triage (Run Immediately)

```bash
set -euo pipefail
echo "=== Perplexity Triage ==="

# 1. Test sonar model
echo -n "sonar: "
curl -s -w "HTTP %{http_code} in %{time_total}s" -o /dev/null \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions
echo ""

# 2. Test sonar-pro model
echo -n "sonar-pro: "
curl -s -w "HTTP %{http_code} in %{time_total}s" -o /dev/null \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar-pro","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions
echo ""

# 3. Check API key validity
echo -n "Auth: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions
echo " (expect 401 = API reachable)"

# 4. DNS check
echo -n "DNS: "
dig +short api.perplexity.ai
```

## Decision Tree

```
API returning errors?
├─ 401/402: Auth issue
│   └─ Verify API key → Regenerate at perplexity.ai/settings/api
├─ 429: Rate limited
│   └─ Enable request queue → Reduce concurrency → Wait
├─ 500/503: Server error
│   ├─ All models affected?
│   │   ├─ YES → Perplexity outage. Enable fallback/cache.
│   │   └─ NO → Model-specific issue. Route to working model.
│   └─ Check Perplexity community forum for status
├─ Timeout: No response
│   ├─ DNS resolves? → Check network/firewall
│   └─ DNS fails? → DNS issue. Use alternative resolver.
└─ 200 but no citations: Search degraded
    └─ Switch to sonar-pro for more citations
```

## Immediate Actions

### Auth Failure (401/402)
```bash
set -euo pipefail
# Verify current key
echo "Key prefix: ${PERPLEXITY_API_KEY:0:5}"
echo "Key length: ${#PERPLEXITY_API_KEY}"

# If key is invalid: regenerate at perplexity.ai/settings/api
# Update in secret manager:
# gcloud secrets versions add perplexity-api-key --data-file=<(echo -n "NEW_KEY")
# kubectl create secret generic perplexity-secrets --from-literal=api-key=NEW_KEY --dry-run=client -o yaml | kubectl apply -f -
# kubectl rollout restart deployment/your-app
```

### Rate Limited (429)
```bash
set -euo pipefail
# Check if we're making too many requests
# Default limit: 50 RPM per API key

# Immediate: reduce concurrency
# kubectl set env deployment/your-app PERPLEXITY_MAX_CONCURRENT=1

# Enable request queuing if not already active
# kubectl set env deployment/your-app PERPLEXITY_QUEUE_MODE=true
```

### Model-Specific Fallback
```typescript
// If sonar-pro is failing, fall back to sonar
async function resilientSearch(query: string) {
  try {
    return await perplexity.chat.completions.create({
      model: "sonar-pro",
      messages: [{ role: "user", content: query }],
    });
  } catch (err: any) {
    if (err.status >= 500) {
      console.warn("sonar-pro unavailable, falling back to sonar");
      return await perplexity.chat.completions.create({
        model: "sonar",
        messages: [{ role: "user", content: query }],
      });
    }
    throw err;
  }
}
```

## Communication Templates

### Internal (Slack)
```
P[1-4] INCIDENT: Perplexity Search Integration
Status: INVESTIGATING | IDENTIFIED | MONITORING | RESOLVED
Impact: [What users see — degraded search, no citations, etc.]
Cause: [API error / rate limit / auth / Perplexity outage]
Action: [What we're doing]
ETA: [Next update time]
IC: @[name]
```

## Post-Incident

### Evidence Collection
```bash
set -euo pipefail
# Collect debug bundle
mkdir -p incident-evidence

# API response during incident
curl -s \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions > incident-evidence/api-response.json

# Application logs
kubectl logs -l app=your-app --since=1h > incident-evidence/app-logs.txt 2>/dev/null || true

tar -czf "incident-$(date +%Y%m%d-%H%M%S).tar.gz" incident-evidence/
```

### Postmortem Template
```markdown
## Incident: Perplexity [Error Type]
**Date:** YYYY-MM-DD | **Duration:** Xh Ym | **Severity:** P[1-4]

### Summary
[1-2 sentences]

### Timeline
- HH:MM — Alert fired: [description]
- HH:MM — Triage: [findings]
- HH:MM — Mitigation: [action taken]
- HH:MM — Resolved

### Root Cause
[Technical explanation — API outage / rate limit / auth / our bug]

### Action Items
- [ ] [Fix] — Owner — Due
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| All models failing | Perplexity outage | Serve cached results, notify users |
| Intermittent 500s | Transient API issue | Retry with backoff |
| Latency spike | Complex searches | Timeout + fallback to sonar |
| No citations | Search degradation | Log and monitor, usually resolves |

## Output
- Issue triaged and categorized
- Remediation applied (fallback/queue/key rotation)
- Stakeholders notified
- Evidence collected for postmortem

## Resources
- [Perplexity Community Forum](https://community.perplexity.ai)
- [Perplexity API Documentation](https://docs.perplexity.ai)

## Next Steps
For data handling, see `perplexity-data-handling`.
