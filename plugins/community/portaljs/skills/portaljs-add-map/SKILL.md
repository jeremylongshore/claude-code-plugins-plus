---
name: portaljs-add-map
description: Render a GeoJSON dataset on an interactive Leaflet map in the Views section of a dataset's showcase. Installs react-leaflet and a Map component, then renders the map for the chosen dataset. Use when a dataset's data is geographic and a map view is needed alongside the showcase's default metadata and download.
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), WebFetch
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - map
  - geojson
  - leaflet
  - dataviz
---

# PortalJS — Add Map

## Overview

Add an interactive Leaflet map as a view on a dataset's **showcase** in a
`portaljs-catalog` portal. The skill installs `react-leaflet`/`leaflet` (added directly —
never `@portaljs/components`), writes a reusable `Map` component split across
`MapView.tsx` (the Leaflet code) and `Map.tsx` (a `dynamic(..., { ssr: false })` wrapper,
since Leaflet touches `window` at module load), and renders `<Map />` into the **Views**
section of the showcase route `pages/[owner]/[slug].tsx` for one chosen GeoJSON dataset.
The dataset should already carry `format: "geojson"` in `datasets.json`; if it doesn't
exist yet, the skill can copy the file and register it first.

## Prerequisites

- A scaffolded PortalJS portal (see `portaljs-new-portal`).
- The target dataset registered in `datasets.json` with `format: "geojson"` (see
  `portaljs-add-dataset`), or a GeoJSON source file/URL to register.
- Node 18+ and npm available in the portal directory.

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-add-map.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-map.md) — the
single source of truth. Read and follow it when executing. Summary:

1. Gather input — dataset slug (or a GeoJSON source to register), portal directory. If any
   is missing, interview the user; never dead-end on a missing value.
2. Validate the portal directory (`datasets.json`, `package.json`,
   `pages/[owner]/[slug].tsx` must exist).
3. Resolve the dataset from `datasets.json`, or validate and register a new GeoJSON
   source (copy to `/public/data/`, append a manifest entry).
4. Install map dependencies: `npm install react-leaflet@^5 leaflet@^1.9` and
   `npm install -D @types/leaflet` (skip if already present).
5. Write `components/MapView.tsx` and `components/Map.tsx` (idempotent — skip if
   `Map.tsx` already exists).
6. Render `<Map />` into the Views section, gated on the dataset's `(namespace, slug)` so
   other showcases are unaffected. Extend an existing view-dispatch block, do not
   overwrite it.
7. Verify with `npx tsc --noEmit` (never `next build` against a live dev server).
8. Report the component, route, and dependency added.

## Output

- **Created:** `components/MapView.tsx` and `components/Map.tsx` (Leaflet wrapper, if
  absent); `public/data/<slug>.geojson` (only when registering a new dataset).
- **Modified:** `pages/[owner]/[slug].tsx` (import + gated `<Map />` in Views);
  `datasets.json` (only when registering a new dataset); `package.json`
  (`react-leaflet`, `leaflet`, `@types/leaflet`).
- **Verified:** `npx tsc --noEmit` passes.
- **Result:** the map renders at `/@<namespace>/<slug>` under a "Views" heading.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| Dataset not found or not GeoJSON | Slug missing from `datasets.json` or `format` is tabular | List GeoJSON datasets and re-prompt; suggest `portaljs-add-chart` for tabular data. |
| Source fetch/copy fails | URL returns non-200 or local path missing | Report the HTTP status or missing path; ask for a corrected source. |
| "Not valid GeoJSON" | Parsed JSON `type` isn't a Feature/geometry type | Tell the user and point to `portaljs-add-dataset` for tabular data. |
| `tsc` failure | Bad import path or gating condition | Fix the first reported error before reporting success. |
| Map appears on every dataset | View not gated on `(namespace, slug)` | Wrap the `<Map />` render in the dataset check shown in the Instructions. |
| Features render in the wrong place | Data isn't WGS84 (EPSG:4326) lon/lat | Reproject the source data to WGS84 before adding. |
| Slow render | Thousands of features in one file (>5MB) | Simplify geometries (e.g. `mapshaper`) before adding. |

## Examples

### Example 1 — Map an already-registered dataset

```
/portaljs-add-map dataset=park-boundaries
```

### Example 2 — Register a local GeoJSON file and map it

```
/portaljs-add-map source=./data/bike-routes.geojson slug=bike-routes name="Bike Routes"
```

### Example 3 — Register a remote GeoJSON URL and map it

```
/portaljs-add-map source=https://example.com/districts.geojson slug=districts namespace=reference
```

## Resources

- Full workflow: [`.claude/commands/portaljs-add-map.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-map.md)
- Map props and troubleshooting reference: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-add-dataset`, `portaljs-add-chart`, `portaljs-define-schema`
- react-leaflet documentation: <https://react-leaflet.js.org/>
