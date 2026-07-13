# Add Map — Reference

Detailed reference for the `portaljs-add-map` skill. The executable workflow lives in
[`.claude/commands/portaljs-add-map.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-map.md).

## `<Map />` props

| Prop | Type | Purpose |
| --- | --- | --- |
| `url` | string | GeoJSON file under `/public`, e.g. `/data/file.geojson`. |
| `data` | `GeoJsonObject` | Inline GeoJSON (alternative to `url`). |
| `height` | number | Pixel height (default `500`). |

Every feature's `properties` become a click popup automatically. Points render as
`circleMarker`s (avoids Leaflet's broken default marker-icon URLs under bundlers); the
view auto-fits the map to the data's bounds on load.

## Dynamic import and SSR

Leaflet touches `window` at module load and cannot run during server rendering. The
component is split in two:

- `MapView.tsx` — holds all Leaflet/react-leaflet code.
- `Map.tsx` — a thin wrapper that loads `MapView` with
  `dynamic(() => import('./MapView'), { ssr: false })` and shows a loading placeholder.

Only the `MapProps` type crosses the boundary (erased at build), so Leaflet code never
reaches the server bundle. Always import `Map` (not `MapView`) from the showcase page.

## Design rationale

- **react-leaflet, not `@portaljs/components`.** The bundled package ships leaflet, vega,
  ag-grid, and pdf.js in one non-tree-shakeable 1.9 MB blob.
- **react-leaflet@^5 vs @^4.** v5 targets React 19, used by the catalog template. Portals
  still on React 18 should install `react-leaflet@^4` instead — its peer dependency
  requires React 18.
- **One showcase route, many datasets.** `pages/[owner]/[slug].tsx` renders every
  dataset, so every view is gated on the dataset's `(namespace, slug)`.
- **Client-side fetch.** `Map` fetches GeoJSON in the browser from `/data/<file>`, the
  same pattern `Table` uses — sidesteps the fact that `.geojson` imports aren't covered
  by `resolveJsonModule`, and works with static export.

## Troubleshooting

- **Map appears on every dataset's showcase** — the `<Map />` render wasn't gated on
  `(namespace, slug)`; wrap it in the dataset check from the Instructions.
- **Features land in the wrong place** — the source data isn't WGS84 (EPSG:4326)
  lon/lat; Leaflet assumes WGS84 and does not reproject. Reproject before adding.
- **Blank map / peer dependency error on install** — portal is on React 18; use
  `react-leaflet@^4` instead of `@^5`.
- **Slow render with large files** — thousands of features (>5MB) render slowly;
  simplify geometries first (e.g. `mapshaper`).
