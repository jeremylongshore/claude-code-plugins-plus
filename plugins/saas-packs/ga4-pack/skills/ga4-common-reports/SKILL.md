---
name: ga4-common-reports
description: |
  Copy-paste recipes for the 6-7 reports every site owner actually wants:
  DAU/MAU/WAU, retention cohort, top pages by source, channel attribution,
  conversion funnel, geo breakdown, device split. Each recipe is a fully-formed
  Data API request. Trigger with "GA4 DAU", "GA4 retention", "GA4 top pages",
  "GA4 funnel", "GA4 channel report", "common GA4 reports".
allowed-tools: Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, analytics, google-analytics, ga4, reports]
compatibility: Designed for Claude Code
---

# GA4 Common Reports

Recipes for the reports that get asked for ~95% of the time. Each one is a complete `runReport` you can paste, change `PROPERTY_ID`, and run. Prerequisite: `ga4-auth-setup` done.

The setup block (same for every recipe):

```python
import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Metric, Dimension,
    FilterExpression, Filter, OrderBy,
)

PROPERTY = f"properties/{os.environ['GA4_PROPERTY_ID']}"
client = BetaAnalyticsDataClient()
```

## 1. Daily Active Users (DAU) — 30-day rolling

```python
req = RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="30daysAgo", end_date="yesterday")],
    metrics=[Metric(name="activeUsers")],
    dimensions=[Dimension(name="date")],
    order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
)
resp = client.run_report(req)
for r in resp.rows:
    print(f"{r.dimension_values[0].value} {r.metric_values[0].value}")
```

**Why `yesterday`, not `today`:** today's number is incomplete and will keep climbing through the day. For a clean rolling DAU, end the window at `yesterday`.

## 2. MAU / WAU — rolling unique users

GA4 doesn't expose MAU as a single metric — you compute it from the same `activeUsers` rolled up over a wider date range. The trick: a single-row report with no date dimension returns the unique count over the entire window (de-duplicated across days).

```python
# MAU (last 30 days)
mau = client.run_report(RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="29daysAgo", end_date="yesterday")],
    metrics=[Metric(name="activeUsers")],
))
mau_count = int(mau.rows[0].metric_values[0].value) if mau.rows else 0

# WAU (last 7 days)
wau = client.run_report(RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="6daysAgo", end_date="yesterday")],
    metrics=[Metric(name="activeUsers")],
))
wau_count = int(wau.rows[0].metric_values[0].value) if wau.rows else 0

print(f"MAU: {mau_count:,}   WAU: {wau_count:,}   Ratio (engagement): {wau_count/mau_count:.2%}")
```

Stickiness rule-of-thumb: `WAU/MAU > 0.5` is good, `> 0.7` is excellent, `< 0.2` means most users visit once and bounce.

## 3. Top pages — last 7 days, ordered by pageviews

```python
req = RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
    metrics=[Metric(name="screenPageViews"), Metric(name="activeUsers"), Metric(name="averageSessionDuration")],
    dimensions=[Dimension(name="pagePath")],
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
    limit=25,
)
resp = client.run_report(req)
print(f"{'Path':<60} {'Views':>8} {'Users':>8} {'AvgSec':>8}")
for r in resp.rows:
    print(f"{r.dimension_values[0].value[:58]:<60} "
          f"{r.metric_values[0].value:>8} {r.metric_values[1].value:>8} "
          f"{float(r.metric_values[2].value):>8.1f}")
```

## 4. Channel attribution — where did users come from?

```python
req = RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="30daysAgo", end_date="yesterday")],
    metrics=[Metric(name="activeUsers"), Metric(name="sessions"), Metric(name="engagedSessions")],
    dimensions=[Dimension(name="sessionDefaultChannelGrouping")],
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
)
resp = client.run_report(req)
print(f"{'Channel':<28} {'Users':>10} {'Sessions':>10} {'Engaged%':>10}")
for r in resp.rows:
    users = int(r.metric_values[0].value)
    sess = int(r.metric_values[1].value)
    eng = int(r.metric_values[2].value)
    eng_rate = eng / sess if sess else 0
    print(f"{r.dimension_values[0].value:<28} {users:>10,} {sess:>10,} {eng_rate:>9.1%}")
```

GA4's default channel grouping has ~12 buckets: Direct, Organic Search, Paid Search, Organic Social, Paid Social, Email, Referral, Display, Video, Affiliates, Audio, etc. Use `sessionSource` + `sessionMedium` for finer-grained attribution (e.g. `google / organic` vs `bing / organic`).

## 5. Retention cohort — week 1 / 2 / 3 / 4 return rate

GA4 has a built-in cohort exploration in the UI but the Data API doesn't expose it cleanly. The workaround: query DAU per week and compute rolling overlap. The cheap approximation:

```python
# Weekly active users for the last 8 weeks
req = RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="56daysAgo", end_date="yesterday")],
    metrics=[Metric(name="activeUsers")],
    dimensions=[Dimension(name="isoYearIsoWeek")],
    order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="isoYearIsoWeek"))],
)
resp = client.run_report(req)
for r in resp.rows:
    print(f"{r.dimension_values[0].value}  {r.metric_values[0].value}")
```

For true cohort retention (e.g. "of users acquired in week N, what % came back in week N+1, N+2, N+3"), you need event-level data — use `ga4-bigquery-export` and write the cohort SQL directly. The Data API can't express the join.

## 6. Conversion funnel — landing → engagement → conversion

GA4 funnels via API: query each step as a separate `runReport` filtered by the event that defines the step, then divide.

```python
def step_users(event_name, days_ago=7):
    return int(client.run_report(RunReportRequest(
        property=PROPERTY,
        date_ranges=[DateRange(start_date=f"{days_ago}daysAgo", end_date="yesterday")],
        metrics=[Metric(name="activeUsers")],
        dimension_filter=FilterExpression(filter=Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.EXACT,
                value=event_name,
            ),
        )),
    )).rows[0].metric_values[0].value)

# Example funnel: landed → engaged → signed up → purchased
steps = [
    ("session_start",  step_users("session_start")),
    ("user_engagement", step_users("user_engagement")),
    ("sign_up",         step_users("sign_up")),
    ("purchase",        step_users("purchase")),
]
top = steps[0][1] or 1
print(f"{'Step':<20} {'Users':>10} {'% of top':>10}")
for name, count in steps:
    print(f"{name:<20} {count:>10,} {count/top:>9.1%}")
```

Limitation: this counts users who fired the event at any point in the window, NOT users who progressed through the funnel in order. For ordered funnels (true sequencing), use BigQuery export or the GA4 UI's Exploration → Funnel report.

## 7. Geo + device split

```python
req = RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="30daysAgo", end_date="yesterday")],
    metrics=[Metric(name="activeUsers"), Metric(name="bounceRate")],
    dimensions=[Dimension(name="country"), Dimension(name="deviceCategory")],
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
    limit=30,
)
resp = client.run_report(req)
for r in resp.rows:
    country, device = r.dimension_values[0].value, r.dimension_values[1].value
    users, bounce = r.metric_values[0].value, float(r.metric_values[1].value)
    print(f"{country:<20} {device:<10} {users:>10} {bounce:>6.1%}")
```

A common signal: if one country dominates with low engagement + high bounce, it's often bot traffic from that country's cloud-host hubs (Singapore, Vietnam, China data centers are the usual suspects).

## When the Data API isn't enough

Three reasons to graduate to BigQuery export:

1. **Sampling** — your queries hit `resp.metadata.data_loss_from_other_row=True`. Sampled = approximate. BQ export = exact.
2. **Custom event analytics** — joining event-level data across sessions, computing retention cohorts, building attribution models. SQL is the only sensible tool.
3. **Cost** — Data API has daily quotas; BQ is pay-per-query (free for small properties, cheap up to ~100M events/day).

See `ga4-bigquery-export` for the setup.

## Related skills

- `ga4-auth-setup` — prerequisite
- `ga4-data-api-query` — the underlying API the recipes here use
- `ga4-realtime-api` — for "right now" data instead of any of the above
- `ga4-bigquery-export` — when these recipes hit their limits
