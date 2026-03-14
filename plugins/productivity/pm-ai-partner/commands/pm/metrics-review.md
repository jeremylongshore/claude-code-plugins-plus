---
name: metrics-review
description: Review metrics and identify what needs attention
allowed-tools: Read, Glob, Grep
---

Help me review metrics and identify what needs attention for: $ARGUMENTS

## Instructions

Conduct a structured metrics review. The goal is not to report numbers — it's to identify what's changed, why it matters, and what action to take.

### Process

1. **Scan for changes** — What metrics moved significantly (up or down) since last review?
2. **Diagnose causes** — For each change, identify likely causes (release, seasonality, external event, instrumentation)
3. **Assess impact** — Quantify who's affected and how much it matters
4. **Recommend action** — For each finding: investigate further, fix now, monitor, or accept

### Tools to Use

- Query available data sources (BigQuery, dashboards, analytics tools) via MCP
- Pull recent release notes or deploy logs for correlation
- Check for known incidents or outages that could explain metric changes
- Compare across dimensions: platform, tier, region, app version

### Output Format

```markdown
# Metrics Review: [Area/Date]

## Headlines
- [Most important metric change — 1 sentence]
- [Second most important — 1 sentence]
- [Third — 1 sentence]

## Dashboard

| Metric | Current | Previous | Change | Trend | Status |
|--------|---------|----------|--------|-------|--------|
| [metric] | [value] | [value] | [delta] | [direction] | OK / Watch / Act |

## Deep Dives

### [Metric that needs attention]
- **What changed:** [description with numbers]
- **Likely cause:** [hypothesis with evidence]
- **Impact:** [users affected, revenue/engagement impact]
- **Recommendation:** [Investigate / Fix / Monitor / Accept]

## Segments to Watch
| Segment | Metric | Observation |
|---------|--------|-------------|
| [e.g., Android 14] | [metric] | [what's different about this segment] |

## Action Items
| Action | Priority | Owner | Deadline |
|--------|----------|-------|----------|
| [action] | P0/P1/P2 | [who] | [when] |

## Next Review
- [When to check these metrics again]
- [What to watch for specifically]
```

### Principles

- **Trends over snapshots** — Always show direction, not just current value
- **Slice before concluding** — Break every aggregate by platform, version, tier before trusting it
- **Correlation is not causation** — A metric moving after a release is suspicious, not proven
- **Verify the instrument** — Before investigating a metric drop, confirm the logging didn't break
- **Recommend, don't just report** — Every finding should end with "so what should we do?"
