# Check Data Quality — Reference

Detailed reference for the `portaljs-check-data-quality` skill. The executable workflow lives in
[`.claude/commands/portaljs-check-data-quality.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-check-data-quality.md).

## Check catalog

| Check | `check` id | Severity | Trigger |
| --- | --- | --- | --- |
| Duplicate rows | `duplicate_rows` | `critical` if >5% of rows, else `warning` | Exact-match rows (all columns) appear more than once. |
| Missing values | `missing_values` | `critical` if ≥20% of rows, else `warning` | Null or blank values in a column, as a share of `row_count`. |
| Invalid year values | `invalid_year_values` | `warning` | A column whose name contains `year` or ends in `_yr` has values that aren't a 4-digit year. |
| Mixed types | `mixed_types` | `warning` | A column's sampled values classify into more than one non-numeric type (e.g. `string` and `date`). |
| Negative values | `negative_values` | `warning` | A numeric column named like `ton`/`amount`/`total`/`count`/`value`/`volume` contains negative numbers. |
| Duplicate identifier values | `duplicate_identifier_values` | `warning` | A column named `id`/`identifier`, or ending in `_id`, has non-unique non-blank values. |
| Ambiguous year columns | `ambiguous_year_columns` | `warning` | More than one column looks year-like (e.g. `calendar_year` and `fiscal_year` both present). |

Value types are inferred per-value, in this priority order: `null` → `blank` →
`boolean` (`true`/`false`/`yes`/`no`, case-insensitive) → `integer` → `float` → `date`
(tries `%Y-%m-%d`, `%Y/%m/%d`, `%m/%d/%Y`, `%d/%m/%Y`, `%Y-%m`, `%b %Y`, `%B %Y`) →
`string` (fallback). `mixed_types` only fires when the mix isn't just `integer`+`float`.

## Report format

```json
{
  "status": "ok | warning | critical",
  "file": "input as given",
  "file_name": "basename of the input",
  "source_type": "local | url",
  "resource_format": "csv | tsv",
  "row_count": 0,
  "column_count": 0,
  "findings": [
    { "severity": "warning", "check": "missing_values", "column": "email",
      "message": "12 rows are null or blank in `email`.", "value": 12, "evidence": null }
  ],
  "recommendations": ["Check missing values in `email`."],
  "column_profiles": [
    { "column": "email", "null_count": 0, "blank_count": 12, "distinct_count": 188,
      "sample_values": ["a@example.com"], "inferred_types": { "string": 200 },
      "numeric_min": null, "numeric_max": null, "year_min": null, "year_max": null }
  ]
}
```

`status` is `critical` if any finding is `critical`, `warning` if any finding exists,
`ok` otherwise. `findings` is sorted most-severe first. `recommendations` is
de-duplicated but not in any particular priority order — triage by `findings` severity
instead.

## Malformed-input error shapes

The script exits `0` with an error JSON instead of raising, so a failed run still
produces parseable output:

```json
{ "error": "File `./missing.csv` is not available.", "file": "./missing.csv" }
{ "error": "Only CSV and TSV files are supported right now.", "file": "./data.xlsx" }
{ "error": "Resource `empty.csv` does not contain tabular headers." }
```

Treat any `error` key in the response as a hard stop — there is no partial report to
salvage underneath it.

## Troubleshooting

- **Report says `ok` but the showcase still looks wrong** — this audit only checks
  schema-level issues (nulls, types, duplicates, ranges); it doesn't check rendering,
  encoding mismatches the browser silently repairs, or column-mapping bugs in the
  showcase component itself.
- **A known-duplicate column isn't flagged as an identifier** — the heuristic only
  matches column names `id`, `identifier`, or ending in `_id` (case-insensitive);
  rename the column or read `column_profiles[].distinct_count` vs `row_count` manually.
- **Numbers reported as `string` type** — thousands separators, currency symbols, or
  units embedded in the cell (e.g. `"1,204"`, `"$50"`) fail the integer/float regex;
  clean the column before re-auditing if the numeric checks matter.
- **`year_min`/`year_max` both `null` despite a real year column** — the column name
  doesn't contain `year` or end in `_yr`; the year heuristic is name-based, not
  content-based.
