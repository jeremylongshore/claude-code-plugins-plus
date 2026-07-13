---
name: portaljs-add-chart
description: Add a chart (line, bar, area, pie, or scatter) to a dataset's showcase in a PortalJS portal. Installs recharts, writes a reusable Chart component, and renders it in the showcase Views section. Use when visualizing a dataset already registered in datasets.json.
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - chart
  - recharts
  - dataviz
  - nextjs
---

# PortalJS — Add Chart

## Overview

Add a visualization to a dataset's **showcase** in a PortalJS portal. The skill installs
`recharts` (added directly — never `@portaljs/components`), writes a reusable client-side
`Chart` component into `components/`, and renders a `<Chart />` into the **Views** section
of the showcase route `pages/[owner]/[slug].tsx` for one chosen dataset. The chart reads the
same `/public/data/<file>` the showcase `<Table />` already uses, so no data is duplicated.
Five chart types are supported: line, bar, area, pie, and scatter.

## Prerequisites

- A scaffolded PortalJS portal (see `portaljs-new-portal`).
- The target dataset already registered in `datasets.json` (see `portaljs-add-dataset`).
- `components/ui/parseCsv.ts` present (ships with the template).
- Node 18+ and npm available in the portal directory.

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-add-chart.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-chart.md) —
the single source of truth. Read and follow it when executing. Summary:

1. Gather input — dataset slug, X column, Y column(s), chart type (default `line`), portal
   directory. If any is missing, interview the user; never dead-end on a missing value.
2. Resolve the dataset from `datasets.json` (`namespace`, `file`, `format`).
3. Validate that the X and every Y column exist in the data file's header; warn on
   non-numeric Y columns (values are coerced with `Number()`).
4. Install the chart library: `npm install recharts@^2.15.0`.
5. Write `components/Chart.tsx` (idempotent — do not overwrite a customized component).
6. Render `<Chart />` into the Views section, gated on the dataset's `(namespace, slug)` so
   other showcases are unaffected. Extend an existing view-dispatch block, do not overwrite.
7. Verify with `npx tsc --noEmit`.
8. Report the component, route, and dependency added.

## Output

- **Created:** `components/Chart.tsx` (recharts wrapper, if absent).
- **Modified:** `pages/[owner]/[slug].tsx` (import + gated `<Chart />` in Views);
  `package.json` (`recharts@^2.15.0`).
- **Verified:** `npx tsc --noEmit` passes.
- **Result:** the chart renders at `/@<namespace>/<slug>` under a "Views" heading.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| Missing dataset/columns | Slug or column not in manifest/header | List available slugs/headers and re-prompt; do not error out. |
| Gaps in the chart | Non-numeric cells coerced to `NaN` | Clean the source data or pick a numeric Y column. |
| `tsc` failure | Bad column prop or import path | Fix the first reported error before reporting success. |
| Sluggish render | Over ~2,000 SVG points | Pre-aggregate the series (e.g. yearly buckets). |

## Examples

### Example 1 — Single line series

```
/portaljs-add-chart co2-emissions x=year y=emissions type=line
```

### Example 2 — Multi-series bar chart

```
/portaljs-add-chart trade x=year y=imports,exports type=bar
```

### Example 3 — Pie chart of a categorical breakdown

```
/portaljs-add-chart budget x=department y=amount type=pie
```

## Resources

- Full workflow: [`.claude/commands/portaljs-add-chart.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-chart.md)
- Chart-type and prop reference: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-add-dataset`, `portaljs-add-map`, `portaljs-define-schema`
- recharts documentation: <https://recharts.org/>
