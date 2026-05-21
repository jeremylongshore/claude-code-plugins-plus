# MCP Tool Reference

Tool signatures for analytics backends. The data-collector agent uses this reference to construct correct MCP tool calls.

> **Last verified against `umami-mcp-server` v2.0.0 — 2026-05-02.** When the package upgrades, re-verify by running `mcp__umami__get_websites` and any one of the metric calls; if signatures drift, update this file in the same PR as any data-collector changes.

## Umami MCP Server (`umami`)

### Authentication

The Umami MCP is configured in `~/.claude.json` under `mcpServers.umami`. For self-hosted Umami: `UMAMI_URL` + `UMAMI_USERNAME` + `UMAMI_PASSWORD` env vars. For Umami Cloud: `UMAMI_API_KEY`. Authentication is handled at MCP-spawn time; no per-call auth needed.

**Backend:** `https://analytics.intentsolutions.io` (self-hosted on Contabo VPS, Watchtower-updated).

**Connectivity sanity check:** call `mcp__umami__verify_token` (self-hosted) or `mcp__umami__get_me` (cloud). If it returns user info, the chain works.

### Available Tools (core set used by data-collector)

The MCP exposes 60+ tools; the data-collector uses this subset. For the full list, see https://github.com/frontedu/umami-mcp-server.

#### `mcp__umami__get_websites`
List all tracked websites. **Always call FIRST** before any per-site query — verifies auth and gives the canonical site IDs.
```
Parameters:
  includeTeams: boolean (optional, default false) — include team-owned websites
Returns: { data: Array of { id, name, domain, createdAt, ... } }
```

#### `mcp__umami__get_stats`
Aggregate stats for a site over a time range, with prior-period comparison.
```
Parameters:
  website_id: string (required) — UUID from get_websites
  start_date:  string (required) — ISO 8601 (e.g. "2026-04-25T00:00:00Z")
  end_date:    string (required) — ISO 8601, must be after start_date
Returns: {
  pageviews, visitors, visits, bounces, totaltime,
  comparison: { pageviews, visitors, visits, bounces, totaltime }
}
```

#### `mcp__umami__get_active`
Current real-time visitor count. No date params.
```
Parameters:
  website_id: string (required)
Returns: { x: number (active visitor count) }
```

#### `mcp__umami__get_metrics`
Breakdown by dimension. Returns `{ x: dimension_value, y: count }` rows.
```
Parameters:
  website_id:  string (required)
  start_date:  string (required, ISO 8601)
  end_date:    string (required, ISO 8601)
  metric_type: string (required) — one of:
                 url, path, referrer, browser, os, device, country,
                 region, city, language, screen, event, hostname, domain,
                 query, channel, tag, distinctId, title, entry, exit
  limit: number (optional, default 10)
Returns: Array of { x: string, y: number }
```

#### `mcp__umami__get_pageviews`
Time-series pageview + session counts.
```
Parameters:
  website_id: string (required)
  start_date: string (required, ISO 8601)
  end_date:   string (required, ISO 8601)
  unit:       string (optional, default "day") — minute, hour, day, month, year
Returns: { pageviews: Array<{x: date, y: count}>, sessions: Array<{x: date, y: count}> }
```

#### `mcp__umami__get_events`
Custom event data (e.g. `install_click`, `cowork_download`, `search_query`).
```
Parameters:
  website_id: string (required)
  start_date: string (required, ISO 8601)
  end_date:   string (required, ISO 8601)
Returns: Array of event objects with timestamps
```

#### `mcp__umami__get_realtime`
Live activity feed (alternative to `get_active` for richer realtime data).
```
Parameters:
  website_id: string (required)
Returns: { visitors, pageviews, countries, ... }
```

### Other Useful Tools (not in default data-collector flow)

| Tool | Use |
|---|---|
| `mcp__umami__compare_periods` | First-class period comparison (vs hand-computing two `get_stats` calls) |
| `mcp__umami__get_funnel_report` | Multi-step conversion funnels (use for full-tier analysis) |
| `mcp__umami__get_journey_report` | User-path / journey analysis |
| `mcp__umami__get_attribution_report` | Channel attribution / multi-touch |
| `mcp__umami__get_geo_insights` | Country/region/city breakdown with insights |
| `mcp__umami__get_retention_report` | User-retention cohort analysis |
| `mcp__umami__get_session_data_properties` | Custom session properties |
| `mcp__umami__get_metrics_expanded` | Same as `get_metrics` with extra dimensions |
| `mcp__umami__verify_token` | Self-hosted auth check (no params) |
| `mcp__umami__get_me` | Cloud auth check (no params) |

When the data-collector needs a capability outside the core set, it should reach for these by exact name rather than improvising.

## Direct REST Fallback (when MCP is unavailable)

If `umami-mcp-server` returns errors and a Claude session restart isn't possible, hit the REST API directly via Bash. The MCP IS the backend's REST API in a thin wrapper.

```bash
# 1. Login → JWT
TOKEN=$(curl -s -X POST https://analytics.intentsolutions.io/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<UMAMI_PASSWORD>"}' | jq -r .token)

# 2. List websites
curl -s "https://analytics.intentsolutions.io/api/websites" \
  -H "Authorization: Bearer $TOKEN" | jq '.data[] | {id,name,domain}'

# 3. Stats (note: REST takes epoch ms, not ISO; converted automatically by MCP)
START=$(date -d '7 days ago' +%s)000
END=$(date +%s)000
curl -s "https://analytics.intentsolutions.io/api/websites/<WEBSITE_ID>/stats?startAt=$START&endAt=$END" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Use this only for diagnostics — production tools should go through the MCP.

## Time Range Helpers

The MCP accepts ISO 8601 strings. Standard ranges (relative to now in ET timezone):

| Label | Calculation |
|-------|------------|
| Today | midnight ET → now |
| Yesterday | midnight-1d → midnight |
| 7d | now - 7 days → now |
| 30d | now - 30 days → now |
| MTD | 1st of month → now |
| QTD | 1st of quarter → now |
| Comparison | Same duration immediately prior (handled by `get_stats` automatically) |

ISO 8601 example: `"2026-04-25T00:00:00-04:00"` (ET) or `"2026-04-25T00:00:00Z"` (UTC).

## GA4 (Fallback — not yet wired)

GA4 integration via the Google Analytics Data API MCP server is not yet configured in this environment. When it is, the data-collector should prefer Umami and fall back to GA4 only for sites that lack Umami coverage.

### Expected Tool Mapping (when GA4 MCP lands)

| Umami Tool | GA4 Equivalent |
|-----------|---------------|
| `mcp__umami__get_stats` | `ga4_run_report` with metrics: sessions, totalUsers, bounceRate |
| `mcp__umami__get_metrics` | `ga4_run_report` with dimensions: source, medium, pagePath |
| `mcp__umami__get_pageviews` | `ga4_run_report` with dateRange + date dimension |
| `mcp__umami__get_events` | `ga4_run_report` with eventName dimension |

## Error Handling

| Error | Action |
|-------|--------|
| `Unexpected token '<', "<!DOCTYPE "` | MCP returned the SPA login page → auth failed at MCP-spawn time. Verify env vars in `~/.claude.json`, restart Claude session. Until then, use the Direct REST Fallback above. |
| `Umami API error 404` (with HTML body) | Same root cause as above — auth-flow regression in the MCP wrapper. |
| Site ID not found | Call `mcp__umami__get_websites` to list; suggest closest match. |
| Empty data | Report zeros with a note. Do NOT fabricate numbers. If ALL sites zero, check whether the tracker `<script>` is installed (see `site-registry.md` per-site repo paths). |
| Rate limit | Wait 5s, retry once. If still failing, report partial data. |
| Timeout | Report which calls succeeded and which timed out. |

## Data Quality Notes

- Umami v2 is privacy-focused: no cookies, no fingerprinting, no consent banner. Visitor counts may differ from GA4 (which uses cookies).
- Bot filtering is server-side. The anomaly-detector should still check for bot-pattern signatures.
- UTM params are preserved through 301 redirects — use `metric_type=referrer` (or `utm_source`/`utm_medium` filters when supported) for redirect-domain attribution. See `site-registry.md § Redirect Domains` for the list of redirect-source values to filter on.
- `get_active` is real-time only — cannot be queried for historical periods.
- ISO 8601 dates accept both `Z` (UTC) and `±HH:MM` (offset) formats. Use ET (`-04:00` / `-05:00`) for human-aligned reporting per `site-registry.md § Reporting Defaults`.
