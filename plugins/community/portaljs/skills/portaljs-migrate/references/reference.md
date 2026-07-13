# PortalJS Migrate — Reference

Field mappings, sink options, and troubleshooting detail for the
[`/portaljs-migrate`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-migrate.md) command. Read the
command file first for the full step-by-step workflow; this document is the
supporting lookup table.

## Supported source formats

| Source | `--source` | How it's read | Typical publishers |
| --- | --- | --- | --- |
| CKAN | `ckan` | REST API (`package_search` / `package_show`) | Any CKAN instance |
| DCAT-US `/data.json` | `dcat` | One catalog document (plain JSON) | DKAN, ArcGIS Hub, data.gov |
| DCAT / DCAT-AP RDF feed | `dcat-rdf` | RDF graph in JSON-LD, Turtle, or RDF/XML | data.europa.eu, national DCAT-AP portals (SE/CH/DE), GeoDCAT-AP |
| Socrata | `socrata` | Discovery API + per-dataset file exports | Socrata-powered open-data sites |
| OpenDataSoft | `ods` | Explore API v2 catalog + exports | ODS-powered portals |
| ArcGIS FeatureServer/MapServer | `arcgis` | Layer metadata + GeoJSON query | Individual ArcGIS map/feature services |

Auto-detection order: `/FeatureServer`/`/MapServer` → arcgis; `.jsonld`/`.ttl`/`.rdf`
or `/catalog.` → dcat-rdf; `.json`/`/data.json` → dcat; `/api/explore/` → ods;
`/api/catalog/` → socrata; otherwise probe CKAN's `package_search`, then ODS, then
`data.json`, then content-negotiate for RDF. An HTML page is followed via its
`<link rel="alternate">` autodiscovery tag when present.

## Sink (target) options

| Target | `--target` | Writes | Notes |
| --- | --- | --- | --- |
| Static PortalJS catalog | `static` (default) | `datasets.json` in a `portaljs-catalog` portal | `link` mode references source URLs; `download` mode copies files into `data/**` under Git LFS, pushed to Cloudflare R2 via Giftless |
| CKAN instance | `ckan` | Datasets/resources via `package_create`/`resource_create` | Requires a write API key (`CKAN_API_KEY`); enables CKAN→CKAN and DKAN→CKAN moves |

`link` is the default: instant, keeps the repo small, but previews and downloads
depend on the source staying reachable. `download` makes the portal
self-contained — every resource routes through Git LFS/R2 regardless of file size,
for consistency across the whole harvest.

## Canonical dataset shape

Every source maps into this shape before it is written to any target:

```jsonc
{
  "slug": "...",            // URL-safe, unique within a namespace
  "namespace": "...",       // CKAN org / DCAT publisher or theme
  "name": "...",            // human title
  "description": "...",     // optional
  "keywords": ["..."],      // optional
  "resources": [
    { "name": "...", "path": "<url-or-filename>", "format": "csv", "title": "..." }
  ]
}
```

Formats are normalized to what the showcase can preview (`csv`, `tsv`, `json`,
`geojson`); anything else is kept as-is and rendered as a download link instead of
a preview.

## Troubleshooting

| Problem | Likely cause | Resolution |
| --- | --- | --- |
| Auto-detect picks the wrong source type | Ambiguous URL (e.g. ends in `.json` but isn't DCAT-US) | Pass `--source` explicitly to skip detection |
| CKAN `ORG_FILTER` drops all results | Org name doesn't exist on the source | Run `organization_list` on the source and confirm the exact name |
| DCAT-RDF harvest reports many `warnings` | Feed has datasets with no title/identifier or no distribution | Expected — the harvester skips those and imports the rest; review `warnings` in the harvest output |
| Socrata/ODS pagination stalls or times out | Very large catalog, no scoping filter | Add `&q=`/`&categories=` (Socrata) or `&where=`/`&refine=` (ODS) to narrow the harvest |
| Slug collisions across a large harvest | Two sources publish datasets with the same name in one namespace | The migrator suffixes colliding slugs (`-2`, `-3`, …) automatically; verify the result in `datasets.json` |
| `npx tsx` fails on `dcat-harvest.ts` | Target portal predates the harvester | Copy `lib/metadata/dcat-harvest.ts` and `dcat-profiles.ts` from `examples/portaljs-catalog/lib/metadata/` |
