---
metatitle: /portaljs-add-dataset – Add a CSV, TSV, JSON, or GeoJSON Dataset to PortalJS
metadescription: The /portaljs-add-dataset skill copies your data into the portal and appends an entry to datasets.json, so the dataset's showcase renders automatically at /@<namespace>/<slug> — all as plain, editable code.
title: /portaljs-add-dataset
description: Add a CSV, TSV, JSON, or GeoJSON dataset — copies the data in and appends a datasets.json entry, so its showcase renders automatically.
---

`/portaljs-add-dataset` adds a dataset to an existing PortalJS portal. It appends an
entry to the `datasets.json` manifest and **routes the data by source, then size** —
local files go to Cloudflare R2 via Git LFS by default, remote URLs are recorded as-is
(no copy) by default. The showcase page then renders automatically at
`/@<namespace>/<slug>` and the dataset appears in the `/search` catalog — both are
driven by the manifest, so no new page file is created.

## When to use it

Run it after [`/portaljs-new-portal`](/docs/skills/portaljs-new-portal), once per dataset you want to
publish. For geographic data you'd rather show on a map, use
[`/portaljs-add-map`](/docs/skills/portaljs-add-map) instead (or in addition).

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| Source | Yes | A local file path (`./data/file.csv`) or a public URL. |
| Portal directory | No | Path to the portal project. Defaults to the current directory. |
| Dataset name | No | Human-readable name. Defaults to the filename. |
| Description | No | Optional one-line description shown on the showcase. |
| Namespace | No | The `@`-prefixed namespace the dataset lives under (theme or owner). Defaults to a sensible value for the portal. |

**Supported formats:** CSV, TSV, JSON (array), and GeoJSON. Anything else is
rejected with a clear message to convert it first.

## How the data is routed

The skill branches on **where the data comes from** before anything else:

| Source | Default | What happens |
| ------ | ------- | ------------ |
| Local file | **R2 via Git LFS** | Moved into the repo, tracked with Git LFS (a ~134 B pointer is committed), and the bytes are pushed to Cloudflare R2 through Giftless. The manifest points at the file's absolute R2 URL, so the browser fetches it straight from R2. |
| Local file (sample) | inline | A fenced exception for bundled sample data or an OSS self-host with no R2: the file is copied into `public/data/` and stays in git. |
| Remote URL | **passthrough** | The URL is recorded as-is — no download, no upload, zero duplication. The browser fetches it directly. |
| Remote URL | adopt (opt-in) | If you want the file hosted and versioned under the portal, it's fetched and pushed to R2 like a local file. |

By default, all added data lives in **R2** — inline storage is reserved for bundled
samples. Remote URLs are left in place unless you opt to adopt them.

> **Querying a remote URL:** serving and download always work, but in-browser
> range/DuckDB queries against a third-party URL need CORS + range support on that host.
> If you need querying and the remote lacks it, adopt the file into R2.

## Example

```
/portaljs-add-dataset ./data/air-quality.csv
```

With a name and description:

```
/portaljs-add-dataset ./data/population.csv — Auckland population by area
```

From a public URL:

```
/portaljs-add-dataset https://example.com/air-quality.csv — Air quality monitoring
```

## What it produces

- The data placed per its route: pushed to R2 via Git LFS (local files), recorded as a
  URL (remote passthrough), or copied to `public/data/<file>` (fenced sample).
- A new entry appended to the `datasets.json` manifest: `{ slug, name, description,
  file, format, namespace }`, where `file` is a bare filename (inline) or an absolute
  URL (R2 / passthrough). Existing entries are preserved.

No page file is created. The template's showcase route (`pages/[owner]/[slug].tsx`)
renders every manifest entry automatically at `/@<namespace>/<slug>`, with a `Table`
preview for tabular data, and the `/search` catalog picks it up from the same
manifest.

When it finishes:

```
✓ Dataset added: Air quality monitoring
  - Data file: public/data/air-quality.csv
  - Manifest: datasets.json (entry appended)
  - Showcase: http://localhost:3000/@environment/air-quality
```

## Where to go next

- **[`/portaljs-add-chart`](/docs/skills/portaljs-add-chart)** — add a chart to the dataset's showcase.
- **[`/portaljs-add-map`](/docs/skills/portaljs-add-map)** — show geographic data on a map.

<DocsPagination prev="/docs/skills/portaljs-new-portal" next="/docs/skills/portaljs-add-resource" />
