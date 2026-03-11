---
name: instantly-observability
description: |
  Set up comprehensive observability for Instantly integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Instantly operations, setting up dashboards,
  or configuring alerting for Instantly integration health.
  Trigger with phrases like "instantly monitoring", "instantly metrics",
  "instantly observability", "monitor instantly", "instantly alerts", "instantly tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Instantly Observability

## Overview
Monitor Instantly email outreach campaign health, deliverability metrics, and sending account reputation. Key signals include email deliverability rate, bounce rate, reply rate, open rate, sending volume vs daily limits, account warmup progress, and spam placement rate. For Instantly, deliverability is the critical metric -- a sending account with high bounces or spam complaints will damage domain reputation and reduce the effectiveness of all campaigns.

## Prerequisites
- Instantly Growth or Hypergrowth plan
- API access with campaign read permissions
- Email deliverability monitoring (inbox placement tester recommended)

## Instructions

### Step 1: Track Campaign Metrics via API
```bash
# Pull campaign performance data
curl "https://api.instantly.ai/api/v1/campaign/analytics?campaign_id=CAMP_ID" \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '{
    sent: .total_sent, delivered: .total_delivered, bounced: .total_bounced,
    opened: .total_opened, replied: .total_replied,
    bounce_rate: (.total_bounced / .total_sent * 100),
    reply_rate: (.total_replied / .total_sent * 100)
  }'
```

### Step 2: Monitor Sending Account Health
```typescript
// instantly-account-monitor.ts
async function monitorAccountHealth() {
  const accounts = await instantlyApi.getAccounts();
  for (const acct of accounts) {
    emitGauge('instantly_account_reputation', acct.reputation_score, { email: acct.email });
    emitGauge('instantly_daily_send_usage_pct', acct.sent_today / acct.daily_limit * 100, { email: acct.email });
    emitGauge('instantly_warmup_progress_pct', acct.warmup_progress, { email: acct.email });

    if (acct.reputation_score < 70) {
      console.warn(`Low reputation: ${acct.email} (score: ${acct.reputation_score})`);
    }
  }
}
```

### Step 3: Set Deliverability Alerts
```yaml
groups:
  - name: instantly
    rules:
      - alert: InstantlyHighBounceRate
        expr: instantly_bounce_rate > 5
        annotations: { summary: "Instantly bounce rate exceeds 5% -- check lead list quality" }
      - alert: InstantlyLowReputation
        expr: instantly_account_reputation < 60
        for: 1h
        annotations: { summary: "Sending account reputation below 60 on {{ $labels.email }}" }
      - alert: InstantlySendingCapNear
        expr: instantly_daily_send_usage_pct > 90
        annotations: { summary: "Sending account at 90% of daily limit" }
      - alert: InstantlyWarmupStalled
        expr: delta(instantly_warmup_progress_pct[24h]) == 0 and instantly_warmup_progress_pct < 100
        annotations: { summary: "Warmup progress stalled on {{ $labels.email }}" }
```

### Step 4: Monitor Campaign Sequence Health
```bash
# Check reply and bounce rates across all active campaigns
curl "https://api.instantly.ai/api/v1/campaign/list?status=active" \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '.[] | {name, status, bounce_rate: (.bounced / .sent * 100), reply_rate: (.replied / .sent * 100), daily_sends: .sent_today}'
```

### Step 5: Dashboard Panels
Track: deliverability rate by campaign, bounce rate trend (alert if rising), sending account reputation scores (table), warmup progress per account, daily send volume vs limits, reply rate over time, and spam complaint rate. A rising bounce rate is the most urgent signal -- it can cascade into domain blacklisting.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Bounce rate >5% | Bad lead list quality | Verify emails before importing, use email verification API |
| Reputation dropping | Too many emails too fast | Reduce daily limit, extend warmup period |
| Campaign paused | Account hit daily send limit | Spread sends across more accounts |
| Opens not tracking | Tracking pixel blocked | Expected for privacy-focused recipients; use reply rate instead |

## Examples
```bash
# Quick health check: overall workspace deliverability
curl -s "https://api.instantly.ai/api/v1/campaign/analytics?period=last_7d" \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '{total_sent, delivered_pct: (.delivered / .sent * 100), bounce_pct: (.bounced / .sent * 100), reply_pct: (.replied / .sent * 100)}'
```
