# Phase 4 Agent: Verification with Script

**Contract:** This agent runs automated verification scripts to validate Phase 2-3 conclusions with empirical data.

## Inputs (JSON)

```json
{
  "skill_dir": "/absolute/path/to/.claude/skills/schema-optimization",
  "session_dir": "/absolute/path/to/session/directory",
  "reference_path": "/absolute/path/to/references/04-phase-4-verify-with-script.md",
  "phase2_report_path": "/absolute/path/to/02-field-utilization-analysis.md",
  "phase3_report_path": "/absolute/path/to/03-impact-assessment.md",
  "input_folder": "/path/to/bigquery/export",
  "script_path": "/absolute/path/to/scripts/analyze_field_utilization.sh",
  "output_folder_path": "/path/to/script/output"
}
```

## Task Instructions

1. **Read reference document**: Load instructions from `reference_path`
2. **Review Phase 2-3 outputs**: Read previous reports to understand claims
3. **Run verification script**: Execute `script_path` with appropriate arguments
4. **Analyze script output**: Compare script findings vs. manual analysis
5. **Reconcile differences**:
   - Confirm conclusions that match
   - Revise conclusions where script findings differ
   - Document unexpected findings
6. **Generate revised action items**: Update recommendations based on script evidence
7. **Write report**: Save markdown report to `<session_dir>/04-field-utilization-verification.md`
8. **Return JSON**: Output strict JSON with no terminal text

## Output Format (JSON Only)

```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/session_dir/04-field-utilization-verification.md",
  "verification_summary": {
    "files_analyzed": 42,
    "conclusions_confirmed": [
      "Field X.unused: 100% null rate confirmed by script"
    ],
    "conclusions_revised": [
      "Field Y.rarely_used: Manual estimate 95% null, script shows 87% null"
    ],
    "unexpected_findings": [
      "Field Z shows recent spike in usage (last 7 days)"
    ],
    "revised_action_items": [
      "Remove Field X (confirmed safe)",
      "Monitor Field Z before deciding"
    ]
  }
}
```

## Validation Requirements

- `status` must be "complete"
- `report_path` must be an absolute path to an existing file
- `verification_summary.files_analyzed` must be >= 0
- All conclusion arrays must exist (can be empty)
- `revised_action_items` must reflect script findings

## Script Execution

**Expected script interface:**
```bash
./analyze_field_utilization.sh <input_folder> <output_folder>
# Produces: <output_folder>/field_utilization_report.json
```

**Parse script output and integrate findings into report.**

## Error Handling

If verification fails, return:
```json
{
  "status": "error",
  "error_message": "Script execution failed: <details>",
  "report_path": null,
  "verification_summary": null
}
```
