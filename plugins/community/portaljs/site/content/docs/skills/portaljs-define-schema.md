---
metatitle: /portaljs-define-schema – Author a Dataset's Frictionless Metadata Profile
metadescription: The /portaljs-define-schema skill infers a Frictionless Table Schema from your data, adds Data Package metadata (license, sources, keywords), and writes it into datasets.json so the showcase renders a typed field reference. Extend or customize via the L0→L3 profile ladder.
title: /portaljs-define-schema
description: Describe what a dataset's data means — infer a Frictionless Table Schema from the file, add license/source/keyword metadata, and surface a typed field table on the showcase.
---

`/portaljs-define-schema` is the **authoring** skill for the metadata-profile contract. Where
[`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset) registers *that a dataset exists*, this skill
describes *what its data means*: it infers a Frictionless **Table Schema** (fields, types,
constraints) from the data, adds the **Data Package** descriptor fields a catalog surfaces
(title, licenses, sources, keywords), and writes them onto the dataset's entry in
`datasets.json`. The showcase at `/@<namespace>/<slug>` then renders a typed
column/description table instead of a bare preview.

The model is **Frictionless-native**. DCAT / DCAT-AP is a serialization layer on top
(designed-in at `lib/metadata/dcat.ts`, built in the later DCAT-interop phase) — this skill
authors the native model, not the export.

It's interactive and never dead-ends: if your brief is thin it lists your datasets, infers
a schema from the data, echoes it for confirmation, and lets you reply "use defaults" to
accept the inferred schema as-is.

## When to use it

Run it after [`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset), once a dataset is in the catalog
and you want its showcase to document the columns — their types, meaning, and constraints —
and carry proper license/source metadata. Skip it for a quick throwaway preview; reach for
it when the dataset is something other people will read or reuse.

## The profile ladder

Most datasets want **L0**. Higher levels are there when you need them.

| Level | What it is | When |
| ----- | ---------- | ---- |
| **L0** | The default `frictionless-tabular` profile; just declare the dataset's schema + metadata. | Default. Standard tabular CSV/TSV. |
| **L1** | Extend L0 with extra package fields. | Need more descriptive metadata, standard validation is fine. |
| **L2** | A fully custom profile (own `schema` + `validate()`) in `lib/metadata`. | A dataset type with validation rules L0 doesn't express. |
| **L3** | Multiple profiles in the registry, resolved per dataset by its `profile` field. | A portal mixing dataset types, each with its own profile. |

See the [metadata contract README](https://github.com/datopian/portaljs/blob/main/examples/portaljs-catalog/lib/metadata/README.md)
for the ladder in full.

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| Dataset | No | Which dataset (slug or `namespace/slug`). Asked — with a list — if missing. |
| Portal directory | No | Defaults to the current directory. |
| Level | No | Defaults to **L0**; the skill offers to go higher only when warranted. |

Nothing is required — with no input it lists your datasets and asks which to describe.

## What it produces

- A **Frictionless Table Schema** inferred from the data — one field per column with an
  inferred `type`, drafted `title`/`description`, and `constraints` (`required`, `unique`,
  `pattern`, `primaryKey`) — confirmed with you before writing.
- **Data Package metadata** — `licenses`, `sources`, `keywords`, `version` — captured in a
  short optional prompt.
- An **updated `datasets.json`**: the schema + metadata written onto the dataset's entry in
  place, matching the extended `Dataset` shape. For L2/L3, a custom profile module in
  `lib/metadata` plus its registration.
- A **typed field table** on the `/@<namespace>/<slug>` showcase, replacing the bare preview.

## Example

```
/portaljs-define-schema population-2022
```

The skill reads `public/data/population-2022.csv`, infers the fields (e.g.
`country: string`, `population: integer`), drafts titles and descriptions, asks for a
license and source, writes the schema + metadata onto the `population-2022` entry under the
default `frictionless-tabular` profile, validates it against the rows, verifies the build,
and reports the showcase URL. With no arguments it lists the datasets and asks which to
describe.

## Where to go next

- **[`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset)** — add another dataset to describe.
- **[`/portaljs-architect`](/docs/skills/portaljs-architect)** — decide the metadata strategy (Frictionless,
  extended, custom, or multi-profile + DCAT) before authoring.

<DocsPagination prev="/docs/skills/portaljs-migrate" next="/docs/skills/portaljs-check-data-quality" />
