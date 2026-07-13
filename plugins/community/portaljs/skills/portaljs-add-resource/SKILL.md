---
name: portaljs-add-resource
description: Add another file (resource) to an EXISTING dataset in a PortalJS portal — a data dictionary, methodology, or an additional data file. Turns a single-file dataset into a multi-resource one; the showcase renders a section per resource. Use when a dataset needs a second file, such as a data dictionary, methodology doc, or an additional period's data.
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Bash(mkdir:*), Bash(cp:*), WebFetch
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - resource
  - data-dictionary
  - metadata
  - catalog
---

# PortalJS — Add Resource

## Overview

Add a resource — an additional file — to a dataset that already exists in a
`portaljs-catalog` portal. Where `/portaljs-add-dataset` creates a **new** dataset
(one file), this skill adds a file to an **existing** one: a data dictionary, a
methodology document, or another data file (e.g. a second year's figures).

Mirrors the Frictionless Data Package model: a dataset holds a `resources[]` array,
and the showcase at `/@<namespace>/<slug>` renders one section per resource (preview,
schema, download). A single-file dataset migrates to `resources[]` automatically the
first time a second file is added — no data is lost.

## Prerequisites

- An existing PortalJS portal (`portaljs-catalog` template) with `datasets.json`,
  `package.json`, and `pages/[owner]/[slug].tsx` present.
- The target dataset already registered in `datasets.json`.
- The new resource's source: a local file path or a public URL, in CSV, TSV, JSON
  (array), or GeoJSON format.
- Node 18+ installed to run `npx next build` for verification.

## Instructions

The canonical, full step-by-step workflow lives in
[`.claude/commands/portaljs-add-resource.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-resource.md)
in this repository — that file is the single source of truth. Read and follow it. Summary:

1. Gather input (interview if thin): `DATASET` (slug or `namespace/slug`), `SOURCE`
   (path or URL), `PORTAL_DIR` (default `.`), `RESOURCE_NAME`, `RESOURCE_TITLE`,
   `DESCRIPTION`. If `DATASET` or `SOURCE` is missing, list datasets from
   `datasets.json` and ask.
2. Validate the portal and locate the dataset entry by slug (and namespace, if
   given). If the dataset does not exist, offer `/portaljs-add-dataset` instead.
3. Detect the format from extension/Content-Type, fetch (check HTTP status) or
   confirm the local path exists, then copy into `PORTAL_DIR/public/data/` under a
   non-colliding filename.
4. Update `datasets.json`: if the dataset has no `resources` yet, migrate its
   top-level `file`/`format`/`schema` into the first resource (lossless), then
   append the new resource; if `resources` already exists, just append, keeping
   `name` unique within the array.
5. Verify the build with `npx next build`, capturing output to a log file; fix
   malformed JSON before reporting success.
6. Report the outcome (see Output below).

## Output

```
✓ Resource added to DATASET: RESOURCE_TITLE (RESOURCE_NAME.EXT)
  - Data file: public/data/RESOURCE_NAME.EXT
  - Manifest:  datasets.json (dataset now has <n> resources)
  - Showcase:  /@<namespace>/<slug> renders a section per resource
```

If this was the first migration to multi-resource, note that the dataset's single
`file` was moved into `resources[]` with no data lost.

## Error Handling

| Symptom | Cause | Fix |
|---|---|---|
| "Dataset not found" | `DATASET` slug/namespace doesn't match any entry in `datasets.json` | List datasets from `datasets.json` and ask the user to pick, or run `/portaljs-add-dataset` to create it |
| `npx next build` fails with a JSON parse error | Manually edited `datasets.json` has a trailing comma or unescaped character | Re-open the file, fix the JSON, and rebuild before reporting success |
| Resource file fails to fetch (non-2xx) | `SOURCE` URL is wrong, private, or the host is down | Confirm the URL in a browser or with `curl -I SOURCE`; ask for a corrected URL or a local path |
| New resource's filename collides with an existing one in `/public/data` | Auto-derived `RESOURCE_NAME` matches an existing file stem | Pick a distinct `RESOURCE_NAME`, or let the skill append a numeric suffix |
| Showcase doesn't render the new section after build | `name` in the new resource object duplicates an existing resource's `name` | Rename the resource's `name` to something unique within that dataset's `resources[]` |

## Examples

### Example 1 — Add a data dictionary to a single-file dataset

```
/portaljs-add-resource orders ./data/orders-data-dictionary.csv --title "Data dictionary"
```
`orders` was a single CSV. It is migrated to a two-resource dataset (the original
data plus the dictionary), and its showcase now renders a section for each.

### Example 2 — Add a resource by URL to a dataset that already has resources

```
/portaljs-add-resource climate-observations https://example.org/data/methodology.json --name methodology --title "Methodology notes"
```
The skill fetches the URL, checks the HTTP status, copies it to
`public/data/methodology.json`, and appends it to the existing `resources[]` array.

### Example 3 — Run with no arguments (interview mode)

```
/portaljs-add-resource
```
With no arguments, the skill lists datasets from `datasets.json`, asks which one to
extend and for the new file's path or URL, then proceeds through steps 2-6 above.

## Resources

- [`.claude/commands/portaljs-add-resource.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-resource.md) — canonical workflow this skill follows
- [`references/reference.md`](references/reference.md) — resource entry fields, single-to-multi-resource layout, troubleshooting
- Related skills: `/portaljs-add-dataset` (create a new dataset), `/portaljs-define-schema` (describe a resource's fields)
- [Frictionless Data — Data Package resources](https://datapackage.org/standard/data-resource/) — the data model this feature mirrors
