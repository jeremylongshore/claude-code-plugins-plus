---
name: ideogram-incident-runbook
description: |
  Execute Ideogram incident response with triage, mitigation, and postmortem.
  Use when responding to Ideogram-related outages, investigating errors,
  or running post-incident reviews for Ideogram integration failures.
  Trigger with phrases like "ideogram incident", "ideogram outage",
  "ideogram down", "ideogram on-call", "ideogram emergency", "ideogram broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, incident-response]

---
# Ideogram Incident Runbook

## Overview
Rapid incident response for Ideogram API outages, auth failures, rate limiting, and degraded generation quality. Covers triage, immediate remediation, fallback activation, and postmortem process.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | API unreachable or all requests failing | < 15 min | 401 on valid key, 500 on all requests |
| P2 | Degraded quality or performance | < 1 hour | P95 latency > 30s, high 429 rate |
| P3 | Minor impact, workaround exists | < 4 hours | Occasional safety rejections, slow downloads |
| P4 | No user impact | Next business day | Monitoring gaps, stale cache |

## Quick Triage (Run These First)

```bash
set -euo pipefail

echo "=== IDEOGRAM TRIAGE ==="

# 1. Test API connectivity and auth
echo -n "API status: "
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request":{"prompt":"triage test","model":"V_2_TURBO","magic_prompt_option":"OFF"}}'
echo ""

# 2. Test V3 endpoint
echo -n "V3 status: "
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.ideogram.ai/v1/ideogram-v3/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -F "prompt=triage test" -F "rendering_speed=FLASH"
echo ""

# 3. Check DNS resolution
echo -n "DNS: "
nslookup api.ideogram.ai 2>/dev/null | grep -A1 "Name:" | tail -1 || echo "lookup failed"

# 4. Measure latency
echo -n "Latency: "
curl -s -o /dev/null -w "%{time_total}s" \
  -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request":{"prompt":"latency test","model":"V_2_TURBO","magic_prompt_option":"OFF"}}'
echo ""
```

## Decision Tree

```
Is api.ideogram.ai returning errors?
├─ YES: What status code?
│   ├─ 401 → Key revoked or misconfigured. See "Auth Failure" below.
│   ├─ 402 → Credits exhausted. Top up immediately.
│   ├─ 422 → Safety filter. Prompt issue, not outage.
│   ├─ 429 → Rate limited. Reduce concurrency.
│   ├─ 500/503 → Ideogram outage. Enable fallback.
│   └─ Timeout → Network or Ideogram performance issue.
├─ NO: Are images generating but quality is bad?
│   ├─ YES → Check model version, style params, magic_prompt setting.
│   └─ NO → Check image download (URLs may have expired).
└─ Not sure: Run triage script above.
```

## Immediate Actions

### 401 -- Authentication Failure
```bash
set -euo pipefail
# Verify key is set
echo "Key present: ${IDEOGRAM_API_KEY:+YES}${IDEOGRAM_API_KEY:-NO}"
echo "Key length: ${#IDEOGRAM_API_KEY}"

# If key was rotated, update everywhere:
# 1. Ideogram dashboard: create new key
# 2. Update secret manager / env vars
# 3. Restart affected services

# Kubernetes
kubectl create secret generic ideogram-secrets \
  --from-literal=api-key="$NEW_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/ideogram-service
```

### 429 -- Sustained Rate Limiting
```bash
set -euo pipefail
# Reduce concurrency immediately
kubectl set env deployment/ideogram-service IDEOGRAM_CONCURRENCY=3

# If sustained, contact Ideogram for limit increase
# partnership@ideogram.ai
```

### 500/503 -- Ideogram Outage
```bash
set -euo pipefail
# Enable fallback mode (return placeholder images)
kubectl set env deployment/ideogram-service IDEOGRAM_FALLBACK=true
kubectl rollout restart deployment/ideogram-service

# Monitor for resolution, then disable fallback
# kubectl set env deployment/ideogram-service IDEOGRAM_FALLBACK=false
```

### 402 -- Credits Exhausted
```
1. Log into ideogram.ai > Settings > API Beta
2. Check current balance
3. Increase auto top-up amount
4. Or manually add credits
5. Verify generation works again
```

## Fallback Implementation
```typescript
const FALLBACK_ENABLED = process.env.IDEOGRAM_FALLBACK === "true";

async function generateWithFallback(prompt: string, options: any = {}) {
  if (FALLBACK_ENABLED) {
    return {
      data: [{
        url: `https://placehold.co/1024x1024/333/fff?text=${encodeURIComponent("Image unavailable")}`,
        seed: 0,
        resolution: "1024x1024",
        is_image_safe: true,
        fallback: true,
      }],
    };
  }

  try {
    return await generateImage(prompt, options);
  } catch (err: any) {
    if (err.status >= 500) {
      console.error("Ideogram 5xx -- serving fallback");
      return generateWithFallback(prompt, options);
    }
    throw err;
  }
}
```

## Communication Templates

### Internal (Slack)
```
P[X] INCIDENT: Ideogram Integration
Status: INVESTIGATING / MITIGATED / RESOLVED
Impact: [e.g., Image generation unavailable for users]
Cause: [e.g., API returning 500, or key revoked]
Action: [e.g., Fallback enabled, monitoring for resolution]
Next update: [time]
Owner: @[name]
```

## Postmortem Template
```markdown
## Incident: Ideogram [Type]
**Date:** YYYY-MM-DD | **Duration:** Xh Ym | **Severity:** P[1-4]

### Summary
[1-2 sentences]

### Timeline
- HH:MM - First alert triggered
- HH:MM - Triage started
- HH:MM - Fallback enabled
- HH:MM - Root cause identified
- HH:MM - Resolved

### Root Cause
[Technical explanation]

### Action Items
- [ ] [Fix] - Owner - Due date
- [ ] [Prevention] - Owner - Due date
```

## Error Handling
| Issue | Detection | Mitigation |
|-------|-----------|------------|
| Total API outage | Health check fails | Enable fallback images |
| Key revoked | 401 on valid config | Rotate key immediately |
| Credits depleted | 402 responses | Top up, pause batch jobs |
| Rate limit flood | Sustained 429 | Reduce concurrency to 3 |

## Output
- Incident identified and categorized by severity
- Immediate remediation applied
- Fallback activated if needed
- Stakeholders notified with template
- Evidence collected for postmortem

## Resources
- [Ideogram API Overview](https://developer.ideogram.ai/ideogram-api/api-overview)
- Enterprise support: `partnership@ideogram.ai`

## Next Steps
For data handling patterns, see `ideogram-data-handling`.
