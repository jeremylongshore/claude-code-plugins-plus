---
name: grammarly-incident-runbook
description: |
  Follow Grammarly incident response runbook for API outages.
  Use when Grammarly API is down, experiencing errors,
  or when investigating service degradation.
  Trigger with phrases like "grammarly down", "grammarly outage",
  "grammarly incident", "grammarly not responding".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Incident Runbook

## Triage Steps

### Step 1: Verify Outage

```bash
# Test API health
curl -s -o /dev/null -w "%{http_code}" \
  https://api.grammarly.com/ecosystem/api/v2/scores

# Test with auth
curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $GRAMMARLY_ACCESS_TOKEN" \
  -X POST https://api.grammarly.com/ecosystem/api/v2/scores \
  -H "Content-Type: application/json" \
  -d '{"text": "Test sentence with enough words for minimum requirement for the Grammarly writing score API diagnostic check."}' 
```

### Step 2: Classify Severity

| Severity | Condition | Action |
|----------|-----------|--------|
| P1 | API returns 5xx for all requests | Activate fallback, notify stakeholders |
| P2 | Intermittent 5xx or high latency | Enable retry logic, monitor |
| P3 | Specific endpoint failing | Route around, file support ticket |

### Step 3: Fallback Mode

```typescript
async function scoreWithFallback(text: string, token: string) {
  try {
    return await grammarlyClient.score(text);
  } catch {
    console.warn('Grammarly API unavailable, returning placeholder');
    return { overallScore: -1, correctness: -1, clarity: -1, engagement: -1, tone: -1, fallback: true };
  }
}
```

## Resources

- [Grammarly Support](https://developer.grammarly.com/docs/support)
