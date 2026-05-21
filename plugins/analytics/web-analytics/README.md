# web-analytics

> Push-based web analytics intelligence — self-hosted Umami (primary) via MCP + GA4 (fallback). 9 specialist agents fetch data, detect anomalies, analyze funnels, verify claims, and deliver narrative reports across your entire site portfolio.

**Install:** `/plugin install web-analytics@claude-code-plugins-plus`

## What it is

Not a dashboard replacement — a **push-based analytics team** that wakes you up when something matters and stays quiet otherwise. Instead of opening Umami / GA every morning to see if anything happened, you ask Claude `/analytics` and get a synthesized report with deltas, anomalies, attribution analysis, and one signal line that tells you what to do next.

## How it works

```
/analytics [tier]
   │
   ▼
orchestrator (this skill)
   │
   ▼
data-collector ──► self-hosted Umami via MCP (primary)
                   GA4 Data API (fallback)
   │
   ▼
parallel specialist agents:
   - traffic-intelligence    (channel attribution)
   - content-seo             (page performance)
   - anomaly-detector        (spike/drop detection)
   - conversion-funnel       (event/goal analysis)
   - audience-segmentation   (cohort/geo)
   - verification-agent      (adversarial QA)
   │
   ▼
reporting-narrative ──► console / email / Slack delivery
```

## Three tiers

| Tier | Time | What you get |
|---|---|---|
| `mini` (default) | ~30 sec | Inline pulse — 5 sites, deltas, one signal |
| `medium` | ~2 min | 4 agents, narrative brief, top movers |
| `full` | ~5 min | All 9 agents, adversarial verification, memory-agent baselines |

## Prerequisites

- **Self-hosted Umami** at a reachable URL (the skill defaults to `https://analytics.intentsolutions.io/api` — set your own via the Umami MCP server config)
- **Umami credentials** (admin user / app password) in env or SOPS
- **GA4 service account JSON** (optional, fallback only)
- For email delivery: the [`email`](https://www.npmjs.com/package/@intentsolutionsio/email) skill
- For Slack delivery: the [`slack`](https://www.npmjs.com/package/@intentsolutionsio/slack) skill

## Configuration

Sites are registered in `references/site-registry.md` — edit that file to add your domains, set per-site baselines (DAU thresholds, expected bounce rates), and tag site categories.

See `references/interpretation-guide.md` for the advisory voice this skill uses — terse, non-alarmist, action-oriented.

## License

MIT
