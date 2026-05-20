---
name: ga4-bigquery-export
description: |
  Wire GA4 → BigQuery for unsampled, queryable event-level data. Covers the
  one-time export setup, the events_YYYYMMDD table schema, partitioning + clustering,
  and the SQL patterns for the reports the Data API can't do well (true cohort
  retention, custom-event attribution, large date ranges). Trigger with
  "GA4 BigQuery", "GA4 to BQ", "event-level GA4 data", "unsampled GA4",
  "GA4 export setup", "GA4 SQL".
allowed-tools: Bash(bq:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, analytics, google-analytics, ga4, bigquery]
compatibility: Designed for Claude Code
---

# GA4 → BigQuery Export

The Data API is good but bounded — sampled past a threshold, capped at ~150 dimensions, no cohort joins. BigQuery export gives you the raw event stream as SQL-queryable tables, **free** at the standard GA4 tier (up to 1M events/day), with no sampling and full event payloads.

This skill: one-time setup, then the SQL recipes for what the Data API can't do well.

## Setup — one time

### 1. Link your GA4 property to a GCP project

In <https://analytics.google.com/>:

1. Admin → Property column → **BigQuery Links**
2. Create a link → pick your GCP project
3. Data location: pick the BQ region for the export tables (US multi-region is fine for most cases; EU if you need data residency)
4. **Export type:**
   - **Daily** — single `events_YYYYMMDD` table per day, written ~24h after midnight. Fine for most reporting.
   - **Streaming** — `events_intraday_YYYYMMDD` table written ~near-real-time. Costs more, useful for hot ops dashboards.
   - Most setups: enable both. Streaming for "today", daily for everything else.
5. **Include advertising identifiers** — uncheck unless you specifically need device-graph data (most don't)
6. Save

The first daily table lands within 24h. The first streaming table is near-immediate. After that you have a new `events_YYYYMMDD` every day forever, no maintenance needed.

### 2. Verify the export is working

```bash
PROJECT=your-gcp-project
DATASET=analytics_123456789       # auto-named after the property ID

bq ls "$PROJECT:$DATASET" 2>&1 | head -10
# Expect: events_YYYYMMDD tables + events_intraday_YYYYMMDD if streaming enabled
```

If you see no dataset, the link is configured but the first export hasn't fired yet — wait 24h.

### 3. Authorize a service account for querying

The SA from `ga4-auth-setup` only has Data API access. For BQ queries, grant the same SA:

```bash
SA_EMAIL=ga4-reader@your-project.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.dataViewer"
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.jobUser"
```

`dataViewer` reads tables; `jobUser` lets the SA run queries (queries are jobs in BQ's model).

## The events table schema (the important columns)

Every row in `events_YYYYMMDD` is one event. The schema is denormalized — user + session + event + page + device all flat in each row.

| Column | Type | Notes |
|---|---|---|
| `event_date` | `STRING` | `'YYYYMMDD'` |
| `event_timestamp` | `INT64` | Microseconds since epoch |
| `event_name` | `STRING` | `page_view`, `session_start`, `purchase`, custom event names |
| `event_params` | `ARRAY<STRUCT<key, value>>` | All event parameters; value is itself a union STRUCT (`string_value`, `int_value`, `float_value`, `double_value`) |
| `user_pseudo_id` | `STRING` | GA4's cookie-based user ID (anonymous unless `user_id` is set) |
| `user_id` | `STRING` | If you set `user_id` via `gtag('set', {user_id: '...'})` |
| `user_properties` | `ARRAY<STRUCT<key, value>>` | Same shape as event_params |
| `device.*` | `STRUCT` | category / os / browser / model |
| `geo.*` | `STRUCT` | country / region / city |
| `traffic_source.*` | `STRUCT` | source / medium / campaign of FIRST session (not current) |
| `session_traffic_source_last_click.*` | `STRUCT` | source / medium of CURRENT session — what you usually want |
| `ga_session_id` (param) | `INT64` | Pulled via `(SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id')` |
| `ga_session_number` (param) | `INT64` | Same idiom — 1 = first session, 2 = second, etc. |

The `event_params` and `user_properties` arrays are the gnarly bit. Pulling a parameter requires UNNEST + filter. The idiom:

```sql
-- Pull the page_location for every page_view
SELECT
  TIMESTAMP_MICROS(event_timestamp) AS ts,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page,
  user_pseudo_id
FROM `your-project.analytics_123456789.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260513' AND '20260520'
  AND event_name = 'page_view'
LIMIT 100;
```

`_TABLE_SUFFIX BETWEEN '...' AND '...'` is the canonical way to scan a date range across the wildcard table. **Always set it** — without a suffix filter, you query the entire history and pay for it.

## Recipe 1 — True cohort retention

The thing the Data API can't do cleanly:

```sql
WITH first_seen AS (
  SELECT
    user_pseudo_id,
    DATE(MIN(TIMESTAMP_MICROS(event_timestamp))) AS first_date
  FROM `your-project.analytics_123456789.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260401' AND '20260520'
  GROUP BY user_pseudo_id
),
activity AS (
  SELECT
    user_pseudo_id,
    DATE(TIMESTAMP_MICROS(event_timestamp)) AS active_date
  FROM `your-project.analytics_123456789.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260401' AND '20260520'
  GROUP BY user_pseudo_id, active_date
)
SELECT
  DATE_TRUNC(f.first_date, WEEK) AS cohort_week,
  DATE_DIFF(a.active_date, f.first_date, WEEK) AS weeks_since,
  COUNT(DISTINCT a.user_pseudo_id) AS active_users
FROM first_seen f
JOIN activity a USING (user_pseudo_id)
GROUP BY cohort_week, weeks_since
ORDER BY cohort_week, weeks_since;
```

Output: rows of `(cohort_week, weeks_since, active_users)`. Pivot in your tool of choice for the classic triangle chart.

## Recipe 2 — Sessions table (denormalized from events)

GA4's BQ export is event-rows, not session-rows. To reason about sessions, build the session table yourself:

```sql
WITH sessions AS (
  SELECT
    user_pseudo_id,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
    MIN(TIMESTAMP_MICROS(event_timestamp)) AS session_start,
    MAX(TIMESTAMP_MICROS(event_timestamp)) AS session_end,
    COUNT(*) AS event_count,
    COUNTIF(event_name = 'page_view') AS pageviews,
    ANY_VALUE(device.category) AS device,
    ANY_VALUE(geo.country) AS country,
    ANY_VALUE(session_traffic_source_last_click.manual_campaign.source) AS source,
    ANY_VALUE(session_traffic_source_last_click.manual_campaign.medium) AS medium,
  FROM `your-project.analytics_123456789.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260513' AND '20260520'
  GROUP BY user_pseudo_id, session_id
  HAVING session_id IS NOT NULL
)
SELECT * FROM sessions
ORDER BY session_start DESC
LIMIT 100;
```

You'd usually `CREATE TABLE` or `CREATE MATERIALIZED VIEW` over this — querying the events table directly every time is slow + expensive.

## Recipe 3 — Top pages by source

```sql
SELECT
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page,
  session_traffic_source_last_click.manual_campaign.source AS source,
  COUNT(*) AS pageviews,
  COUNT(DISTINCT user_pseudo_id) AS users
FROM `your-project.analytics_123456789.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260513' AND '20260520'
  AND event_name = 'page_view'
GROUP BY page, source
HAVING pageviews > 10        -- filter the long tail
ORDER BY pageviews DESC
LIMIT 50;
```

## Cost considerations

BigQuery costs $5/TB scanned (first 1 TB/month free). What that translates to in practice:

| Scenario | ~TB / query |
|---|---|
| Small site, 1k events/day, 30-day window | < 1 GB |
| Medium site, 100k events/day, 30-day window | ~10 GB |
| Large site, 1M events/day, 30-day window | ~100 GB |
| Same scenarios but querying the full 14-month history | 12-15x the above |

Stay under the free tier with normal usage. Cost-saving patterns:

1. **Always set `_TABLE_SUFFIX BETWEEN`** — don't scan all history if you only need 7 days
2. **Materialize hot queries** — CREATE TABLE / CREATE MATERIALIZED VIEW for sessions, daily aggregates, etc.
3. **`SELECT` only the columns you need** — BQ is columnar; selecting `event_params` array always reads the whole array even if you only want one parameter
4. **Use `--dry-run`** before any new query to see TB scanned: `bq query --dry_run --use_legacy_sql=false "SELECT ..."`

## Streaming vs daily — which to query

| Table prefix | When |
|---|---|
| `events_YYYYMMDD` | Stable historical data. Use for reports, analysis. |
| `events_intraday_YYYYMMDD` | "Today" data, near-realtime. Schema is identical, but rows may not be deduped yet. |
| `events_*` (wildcard) | When the date range crosses both. BQ will scan both transparently. |

Today's data lives in `events_intraday_TODAY`; tomorrow it gets rolled into `events_TODAY` and the intraday table for today is dropped. So if you have a query that needs both stable history + today, use `events_*` and filter on `_TABLE_SUFFIX`.

## Common gotchas

| Issue | Why |
|---|---|
| Numbers don't match the GA4 UI exactly | UI uses different identity-stitching for cross-device users; raw events are pre-stitching. Off by a few % is expected. |
| `event_params` UNNEST returns NULL | The key doesn't exist on that event. Always wrap in `(SELECT ... LIMIT 1)` so missing-key events return NULL instead of erroring. |
| Query scans way more than expected | Missing `_TABLE_SUFFIX` filter, OR using `events_*` without a `_TABLE_SUFFIX BETWEEN` clause |
| `events_intraday_*` has 2x the rows you'd expect | Intraday tables aren't deduped; the same event may appear twice if it was buffered + retried. The daily rollup dedupes. |
| No `user_id` even though I set it on the front-end | `user_id` is the explicit identifier; `user_pseudo_id` is the auto-generated cookie ID. If `user_id` is consistently NULL, the `gtag('set', {user_id: ...})` call is firing AFTER the event you're checking, or it's set on a property that the export doesn't pull. |

## Related skills

- `ga4-auth-setup` — for the service account that queries BQ
- `ga4-data-api-query` — when you DON'T need event-level granularity (Data API is faster + cheaper for aggregates)
- `ga4-common-reports` — the Data API recipes that BQ supersedes
