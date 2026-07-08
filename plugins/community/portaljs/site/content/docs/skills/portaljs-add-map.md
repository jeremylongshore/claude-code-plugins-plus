---
metatitle: /portaljs-add-map – Render a GeoJSON Dataset on an Interactive Map in PortalJS
metadescription: The /portaljs-add-map skill installs react-leaflet, generates a reusable Map component, and adds a map view to a dataset's showcase — rendering GeoJSON on an interactive Leaflet map.
title: /portaljs-add-map
description: Render a GeoJSON dataset on an interactive Leaflet map as a view on its showcase.
---

`/portaljs-add-map` adds an interactive map view of a GeoJSON dataset to an existing PortalJS
portal. It copies the GeoJSON into `/public/data/`, installs `react-leaflet` /
`leaflet` (once), generates a reusable `Map` component, and adds a map view into the
**Views** section of the dataset's showcase (`pages/[owner]/[slug].tsx`).

## When to use it

Use it when your data is geographic (points, lines, polygons) and you want a map
view of it. If the GeoJSON isn't yet in the portal, add it first with
[`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset); the map is added as a view alongside the
dataset's other views, so a single showcase can offer both a properties table and a
map.

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| Source | Yes | A local file path or public URL. Must be **GeoJSON** (a `Feature`, `FeatureCollection`, or geometry object). |
| Portal directory | No | Path to the portal project. Defaults to the current directory. |
| Map name | No | Human-readable name. Defaults to the filename. |
| Description | No | Optional one-line description shown on the page. |

The skill validates that the target is a PortalJS portal and that the source is
valid GeoJSON before doing anything; non-GeoJSON sources are rejected with a
pointer to `/portaljs-add-dataset`.

## Example

```
/portaljs-add-map ./data/auckland-suburbs.geojson
```

From a public URL with a name:

```
/portaljs-add-map https://example.com/cities.geojson — Major cities
```

## What it produces

- The GeoJSON copied to `public/data/<slug>.geojson`.
- `react-leaflet` and `leaflet` added to `package.json` (installed once).
- The GeoJSON copied to `public/data/<file>` and, if not already present, a
  `datasets.json` entry appended for it (so the showcase route renders it).
- A reusable `components/Map.tsx` plus `components/MapView.tsx` — split so Leaflet
  is loaded with `dynamic(..., { ssr: false })` and never reaches the server
  bundle. Every feature's `properties` become a click popup automatically.
- A `<Map />` view added to the **Views** section of the showcase route
  (`pages/[owner]/[slug].tsx`), rendered for the chosen dataset's `(namespace, slug)`
  and fetching the GeoJSON client-side. No separate page is created and nothing is
  registered on the home page.

It runs the build before reporting success. When it finishes:

```
✓ Map added: Auckland suburbs
  - Data file: public/data/auckland-suburbs.geojson
  - Component: components/Map.tsx (+ MapView.tsx)
  - View: pages/[owner]/[slug].tsx — <Map> for @auckland-council/auckland-suburbs
  - Showcase: http://localhost:3000/@auckland-council/auckland-suburbs
```

## Where to go next

- **[`/portaljs-add-chart`](/docs/skills/portaljs-add-chart)** — add a chart to a tabular dataset.
- **[`/portaljs-deploy`](/docs/skills/portaljs-deploy)** — publish the portal.

<DocsPagination prev="/docs/skills/portaljs-add-chart" next="/docs/skills/portaljs-connect-ckan" />
