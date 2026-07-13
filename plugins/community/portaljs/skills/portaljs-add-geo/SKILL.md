---
name: portaljs-add-geo
description: Auto-ingest a geospatial file (GeoJSON, Shapefile, GeoPackage, KML/KMZ, FlatGeobuf, CSV-with-geometry) into a PortalJS portal on the user's own machine, with no server. Normalizes CRS to EPSG:4326, derives a PMTiles render tier and a GeoParquet query tier, pushes all three artifacts to Cloudflare R2 via Git LFS, and appends one dual-tier datasets.json entry the showcase auto-renders. Use when the source is a vector geo format that needs a map or spatial-query view.
allowed-tools: Read, Write, Edit, Bash(ogr2ogr:*), Bash(ogrinfo:*), Bash(tippecanoe:*), Bash(duckdb:*), Bash(git:*), Bash(curl:*), Bash(npx:*), Bash(node:*), Bash(mkdir:*), Bash(cp:*), Bash(wc:*), Bash(command:*), WebFetch
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18/19, Node 18+). Requires native GDAL, tippecanoe, and duckdb on the user's machine (macOS or Linux/WSL). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - geospatial
  - pmtiles
  - geoparquet
  - duckdb
---

# PortalJS — Add Geo

## Overview

Turn one geospatial upload into a **dual-tier** PortalJS dataset entirely on the user's
machine — **no server-side container compute**, keeping the zero-backend bet end-to-end.
From a single source the skill derives two serverless tiers plus the preserved original:

- **PMTiles** (render tier) — a vector-tile archive `<MapPreview>` renders with MapLibre GL
  over HTTP range requests; any dataset size pans and zooms with no tile server.
- **GeoParquet** (query tier) — a GeoParquet 1.1 file (covering `bbox` column, Hilbert-sorted)
  `<GeoQuery>` runs spatial SQL over in place via DuckDB-Wasm.
- **Original** — the untouched upload in its native CRS, kept downloadable.

All three land on Cloudflare R2 (Git LFS → Giftless), and the skill appends **one**
`datasets.json` entry whose `resources[]` match the shape the showcase auto-renders (the
`@reference/world-boundaries` demo, PR #1647): `pmtiles` → `<MapPreview>`, `geoparquet` →
`<GeoQuery>`, original → download. No page edits are needed. It automates the manual
`tippecanoe`/`duckdb` recipes in the template README.

## Prerequisites

- A scaffolded `portaljs-catalog` portal whose template ships `components/MapPreview.tsx` and
  `components/GeoQuery.tsx` (PR #1647 or later).
- Native CLIs on the user's machine: **GDAL** (`ogr2ogr`, `ogrinfo`), **tippecanoe**, and
  **duckdb** (with the `spatial` extension). macOS: `brew install gdal tippecanoe duckdb`;
  Debian/Ubuntu: `apt-get install gdal-bin duckdb` + tippecanoe (apt or build from source);
  Windows: use WSL. The skill hard-stops with the install hint if any is missing.
- Arc credentials for the Git-LFS → R2 push (the same token `portaljs-deploy` resolves), or
  an OSS self-hosted Giftless.

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-add-geo.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-geo.md)
— the single source of truth. Read and follow it when executing. Summary:

1. Gather input — source (geo file path or URL), portal directory, namespace. Interview if
   missing; never dead-end.
2. Detect the native tools (`ogr2ogr`, `tippecanoe`, `duckdb` + `spatial`). Any missing →
   print the per-OS install and stop.
3. Validate the portal directory and confirm the geo showcase components exist.
4. Fetch (if URL) and detect the input format; reject raster and bare `.shp`.
5. Preserve the original, then normalize to EPSG:4326 GeoJSON with `ogr2ogr -t_srs EPSG:4326`.
6. Apply the size escape hatch (measure normalized-GeoJSON bytes): warn ≥ 500 MB; skip PMTiles
   and emit GeoParquet-only > 2 GB (documented, never silent).
7. Derive PMTiles with `tippecanoe -zg --drop-densest-as-needed`.
8. Derive GeoParquet with `duckdb` — covering `bbox` STRUCT + `ST_Hilbert` order; verify a
   range read.
9. Track all three files with Git LFS, mint an Arc JWT, push to R2, prune, and build the
   absolute `data.portaljs.com` URLs.
10. Append one dual-tier `datasets.json` entry (`pmtiles` + `geoparquet` + original resources).
11. Verify: `npx tsc --noEmit` and a `Range:` 206 check on the R2 URL.
12. Report the tiers, manifest entry, and showcase route.

## Output

- **Created:** `data/<slug>.pmtiles`, `data/<slug>.parquet`, `data/<slug>.<origext>` (all
  LFS-tracked → R2); `data/<slug>.4326.geojson` (intermediate; can be pruned).
- **Modified:** `datasets.json` (one dual-tier entry appended); `.gitattributes` (LFS tracking).
- **Verified:** `npx tsc --noEmit` passes; the R2 URLs answer HTTP 206 range reads.
- **Result:** `/@<namespace>/<slug>` renders the PMTiles map and the GeoParquet spatial-query
  panel together, with no page edits.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| `MISSING_TOOLS` | `ogr2ogr`/`tippecanoe`/`duckdb` (or duckdb `spatial`) absent | Print the per-OS install line and stop; re-run after installing. |
| `UNSUPPORTED_FORMAT` | Raster `.tif`/`.tiff` (COG tier, later phase) | Use `portaljs-add-dataset` for tabular; await the COG phase. |
| `SHAPEFILE_NOT_ZIPPED` | Bare `.shp` with no siblings | Zip the whole `.shp/.dbf/.shx/.prj` set and pass the `.zip`. |
| `MULTI_LAYER` | GPKG/KML with more than one layer | List layers and ask which to ingest; pass the layer name. |
| `REPROJECTION_FAILED` | `ogr2ogr` error, often a missing `.prj` | Show stderr; re-run with `-s_srs EPSG:<code>`. |
| `EMPTY_OUTPUT` | Normalized GeoJSON has 0 features | Check the geometry column / CRS of the source. |
| `TILING_FAILED` / `GEOPARQUET_FAILED` | tippecanoe or duckdb non-zero | Show stderr; for very large inputs see the size escape hatch. |
| `LFS_PUSH_FAILED` | Missing/expired Arc token or unset `lfs.url` | Re-mint the JWT (see `portaljs-deploy`); confirm `git config lfs.url`. |

## Examples

### Example 1 — Ingest a GeoJSON into both tiers

```
/portaljs-add-geo source=./data/rivers.geojson name="World Rivers" namespace=reference
```

### Example 2 — Zipped Shapefile from a URL

```
/portaljs-add-geo source=https://example.com/admin-boundaries.zip slug=admin-boundaries
```

### Example 3 — GeoPackage with an explicit layer and namespace

```
/portaljs-add-geo source=./data/census.gpkg slug=census-tracts namespace=statistics
```

## Resources

- Full workflow: [`.claude/commands/portaljs-add-geo.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-geo.md)
- Flags, thresholds, and the dual-tier manifest shape: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-add-dataset`, `portaljs-add-map`, `portaljs-add-resource`, `portaljs-deploy`
- tippecanoe: <https://github.com/felt/tippecanoe> · DuckDB spatial: <https://duckdb.org/docs/extensions/spatial>
