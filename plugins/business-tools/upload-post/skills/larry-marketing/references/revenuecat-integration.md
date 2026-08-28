# RevenueCat Integration

## Setup

Add RevenueCat config to `config.json`:

```json
{
  "revenuecat": {
    "v1SecretKey": "sk_...",
    "projectId": "your-project-id"
  }
}
```

Get the **V1 Secret API Key** from RevenueCat Dashboard → Project Settings → API Keys. Use the **secret** key (sk_), NOT the public key.

## API Endpoints

### Get Overview Metrics
RevenueCat doesn't expose dashboard overview via API. Use the V1 subscriber endpoint to track individual conversions, or scrape the dashboard via browser automation.

**Alternative: Webhooks.** Set up RevenueCat webhooks to log events (trial_started, initial_purchase, renewal, cancellation) to a local JSON file that the skill can read.

### Get Subscriber Info (V1)
```
GET https://api.revenuecat.com/v1/subscribers/{app_user_id}
Authorization: Bearer {v1SecretKey}
```

Returns: active subscriptions, entitlements, purchase history, management URL.

### List Subscribers (V2 — if available)
```
GET https://api.revenuecat.com/v2/projects/{projectId}/customers
Authorization: Bearer {v2SecretKey}
```

## Daily Report Script

`scripts/daily-report.js` runs daily to:

1. **Pull platform analytics** from Upload-Post (last 3 days of posts)
2. **Pull conversion data** from RevenueCat webhook logs OR manual input
3. **Cross-reference** post timing with conversion spikes
4. **Generate report** identifying which hooks drove actual revenue

### Cross-Reference Logic

```
For each day in last 3 days:
  1. Get all TikTok posts and their view counts
  2. Get all new trials + paid conversions from RevenueCat
  3. Correlate: conversion spikes within 24h of high-view posts
  4. Score each hook: (conversions in 24h window) / (views / 1000) = conversion rate per 1K views
  5. Rank hooks by conversion rate, not just views
```

### Why 3 Days?
- TikTok posts peak at 24-48h then tail off
- Conversion attribution window is ~24-72h
- Shorter = miss delayed conversions, longer = too noisy

## Webhook Setup (Recommended)

In RevenueCat Dashboard → Project Settings → Webhooks:

1. Set webhook URL to your server OR log to file
2. Events to track:
   - `INITIAL_PURCHASE` — new paid subscriber
   - `TRIAL_STARTED` — new trial
   - `TRIAL_CONVERTED` — trial → paid
   - `RENEWAL` — existing subscriber renewed
   - `CANCELLATION` — subscriber cancelled
   - `EXPIRATION` — subscription expired

Store events in `tiktok-marketing/rc-events.json`:
```json
[
  {
    "event": "INITIAL_PURCHASE",
    "timestamp": "2026-02-15T14:00:00Z",
    "product": "fullAccessMonthly",
    "revenue": 4.99,
    "currency": "USD"
  }
]
```

If no webhook available, the user can manually update this file or the agent can prompt for daily numbers:
- "How many new trials today?"
- "How many paid conversions?"
- "Current MRR?"

## Report Output

The daily report generates `tiktok-marketing/reports/YYYY-MM-DD.md`:

```markdown
# Daily Marketing Report — Feb 15, 2026

## TikTok Performance (Last 3 Days)
| Date | Hook | Views | Likes | Saves |
|------|------|-------|-------|-------|
| Feb 15 | boyfriend + catalogue | 12,400 | 340 | 67 |
| Feb 14 | sister prison cell | 8,200 | 215 | 43 |
| Feb 13 | nan hook | 3,100 | 89 | 12 |

## Conversions (Last 3 Days)
- New trials: 14
- Trial → Paid: 6
- New direct purchases: 2
- Revenue: $47.92

## Attribution
- Feb 15 spike (8 trials) correlates with "boyfriend + catalogue" post (12.4K views)
- Estimated conversion rate: 0.65 per 1K views (GOOD)

## Recommendations
- DOUBLE DOWN on relationship conflict hooks (boyfriend/sister/nan)
- Drop listicle format (Feb 13 — low views, 0 correlating conversions)
- Test: "My [person] didn't believe AI could redesign our [room]"
```
