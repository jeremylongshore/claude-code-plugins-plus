# Site Registry

Universal configuration for the web analytics agent team. Edit this file to personalize
for your sites, tracking backends, and business goals. No other file needs to change.

## Analytics Backend

| Setting | Value |
|---------|-------|
| Primary | Umami (self-hosted, Contabo) |
| Fallback | GA4 (tonsofskills: `G-9Z1DTMTT44`, jeremylongshore: `G-40E6F2PYMQ`, startaitools: `G-PENDING`, intentsolutions: Firebase only) |
| MCP Server | `umami` via user-scope settings (npx umami-mcp-server) |
| Umami URL | `https://analytics.intentsolutions.io` |
| Umami Admin | `admin` (password in `~/.env` as `UMAMI_PASSWORD`) |

## Tracked Sites

### tonsofskills.com (primary product)

| Field | Value |
|-------|-------|
| Umami Site ID | `0cee47ed-bee5-48da-8fed-46b3d8a2ddd3` |
| GA4 ID | `G-9Z1DTMTT44` |
| Type | Plugin marketplace |
| Key Pages | `/`, `/explore`, `/skills`, `/cowork`, `/docs`, `/playbooks` |
| Conversion Events | `install_click`, `cowork_download`, `search_query`, `plugin_view` |
| Funnel | Landing → Explore → Plugin Page → Install CTA → Cowork Download |
| Baseline Daily Visitors | ~50-200 (growing) |
| Primary Traffic Sources | Direct, GitHub referral, organic search, AI referral |
| Business Goals | Plugin installs, cowork downloads, return visitors |
| Alert Thresholds | >30% traffic drop, >50% bounce rate spike, new AI referrer |

### startaitools.com (blog)

| Field | Value |
|-------|-------|
| Umami Site ID | `4071f4db-4249-4ce6-a929-665598975d67` |
| GA4 ID | `G-PENDING` (TODO: create GA4 property) |
| Type | Technical blog |
| Key Pages | `/blog`, `/blog/*`, `/about` |
| Conversion Events | `article_read`, `syndication_click`, `newsletter_signup` |
| Baseline Daily Visitors | ~20-80 |
| Primary Traffic Sources | Organic search, DEV.to syndication, Hashnode, X/Twitter |
| Business Goals | Organic traffic growth, article engagement, syndication reach |
| Alert Thresholds | >25% organic drop, top article traffic loss |

### jeremylongshore.com (portfolio)

| Field | Value |
|-------|-------|
| Umami Site ID | `3cea8ff2-5842-4090-a8a3-d2dc128f5385` |
| GA4 ID | `G-40E6F2PYMQ` |
| Type | Personal portfolio |
| Key Pages | `/`, `/projects`, `/about`, `/blog` |
| Conversion Events | `project_click`, `contact_form`, `resume_download` |
| Baseline Daily Visitors | ~5-30 |
| Primary Traffic Sources | Direct, LinkedIn, GitHub |
| Business Goals | Professional visibility, project showcase engagement |
| Alert Thresholds | >50% drop (low baseline = noisy) |

### intentsolutions.io (business)

| Field | Value |
|-------|-------|
| Umami Site ID | `474bce85-f97d-409c-aba5-1e1ff36ee571` |
| GA4 ID | N/A (Firebase Analytics only) |
| Type | Business consulting |
| Key Pages | `/`, `/services`, `/contact`, `/case-studies` |
| Conversion Events | `contact_submit`, `service_inquiry`, `case_study_view` |
| Baseline Daily Visitors | ~5-20 |
| Primary Traffic Sources | Direct, organic, LinkedIn |
| Business Goals | Lead generation, consultation requests |
| Alert Thresholds | Any conversion event spike (rare = significant) |

### diagnosticpro.io (product)

| Field | Value |
|-------|-------|
| Umami Site ID | `52a9058c-e734-4276-a188-8e30c87941f6` |
| GA4 ID | TBD |
| Type | Diagnostic platform product |
| Repo | `~/000-projects/diagnostic-platform/DiagnosticPro` |
| Key Pages | TBD (populate after first 7d of data) |
| Baseline Daily Visitors | TBD (no data yet — registered 2026-05-02) |
| Primary Traffic Sources | TBD |
| Business Goals | TBD |
| Alert Thresholds | TBD |

> Registered in Umami 2026-05-02 alongside the tracker rollout. Tracker
> install pending in the diagnostic-platform/DiagnosticPro repo.

## Redirect Domains

These domains 301-redirect to tonsofskills.com with UTM params (verified 2026-05-02). Tracking happens at the destination; filter by `utm_source` in Umami to see per-redirect performance. **No separate Umami site IDs needed** — the tonsofskills tracker captures these visits.

| Domain | Destination | UTM Source | Purpose |
|--------|-------------|-----------|---------|
| claudecodeplugins.io | `tonsofskills.com/?utm_source=claudecodeplugins.io&utm_medium=redirect` | `claudecodeplugins.io` | Brand redirect |
| claudecodeskills.io | `tonsofskills.com/?utm_source=claudecodeskills.io&utm_medium=redirect` | `claudecodeskills.io` | Brand redirect |
| claudecoworkskills.io | `tonsofskills.com/cowork?utm_source=claudecoworkskills.io&utm_medium=redirect` | `claudecoworkskills.io` | Cowork-specific brand redirect |

## Reporting Defaults

| Setting | Value |
|---------|-------|
| Default Tier | mini |
| Default Time Range | 7d (last 7 days) |
| Comparison Period | Previous equivalent period |
| Timezone | America/New_York (ET) |
| Currency | USD |
| Notification Channel | Console (default), Slack (#operation-hired), Email (jeremy@intentsolutions.io) |

## Seasonal Adjustments

| Period | Expected Impact |
|--------|----------------|
| Weekends | -30-50% traffic (dev audience) |
| US Holidays | -40-60% traffic |
| Major Claude/Anthropic announcements | +200-500% spike on tonsofskills |
| DEV.to trending | +100-300% spike on startaitools |

## Custom Segments

| Segment | Definition | Priority |
|---------|-----------|----------|
| AI Referrals | Referrer contains `chat.openai`, `claude.ai`, `perplexity`, `gemini` | High — track growth |
| GitHub Traffic | Referrer contains `github.com` | High — primary funnel |
| Organic Search | Source = google, bing, duckduckgo | Medium — SEO signal |
| Social | Source = twitter, linkedin, reddit, hackernews | Medium — amplification |
| Direct | No referrer | Low — hard to attribute |
