---
name: portaljs-add-dataset
description: Add a dataset (CSV, TSV, JSON, or GeoJSON) to an existing PortalJS portal. Appends an entry to datasets.json so the catalog and showcase render it automatically; routes the data by source (local file vs remote URL) — R2 via Git LFS by default, remote URLs by passthrough. Use when registering a new dataset in a scaffolded portal.
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(git:*), Bash(curl:*), Bash(mkdir:*), Bash(cp:*), WebFetch
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - dataset
  - csv
  - geojson
  - catalog
---

# PortalJS — Add Dataset

## Overview

Register a dataset in a PortalJS (`portaljs-catalog`) portal. The skill appends one entry to
`datasets.json` — the single source of truth for the catalog — and routes the underlying
bytes by **source first, then size**: a local file defaults to R2 via Git LFS, a remote URL
defaults to passthrough (no copy). No per-dataset page is created; the catalog at `/search`
lists the new entry and the dynamic showcase route `pages/[owner]/[slug].tsx` renders it
automatically at `/@<namespace>/<slug>`. Supported formats for the showcase preview: CSV,
TSV, JSON (array), and GeoJSON.

## Prerequisites

- A scaffolded PortalJS portal (see `portaljs-new-portal`) with `datasets.json`,
  `package.json`, and `pages/[owner]/[slug].tsx` present.
- The source data: a local file path or a publicly reachable URL.
- For the R2/Git LFS default route: `git` and `git-lfs` installed, and an Arc account token
  (or an OSS Giftless key) to mint a push-scoped LFS credential.
- Node 18+ and npm available in the portal directory.

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-add-dataset.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-dataset.md) —
the single source of truth. Read and follow it when executing. Summary:

1. Gather input from `$ARGUMENTS` — source (file path or URL), portal directory (default
   `.`), dataset name/slug, description, namespace. If the source is missing, interview the
   user; never dead-end.
2. Validate the portal directory: confirm `datasets.json`, `package.json`, and
   `pages/[owner]/[slug].tsx` exist.
3. Detect the format from the file extension, URL extension, or `Content-Type` header
   (CSV, TSV, JSON array, or GeoJSON); reject anything else and ask for a conversion.
4. Route the data by source: remote URL → passthrough (default) or adopt into R2 (opt-in);
   local file → R2 via Git LFS (default) or inline into `public/data/` (fenced exception for
   bundled samples or an OSS-no-R2 fallback).
5. Append one entry to `datasets.json` — `slug`, `namespace`, `name`, `description`, `file`
   (the routed path/URL), `format` — keeping `(namespace, slug)` unique.
6. Verify the build with `npx next build`; fix errors (commonly malformed JSON) before
   reporting success.
7. Report the route taken, the manifest change, and the showcase URL.

## Output

- **Modified:** `datasets.json` (one entry appended).
- **Created (route-dependent):** `data/<slug>.<ext>` tracked via Git LFS (R2 default), or
  `public/data/<slug>.<ext>` (inline exception). Nothing is created for remote passthrough.
- **Verified:** `npx next build` passes.
- **Result:** the dataset appears in `/search` and renders at `/@<namespace>/<slug>`.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| Fetch fails for a URL source | Non-200 status or unreachable host | Report the HTTP status and ask the user to confirm the URL is publicly accessible. |
| "Not a portaljs-catalog portal" | `datasets.json` missing | This is an older single-page template; ask the user how to proceed rather than failing silently. |
| Unsupported format | Extension/content-type isn't csv/tsv/json/geojson | Ask the user to convert the source before continuing. |
| `git lfs push` has nothing to stream | `git lfs install --local` never ran, so raw bytes were committed instead of a pointer | Run `git lfs install --local` before `git lfs track`, re-add and re-commit the file. |
| R2 PUT returns 400 | A broad `http.extraHeader` was set and replayed onto the presigned URL | Use the `_jwt` Basic-auth piggyback in `lfs.url` only — never a global `http.extraHeader`. |
| `(namespace, slug)` clash | Another entry already uses that pair | Ask the user for a different slug or namespace. |
| `next build` fails | Malformed JSON in `datasets.json` | Print the build log, fix the JSON, rebuild before reporting success. |

## Examples

### Example 1 — Local CSV, default R2 route

```
/portaljs-add-dataset ./data/co2-emissions.csv namespace=climate
```
Moves the file into `data/`, tracks it with Git LFS, pushes it to R2, and appends a manifest
entry whose `file` is the resulting `https://data.portaljs.com/...` URL.

### Example 2 — Remote URL, passthrough (no download)

```
/portaljs-add-dataset https://example.org/open-data/trade.csv namespace=trade
```
Detects the format from the response headers and records the URL as-is in `datasets.json` —
no bytes are copied.

### Example 3 — GeoJSON adopted into R2

```
/portaljs-add-dataset https://example.org/boundaries.geojson namespace=reference adopt=true
```
Downloads the file, then routes it as a local file through the Git LFS → R2 path so it is
hosted and versioned under the portal (useful when in-browser range queries are needed).

### Example 4 — Bundled sample data, inline exception

```
/portaljs-add-dataset ./samples/demo.csv namespace=reference
```
When the portal has no R2 credentials (OSS self-host) or the file is bundled sample data,
the skill copies it into `public/data/` instead, per the `.gitattributes` inline fence.

## Resources

- Full workflow: [`.claude/commands/portaljs-add-dataset.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-dataset.md)
- Manifest fields and routing details: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-new-portal`, `portaljs-add-chart`, `portaljs-add-map`, `portaljs-define-schema`
- Git LFS documentation: <https://git-lfs.com/>
