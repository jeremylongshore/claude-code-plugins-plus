# Add Geo — Reference

Detailed reference for the `portaljs-add-geo` skill. The executable workflow lives in
[`.claude/commands/portaljs-add-geo.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-geo.md).

## Native tools and why each is needed

| Tool | Role | Why |
| --- | --- | --- |
| GDAL `ogr2ogr` / `ogrinfo` | Read every vector input, reproject → EPSG:4326, emit the normalized GeoJSON intermediate | Widest driver set (SHP, GPKG, KML/KMZ, FGB, CSV-geom) |
| `tippecanoe` | normalized GeoJSON → PMTiles (render tier) | No mature WASM build exists; PMTiles fundamentally needs the native binary |
| `duckdb` + `spatial` | normalized GeoJSON → GeoParquet 1.1 (covering `bbox` + Hilbert) | The proven writer — `<GeoQuery>` (PR #1647) was verified against duckdb output; ogr2ogr's Parquet driver won't cleanly emit the covering-bbox column + Hilbert order the bbox-first query needs to prune |

Install: macOS `brew install gdal tippecanoe duckdb`; Debian/Ubuntu
`apt-get install gdal-bin duckdb` plus tippecanoe (apt where available, else build from
[felt/tippecanoe](https://github.com/felt/tippecanoe)); Windows is unsupported first-cut —
use WSL (Ubuntu) and follow the Debian path.

## Input format matrix

| Input | Extensions | `ogr2ogr` source spec |
| --- | --- | --- |
| GeoJSON | `.geojson`, `.json` (type `FeatureCollection`/`Feature`/geometry) | the file path |
| Zipped Shapefile | `.zip` (`.shp` + `.dbf` + `.shx` [+ `.prj`]) | `/vsizip/<abs>.zip` |
| GeoPackage | `.gpkg` | the file path (multi-layer → pass a layer name) |
| KML / KMZ | `.kml`, `.kmz` | the file path (GDAL LIBKML driver) |
| FlatGeobuf | `.fgb` | the file path |
| CSV + geometry | `.csv` with WKT or lat/lon columns | `-oo GEOM_POSSIBLE_NAMES=…` or `-oo X_POSSIBLE_NAMES=…,Y_POSSIBLE_NAMES=…` + `-oo KEEP_GEOM_COLUMNS=NO` |
| Raster | `.tif`, `.tiff` | **unsupported** — COG is a later phase |

## Exact derivation commands

Normalize (RFC 7946 clamps to 4326 lon/lat, right-hand winding):
```bash
ogr2ogr -f GeoJSON -t_srs EPSG:4326 -lco RFC7946=YES out.4326.geojson <src>
```
PMTiles (attributes preserved for click-to-inspect):
```bash
tippecanoe -zg --drop-densest-as-needed --extend-zooms-if-still-dropping --force \
  -o out.pmtiles out.4326.geojson
```
GeoParquet (covering `bbox` STRUCT + Hilbert order; `ST_Read` yields a `geom` column):
```bash
duckdb -c "LOAD spatial;
  COPY (
    SELECT * EXCLUDE (geom),
      {'xmin': ST_XMin(geom), 'ymin': ST_YMin(geom),
       'xmax': ST_XMax(geom), 'ymax': ST_YMax(geom)} AS bbox,
      geom AS geometry
    FROM ST_Read('out.4326.geojson')
    ORDER BY ST_Hilbert(geom, {'min_x':-180,'min_y':-90,'max_x':180,'max_y':90}::BOX_2D)
  ) TO 'out.parquet' (FORMAT PARQUET, ROW_GROUP_SIZE 25000);"
```

## Size escape hatch

Measured on the **normalized GeoJSON** — exactly what both tools ingest, and
format-independent. Heuristics for an ~8–16 GB laptop; tune as needed.

| Normalized GeoJSON | Behavior |
| --- | --- |
| < 500 MB | Both tiers, no warning. |
| 500 MB – 2 GB (or ≥ ~5M features) | Soft warn (minutes + GB RAM), then proceed. |
| > 2 GB | Skip PMTiles, emit **GeoParquet-only** (duckdb streams row groups). Report exactly what was skipped and offer: (a) keep it query-only, or (b) tile on a bigger machine and attach the PMTiles later with `portaljs-add-resource`. Never a silent truncation. |

## Dual-tier `datasets.json` shape

One dataset, `resources[]` = `pmtiles` (render) + `geoparquet` (query, with a bbox-first
`query` over the data's own extent) + the original (download). This is exactly what the
showcase route renders per `format`:

- `format: "pmtiles"` → `components/MapPreview.tsx` (MapLibre GL, range reads).
- `format: "geoparquet"` → `components/GeoQuery.tsx` (DuckDB-Wasm + spatial, in place).
- any other format → a download link.

The `geoparquet` resource's `query` uses the bbox-first pattern — a cheap covering-bbox
filter prunes Parquet row groups, then `ST_Intersects` refines to the exact predicate —
and projects a `geojson` column (via `ST_AsGeoJSON`) that drives the MapLibre overlay.

## Design rationale

- **Zero backend, end-to-end.** All conversion runs on the user's machine; the browser then
  fetches the derivatives straight from R2. No server compute is introduced — the locked
  direction (2026-07-08) that overrides po-6sr §7's server-compute sketch.
- **Two derivatives, not three.** PMTiles + GeoParquet are the canonical artifacts; the
  original is preserved for download. FlatGeobuf is deliberately not emitted (a format with
  no showcase view).
- **No page edits.** Unlike `portaljs-add-map`, the dual-tier resources render purely from
  their `format`, so this skill only writes data + one manifest entry.
- **Git LFS mechanics mirror `portaljs-add-dataset` §4c** — `git lfs install --local`, per-file
  tracking, an Arc-minted `_jwt` token in `lfs.url` (never a broad `http.extraHeader`, which
  would break the presigned R2 PUT), push to R2 with no GitHub remote required, then prune.
