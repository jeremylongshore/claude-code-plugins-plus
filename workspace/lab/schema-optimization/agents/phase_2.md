# Phase 2 Agent: Field Utilization Analysis

**Contract:** This agent analyzes field usage patterns to identify unused or low-utilization fields.

## Inputs (JSON)

```json
{
  "skill_dir": "/absolute/path/to/.claude/skills/schema-optimization",
  "session_dir": "/absolute/path/to/session/directory",
  "reference_path": "/absolute/path/to/references/02-phase-2.md",
  "phase1_report_path": "/absolute/path/to/01-initial-schema-analysis.md",
  "input_folder": "/path/to/bigquery/export"
}
```

## Task Instructions

1. **Read reference document**: Load instructions from `reference_path`
2. **Review Phase 1 output**: Read `phase1_report_path` for context
3. **Analyze field utilization**:
   - Identify fields with null values > 90%
   - Detect fields never queried or referenced
   - Calculate utilization percentages
   - Group findings by impact level
4. **Generate recommendations**: Suggest fields for removal or archival
5. **Write report**: Save markdown report to `<session_dir>/02-field-utilization-analysis.md`
6. **Return JSON**: Output strict JSON with no terminal text

## Output Format (JSON Only)

```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/session_dir/02-field-utilization-analysis.md",
  "utilization_summary": {
    "unused_fields": [
      {"table": "table_name", "field": "field_name", "null_pct": 100}
    ],
    "low_utilization_fields": [
      {"table": "table_name", "field": "field_name", "null_pct": 95}
    ],
    "recommendations": [
      "Remove unused fields from table X",
      "Archive low-utilization fields to cold storage"
    ]
  }
}
```

## Validation Requirements

- `status` must be "complete"
- `report_path` must be an absolute path to an existing file
- `utilization_summary.unused_fields` must be an array
- `utilization_summary.low_utilization_fields` must be an array
- `utilization_summary.recommendations` must be an array (can be empty)

## Error Handling

If analysis fails, return:
```json
{
  "status": "error",
  "error_message": "Description of what went wrong",
  "report_path": null,
  "utilization_summary": null
}
```
