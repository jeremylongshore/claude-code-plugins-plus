# Phase 1 Reference: Initial Schema Analysis

## Context

This phase establishes the baseline understanding of the database schema. You will analyze exported schema files to identify the structure, data types, and potential issues that will inform later optimization phases.

This is the foundation - later phases build on the metrics and findings you establish here.

## Inputs Available

- `skill_dir`: Absolute path to the schema-optimization skill directory
- `session_dir`: Absolute path to this workflow run's session directory
- `input_folder`: Path to directory containing BigQuery schema export files (JSON/CSV)
- `extraction_type`: Type of data format (e.g., "bigquery_json")

## Step-by-Step Procedure

### Step 1: Scan Input Directory

List all files in `input_folder`:

```bash
ls -lh <input_folder>/
```

Identify:
- File count
- File types (JSON, CSV, other)
- Total size
- Naming patterns

### Step 2: Parse Schema Files

For each JSON file in `input_folder`:

**If BigQuery JSON format:**
- Extract table name (from filename or JSON structure)
- Parse schema array to get field definitions
- For each field, extract:
  - Field name
  - Data type (STRING, INTEGER, FLOAT, TIMESTAMP, etc.)
  - Mode (NULLABLE, REQUIRED, REPEATED)
  - Description (if present)

**If CSV format:**
- First row should contain headers
- Subsequent rows contain table/field definitions

### Step 3: Calculate Metrics

Aggregate across all files:

```
total_tables = count of unique table names
total_fields = sum of fields across all tables
```

Analyze data types:
```
- Count STRING fields
- Count INTEGER fields
- Count TIMESTAMP fields
- Count other types
```

Analyze nullability:
```
- Count NULLABLE fields
- Count REQUIRED fields
- Calculate nullable_pct = (nullable / total_fields) * 100
```

### Step 4: Identify Patterns

Look for:

**Naming conventions:**
- Do tables have prefixes? (e.g., `dim_`, `fact_`, `staging_`)
- Do fields follow patterns? (e.g., `id`, `created_at`, `updated_at`)
- Are there legacy patterns? (e.g., `old_`, `deprecated_`, `legacy_`)

**Common field names:**
- How many tables have `id` field?
- How many have `created_at` / `updated_at`?
- How many have `deleted_at` (soft deletes)?

**Data type anomalies:**
- Are there STRING fields that should be INTEGER/TIMESTAMP?
- Are there overly wide types? (e.g., STRING when ENUM would work)

### Step 5: Flag Potential Issues

Identify:

**Duplicate schemas:**
- Do multiple tables have identical field lists?
- Are there near-duplicates (80%+ overlap)?

**Naming inconsistencies:**
- Same concept with different names (e.g., `user_id` vs `userId` vs `uid`)
- Misspellings or typos

**Deprecated patterns:**
- Fields with names like `old_`, `legacy_`, `deprecated_`
- NULL descriptions where they should exist

### Step 6: Write Report

Save to: `{session_dir}/01-initial-schema-analysis.md`

**Required sections:**

```markdown
# Phase 1: Initial Schema Analysis

**Session:** <session_id from session_dir>
**Generated:** <timestamp>
**Input:** <input_folder>
**Extraction Type:** <extraction_type>

---

## Executive Summary

- Analyzed N tables with M total fields
- Identified X naming patterns
- Found Y potential issues
- Z% of fields are nullable

---

## Methodology

Parsed schema files from <input_folder> using <extraction_type> format.
Extracted field definitions, analyzed patterns, calculated metrics.

---

## Schema Overview

### Tables
- Total tables: N
- Table size range: X-Y fields per table
- Average fields per table: Z

### Fields
- Total fields across all tables: M
- NULLABLE fields: X (Y%)
- REQUIRED fields: A (B%)

### Data Types
| Type | Count | Percentage |
|------|-------|------------|
| STRING | X | Y% |
| INTEGER | X | Y% |
| FLOAT | X | Y% |
| TIMESTAMP | X | Y% |
| BOOLEAN | X | Y% |
| Other | X | Y% |

---

## Naming Patterns

### Table Prefixes
- `dim_`: X tables (dimension tables)
- `fact_`: Y tables (fact tables)
- `staging_`: Z tables (staging tables)
- No prefix: W tables

### Common Field Names
- `id`: Present in X/N tables (Y%)
- `created_at`: Present in X/N tables (Y%)
- `updated_at`: Present in X/N tables (Y%)
- `deleted_at`: Present in X/N tables (Y%)

---

## Issues Identified

### 1. Potential Duplicates
- Tables A and B have identical schemas (X fields match exactly)

### 2. Naming Inconsistencies
- User ID field has 3 variants: `user_id` (X tables), `userId` (Y tables), `uid` (Z tables)

### 3. Legacy/Deprecated Fields
- Found N fields with naming patterns suggesting deprecation:
  - `legacy_field_name` in table X
  - `old_column_name` in table Y

---

## Key Findings (Machine-Readable)

```json
{
  "total_tables": N,
  "total_fields": M,
  "nullable_pct": X.Y,
  "table_prefixes": {
    "dim_": X,
    "fact_": Y,
    "staging_": Z
  },
  "common_fields": {
    "id": X,
    "created_at": Y,
    "updated_at": Z
  },
  "issues_count": N
}
```

---

## Recommendations for Phase 2

- Focus field utilization analysis on NULLABLE fields (X% of total)
- Investigate duplicate schemas (tables A and B)
- Check if legacy/deprecated fields are actually unused
- Analyze STRING fields for potential type optimization

---

*Generated by Phase 1 Agent*
*Report Path: 01-initial-schema-analysis.md*
```

### Step 7: Return JSON

Return ONLY the following JSON (no explanatory text):

```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/session_dir/01-initial-schema-analysis.md",
  "schema_summary": {
    "total_tables": 0,
    "total_fields": 0,
    "key_findings": [
      "Finding 1: Description",
      "Finding 2: Description",
      "Finding 3: Description"
    ]
  }
}
```

**CRITICAL:**
- Write report file BEFORE returning JSON
- Use absolute path for report_path
- Include all required keys in schema_summary
- status must be "complete" (or "error" if failed)

## Quality Checklist

Before returning JSON, verify:
- [ ] Report file exists on disk
- [ ] All tables were scanned
- [ ] Metrics are accurate (manually verify sample)
- [ ] Key findings are evidence-based (cite specific examples)
- [ ] Machine-readable JSON block is valid
- [ ] Recommendations for Phase 2 are actionable

## Error Handling

If you encounter errors:

**Cannot read input files:**
```json
{
  "status": "error",
  "error_message": "Failed to read files in input_folder: <details>",
  "report_path": null,
  "schema_summary": null
}
```

**Invalid schema format:**
```json
{
  "status": "error",
  "error_message": "Schema files not in expected format: <details>",
  "report_path": null,
  "schema_summary": null
}
```

**No files found:**
```json
{
  "status": "error",
  "error_message": "No schema files found in input_folder",
  "report_path": null,
  "schema_summary": null
}
```

---

*This reference doc provides step-by-step instructions for Phase 1 agents.*
