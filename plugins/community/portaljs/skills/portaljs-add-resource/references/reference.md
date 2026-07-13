# PortalJS — Add Resource Reference

Companion reference for the
[`/portaljs-add-resource`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-add-resource.md) command —
the command file is the single source of truth for the step-by-step workflow; this page
covers the data shapes and troubleshooting detail that don't fit inline.

## Resource entry fields

Each object in a dataset's `resources[]` array (see `Resource` in `lib/providers/types.ts`):

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Short id, unique within the dataset's `resources[]`; used as the showcase section key/anchor |
| `path` | yes | Relative path under `/public/data`, e.g. `orders-data-dictionary.csv` |
| `format` | yes | `csv`, `tsv`, `json`, or `geojson` — detected from extension/Content-Type |
| `title` | recommended | Human-readable heading shown in the showcase section |
| `description` | optional | One-line summary; omit only if there genuinely is none |
| `schema` | optional | Frictionless Table Schema for this resource's fields — see `/portaljs-define-schema` |

Package-level fields (`description`, `keywords`, `licenses`, `sources`, `version`, …) stay
on the dataset object, not on individual resources.

## Single-file to multi-resource migration

A dataset starts as a flat, single-file shape:

```json
{ "slug": "orders", "name": "Orders", "file": "orders.csv", "format": "csv", "schema": { ... } }
```

Adding a second resource migrates it losslessly into `resources[]` — the original file
becomes the first resource, and the top-level `file`/`format`/`schema` are removed:

```json
{
  "slug": "orders",
  "name": "Orders",
  "resources": [
    { "name": "data", "path": "orders.csv", "format": "csv", "title": "Orders", "schema": { ... } },
    { "name": "data-dictionary", "path": "orders-data-dictionary.csv", "format": "csv", "title": "Data dictionary" }
  ]
}
```

Datasets that already have `resources[]` simply get the new object appended. No page code
changes: `getResources()` (`lib/datasets.ts`) reads the array and the showcase at
`/@<namespace>/<slug>` renders one section per resource automatically.

## Troubleshooting

- **Build fails after editing `datasets.json` by hand.** Run the JSON through a linter or
  `node -e "JSON.parse(require('fs').readFileSync('datasets.json'))"` to find the syntax
  error before rebuilding.
- **New section doesn't show up in the showcase.** Confirm the resource's `name` is unique
  within that dataset's `resources[]` — a duplicate silently overwrites the anchor.
- **Wrong format detected for a URL source.** Content-Type sniffing can be wrong for
  misconfigured servers; pass an explicit extension in the destination filename to force
  the format.
- **Large resource files.** Files over a few MB slow down client-side preview; note this
  in the dataset page and consider CKAN's `datastoreConfig` for server-side pagination
  instead of a static file.
