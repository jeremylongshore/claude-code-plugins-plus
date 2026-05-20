# ga4-pack

> Claude Code skill pack for Google Analytics 4. 5 starter skills covering the operationally-leveraged paths: auth setup, Data API v1 queries, Realtime API, common reports (DAU / MAU / retention / top pages), and BigQuery export.

**Install:** `/plugin install ga4-pack@claude-code-plugins-plus`

**Links:** [Tons of Skills](https://tonsofskills.com/learn/ga4/) · [GA4 Data API v1 docs](https://developers.google.com/analytics/devguides/reporting/data/v1) · [GA4 BigQuery export](https://support.google.com/analytics/answer/9358801)

---

## What's in the box

| Skill | When to use it |
|---|---|
| `ga4-auth-setup` | First-time setup of OAuth user creds OR a service account for read-only analytics access. |
| `ga4-data-api-query` | Building a properly-structured `runReport` request against the Data API v1 — metrics, dimensions, date ranges, filters, ordering. |
| `ga4-realtime-api` | Pulling active-users / current-session data from the Realtime endpoint. Different shape, different limits than the standard Data API. |
| `ga4-common-reports` | The canonical reports every site owner wants: DAU/MAU, retention, top pages, top sources, conversion funnel. Copy-paste recipes. |
| `ga4-bigquery-export` | Wiring GA4 → BigQuery for unsampled, queryable event-level data. Schema, partitioning, common SQL patterns. |

Five skills, not thirty. **Intentional**: GA4's API surface is wide but the operational paths most engineers actually need are narrow. Each skill in this pack is a real reference — not boilerplate. If you need a specialized use case (e.g., GA4 Measurement Protocol, custom event taxonomy, consent-mode signal handling), open an issue and we'll add a focused skill.

## When NOT to use this pack

- **You're using Umami / Plausible / Fathom instead of GA4**: use `web-analytics` instead — that pack is Umami-primary, GA4 as fallback only.
- **You need to write events from a website**: this pack is read-only / reporting-focused. For event instrumentation, use Google's official tag manager guides directly.
- **You're on Universal Analytics (UA)**: UA was sunset 2023-07-01. Migrate to GA4 first; this pack assumes GA4 properties.

## Prerequisites

- A GA4 property (not Universal Analytics)
- One of:
  - **OAuth user credentials** with `analytics.readonly` scope (for ad-hoc / interactive use)
  - **Service account** with the GA4 property's API access (for automated / CI use)
- For BigQuery export: a linked GCP project with BigQuery enabled (no extra cost — GA4 → BQ is free for the standard tier; sampling-free)

See `ga4-auth-setup` for the actual setup steps.

## Trigger examples

| You ask Claude | Skill that fires |
|---|---|
| "Set up GA4 auth with a service account" | `ga4-auth-setup` |
| "Query DAU for the last 30 days from GA4" | `ga4-data-api-query` |
| "How many people are on my site right now?" | `ga4-realtime-api` |
| "Show me retention week-over-week from GA4" | `ga4-common-reports` |
| "I want unsampled GA4 data — set up the BigQuery export" | `ga4-bigquery-export` |
