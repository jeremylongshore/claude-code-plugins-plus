---
name: clay-incident-runbook
description: |
  Execute Clay incident response procedures for enrichment failures, credit exhaustion, and data flow outages.
  Use when Clay enrichments stop working, webhook delivery fails,
  or CRM sync breaks in production.
  Trigger with phrases like "clay incident", "clay outage", "clay down",
  "clay emergency", "clay broken", "clay enrichment stopped".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, incident-response]

---
# Clay Incident Runbook

## Overview

Rapid response procedures for Clay-related production incidents. Clay is a hosted SaaS platform, so incidents fall into two categories: (1) Clay-side issues (platform outage, provider degradation) and (2) your-side issues (webhook misconfiguration, credit exhaustion, handler failures).

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete data flow stopped | < 15 min | Credits exhausted, webhook URL expired, Clay outage |
| P2 | Degraded enrichment | < 1 hour | Low hit rates, slow processing, CRM sync errors |
| P3 | Minor impact | < 4 hours | Single provider down, intermittent webhook failures |
| P4 | No user impact | Next business day | Monitoring gaps, cost optimization needed |

## Instructions

### Step 1: Quick Triage (2 Minutes)

```bash
#!/bin/bash
# clay-triage.sh — rapid diagnostic for Clay incidents
set -euo pipefail

echo "=== Clay Incident Triage ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# 1. Check Clay platform status
echo "--- Clay Platform Status ---"
curl -s -o /dev/null -w "clay.com: HTTP %{http_code}\n" https://www.clay.com
echo ""

# 2. Test webhook delivery
echo "--- Webhook Test ---"
if [ -n "${CLAY_WEBHOOK_URL:-}" ]; then
  WEBHOOK_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$CLAY_WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{"_triage": true, "_ts": "'$(date -u +%s)'"}')
  echo "Webhook: HTTP $WEBHOOK_CODE"
  if [ "$WEBHOOK_CODE" = "200" ]; then echo "  -> Webhook OK"; fi
  if [ "$WEBHOOK_CODE" = "404" ]; then echo "  -> ISSUE: Webhook URL invalid/expired"; fi
  if [ "$WEBHOOK_CODE" = "429" ]; then echo "  -> ISSUE: Rate limited"; fi
else
  echo "CLAY_WEBHOOK_URL not set!"
fi
echo ""

# 3. Test Enterprise API (if applicable)
echo "--- Enterprise API Test ---"
if [ -n "${CLAY_API_KEY:-}" ]; then
  API_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "https://api.clay.com/v1/people/enrich" \
    -H "Authorization: Bearer $CLAY_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"email": "triage@test.com"}')
  echo "Enterprise API: HTTP $API_CODE"
  if [ "$API_CODE" = "401" ]; then echo "  -> ISSUE: API key invalid/expired"; fi
  if [ "$API_CODE" = "403" ]; then echo "  -> ISSUE: Not on Enterprise plan or key revoked"; fi
else
  echo "No Enterprise API key configured"
fi
echo ""

# 4. Check your callback endpoint
echo "--- Callback Endpoint ---"
CALLBACK_URL="${CLAY_CALLBACK_URL:-https://your-app.com/api/health}"
curl -s -o /dev/null -w "Callback: HTTP %{http_code}\n" "$CALLBACK_URL" || echo "Callback endpoint unreachable!"
```

### Step 2: Decision Tree

```
Enrichment not running?
├── Check Clay UI: any red error cells?
│   ├── YES: Click cells, read error messages → go to Error Resolution
│   └── NO: Continue
├── Is auto-run enabled? (Table Settings > Auto-update)
│   ├── NO: Enable auto-update at table level, then column level
│   └── YES: Continue
├── Do you have credits remaining? (Settings > Plans & Billing)
│   ├── NO: Add credits or connect own provider API keys → P1
│   └── YES: Continue
├── Is the webhook accepting data? (Test with curl)
│   ├── NO: Re-create webhook (50K limit may be hit) → P1
│   └── YES: The issue is likely provider-side
└── Check individual enrichment providers in Clay Settings > Connections
    ├── Provider connection lost → Reconnect API key
    └── Provider rate limited → Wait or switch to different provider
```

### Step 3: Common Incident Resolutions

**P1: Credits Exhausted**
```
1. Check: Settings > Plans & Billing > Credit balance
2. Immediate: Connect your own provider API keys (0 credits)
3. Short-term: Add credit pack or upgrade plan
4. Prevent: Set credit burn alerts (see clay-observability)
```

**P1: Webhook URL Expired (50K Limit)**
```
1. Check: Table > + Add > Webhooks — does existing webhook show "limit reached"?
2. Fix: Create new webhook on same table
3. Update: Change CLAY_WEBHOOK_URL in all deployment secrets
4. Verify: Send test payload to new webhook URL
```

**P2: Low Enrichment Hit Rate**
```
1. Check: Sample 10 rows — are input domains valid?
2. Check: Are providers connected? (Settings > Connections)
3. Fix: Pre-filter invalid rows, reconnect providers
4. Monitor: Track hit rate for next hour
```

**P2: CRM Sync Failures**
```
1. Check: HTTP API column errors (click red cells)
2. Common: CRM API key expired → regenerate and update in column config
3. Common: Field mapping changed → update column body JSON
4. Test: Run HTTP API column on single row manually
```

### Step 4: Communication Template

```markdown
## Clay Incident Notification

**Severity:** P[1/2/3]
**Time detected:** [UTC timestamp]
**Impact:** [What's not working]
**Affected:** [Teams/workflows affected]

**Current Status:** [Investigating / Mitigating / Resolved]

**Actions Taken:**
1. [Action 1]
2. [Action 2]

**Next Update:** [Time]

**Root Cause:** [If known]
**Resolution:** [Steps taken to fix]
**Prevention:** [What we'll do to prevent recurrence]
```

### Step 5: Postmortem Template

| Item | Details |
|------|---------|
| Incident Date | [Date] |
| Duration | [X hours] |
| Severity | P[1/2/3] |
| Impact | [Leads not enriched / CRM not updated / Credits exhausted] |
| Root Cause | [e.g., Webhook hit 50K limit without monitoring] |
| Detection | [How was it discovered? Alert / user report / manual check] |
| Resolution | [Steps taken] |
| Credits Lost | [Estimate of wasted credits, if any] |
| Prevention | [Monitoring gaps to close, safeguards to add] |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't access Clay dashboard | Browser/network issue | Try incognito, different browser, or mobile |
| Webhook test returns nothing | Webhook URL malformed | Re-copy full URL from Clay table |
| All providers returning empty | Account-level issue | Contact Clay support at community.clay.com |
| CRM pushing wrong data | Column references changed | Re-map HTTP API column body fields |

## Resources

- [Clay Community Support](https://community.clay.com)
- [Clay University](https://university.clay.com)

## Next Steps

For data handling and compliance, see `clay-data-handling`.
