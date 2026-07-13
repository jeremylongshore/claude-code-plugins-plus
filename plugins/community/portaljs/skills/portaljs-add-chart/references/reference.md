# Add Chart — Reference

Detailed reference for the `portaljs-add-chart` skill. The executable workflow lives in
[`.claude/commands/portaljs-add-chart.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-chart.md).

## Chart types

| Type | Uses | Notes |
| --- | --- | --- |
| `line` (default) | X vs one or more numeric Y series | `type="monotone"`, dots hidden. |
| `bar` | X vs one or more numeric Y series | One bar per Y column. |
| `area` | X vs one or more numeric Y series | Filled at 20% opacity. |
| `pie` | `x` → slice name, `y[0]` → slice value | First Y column only. |
| `scatter` | numeric `x` vs numeric `y[0]` | Both axes numeric; first Y only. |

Pie and scatter use only the first Y column. Pass multiple Y columns for multi-series
line, bar, and area charts.

## `<Chart />` props

| Prop | Type | Purpose |
| --- | --- | --- |
| `url` | string | CSV/TSV file under `/public`, e.g. `/data/file.csv`. |
| `data` | `Row[]` | Pre-parsed rows (alternative to `url`). |
| `type` | `line \| bar \| area \| pie \| scatter` | Chart form (default `line`). |
| `x` | string | X-axis / category column key. |
| `y` | `string \| string[]` | One or more numeric column keys to plot. |
| `height` | number | Pixel height (default `320`). |

## Design rationale

- **recharts, not `@portaljs/components`.** The bundled package ships leaflet, vega,
  ag-grid, and pdf.js in one non-tree-shakeable 1.9 MB blob. recharts is ~100 KB gzipped
  and tree-shakes.
- **Numeric coercion.** CSV cells are strings; the component runs `Number()` on every Y
  value. Non-numeric cells become `NaN` and render as gaps.
- **One showcase route, many datasets.** `pages/[owner]/[slug].tsx` renders every dataset,
  so every view is gated on the dataset's `(namespace, slug)`.
- **Client-side rendering.** The chart fetches in the browser like `Table`, so it works
  with static export and needs no server code.

## Troubleshooting

- **`parseCsv` not found** — the portal predates the current template. Copy
  `parseCsv.ts` from `examples/portaljs-catalog/components/ui/`.
- **Chart appears on every dataset** — a view was not gated on `(namespace, slug)`.
- **Large series render slowly** — pre-aggregate above ~2,000 points.
