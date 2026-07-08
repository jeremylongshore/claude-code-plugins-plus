---
metatitle: /portaljs-migrate – Harvest Datasets from CKAN or DCAT into a PortalJS Catalog
metadescription: The /portaljs-migrate skill harvests datasets from a CKAN instance or a DCAT-US /data.json catalog (DKAN, ArcGIS Hub, data.gov) into a static PortalJS catalog — link by URL or download the data into Cloudflare R2 via Git LFS, as plain editable datasets.json entries.
title: /portaljs-migrate
description: Harvest datasets from a CKAN instance or a DCAT /data.json catalog into the static PortalJS catalog — the copy-into-the-portal path.
---

`/portaljs-migrate` harvests datasets from an external open-data platform **into** an existing
`portaljs-catalog` portal. It reads the source over its API, maps each dataset to the
template's canonical shape, and writes the results into `datasets.json` — so the `/search`
catalog and the `/@<namespace>/<slug>` showcases render them like any hand-added dataset.

It's the inverse of [`/portaljs-connect-ckan`](/docs/skills/portaljs-connect-ckan): connect-ckan keeps the
source authoritative and reads it live at build time; `/portaljs-migrate` takes a one-time
(re-runnable) **snapshot** into the static catalog, so the portal stands alone with no
backend.

## Hub-and-spoke

Every source is read into one **canonical** shape (the Frictionless-aligned
`Dataset`/`Resource` type), then written to the target from that form — so a source is
added once and works with every target.

**Sources (v1):**

| Source | `--source` | Read via | Covers |
| ------ | ---------- | -------- | ------ |
| **CKAN** | `ckan` | `package_search` / `package_show` | any CKAN instance |
| **DCAT-US `/data.json`** | `dcat` | one catalog document | **DKAN, ArcGIS Hub, data.gov**, other DCAT-US publishers |
| **Socrata** | `socrata` | Discovery API + resource exports | Socrata-powered sites |
| **OpenDataSoft** | `ods` | Explore API v2 + exports | ODS-powered portals |
| **ArcGIS FeatureServer / MapServer** | `arcgis` | layer metadata + GeoJSON query | individual ArcGIS services (each layer → a GeoJSON dataset) |

> DKAN, ArcGIS Hub, and data.gov publish a DCAT-US `/data.json` — use **dcat** for those whole
> catalogs; use **arcgis** for an individual FeatureServer/MapServer.

**Targets:**

| Target | `--target` | Writes |
| ------ | ---------- | ------ |
| **Static PortalJS catalog** (default) | `static` | `datasets.json` (+ in `download` mode, data files pushed to Cloudflare R2 via Git LFS / Giftless) |
| **CKAN instance** | `ckan` | datasets/resources into a CKAN backend via its action API |

The CKAN target enables platform-to-platform moves — **CKAN→CKAN** and **DKAN→CKAN** — since
any reader feeds any writer through the canonical shape.

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| Source URL | Yes | A CKAN base URL, or a DCAT `/data.json` URL. |
| Source type | No | `ckan`, `dcat`, `socrata`, `ods`, or `arcgis`; auto-detected from the URL if omitted. |
| Org / group filter | No | CKAN source only — restrict the harvest. |
| `--target` | No | `static` (default) or `ckan`. |
| Portal directory | No | Static target — defaults to the current directory. |
| Copy mode | No | Static target — `link` (default) or `download`. |
| Target CKAN URL | For `--target ckan` | The CKAN instance to write into. |
| `CKAN_API_KEY` (env) | For `--target ckan` | A **write** API key, read from the environment — never passed on the command line. |
| Owner org | No | CKAN target — file every dataset under this org (created if missing; defaults to each dataset's namespace). |
| `--dry-run` | No | Preview what would be written, change nothing. |
| `--replace` | No | Static target — clear existing entries first (default: upsert). |

## Examples

Harvest a whole CKAN instance:

```
/portaljs-migrate https://demo.dev.datopian.com
```

Harvest one CKAN organization, downloading the files into the repo:

```
/portaljs-migrate https://demo.dev.datopian.com --org transport --download
```

Harvest a DCAT catalog (DKAN / ArcGIS Hub / data.gov):

```
/portaljs-migrate https://hub.arcgis.com/data.json --source dcat
```

Harvest a Socrata site, an OpenDataSoft portal, or a single ArcGIS service:

```
/portaljs-migrate https://data.cityofnewyork.us --source socrata
/portaljs-migrate https://data.opendatasoft.com --source ods
/portaljs-migrate https://services.arcgis.com/…/FeatureServer --source arcgis
```

Move one CKAN instance's datasets into another CKAN (set the write key first):

```
export CKAN_API_KEY=…           # write key for the destination
/portaljs-migrate https://source-ckan.example --target ckan --target-url https://dest-ckan.example --owner-org my-org
```

> Copy modes apply to the **static** target. For `--target ckan`, see *CKAN target* below.

## Copy modes (static target)

- **`link` (default)** — each resource's `path` is set to the **source file URL**. No files
  are copied; the catalog references the source's hosting. Fast and light, but previews and
  downloads depend on the source staying up and allowing cross-origin reads.
- **`download`** — every resource is pulled into the repo under **Git LFS** and pushed to
  **Cloudflare R2 via Giftless** (the same path [`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset)
  uses), and `path` is set to the absolute R2 URL. All files go through LFS — no size
  threshold — so the portal is fully self-contained and the repo stays tiny (only ~130-byte
  pointers) no matter how large the catalog. The bytes live in R2, not in git or on the source.

Both produce the same `datasets.json`; only `resources[].path` differs. The template's
`resourceUrl()` returns absolute paths unchanged, which is what makes both modes work.

## What it produces

- **`datasets.json`** — the harvested datasets, upserted by `(namespace, slug)` (re-running
  refreshes changed datasets without duplicating them). Existing entries — including the
  template's samples — are kept unless you pass `--replace`.
- **data files in Cloudflare R2** (download mode only) — pushed via Git LFS / Giftless; the
  repo holds only the LFS pointers under `data/`, and `resources[].path` points at R2.

It runs a full `npm run build` and reports how many datasets were imported and pages
generated before declaring success.

## CKAN target

With `--target ckan`, `/portaljs-migrate` pushes the canonical datasets into a CKAN instance instead
of writing `datasets.json`: it ensures the owner organization exists, then `package_create`
(or `package_update` on re-run) for each dataset and `resource_create` for each resource,
authenticating with the `CKAN_API_KEY` env var. The slug becomes CKAN's package `name`;
`name`/`description`/`keywords` map to `title`/`notes`/`tags`. In `link` mode the resource
`url` references the source file (v1 does not re-upload bytes into CKAN). It stops on the
first auth/permission error rather than half-migrating.

## After migrating

- [`/portaljs-check-data-quality`](/docs/skills/portaljs-check-data-quality) — validate the harvested data.
- [`/portaljs-define-schema`](/docs/skills/portaljs-define-schema) — add Frictionless schemas (sources rarely
  ship them).
- [`/portaljs-add-chart`](/docs/skills/portaljs-add-chart) / [`/portaljs-add-map`](/docs/skills/portaljs-add-map) — they work on
  migrated datasets exactly as on hand-added ones.
- [`/portaljs-deploy`](/docs/skills/portaljs-deploy) — publish the catalog.

## Notes

- **Large catalogs** make many static pages and a slow build. Use the CKAN org/group filters
  (or a DCAT source already scoped to a site) to migrate a subset; the skill reports how many
  were imported vs. available.
- **Schemas** aren't inferred during the harvest — add them afterward with `/portaljs-define-schema`.
- **Formats.** CSV/TSV/JSON/GeoJSON preview in the showcase; any other format is kept and
  shown as a download link.

## Where to go next

- **[`/portaljs-connect-ckan`](/docs/skills/portaljs-connect-ckan)** — the live read-through alternative.
- **[Backends](/docs/backends)** — integration notes per platform.

<DocsPagination prev="/docs/skills/portaljs-connect-ckan" next="/docs/skills/portaljs-define-schema" />
