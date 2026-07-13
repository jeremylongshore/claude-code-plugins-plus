---
name: portaljs-define-schema
description: Define a dataset's metadata profile — infer a Frictionless Table Schema from its data, add Data Package metadata (license, sources, keywords), and write it into datasets.json so the showcase renders a typed field table. Extend or customize via the L0-L3 profile ladder. Use when a registered dataset needs field types, constraints, or catalog metadata before publishing.
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(node:*), Bash(head:*)
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - schema
  - frictionless
  - metadata
  - datapackage
---

# PortalJS — Define Schema

## Overview

Define a dataset's metadata profile — the **authoring** skill for the metadata-profile
contract (`lib/metadata`). Where `portaljs-add-dataset` registers *that* a dataset exists,
this skill describes *what its data means*: infer a Frictionless **Table Schema** (fields,
types, constraints) from sampled data, add the **Data Package** fields a catalog surfaces
(title, licenses, sources, keywords), and write them onto the dataset's entry in
`datasets.json`. The showcase at `/@<namespace>/<slug>` then renders a typed field table
instead of a bare preview. The model is Frictionless-native; DCAT is a serialization layer
built on top later, not authored here.

The skill runs on a profile ladder — reach for higher levels only when needed:

| Level | What it is | When |
| --- | --- | --- |
| L0 | Default `frictionless-tabular` profile; declare schema + metadata. | Default. Standard tabular CSV/TSV. |
| L1 | L0 plus extra descriptive package fields. | Extra metadata, standard validation is fine. |
| L2 | Fully custom profile (own schema template + `validate()`). | A dataset type needing custom validation rules. |
| L3 | Multiple registered profiles, resolved per dataset. | A portal mixing dataset types. |

The skill is interactive and never dead-ends: if input is thin it interviews in short
rounds, infers defaults from the data, echoes the schema for confirmation, and accepts
"use defaults" to proceed with the inferred schema as-is.

## Prerequisites

- A scaffolded PortalJS portal with the metadata contract (`lib/metadata/types.ts`,
  `pages/[owner]/[slug].tsx`); see `portaljs-new-portal`.
- The target dataset already registered in `datasets.json` (see `portaljs-add-dataset`).
- For tabular schema inference, the dataset's CSV/TSV file present under
  `PORTAL_DIR/public/data/`. JSON/GeoJSON datasets get package metadata only — no `fields`.
- Node 18+; `tsx` optional, used for the schema-validation check.

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-define-schema.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-define-schema.md) —
the single source of truth. Read and follow it when executing. Summary:

1. Gather `PORTAL_DIR`, `DATASET` (slug or `namespace/slug`), and `LEVEL` (default `L0`)
   from input; if `DATASET` is missing, list the portal's slugs and ask.
2. Validate the portal has the metadata contract (`datasets.json`, `lib/metadata/types.ts`,
   the showcase route); proceed anyway if `lib/metadata/` predates the contract.
3. For tabular datasets, sample the header and ~50 rows from `public/data/<file>` and infer
   each field's type, constraints (`required`, `unique`, `pattern`), and a primary key.
4. Echo the inferred schema as a table for confirmation; offer to go beyond L0 only if
   warranted.
5. Ask for optional Data Package metadata: license, source(s), keywords, version.
6. Write the schema and metadata onto the dataset's entry in `datasets.json` in place,
   preserving all other fields; for L2/L3, scaffold and register a custom profile module.
7. Optionally validate the schema against the data's rows via the profile's `validate()`.
8. Verify with `npx next build`; fix malformed JSON or an invalid `FieldType` before
   reporting success.
9. Report the profile, fields, metadata set, and the showcase URL.

## Output

- **Modified:** `datasets.json` (target entry gains `profile`, `schema`, `licenses`,
  `sources`, `keywords`, `version` — unset fields omitted).
- **Created (L2/L3 only):** `lib/metadata/<profile-id>.ts`; `lib/metadata/registry.ts`
  updated with a `registerProfile(...)` call.
- **Verified:** `npx next build` succeeds.
- **Result:** `/@<namespace>/<slug>` renders a typed field table in place of a bare preview.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| Dataset not found in `datasets.json` | Wrong slug or missing `namespace/` prefix | List available slugs and re-prompt. |
| `lib/metadata/` missing | Portal predates the metadata-profile contract | Proceed anyway — schema fields are optional and ignored by older showcases. |
| No `fields` schema produced | Dataset is JSON/GeoJSON, not tabular | Expected — capture Data Package metadata only. |
| Validation reports type errors | Sampled values don't coerce to the inferred type | Relax the `type` or drop the offending `required`/`pattern` constraint. |
| `next build` fails on `datasets.json` | Stray comma or a type outside `FieldType` | Fix the JSON/type and rebuild before reporting success. |

## Examples

### Example 1 — Default L0 schema for a CSV dataset

```
/portaljs-define-schema population-2022
```
Infers fields (e.g. `country: string`, `population: integer`), drafts titles, asks for a
license and source, and writes the schema under the default `frictionless-tabular` profile.

### Example 2 — Metadata only for a GeoJSON dataset

```
/portaljs-define-schema neighborhoods-geo
```
GeoJSON has no tabular `fields`; the skill captures license, sources, and keywords onto the
entry and skips schema inference.

### Example 3 — Custom L2 profile with its own validation

```
/portaljs-define-schema co2-emissions level=L2
```
Scaffolds `lib/metadata/co2-emissions-profile.ts` with a custom `validate()`, registers it
in `lib/metadata/registry.ts`, and sets `"profile": "co2-emissions-profile"` on the entry.

## Resources

- Full workflow: [`.claude/commands/portaljs-define-schema.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-define-schema.md)
- Field-type and troubleshooting reference: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-add-dataset`, `portaljs-add-dcat`, `portaljs-check-data-quality`
- Frictionless Table Schema specification: <https://datapackage.org/standard/table-schema/>
