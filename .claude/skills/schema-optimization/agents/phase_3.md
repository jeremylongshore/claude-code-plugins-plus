# Phase 3 Agent: Impact Assessment

**Contract:** This agent evaluates the impact of proposed schema changes on systems, queries, and costs.

## Inputs (JSON)

```json
{
  "skill_dir": "/absolute/path/to/.claude/skills/schema-optimization",
  "session_dir": "/absolute/path/to/session/directory",
  "reference_path": "/absolute/path/to/references/03-phase-3.md",
  "phase1_report_path": "/absolute/path/to/01-initial-schema-analysis.md",
  "phase2_report_path": "/absolute/path/to/02-field-utilization-analysis.md",
  "input_folder": "/path/to/bigquery/export"
}
```

## Task Instructions

1. **Read reference document**: Load instructions from `reference_path`
2. **Review previous phases**: Read Phase 1 and Phase 2 reports for context
3. **Assess impact**:
   - Categorize changes by risk level (high/medium/low)
   - Estimate storage savings per change
   - Identify dependent queries and systems
   - Calculate migration complexity
4. **Generate impact matrix**: Risk vs. savings analysis
5. **Write report**: Save markdown report to `<session_dir>/03-impact-assessment.md`
6. **Return JSON**: Output strict JSON with no terminal text

## Output Format (JSON Only)

```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/session_dir/03-impact-assessment.md",
  "impact_summary": {
    "high_risk_changes": [
      {"change": "Remove field X", "reason": "Used in production queries"}
    ],
    "medium_risk_changes": [
      {"change": "Archive field Y", "reason": "Used in monthly reports"}
    ],
    "low_risk_changes": [
      {"change": "Remove field Z", "reason": "No known dependencies"}
    ],
    "estimated_savings": {
      "storage_gb": 150.5,
      "monthly_cost_usd": 45.25,
      "query_cost_reduction_pct": 12.5
    }
  }
}
```

## Validation Requirements

- `status` must be "complete"
- `report_path` must be an absolute path to an existing file
- All `*_risk_changes` arrays must exist (can be empty)
- `estimated_savings` must contain numeric values
- Risk categorization must be evidence-based

## Error Handling

If analysis fails, return:
```json
{
  "status": "error",
  "error_message": "Description of what went wrong",
  "report_path": null,
  "impact_summary": null
}
```
