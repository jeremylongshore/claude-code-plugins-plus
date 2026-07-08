---
metatitle: /portaljs-add-chart – Add a Line, Bar, Area, Pie, or Scatter Chart to PortalJS
metadescription: The /portaljs-add-chart skill installs recharts, writes a reusable Chart component, and adds a chart view to a dataset's showcase — reading the same data the table already uses.
title: /portaljs-add-chart
description: Add a line, bar, area, pie, or scatter chart as a view on a dataset's showcase, reading the same data the table already uses.
---

`/portaljs-add-chart` adds a chart view to an existing dataset's showcase. It installs
`recharts`, writes a reusable client-side `Chart` component into the portal's
`components/`, and adds a `<Chart />` into the **Views** section of the showcase
route (`pages/[owner]/[slug].tsx`), keyed to the chosen `(namespace, slug)`. The
chart reads the same `/public/data/*` file the dataset's table already uses — no
data is duplicated.

## When to use it

Run it after [`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset) has added the dataset
you want to chart.

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| Dataset | Yes | The dataset slug (e.g. `country-codes`). The dataset must already exist in `datasets.json`. |
| X axis column | Yes | The column for the category / X axis (e.g. `year`). |
| Y axis column(s) | Yes | One or more numeric columns to plot (e.g. `population` or `imports,exports`). |
| Chart type | No | `line` (default), `bar`, `area`, `pie`, or `scatter`. |
| Portal directory | No | Path to the portal project. Defaults to the current directory. |
| Title | No | Chart heading. Defaults to one derived from the Y columns. |

The skill validates that the requested columns exist in the data and warns if a Y
column looks non-numeric (values are coerced with `Number()`). Pie and scatter use
the first Y column only; pass extra Y columns for multi-series line, bar, or area
charts.

## Example

```
/portaljs-add-chart country-codes --x year --y population --type line
```

In natural language:

```
/portaljs-add-chart the population dataset — plot population over year as a line chart
```

## What it produces

- `recharts` added to `package.json` (installed directly — not the heavier
  `@portaljs/components` bundle).
- A reusable `components/Chart.tsx` (written once; an existing customized component
  is never overwritten).
- A `<Chart />` view added to the **Views** section of the showcase route
  (`pages/[owner]/[slug].tsx`), rendered only for the chosen dataset's
  `(namespace, slug)`. No separate page is created and nothing is registered on the
  home page.

It type-checks the project (`tsc --noEmit`) before reporting success. When it
finishes:

```
✓ Chart added to country-codes
  - Component: components/Chart.tsx (recharts)
  - View: pages/[owner]/[slug].tsx — <Chart type="line" x="year" y="population"> for @reference/country-codes
  - Dependency: recharts@^2.15.0 added to package.json
```

> recharts 2.15 declares React 19 support, but its bundled `react-is` must match
> your React. The catalog template pins `"overrides": { "react-is": "^19.0.0" }`
> in `package.json` so this works out of the box on React 19.

## Where to go next

- **[`/portaljs-add-map`](/docs/skills/portaljs-add-map)** — render geographic data on a map instead.
- **[`/portaljs-deploy`](/docs/skills/portaljs-deploy)** — publish the portal once it looks right.

<DocsPagination prev="/docs/skills/portaljs-add-resource" next="/docs/skills/portaljs-add-map" />
