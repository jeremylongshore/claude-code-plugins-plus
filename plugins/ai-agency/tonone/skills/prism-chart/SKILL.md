---
name: prism-chart
description: |
  Use when asked to implement a chart, select a visualization type, or build a
  data display component. Examples: "implement chart for time series", "best
  visualization for comparison data", "chart component for analytics"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# prism-chart — Chart & Visualization Selection

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

User needs a chart implementation, visualization type recommendation, or data display component.

## Workflow

1. **Identify data type** from user request (time series, comparison, distribution, composition, relationship, etc.)
2. **Search chart knowledge base:**
   ```bash
   python3 -m prism_agent.uiux search --domain chart --query "{data_type}" --limit 3
   ```
3. **Evaluate results** for: data volume threshold, accessibility grade, interaction level
4. **Output** recommendation with library choice and accessibility fallback

## Output format

```
┌─ Chart Recommendation — {data_type} ────────────────────────────────┐
│ Chart type:        {chart_type}                                      │
│ Library:           {library} (Chart.js / Recharts / D3 / Plotly)    │
│ Accessibility:     {grade} (AA / A / Below AA)                      │
│ Interaction level: {level} (static / hover / drill-down)            │
│ Data volume:       {threshold} (max recommended data points)        │
├─ Color guidance ────────────────────────────────────────────────────┤
│ {color_guidance}                                                     │
├─ Accessibility fallback ────────────────────────────────────────────┤
│ {fallback_description}                                               │
└──────────────────────────────────────────────────────────────────────┘
```

## Anti-patterns

- Never ignore data volume threshold — recommend aggregation if data exceeds it
- Never skip accessibility fallback for charts graded below AA
- Never choose a chart type based on visual appeal over data clarity
- Never recommend a library without confirming it is compatible with the detected stack

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
