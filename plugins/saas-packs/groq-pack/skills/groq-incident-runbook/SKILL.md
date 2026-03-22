---
name: groq-incident-runbook
description: |
  Execute Groq incident response: triage, mitigation, fallback, and postmortem.
  Use when responding to Groq-related outages, investigating errors,
  or running post-incident reviews for Groq integration failures.
  Trigger with phrases like "groq incident", "groq outage",
  "groq down", "groq on-call", "groq emergency", "groq broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, incident-response]

---
# Groq Incident Runbook

## Overview
Rapid incident response procedures for Groq API failures. Groq is a third-party inference provider -- when it goes down, your mitigation options are: wait, fall back to a different model, or fall back to a different provider.

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete API failure | < 15 min | Groq API returns 5xx on all models |
| P2 | Degraded performance | < 1 hour | High latency, partial 429s, one model down |
| P3 | Minor impact | < 4 hours | Intermittent errors, non-critical feature affected |
| P4 | No user impact | Next business day | Monitoring gap, cost anomaly |

## Quick Triage (Run First)

```bash
set -euo pipefail
echo "=== 1. Groq API Status ==="
curl -sf https://status.groq.com > /dev/null && echo "status.groq.com: REACHABLE" || echo "status.groq.com: UNREACHABLE"

echo ""
echo "=== 2. API Authentication ==="
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY")
echo "GET /models: HTTP $HTTP_CODE"

echo ""
echo "=== 3. Model Availability ==="
for model in "llama-3.1-8b-instant" "llama-3.3-70b-versatile"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $GROQ_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":1}")
  echo "$model: HTTP $CODE"
done

echo ""
echo "=== 4. Rate Limit Status ==="
curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -iE "^(x-ratelimit|retry-after)" || echo "No rate limit headers"
```

## Decision Tree

```
Is the Groq API responding?
├─ NO (timeout/connection refused):
│   ├─ Check status.groq.com
│   │   ├─ Incident reported → Wait, enable fallback provider
│   │   └─ No incident → Network issue on our side (check DNS, firewall, proxy)
│   └─ Check if api.groq.com resolves: dig api.groq.com
│
├─ YES, but 401/403:
│   ├─ API key revoked or expired → Rotate key
│   └─ Key not set in environment → Check secret manager
│
├─ YES, but 429:
│   ├─ retry-after header present → Wait that many seconds
│   ├─ All models 429 → Org-level limit hit; reduce traffic or upgrade plan
│   └─ One model 429 → Route to a different model
│
├─ YES, but 500/503:
│   ├─ One model → Groq capacity issue on that model; use fallback model
│   └─ All models → Groq-wide outage; enable fallback provider
│
└─ YES, but slow (latency > 2s):
    ├─ Large prompts → Reduce input size
    ├─ 70B model → Switch to 8B for speed
    └─ queue_time high → Groq queue congestion; try different model
```

## Immediate Mitigations

### Enable Fallback to Different Model
```typescript
// If primary model is failing, route to fallback
async function mitigateModelFailure(messages: any[]) {
  const models = [
    "llama-3.3-70b-versatile",  // Primary
    "llama-3.3-70b-specdec",    // Same quality, different infra
    "llama-3.1-8b-instant",     // Fastest, most available
  ];

  for (const model of models) {
    try {
      return await groq.chat.completions.create({
        model,
        messages,
        max_tokens: 1024,
        timeout: 10_000,
      });
    } catch (err: any) {
      console.warn(`Model ${model} failed: ${err.status} ${err.message}`);
      continue;
    }
  }

  throw new Error("All Groq models unavailable");
}
```

### 429 Rate Limit — Immediate Actions
```bash
set -euo pipefail
# Check exact limit info
curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -i "x-ratelimit\|retry-after"

# Options:
# 1. Wait for retry-after seconds
# 2. Switch to a different model (each model has separate limits)
# 3. Reduce request volume (disable non-critical features)
# 4. If persistent, upgrade Groq plan at console.groq.com
```

### 401 Auth Failure — Key Rotation
```bash
set -euo pipefail
# 1. Verify current key
echo "Current key prefix: ${GROQ_API_KEY:0:8}"

# 2. Create new key at console.groq.com/keys
# 3. Test new key
curl -s -o /dev/null -w "%{http_code}" \
  https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $NEW_GROQ_KEY"

# 4. Deploy new key to production
# 5. Delete old key in console
```

## Communication Templates

### Internal Alert (Slack/PagerDuty)
```
P[1-4] INCIDENT: Groq API [Error Type]
Status: INVESTIGATING | MITIGATING | RESOLVED
Impact: [What users see]
Current action: [What we're doing]
Fallback: [Enabled/Disabled]
Next update in: [Time]
Commander: @[name]
```

### Status Page (External)
```
AI Feature Performance Issue

We're experiencing [degraded performance / intermittent errors] with our AI features.
[Feature X] may respond slower than usual.
We've activated backup systems and are monitoring the situation.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection
```bash
set -euo pipefail
INCIDENT_DIR="groq-incident-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$INCIDENT_DIR"

# API diagnostics
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" > "$INCIDENT_DIR/models.json"

# Application logs (redacted)
kubectl logs -l app=your-app --since=1h 2>/dev/null | \
  grep -i "groq\|429\|error\|timeout" | \
  sed 's/gsk_[a-zA-Z0-9]*/gsk_REDACTED/g' | \
  tail -100 > "$INCIDENT_DIR/app-logs.txt"

tar -czf "$INCIDENT_DIR.tar.gz" "$INCIDENT_DIR"
echo "Evidence bundle: $INCIDENT_DIR.tar.gz"
```

### Postmortem Template
```markdown
## Incident: Groq [Error Type] — [Date]
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Impact:** [N users affected, feature X degraded]

### Timeline
- HH:MM — First alert fired
- HH:MM — On-call acknowledged, began triage
- HH:MM — Root cause identified: [cause]
- HH:MM — Mitigation applied: [what]
- HH:MM — Resolved, monitoring

### Root Cause
[Was it Groq-side or our side? Rate limit hit? Model deprecated? Key expired?]

### What Went Well
- [Fallback activated automatically]

### What Could Improve
- [Alert fired too late / fallback didn't work / no runbook]

### Action Items
- [ ] [Action] — Owner — Due date
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status.groq.com | Network issue | Use mobile or different network |
| All models failing | Groq-wide outage | Enable fallback provider (OpenAI, etc.) |
| Key rotation fails | No admin access | Escalate to team lead with console access |
| Fallback provider also down | Multi-provider outage | Degrade gracefully, show cached content |

## Resources
- [Groq Status Page](https://status.groq.com)
- [Groq Error Codes](https://console.groq.com/docs/errors)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)

## Next Steps
For data handling compliance, see `groq-data-handling`.
