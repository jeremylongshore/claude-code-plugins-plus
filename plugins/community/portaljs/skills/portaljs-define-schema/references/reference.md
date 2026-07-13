# Define Schema — Reference

Detailed reference for the `portaljs-define-schema` skill. The executable workflow lives in
[`.claude/commands/portaljs-define-schema.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-define-schema.md).

## The L0-L3 profile ladder

| Level | Schema source | Validation | Registered in `lib/metadata` |
| --- | --- | --- | --- |
| L0 | Default `frictionless-tabular` profile; schema declared per dataset. | Type-coercion + the constraint subset (`required`, `unique`, `pattern`, `enum`, min/max). | No — built in. |
| L1 | Same as L0, plus extra `PackageMetadata` fields (`keywords`, `sources`, `version`, ...). | Same as L0. | No — built in. |
| L2 | A custom profile module with its own pinned `schema` and `validate()`. | Whatever rules the profile implements. | Yes — `registerProfile()` once. |
| L3 | Multiple custom (or built-in) profiles, resolved per dataset by its `profile` id. | Per-profile, dispatched by `getProfile(id)`. | Yes — each profile registered. |

`getProfile(id)` falls back to the default `frictionless-tabular` profile for any
unrecognized id, so a dataset never fails to render for lacking a profile.

## Frictionless field types (`FieldType`)

Source: `lib/metadata/types.ts`. Use exactly these values in `schema.fields[].type` —
anything else fails the `next build` type check.

| Type | Inferred when | Notes |
| --- | --- | --- |
| `string` | Default / ambiguous or empty column. | Never guess a narrower type from a sparse sample. |
| `integer` | Every sampled value matches `^[+-]?\d+$`. | |
| `number` | Numeric but not all integer. | |
| `year` | All sampled values are 4 digits. | Distinct from `integer` for calendar years. |
| `boolean` | true/false, yes/no, 0/1. | |
| `date` / `datetime` | `Date.parse`-able. | Set `format` for a non-ISO pattern. |
| `time` | Time-only values. | |
| `yearmonth` | `YYYY-MM`. | |
| `duration` | ISO 8601 duration. | Rare in flat CSV data. |
| `geopoint` | `"lon, lat"` pairs. | |
| `geojson` | Embedded GeoJSON geometry per row. | Rare for CSV; typical for JSON datasets. |
| `object` / `array` | Structured cell content (JSON datasets). | |
| `any` | Explicitly untyped by choice. | Use sparingly — defeats the point of a schema. |

Constraints (`FieldConstraints`): `required`, `unique`, `enum`, `minimum`, `maximum`,
`minLength`, `maxLength`, `pattern` — a subset of the full Frictionless constraint
vocabulary chosen so an L0 catalog can check them against a loaded CSV without a full
validator library.

## Data Package fields written to `datasets.json`

`licenses[]` (`{ name, title, path }`), `sources[]` (`{ title, path, email }`),
`keywords[]`, `version`, `created`/`modified` (ISO 8601). All optional — a dataset with
none still lists, previews, and renders; the showcase just omits the schema table.

## Troubleshooting

- **Inferred type looks wrong** — the ~50-row sample may not represent the full column
  (e.g. a numeric ID column with a stray blank early on inferring `string`). Correct it
  in the confirmation step before writing.
- **`profile` id doesn't resolve to a custom L2/L3 module** — confirm
  `registerProfile(...)` was added to `lib/metadata/registry.ts` and runs at app
  bootstrap, not just defined in the profile file.
- **Schema written but showcase still shows a bare preview** — check the portal predates
  the metadata contract (`lib/metadata/` absent); the fields are written but the older
  showcase route doesn't read them yet.
- **Want DCAT / open-data harvesting** — don't hand-write DCAT here. `toDCAT`/`fromDCAT`
  in `lib/metadata/dcat.ts` are the interop layer; see `portaljs-add-dcat`.
