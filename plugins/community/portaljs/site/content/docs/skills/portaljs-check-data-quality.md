---
metatitle: /portaljs-check-data-quality – Audit a Tabular Dataset for Quality Issues
metadescription: The /portaljs-check-data-quality skill runs a read-only audit of a CSV or TSV file — local or remote — flagging null and blank values, duplicate rows, mixed-type columns, suspect numerics, and date-field problems, and returns a structured JSON report with findings and recommendations.
title: /portaljs-check-data-quality
description: Audit a tabular file (CSV/TSV) for common data quality problems — nulls, duplicates, mixed types, suspect numerics, date issues — and get a structured report before you publish it.
---

`/portaljs-check-data-quality` is the **auditing** skill for the dataset contract. Before you
add a file to the catalog with [`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset) or
describe it with [`/portaljs-define-schema`](/docs/skills/portaljs-define-schema), this skill
looks at the data itself and reports what's wrong with it — missing values, duplicate rows,
columns whose types don't line up, numbers that look like errors, and date fields that won't
sort. It **reads**; it never edits the file or the catalog.

It accepts one CSV or TSV at a time, by local path or `http`/`https` URL, and returns a
structured JSON report you can act on — or hand to `/portaljs-define-schema` to bake the
findings into a schema.

## When to use it

Run it when you're about to publish a dataset other people will read or reuse, and you want
to know what to fix first — or when a showcase looks wrong (blank cells, garbled numbers, a
date column that won't sort) and you need to find the cause. Skip it for a quick throwaway
preview. It only runs when you explicitly ask to check or audit data quality.

## What it checks

- row count, and null / blank values per column
- duplicate rows, and duplicate values in likely identifier columns
- numeric ranges (min/max) and negative values where they're suspect
- likely year / date field quality
- ambiguous overlapping year columns (e.g. `calendar year` vs `fiscal year`)
- mixed-type columns, inferred from sampled values

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| File | Yes | One CSV or TSV, as a local path or an `http`/`https` URL. |
| `python3` | Yes | Used to run the audit; the skill is read-only and installs nothing. |

## Example

```
/portaljs-check-data-quality ./public/data/trash.csv
```

The skill profiles the file and returns a JSON report:

- `status` — `ok`, `warning`, or `critical`
- `file`, `file_name`, `source_type`, `row_count`, `column_count`
- `findings` — the structured issues it found
- `recommendations` — suggested next steps
- `column_profiles` — a per-column summary

A remote file works the same way:

```
/portaljs-check-data-quality https://example.com/trash.csv
```

## Where to go next

- **[`/portaljs-define-schema`](/docs/skills/portaljs-define-schema)** — turn the findings into a
  typed Frictionless schema with the right constraints.
- **[`/portaljs-add-dataset`](/docs/skills/portaljs-add-dataset)** — add the cleaned dataset to the
  catalog.

<DocsPagination prev="/docs/skills/portaljs-define-schema" next="/docs/skills/portaljs-deploy" />
