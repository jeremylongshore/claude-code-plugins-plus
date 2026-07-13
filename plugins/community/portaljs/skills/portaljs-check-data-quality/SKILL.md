---
name: portaljs-check-data-quality
description: Audit a local or remote tabular file (CSV/TSV) for common data quality issues — schema, nulls, types, duplicates. Read-only. Use when a dataset needs a quality check before publishing, or a showcase renders wrong (blank cells, garbled numbers, an unsortable date column) and the cause needs isolating.
allowed-tools: Bash(curl:*), Bash(awk:*), Bash(sort:*), Bash(head:*), Bash(wc:*)
version: 1.0.0
author: Datopian <hello@datopian.com>
license: MIT
compatibility: Claude Code with PortalJS portals (Next.js 14, React 18, Node 18+). Runs from any project via the plugin, a personal ~/.claude/commands install, or a portaljs clone.
tags:
  - portaljs
  - data-portal
  - data-quality
  - audit
  - csv
  - validation
---

# PortalJS — Check Data Quality

## Overview

Run a read-only quality audit of one CSV or TSV file, local or remote, and return a
structured JSON report. The audit profiles every column — null/blank counts, inferred
value types, numeric ranges, likely year/date fields — and flags duplicate rows,
duplicate values in identifier-like columns, ambiguous overlapping year columns (e.g.
`calendar year` vs `fiscal year`), and mixed-type columns. It never edits the source
file, `datasets.json`, or any other project file; it only reads the target file (a
remote URL is downloaded to a temp file that is deleted before the run ends) and
prints a report. Use it before publishing a dataset with `portaljs-add-dataset`, or to
diagnose why a showcase renders wrong.

## Prerequisites

- `python3` on `PATH` — the audit logic runs as an embedded Python script; nothing is
  installed.
- One CSV or TSV file, given as a local path or an `http`/`https` URL. Only one file
  per run.

## Instructions

The canonical, full step-by-step workflow is
[`.claude/commands/portaljs-check-data-quality.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-check-data-quality.md) —
the single source of truth. Read and follow it when executing. Summary:

1. Gather input — the file path or URL to audit. If missing, ask for it; never dead-end.
2. Resolve the source: if it's an `http`/`https` URL, download it to a temp file first;
   otherwise use the local path as given.
3. Validate the extension is `.csv` or `.tsv`. If not, or the file is missing, or the
   header row is empty, stop and surface the error JSON as-is — do not guess a fix.
4. Profile every column: null/blank counts, distinct values, sample values, inferred
   per-value type (boolean/integer/float/date/string), numeric min/max, and year
   range for columns whose name looks year-like.
5. Derive findings from the profiles — duplicate rows, missing-value ratios, invalid
   year values, mixed types, suspect negative values, duplicate identifier values, and
   ambiguous overlapping year columns — each tagged `critical`, `warning`, or `info`.
6. Assemble the JSON report (`status`, file metadata, `findings`, `recommendations`,
   `column_profiles`), print it, and clean up the temp file if one was created.
7. Relay the report to the user as-is; do not modify the source file, `datasets.json`,
   or any other project file based on the findings — that's a separate, explicit step.

## Output

A single JSON object printed to stdout:

- `status` — `ok`, `warning`, or `critical`.
- `file`, `file_name`, `source_type` (`local` or `url`), `row_count`, `column_count`.
- `findings` — structured issues, most severe first.
- `recommendations` — de-duplicated suggested next steps.
- `column_profiles` — per-column summary (nulls, blanks, distinct count, sample
  values, inferred types, numeric/year ranges).

No files are created or modified. A remote URL's temp download is removed on exit,
success or failure alike.

## Error Handling

| Symptom | Cause | Fix |
| --- | --- | --- |
| `"File ... is not available."` | Local path is wrong, or the URL download failed | Verify the path or URL is reachable and retry. |
| `"Only CSV and TSV files are supported right now."` | File extension isn't `.csv`/`.tsv` | Convert the file, or point to its tabular source instead. |
| `"... does not contain tabular headers."` | File is empty or the header row is malformed | Open the file and confirm it has a valid, non-empty header line. |
| Command hangs on a URL | Remote host is slow or blocks non-browser requests | Download the file manually and audit the local copy instead. |
| `python3: command not found` | Python 3 isn't installed or not on `PATH` | Install Python 3, or run the audit where it's available. |
| Report looks truncated in the terminal | Large report wrapped/paginated by the shell | Redirect to a file (`> report.json`) and open it separately. |

## Examples

### Example 1 — Audit a local CSV before publishing

```
/portaljs-check-data-quality ./public/data/trash.csv
```

### Example 2 — Audit a remote CSV over HTTPS

```
/portaljs-check-data-quality https://example.com/trash.csv
```

### Example 3 — Audit a TSV and save the report for review

```bash
bash scripts/check-data-quality.sh ./data/emissions.tsv > /tmp/emissions-quality.json
```

### Example 4 — Read a `critical` status report

```json
{
  "status": "critical",
  "findings": [
    { "severity": "critical", "check": "duplicate_rows", "message": "42 duplicate rows found." }
  ],
  "recommendations": ["Review and deduplicate repeated rows if they are not intentional."]
}
```
Fix the flagged rows/columns, then re-run the audit before publishing.

## Resources

- Full workflow: [`.claude/commands/portaljs-check-data-quality.md`](https://github.com/datopian/portaljs/blob/main/.claude/commands/portaljs-check-data-quality.md)
- Detailed check catalog and troubleshooting: [`references/reference.md`](references/reference.md)
- Related skills: `portaljs-add-dataset`, `portaljs-define-schema`
- Python `csv` module (parsing behavior this audit relies on): <https://docs.python.org/3/library/csv.html>
