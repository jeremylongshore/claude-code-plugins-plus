# @portaljs/core

Core Portal.JS package containing components, styles, and utils.

## `<MapPreview>` — serverless preview of tiled geo data (PMTiles)

Renders a vector [PMTiles](https://docs.protomaps.com/pmtiles/) archive with
MapLibre GL straight from any static HTTP host (R2, S3, `/public`) via HTTP
range requests — only the tiles in view are fetched, so any-size datasets pan
and zoom with no tile server. Click a feature to inspect its properties.

```tsx
import { MapPreview } from "@portaljs/core";

<MapPreview
  url="https://example.com/data/boundaries.pmtiles" // or a relative path
  // center={[0, 20]} zoom={3}      — omit to auto-fit the tileset bounds
  // basemap={false}                — offline mode; defaults to the free MapLibre demo tiles style
  // color="#2f6f4f" height={480}
  attribution="Natural Earth"
/>
```

SSR-safe by construction: `maplibre-gl` and `pmtiles` load via dynamic
`import()` in the browser only, so the component can be rendered by Next.js
pages without a `next/dynamic` wrapper (though wrapping with `{ ssr: false }`
still defers the chunk until a map actually mounts).

Make PMTiles from GeoJSON/Shapefile with
[tippecanoe](https://github.com/felt/tippecanoe):

```bash
tippecanoe -zg --drop-densest-as-needed -o out.pmtiles in.geojson
```
