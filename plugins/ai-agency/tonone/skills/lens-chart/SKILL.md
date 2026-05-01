---
name: lens-chart
description: |
  Use when asked to select chart types for analytics dashboards, choose BI
  visualizations, or design data displays. Examples: "best chart for sales data",
  "dashboard visualization for metrics", "analytics chart selection"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# lens-chart — BI & Analytics Chart Selection

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

User needs chart type selection or visualization recommendations for analytics dashboards or BI contexts.

## Workflow

1. **Identify data type and BI context** from user request (sales trends, cohort analysis, funnel, KPI comparison, etc.)
2. **Search chart knowledge base:**
   ```bash
   python3 -m lens_agent.uiux search --domain chart --query "{data_type}" --limit 3
   ```
3. **Search style for BI context:**
   ```bash
   python3 -m lens_agent.uiux search --domain style --query "{context}" --limit 2
   ```
4. **Evaluate for BI requirements:** data density, drill-down capability, real-time support, library recommendation
5. **Output** optimized for decision-making, not decoration

## Output format

```
┌─ BI Chart Recommendation — {data_type} ─────────────────────────────┐
│ Chart type:        {chart_type}                                      │
│ Library:           {library}                                         │
│ Data density:      {density} (low / medium / high)                  │
│ Drill-down:        {drill_down} (yes / no / limited)                │
│ Real-time support: {real_time} (yes / no)                           │
│ Accessibility:     {grade}                                           │
├─ Decision test ─────────────────────────────────────────────────────┤
│ "Does this answer a decision?" → {yes_no}: {rationale}              │
└──────────────────────────────────────────────────────────────────────┘
```

## Anti-patterns

- Never choose decorative over data-dense visualizations for BI contexts
- Never skip the "does this answer a decision?" test — every chart must justify its inclusion
- Never skip accessibility fallback for charts graded below AA
- Never recommend real-time charts without confirming the data pipeline supports streaming

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
