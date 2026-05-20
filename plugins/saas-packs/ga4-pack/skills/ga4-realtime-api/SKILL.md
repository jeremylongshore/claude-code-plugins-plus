---
name: ga4-realtime-api
description: |
  Pull current-session / active-user data from the GA4 Realtime endpoint —
  a separate API surface from runReport with different metrics, dimensions, and
  freshness guarantees (~30 min rolling window instead of T-48h). Trigger with
  "GA4 realtime", "active users right now", "GA4 current sessions",
  "who's on my site now".
allowed-tools: Bash(python3:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, analytics, google-analytics, ga4, realtime]
compatibility: Designed for Claude Code
---

# GA4 Realtime API

The Realtime API is GA4's "what's happening right now" endpoint. Different from `runReport`:

| | `runReport` (Data API) | `runRealtimeReport` (Realtime) |
|---|---|---|
| Freshness | ~24-48h lag, stable | Last ~30 min, rolling |
| Window | Any date range | Implicit — last 30 min |
| Metrics | ~50 supported | ~10 supported (subset) |
| Dimensions | ~150 supported | ~15 supported (subset) |
| Quota | Per-property daily | Separate Realtime quota |
| Use case | Reports, dashboards, trend analysis | Live dashboards, monitoring, "are we down?" |

Don't try to use `runReport` for now-data — its freshest data point is yesterday. Use `runRealtimeReport`.

## Minimum viable call

```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunRealtimeReportRequest, Metric, Dimension,
)

client = BetaAnalyticsDataClient()
resp = client.run_realtime_report(RunRealtimeReportRequest(
    property="properties/123456789",
    metrics=[Metric(name="activeUsers")],
))

# Single-row response when there are no dimensions
total = int(resp.rows[0].metric_values[0].value) if resp.rows else 0
print(f"Active users right now: {total}")
```

No `date_ranges` block — the implicit window is the last 30 min. Adding one will error.

## Realtime metrics (the full list)

| Metric | What it counts |
|---|---|
| `activeUsers` | Unique users in the last 30 min |
| `screenPageViews` | Pageviews + screenviews in the last 30 min |
| `eventCount` | Total events in the last 30 min |
| `conversions` | Conversion events in the last 30 min |
| `keyEvents` | Key events (post-2024 rename of conversions) |

Custom-event aggregates (e.g. `purchase_revenue`) are NOT in the Realtime API. If you need realtime revenue, derive it from `eventCount` filtered to `eventName=="purchase"` plus your average AOV.

## Realtime dimensions (the full list)

| Dimension | Use |
|---|---|
| `country`, `city` | Geo of currently-active users |
| `deviceCategory` | desktop / mobile / tablet split |
| `unifiedScreenName` / `unifiedScreenClass` | App screen / web title |
| `eventName` | Event-type breakdown |
| `streamId`, `streamName` | When property has multiple data streams (web + iOS + Android) |
| `platform` | web / ios / android |
| `appVersion`, `audienceName`, `audienceId` | When defined in the property |

That's the full list. ~15 dims total. Compare to `runReport`'s ~150.

## Common realtime queries

### "How many people are on my site right now?"

```python
resp = client.run_realtime_report(RunRealtimeReportRequest(
    property="properties/123456789",
    metrics=[Metric(name="activeUsers")],
))
print(int(resp.rows[0].metric_values[0].value) if resp.rows else 0)
```

### "Active users by country, right now"

```python
resp = client.run_realtime_report(RunRealtimeReportRequest(
    property="properties/123456789",
    metrics=[Metric(name="activeUsers")],
    dimensions=[Dimension(name="country")],
    limit=20,
))
for r in resp.rows:
    print(f"{r.dimension_values[0].value:25s} {r.metric_values[0].value}")
```

### "Which events are firing in the last 30 min?"

```python
resp = client.run_realtime_report(RunRealtimeReportRequest(
    property="properties/123456789",
    metrics=[Metric(name="eventCount")],
    dimensions=[Dimension(name="eventName")],
    limit=30,
))
```

This is the live event firehose — useful to verify a new tracking deployment is actually firing.

### "Top pages right now"

```python
resp = client.run_realtime_report(RunRealtimeReportRequest(
    property="properties/123456789",
    metrics=[Metric(name="screenPageViews")],
    dimensions=[Dimension(name="unifiedScreenName")],   # NOT pagePath — that's Data-API-only
    limit=20,
))
```

Realtime doesn't expose `pagePath` directly. Use `unifiedScreenName` (the page title) or `unifiedScreenClass`. To get path-level granularity in realtime, push a custom event with the path as a parameter, then query by `eventName` + that custom dimension.

## Filters

Same shape as `runReport` — `FilterExpression` / `Filter` blocks. Realtime supports `dimension_filter` and `metric_filter` but not the full set of dimensions / metrics; check the [Realtime API schema](https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-api-schema) before writing complex filters.

## Quotas — different from Data API

Realtime has its own quota bucket. Defaults (2026):

- 5,000 requests per project per day
- 250 requests per property per day
- 60 requests per minute per property

For a live dashboard polling every 10s: that's 6 RPM, well within limits. For a hot incident where you want minute-by-minute data, you can poll up to 60x/min per property.

## Don't poll faster than 30s

The data window is the last 30 min. Polling faster than ~30s wastes quota without meaningful resolution change. For most "live" use cases, 60s polling is plenty.

## Common gotchas

| Issue | Why |
|---|---|
| `activeUsers` doesn't match the GA4 web UI's "Realtime" overview | The UI uses a slightly different window (~5 min default) and may include in-flight events not yet reportable via API. Web UI > API for instant-incidents. |
| Empty rows on a busy site | Property may be using a different stream you didn't filter for. Add `Dimension(name="streamId")` to see splits. |
| `400 INVALID_ARGUMENT: Realtime reports do not support dimension X` | Using a Data-API-only dimension (e.g. `pagePath`, `sessionSource`). Use a Realtime dimension. |
| Latency between front-end event and Realtime visibility | ~10-30 seconds is normal. If >2 minutes, check the GA4 DebugView for event delivery issues. |

## Related skills

- `ga4-auth-setup` — prerequisite
- `ga4-data-api-query` — for any window longer than 30 min
- `ga4-common-reports` — for canonical reports (DAU/MAU/retention) which are NOT realtime-able
