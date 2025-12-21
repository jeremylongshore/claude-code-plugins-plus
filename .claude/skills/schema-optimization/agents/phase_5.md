# Phase 5 Agent: Final Recommendations

**Contract:** This agent synthesizes all phase outputs into actionable recommendations with implementation plans.

## Inputs (JSON)

```json
{
  "skill_dir": "/absolute/path/to/.claude/skills/schema-optimization",
  "session_dir": "/absolute/path/to/session/directory",
  "reference_path": "/absolute/path/to/references/05-phase-5.md",
  "phase1_report_path": "/absolute/path/to/01-initial-schema-analysis.md",
  "phase2_report_path": "/absolute/path/to/02-field-utilization-analysis.md",
  "phase3_report_path": "/absolute/path/to/03-impact-assessment.md",
  "phase4_report_path": "/absolute/path/to/04-field-utilization-verification.md"
}
```

## Task Instructions

1. **Read reference document**: Load instructions from `reference_path`
2. **Review all phase outputs**: Read all 4 previous phase reports
3. **Synthesize findings**:
   - Aggregate verified conclusions
   - Prioritize actions by ROI (risk vs. savings)
   - Group recommendations by theme
4. **Create implementation plan**:
   - Sequence actions (quick wins first, then complex changes)
   - Define rollback procedures
   - Estimate timeline per action
   - Assign owner/responsibility
5. **Define success metrics**: KPIs for tracking optimization impact
6. **Write report**: Save markdown report to `<session_dir>/05-final-recommendations.md`
7. **Return JSON**: Output strict JSON with no terminal text

## Output Format (JSON Only)

```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/session_dir/05-final-recommendations.md",
  "recommendations_summary": {
    "priority_actions": [
      {
        "action": "Remove 15 unused fields from table_X",
        "impact": "Save 45GB storage, reduce query cost 8%",
        "risk": "low",
        "effort": "2 hours"
      }
    ],
    "implementation_plan": [
      {
        "phase": "Quick Wins (Week 1)",
        "actions": ["Remove verified unused fields"],
        "owner": "Data Engineering Team"
      },
      {
        "phase": "Medium Impact (Week 2-3)",
        "actions": ["Archive low-utilization fields"],
        "owner": "Data Engineering + Analytics"
      }
    ],
    "success_metrics": [
      "Storage reduction: Target 30% decrease",
      "Query performance: Target 15% faster avg query time",
      "Cost savings: Target $500/month reduction"
    ]
  }
}
```

## Validation Requirements

- `status` must be "complete"
- `report_path` must be an absolute path to an existing file
- `priority_actions` must be sorted by ROI (highest impact first)
- `implementation_plan` must have realistic timeline
- `success_metrics` must be measurable and specific

## Error Handling

If synthesis fails, return:
```json
{
  "status": "error",
  "error_message": "Description of what went wrong",
  "report_path": null,
  "recommendations_summary": null
}
```
