---
name: figma-incident-runbook
description: |
  Respond to Figma API outages, auth failures, and rate limit incidents.
  Use when Figma integration is down, experiencing errors,
  or running post-incident reviews for Figma-related failures.
  Trigger with phrases like "figma incident", "figma outage",
  "figma down", "figma broken", "figma emergency".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Incident Runbook

## Overview
Rapid incident response procedures for Figma REST API integration failures. Covers triage, mitigation, and postmortem for the most common failure modes.

## Prerequisites
- Access to application logs and metrics
- Figma PAT for health checks
- Communication channel (Slack, PagerDuty)

## Instructions

### Step 1: Quick Triage (First 5 Minutes)
```bash
#!/bin/bash
echo "=== Figma Incident Triage ==="

# 1. Is Figma itself down?
echo -n "Figma Status: "
curl -s https://www.figmastatus.com/api/v2/status.json 2>/dev/null \
  | jq -r '.status.description // "Cannot reach status page"'

# 2. Is our token valid?
echo -n "Auth Check: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me)
echo "$HTTP_CODE"

# 3. Can we read a known file?
echo -n "File Access: "
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1" \
  | jq -r '.name // "FAILED"'

# 4. Are we rate limited?
echo "Rate Limit Headers:"
curl -s -D - -o /dev/null \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me 2>/dev/null \
  | grep -iE "(retry-after|rate-limit|figma)" || echo "No rate limit headers"
```

### Step 2: Decision Tree
```
API returning errors?
├── 403 Forbidden
│   ├── Token expired (>90 days) → Rotate PAT immediately
│   ├── Wrong scopes → Regenerate with correct scopes
│   └── File not shared → Check file permissions
│
├── 429 Rate Limited
│   ├── Retry-After < 60s → Wait and retry automatically
│   ├── Retry-After > 300s → Reduce request volume
│   └── X-Figma-Rate-Limit-Type: low → Consider upgrading plan
│
├── 404 Not Found
│   ├── File deleted → Check with file owner
│   ├── Wrong file key → Verify FIGMA_FILE_KEY
│   └── API path wrong → Check endpoint documentation
│
├── 500/503 Server Error
│   ├── status.figma.com shows incident → Wait for resolution
│   ├── Intermittent → Retry with backoff
│   └── Persistent → Contact Figma support
│
└── Network Error (ECONNREFUSED, timeout)
    ├── DNS resolution failing → Check DNS config
    ├── Firewall blocking → Verify outbound HTTPS to api.figma.com
    └── TLS error → Check Node.js version (18+ required)
```

### Step 3: Immediate Mitigation

**For 403 (Token Expired):**
```bash
# Generate new PAT in Figma Settings > Personal access tokens
# Then update your deployment:

# GitHub Actions
gh secret set FIGMA_PAT --body "figd_new-token-here"

# Cloud Run
echo -n "figd_new-token" | gcloud secrets versions add figma-pat --data-file=-
gcloud run services update my-service --update-secrets="FIGMA_PAT=figma-pat:latest"

# Fly.io
fly secrets set FIGMA_PAT=figd_new-token
```

**For 429 (Rate Limited):**
```typescript
// Emergency: disable non-critical Figma calls
const EMERGENCY_MODE = process.env.FIGMA_EMERGENCY === 'true';

async function safeFigmaCall<T>(
  path: string,
  critical: boolean = false
): Promise<T | null> {
  if (EMERGENCY_MODE && !critical) {
    console.warn(`Figma call skipped (emergency mode): ${path}`);
    return null;
  }
  return figmaFetch(path);
}
```

**For 500/503 (Figma Down):**
```typescript
// Serve cached data when Figma is unavailable
async function getTokensWithFallback() {
  try {
    return await extractTokensFromFigma();
  } catch (error) {
    console.warn('Figma unavailable, serving cached tokens');
    // Return last-known-good tokens from cache or file
    const cached = await readFile('output/tokens.json', 'utf-8');
    return JSON.parse(cached);
  }
}
```

### Step 4: Communication
```markdown
## Internal Notification (Slack)
**Figma Integration Alert**
- Status: INVESTIGATING / MITIGATED / RESOLVED
- Impact: [Design token sync paused / Asset export failing]
- Cause: [403 expired token / 429 rate limit / Figma outage]
- Action: [Rotating token / Reducing request rate / Waiting for Figma]
- ETA: [Next update in 15 min]

## External (if applicable)
Design system updates may be delayed due to a temporary issue
with our Figma integration. Cached data is being served.
```

### Step 5: Postmortem Template
```markdown
## Figma Incident Postmortem
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P1/P2/P3

### Summary
[One sentence: what happened and what was the impact]

### Timeline
- HH:MM UTC - First alert fired (describe alert)
- HH:MM UTC - On-call acknowledged
- HH:MM UTC - Root cause identified
- HH:MM UTC - Mitigation applied
- HH:MM UTC - Full resolution confirmed

### Root Cause
[Technical explanation, e.g., "PAT expired after 90 days without rotation"]

### Action Items
- [ ] Set up PAT rotation reminder at 80-day mark
- [ ] Add 403 alert to PagerDuty
- [ ] Implement cached fallback for token data
```

## Output
- Issue identified via triage script
- Root cause determined from decision tree
- Mitigation applied (token rotation, fallback mode, etc.)
- Stakeholders notified
- Postmortem documented

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status.figma.com | Network issue | Try from different network or mobile |
| Triage script fails | PAT not set | Set FIGMA_PAT before running |
| Fallback data stale | Last cache too old | Set up regular cache refresh |
| Alert not firing | Missing metrics | Verify Prometheus scrape config |

## Resources
- [Figma Status Page](https://status.figma.com)
- [Figma Support](https://help.figma.com/hc/en-us/requests/new)
- [Figma Developer Forum](https://forum.figma.com/)

## Next Steps
For data handling, see `figma-data-handling`.
