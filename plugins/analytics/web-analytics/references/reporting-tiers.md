# Reporting Tiers

Defines the three output tiers — what agents run, what data is collected, and how
the output is formatted. The orchestrator (SKILL.md) uses this to route requests.

## Tier Comparison

| Dimension | Mini | Medium | Full |
|-----------|------|--------|------|
| Agents | None (inline) | 4 (collector, traffic, content, anomaly, reporter) | All 9 |
| Data Calls | 2 per site | 5 per site | 11 per site |
| Output Lines | 10-15 | 40-60 | 100-200 |
| Target Time | ~30s | ~2min | ~5min |
| Delivery | Console only | Console, email, Slack | Console, email, Slack |
| Analysis Depth | Numbers only | Trends + context | Full strategy |
| Verification | None | None | Yes (verification agent) |
| Memory Update | No | No | Yes (memory agent) |

## Mini Tier

**When to use:** Quick check, "how's my traffic?", morning glance, real-time status.

**Data collected per site:**
1. `mcp__umami__get_stats` — aggregate (returns current period + comparison block in one call — do NOT call twice)
2. `mcp__umami__get_active` — real-time visitor count

**Output format:**
```
## Analytics Pulse — {date}

**Portfolio:** {total_visitors} visitors across {n} sites ({+/-n%} vs prior {period})

| Site | Visitors | Pageviews | Bounce | Trend |
|------|----------|-----------|--------|-------|
| tonsofskills.com | {n} | {n} | {n%} | ↑ +12% |
| startaitools.com | {n} | {n} | {n%} | → flat |
| jeremylongshore.com | {n} | {n} | {n%} | ↓ -8% |
| intentsolutions.io | {n} | {n} | {n%} | → flat |
| diagnosticpro.io | {n} | {n} | {n%} | → flat |

**Top Signal:** {one-sentence highlight}
**Active Now:** {n} visitors
```

**Rules:**
- No subagents — orchestrator handles inline
- Under 15 lines
- One signal only — the most notable change
- Trend arrows: ↑ (>10% up), ↓ (>10% down), → (within 10%)
- No recommendations (just facts)

## Medium Tier

**When to use:** Daily brief, "what happened this week?", stakeholder update.

**Data collected per site:**
1. All mini data
2. `mcp__umami__get_metrics` metric_type=referrer — traffic sources (limit 15)
3. `mcp__umami__get_metrics` metric_type=url — top pages (limit 20)
4. `mcp__umami__get_pageviews` unit=day — daily time series

**Agents invoked:**
1. data-collector → fetches all medium data
2. traffic-intelligence → channel/source analysis
3. content-seo → page performance
4. anomaly-detector → spike/drop detection
5. reporting-narrative → compile final output

**Output format:**
```
## Analytics Brief — {date_range}

### Executive Summary
{2-3 sentences: headline insight, key change, recommended action}

### Portfolio Overview
| Site | Visitors | PVs | Bounce | Δ | Signal |
|------|----------|-----|--------|---|--------|
| {site} | {n} | {n} | {n%} | {+/-n%} | {brief note} |

### Traffic Sources
{From traffic-intelligence: top channels, notable shifts, AI referral callout}

### Top Content
{From content-seo: top 5 pages, risers/decliners, content type performance}

### Anomalies
{From anomaly-detector: flagged issues or "No anomalies detected"}

### Recommended Actions
1. {Specific, data-backed action}
2. {Specific, data-backed action}
3. {Specific, data-backed action}
```

**Rules:**
- 40-60 lines
- 3 recommendations max
- Every number in context (vs baseline or prior period)
- Anomalies section always present (even if "none")

## Full Tier

**When to use:** Weekly deep-dive, monthly review, strategy planning, investor-grade report.

**Data collected per site:**
1. All medium data
2. `mcp__umami__get_metrics` metric_type=browser — technology
3. `mcp__umami__get_metrics` metric_type=os — platforms
4. `mcp__umami__get_metrics` metric_type=device — mobile/desktop
5. `mcp__umami__get_metrics` metric_type=country — geography
6. `mcp__umami__get_events` — custom events
7. `mcp__umami__get_metrics` metric_type=referrer + post-filter on `utm_source` values from `site-registry.md § Redirect Domains` — redirect-domain attribution

**Agents invoked:**
1. data-collector → fetches ALL data types
2. traffic-intelligence → full channel analysis + AI referral deep dive
3. content-seo → full page analysis + content gaps
4. anomaly-detector → comprehensive anomaly scan
5. conversion-funnel → event/goal/funnel analysis
6. audience-segmentation → cohort/geo/device analysis
7. verification-agent → adversarial quality check on all outputs
8. reporting-narrative → compile comprehensive report
9. memory-agent → update rolling baselines

**Output format:**
```
## Analytics Deep Dive — {date_range}

### Executive Summary
{3-5 sentences: strategic overview}

### Portfolio Health
{Multi-site overview with cross-site patterns}

### Traffic Intelligence
{Full channel analysis, AI referrals, redirect domains}

### Content & SEO
{Page performance, content gaps, topic recommendations}

### Conversion Analysis
{Funnel stages, event data, goal completion}

### Audience Profile
{Cohorts, geography, devices, new vs returning}

### Anomaly Report
{All detected anomalies with severity}

### Data Quality & Verification
{Verification agent's confidence assessment and caveats}

### Strategic Recommendations
1. **[Priority]** {Action} — {rationale} — {expected impact}
2. **[Priority]** {Action} — {rationale} — {expected impact}
3. **[Priority]** {Action} — {rationale} — {expected impact}

### Appendix
{Detailed data tables for reference}
```

**Rules:**
- 100-200 lines
- Up to 5 strategic recommendations, prioritized
- Verification notes included prominently
- Appendix with raw tables (not duplicated in body)
- Memory agent runs post-report to update baselines

## Delivery Formatting

### Console (all tiers)
- Standard markdown
- Monospace-friendly tables
- No images or links

### Email (medium + full tiers)
- Subject line: "Analytics {Tier} — {date} — {headline}"
- Plain-text sections (no raw markdown tables — use aligned text)
- Key metric callouts in bold
- Limit to 5000 chars for email body

### Slack (medium + full tiers)
- Slack mrkdwn format (`*bold*`, `_italic_`, `` `code` ``)
- Respect 3000-char message limit
- If over limit, split into 2 messages: summary + details
- Use compact table format (pipe-separated, not markdown)
