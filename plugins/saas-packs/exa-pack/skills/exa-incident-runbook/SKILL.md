---
name: exa-incident-runbook
description: |
  Execute Exa incident response with triage, mitigation, and postmortem procedures.
  Use when responding to Exa-related outages, investigating errors,
  or running post-incident reviews for Exa integration failures.
  Trigger with phrases like "exa incident", "exa outage",
  "exa down", "exa on-call", "exa emergency", "exa broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, incident-response]

---
# Exa Incident Runbook

## Overview
Rapid incident response procedures for Exa search API issues. Exa errors include a `requestId` field for support escalation. Default rate limit is 10 QPS. Contact hello@exa.ai for urgent production issues.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | All Exa calls failing | < 15 min | 401/500 on every request |
| P2 | Degraded performance | < 1 hour | High latency, partial failures |
| P3 | Minor impact | < 4 hours | Empty results, content fetch failures |
| P4 | No user impact | Next business day | Monitoring gaps |

## Quick Triage (Run First)

```bash
set -euo pipefail
echo "=== Exa Triage ==="

# 1. Test API connectivity
echo -n "API Status: "
HTTP_CODE=$(curl -s -o /tmp/exa-triage.json -w "%{http_code}" \
  -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"triage test","numResults":1}')
echo "$HTTP_CODE"

# 2. Show error details if not 200
if [ "$HTTP_CODE" != "200" ]; then
  echo "Error response:"
  cat /tmp/exa-triage.json | python3 -m json.tool 2>/dev/null || cat /tmp/exa-triage.json
fi

# 3. Check if it's a key issue
echo ""
echo "API Key: ${EXA_API_KEY:+SET (${#EXA_API_KEY} chars)}"
```

## Decision Tree

```
Exa API returning errors?
├── YES: What HTTP code?
│   ├── 401 → API key invalid/expired → Regenerate at dashboard.exa.ai
│   ├── 402 → Credits exhausted → Top up at dashboard.exa.ai
│   ├── 429 → Rate limited → Implement backoff, enable caching
│   ├── 5xx → Exa server issue → Retry with backoff, wait for resolution
│   └── 400 → Bad request → Fix request parameters
└── NO: Is search quality degraded?
    ├── Empty results → Broaden query, check date/domain filters
    ├── Low relevance → Switch search type, rephrase query
    └── Slow responses → Switch to faster search type, add caching
```

## Immediate Actions by Error Code

### 401/403 — Authentication
```bash
set -euo pipefail
# Verify API key
echo "Key present: ${EXA_API_KEY:+yes}"
echo "Key length: ${#EXA_API_KEY}"

# Test with a simple search
curl -v -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"auth test","numResults":1}' 2>&1 | grep "< HTTP"

# Fix: regenerate key at dashboard.exa.ai and update env
```

### 429 — Rate Limited
```typescript
// Enable emergency caching to reduce API calls
import { LRUCache } from "lru-cache";

const emergencyCache = new LRUCache<string, any>({
  max: 10000,
  ttl: 30 * 60 * 1000, // 30-minute emergency TTL
});

// Reduce concurrent requests
import PQueue from "p-queue";
const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 5 });
```

### 5xx — Exa Server Errors
```typescript
// Enable graceful degradation
async function searchWithFallback(query: string, opts: any) {
  try {
    return await exa.searchAndContents(query, opts);
  } catch (err: any) {
    if (err.status >= 500) {
      console.error(`[Exa] ${err.status}: ${err.message} (requestId: ${err.requestId})`);
      // Return cached results or show degraded UI
      const cached = emergencyCache.get(query);
      if (cached) return cached;
      return { results: [], _degraded: true };
    }
    throw err;
  }
}
```

## Communication Templates

### Internal (Slack)
```
P[1-4] INCIDENT: Exa Search Integration
Status: INVESTIGATING
Impact: [Describe user impact]
Error: [HTTP code] [error tag]
RequestId: [from error response]
Current action: [What you're doing]
Next update: [Time]
```

### Support Escalation
```
To: hello@exa.ai
Subject: [P1/P2] Production issue — [brief description]

RequestId: [from error response]
Timestamp: [ISO 8601]
HTTP Status: [code]
Error Tag: [tag from response]
Frequency: [every request / intermittent / percentage]
Impact: [number of affected users/requests]
```

## Post-Incident

### Evidence Collection
```bash
set -euo pipefail
# Capture recent error logs
kubectl logs -l app=exa-integration --since=1h 2>/dev/null | grep -i "error\|429\|500" | tail -50

# Capture metrics snapshot
curl -s "localhost:9090/api/v1/query?query=rate(exa_search_error[1h])" 2>/dev/null
```

### Postmortem Template
```markdown
## Incident: Exa [Error Type]
**Date:** YYYY-MM-DD | **Duration:** Xh Ym | **Severity:** P[1-4]

### Summary
[1-2 sentence description]

### Timeline
- HH:MM — First error detected
- HH:MM — Triage began
- HH:MM — Root cause identified
- HH:MM — Mitigation applied
- HH:MM — Full recovery

### Root Cause
[Technical explanation]

### Action Items
- [ ] [Preventive measure] — Owner — Due date
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Intermittent 5xx | Exa server issues | Retry with backoff, check status page |
| All requests 401 | API key rotated/expired | Regenerate at dashboard.exa.ai |
| Sudden empty results | Exa index issue | Switch search type, broaden query |
| Latency spike | Exa under load | Use `fast` type, enable caching |

## Resources
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)
- [Exa Support](mailto:hello@exa.ai)

## Next Steps
For data handling, see `exa-data-handling`. For debugging, see `exa-debug-bundle`.
