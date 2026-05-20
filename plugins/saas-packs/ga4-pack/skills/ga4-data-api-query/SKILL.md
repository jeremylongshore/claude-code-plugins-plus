---
name: ga4-data-api-query
description: |
  Build a runReport request against the GA4 Data API v1 — pick valid metric/dimension
  combinations, set date ranges that respect data-freshness limits, apply filters,
  paginate large result sets, handle sampling thresholds. Trigger with "query GA4",
  "GA4 Data API", "runReport", "fetch GA4 metrics", "GA4 pageviews", "GA4 sessions".
allowed-tools: Bash(python3:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, analytics, google-analytics, ga4, data-api]
compatibility: Designed for Claude Code
---

# GA4 Data API v1 — runReport

The Data API v1 is the canonical read path for GA4. One endpoint (`runReport`) covers most use cases. Two paths matter for picking the right query: **dimensions** describe rows (date, page, source), **metrics** describe values (sessions, users, events). Not every combination is valid — see "Compatibility" below.

Prerequisite: auth working (see `ga4-auth-setup`).

## The minimum viable query

```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Metric, Dimension,
)

client = BetaAnalyticsDataClient()

req = RunReportRequest(
    property="properties/123456789",     # YOUR property ID (digits only)
    date_ranges=[
        DateRange(start_date="30daysAgo", end_date="today"),
    ],
    metrics=[Metric(name="activeUsers")],
    dimensions=[Dimension(name="date")],
)
resp = client.run_report(req)

for row in resp.rows:
    date = row.dimension_values[0].value     # YYYYMMDD string
    users = row.metric_values[0].value       # numeric string
    print(f"{date}: {users}")
```

That's the full skeleton. Everything below extends this shape.

## The 12 metrics worth knowing

| Metric | What it counts | Notes |
|---|---|---|
| `activeUsers` | Unique users with engagement in the window | The "users" people mean by default |
| `newUsers` | First-seen users in the window | |
| `totalUsers` | All users (engaged or not) — superset of `activeUsers` | |
| `sessions` | Sessions started in the window | Re-engages after 30min inactivity |
| `engagedSessions` | Sessions ≥10s OR ≥2 pageviews OR ≥1 conversion | The "good" sessions |
| `screenPageViews` | Pageviews + app screenviews combined | What people mean by "pageviews" |
| `eventCount` | Total event count (every event, not just `page_view`) | Often misleadingly large |
| `bounceRate` | `(sessions - engagedSessions) / sessions` | Lower is better |
| `averageSessionDuration` | Avg seconds per session | Across `sessions`, not `engagedSessions` |
| `eventsPerSession` | `eventCount / sessions` | |
| `conversions` | Events flagged as conversions in the property setup | Property-specific |
| `totalRevenue` | Sum of `purchase` event revenue | Currency = property default |

`bounceRate` and `averageSessionDuration` are ratios — don't `SUM` them across rows; they're already aggregated within each row's group.

## The 12 dimensions worth knowing

| Dimension | Cardinality | When to use |
|---|---|---|
| `date` | Low (1/day) | Time series |
| `dateHour` | Med | Intra-day patterns |
| `pagePath` | High | Top-pages reports |
| `pageTitle` | High | When path is opaque (e.g. SPA hash routes) |
| `sessionSource` / `sessionMedium` | Med | Attribution |
| `sessionDefaultChannelGrouping` | Low (~12 channels) | High-level traffic source breakdown |
| `country` / `region` / `city` | Med / Med / High | Geo |
| `deviceCategory` | Low (desktop/mobile/tablet) | |
| `browser` / `operatingSystem` | Med | Tech audit |
| `landingPage` | High | Entry-page reports |
| `eventName` | Med | Event-level breakdowns |
| `customEvent:<name>` | Property-specific | If you defined custom dimensions in the property setup |

## Compatibility — not every (dim, metric) combo is valid

GA4 enforces a compatibility matrix at the API level. If you ask for `sessions` + `customEvent:purchaseId` together you may get an empty result or a `400 INVALID_ARGUMENT`. Two rules cover ~90% of cases:

1. **User-scoped vs session-scoped vs event-scoped dimensions don't always mix with each other's metrics.** Stick to dimensions in the same scope as your headline metric where possible.
2. **High-cardinality custom dimensions can trigger sampling.** GA4 will silently sample if a single query touches more than the property's data-quota threshold; the response includes `metadata.dataLossFromOtherRow=true`. Check it.

If you're unsure, query the compatibility metadata endpoint:
```python
from google.analytics.data_v1beta.types import CheckCompatibilityRequest
compat = client.check_compatibility(CheckCompatibilityRequest(
    property="properties/123456789",
    dimensions=[Dimension(name="pagePath"), Dimension(name="sessionSource")],
    metrics=[Metric(name="screenPageViews"), Metric(name="sessions")],
))
print(compat)
```

## Filters

Filters are nested expressions. The common case: filter rows by a dimension value.

```python
from google.analytics.data_v1beta.types import (
    FilterExpression, Filter, FilterExpressionList,
)

# Just pages under /docs/
docs_only = FilterExpression(
    filter=Filter(
        field_name="pagePath",
        string_filter=Filter.StringFilter(
            match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
            value="/docs/",
            case_sensitive=False,
        ),
    ),
)

# AND combine: organic search AND not from referrer "spam.com"
combined = FilterExpression(
    and_group=FilterExpressionList(expressions=[
        FilterExpression(filter=Filter(
            field_name="sessionMedium",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.EXACT,
                value="organic",
            ),
        )),
        FilterExpression(not_expression=FilterExpression(filter=Filter(
            field_name="sessionSource",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.EXACT,
                value="spam.com",
            ),
        ))),
    ]),
)

req = RunReportRequest(
    property="properties/123456789",
    date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    metrics=[Metric(name="sessions")],
    dimensions=[Dimension(name="pagePath")],
    dimension_filter=docs_only,
)
```

Use `metric_filter` for filtering by metric (e.g. only rows where `sessions > 100`). Same shape.

## Date ranges

| Form | Meaning |
|---|---|
| `"2026-05-01"` | Absolute (ISO date) |
| `"30daysAgo"` | Relative — N days before today |
| `"yesterday"`, `"today"` | Named relative |
| `"NdaysAgo"` to `"today"` | Standard rolling window |

GA4 has **48-hour data freshness** — today's numbers fluctuate; yesterday's settle ~24h after midnight in the property's timezone; numbers older than 48h are stable. Don't draw conclusions from "today" alone.

Multiple `date_ranges` in one request gives you a comparison report:
```python
DateRange(start_date="30daysAgo", end_date="yesterday", name="current"),
DateRange(start_date="60daysAgo", end_date="31daysAgo", name="prior"),
```
The response will have `dateRange` as an extra dimension on each row.

## Pagination

```python
req = RunReportRequest(
    # ... as above
    limit=10_000,    # max 250_000 per request
    offset=0,
)
resp = client.run_report(req)
# resp.row_count is the TOTAL matching rows; resp.rows is the current page
while resp.row_count > req.offset + len(resp.rows):
    req.offset += len(resp.rows)
    resp = client.run_report(req)
    # process resp.rows
```

For result sets over ~1M rows, use `ga4-bigquery-export` instead.

## Sampling — always check

```python
resp = client.run_report(req)
if resp.metadata.data_loss_from_other_row:
    print("WARNING: data was sampled. Tighten date range, drop high-cardinality dimensions, or use BigQuery export for unsampled data.")
```

If sampled, results are statistically valid but not exact. For exact counts, BigQuery export is the only path.

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `400 INVALID_ARGUMENT: dimension X is incompatible with metric Y` | Compatibility matrix violation | Use `check_compatibility` to find a valid combination |
| `400 The request must contain at least one valid dimension` | All dimensions in the list are invalid (typo, deprecated name) | Check the [Dimensions & metrics explorer](https://ga-dev-tools.google/ga4/dimensions-metrics-explorer/) |
| `503 RESOURCE_EXHAUSTED` | Per-property quota hit | Wait 1h or raise quota; batch fewer queries |
| Empty `rows` despite valid query | Date range outside data window OR property has no data for that period | Sanity-check with a known-good query (e.g. `activeUsers` over `today`) |

## Related skills

- `ga4-auth-setup` — prerequisite
- `ga4-realtime-api` — for "right now" data instead of `runReport`'s ~24h lag
- `ga4-common-reports` — copy-paste recipes for the canonical 6-7 reports
- `ga4-bigquery-export` — when you've outgrown the Data API
