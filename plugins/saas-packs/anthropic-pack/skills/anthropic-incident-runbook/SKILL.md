---
name: anthropic-incident-runbook
description: |
  Respond to Anthropic API incidents — outages, degraded performance,
  error spikes, and rate limit issues in production.
  Trigger with "anthropic down", "claude outage", "anthropic incident",
  "claude not responding", "anthropic 529".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, incident, runbook]
---

# Anthropic Incident Runbook

## Step 1: Confirm the Issue
```bash
# Check Anthropic status
curl -s https://status.anthropic.com/api/v2/status.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"Status: {d['status']['description']} ({d['status']['indicator']})\")"

# Test API directly
curl -s -w "\nHTTP %{http_code} in %{time_total}s\n" \
  https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":5,"messages":[{"role":"user","content":"ping"}]}'
```

## Step 2: Classify Severity
| Symptom | Severity | Action |
|---------|----------|--------|
| 529 overloaded (intermittent) | Low | SDK auto-retries handle this |
| 529 overloaded (sustained 5+ min) | Medium | Switch to fallback model |
| 401/403 on all requests | High | API key issue — check console |
| All requests timing out | High | Check status page, activate fallback |
| Status page shows incident | Varies | Follow status page updates |

## Step 3: Activate Fallback
```typescript
async function callWithFallback(params: Anthropic.MessageCreateParams) {
  try {
    return await client.messages.create(params);
  } catch (err) {
    if (err instanceof Anthropic.APIError && (err.status === 529 || err.status === 500)) {
      // Try a different model
      if (params.model.includes('opus')) {
        return await client.messages.create({ ...params, model: 'claude-sonnet-4-20250514' });
      }
      if (params.model.includes('sonnet')) {
        return await client.messages.create({ ...params, model: 'claude-haiku-4-5-20251001' });
      }
    }
    throw err;
  }
}
```

## Step 4: Communicate
- Update your status page if user-facing
- Note: Anthropic incidents typically resolve in 15-60 minutes

## Step 5: Post-Incident
- Check your error logs for the incident window
- Calculate impact (failed requests, user impact)
- Verify all systems recovered

## Resources
- [Anthropic Status](https://status.anthropic.com)
- [Status API](https://status.anthropic.com/api)

## Next Steps
See `anthropic-reliability-patterns` for building resilient integrations.
