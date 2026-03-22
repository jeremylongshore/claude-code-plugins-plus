---
name: firecrawl-incident-runbook
description: |
  Execute Firecrawl incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Firecrawl-related outages, investigating scrape/crawl failures,
  or running post-incident reviews for Firecrawl integration issues.
  Trigger with phrases like "firecrawl incident", "firecrawl outage",
  "firecrawl down", "firecrawl on-call", "firecrawl emergency", "firecrawl broken".
allowed-tools: Read, Grep, Bash(curl:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, incident-response]

---
# Firecrawl Incident Runbook

## Overview
Rapid incident response procedures for Firecrawl integration failures. Covers API outage triage, credential issues, credit exhaustion, crawl job failures, and webhook delivery problems.

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete failure | < 15 min | API returns 401/500 on all requests |
| P2 | Degraded service | < 1 hour | High latency, partial failures, 429s |
| P3 | Minor impact | < 4 hours | Webhook delays, some empty scrapes |
| P4 | No user impact | Next business day | Monitoring gaps, credit warnings |

## Quick Triage (Run First)

```bash
set -euo pipefail
# 1. Test Firecrawl API directly
echo "=== API Health ==="
curl -s -w "\nHTTP %{http_code}\n" https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}' | jq '{success, error}'

# 2. Check credit balance
echo "=== Credits ==="
curl -s https://api.firecrawl.dev/v1/team/credits \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" | jq .

# 3. Check our app health
echo "=== App Health ==="
curl -sf https://api.yourapp.com/health | jq '.services.firecrawl' || echo "App unhealthy"
```

## Decision Tree

```
Firecrawl API returning errors?
├─ 401: API key invalid
│   → Verify key at firecrawl.dev/app, rotate if needed
├─ 402: Credits exhausted
│   → Upgrade plan or wait for monthly reset
├─ 429: Rate limited
│   → Reduce concurrency, enable backoff, check Retry-After
├─ 500/503: Firecrawl outage
│   → Enable fallback mode, monitor firecrawl.dev status
└─ API working fine
    └─ Our integration issue
        ├─ Empty markdown → Increase waitFor, check target site
        ├─ Crawl stuck → Check job status, enforce timeout
        └─ Webhook not firing → Verify endpoint, check signature
```

## Immediate Actions by Error Type

### 401 — Authentication Failure
```bash
set -euo pipefail
# Verify current key
echo "Key prefix: ${FIRECRAWL_API_KEY:0:5}"
echo "Key length: ${#FIRECRAWL_API_KEY}"

# Test with explicit key
curl -s https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}' | jq .success

# If fails: regenerate key at firecrawl.dev/app and update all environments
```

### 402 — Credits Exhausted
```bash
set -euo pipefail
# Check balance
curl -s https://api.firecrawl.dev/v1/team/credits \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" | jq .

# Immediate: disable non-critical scraping
# Long-term: upgrade plan or implement credit budget
```

### 429 — Rate Limited
```typescript
// Enable emergency rate limiting
const EMERGENCY_DELAY_MS = 5000; // 5s between requests

async function emergencyScrape(url: string) {
  await new Promise(r => setTimeout(r, EMERGENCY_DELAY_MS));
  return firecrawl.scrapeUrl(url, { formats: ["markdown"] });
}
```

### 500/503 — Firecrawl Outage
```typescript
// Enable graceful degradation
async function scrapeWithFallback(url: string) {
  try {
    return await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
  } catch (error: any) {
    if (error.statusCode >= 500) {
      console.error("Firecrawl unavailable — using cached content");
      return getCachedContent(url); // serve stale data
    }
    throw error;
  }
}
```

## Communication Templates

### Internal (Slack)
```
P[1-4] INCIDENT: Firecrawl Integration
Status: INVESTIGATING
Impact: [Describe user-facing impact]
Error: [401/402/429/500] — [brief description]
Action: [What you're doing right now]
Next update: [time]
```

## Post-Incident

### Evidence Collection
```bash
set -euo pipefail
# Collect debug bundle
mkdir -p incident-$(date +%Y%m%d)
curl -s https://api.firecrawl.dev/v1/team/credits \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" > incident-$(date +%Y%m%d)/credits.json

# Application logs
kubectl logs -l app=my-app --since=1h | grep -i firecrawl > incident-$(date +%Y%m%d)/logs.txt 2>/dev/null || true
```

### Postmortem Template
```
## Incident: Firecrawl [Error Type]
Date: YYYY-MM-DD | Duration: X hours | Severity: P[1-4]

### Summary
[1-2 sentence description]

### Timeline
- HH:MM — [First alert]
- HH:MM — [Investigation started]
- HH:MM — [Root cause identified]
- HH:MM — [Resolved]

### Root Cause
[Technical explanation]

### Action Items
- [ ] [Preventive measure] — Owner — Due date
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach Firecrawl API | Network/DNS issue | Try from different network, check DNS |
| All scrapes return empty | Target site changed | Verify manually, adjust scrape options |
| Crawl jobs never complete | Queue backup | Cancel stuck jobs, reduce concurrency |
| Webhook endpoint unreachable | Deployment issue | Check HTTPS cert, DNS, firewall |

## Resources
- [Firecrawl Dashboard](https://firecrawl.dev/app)
- [Firecrawl Status](https://firecrawl.dev/status)
- [GitHub Issues](https://github.com/mendableai/firecrawl/issues)

## Next Steps
For data handling, see `firecrawl-data-handling`.
