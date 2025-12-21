---
name: schema-optimization-orchestrator
description: |
  Multi-phase schema optimization workflow orchestrator. Creates session directories,
  spawns phase agents sequentially, validates outputs, aggregates results.
  Trigger: "run schema optimization", "optimize schema workflow", "execute schema phases"
allowed-tools: Read, Write, Bash, Task
version: 1.0.0
license: MIT
author: Intent Solutions IO <jeremy@intentsolutions.io>
---

# Schema Optimization Orchestrator

Runs a multi-phase schema optimization workflow with strict validation and evidence collection.

## Workflow Pattern

This is a **test harness** pattern:
- Creates isolated session directory per run
- Spawns 5 phase agents sequentially
- Each phase reads reference docs, runs scripts, writes reports
- Validates JSON outputs and file artifacts
- Aggregates final summary

## Inputs (JSON)

```json
{
  "skill_dir": "/absolute/path/to/.claude/skills/schema-optimization",
  "input_folder": "/path/to/bigquery/export",
  "extraction_type": "bigquery_json",
  "session_dir_base": ".claude/skills/schema-optimization/reports/runs"
}
```

Required:
- **skill_dir**: Absolute path to this skill directory
- **input_folder**: Path to data to analyze
- **extraction_type**: Type of data extraction (e.g., "bigquery_json")

Optional:
- **session_dir_base**: Where to create run directories (default: reports/runs)

## Orchestration Steps

### 1. Create Session Directory

```bash
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
SESSION_DIR="${session_dir_base}/${TIMESTAMP}"
mkdir -p "${SESSION_DIR}"
```

### 2. Run Phase 1: Initial Schema Analysis

Spawn Phase 1 agent with:

```json
{
  "skill_dir": "<skill_dir>",
  "session_dir": "<SESSION_DIR>",
  "reference_path": "<skill_dir>/references/01-phase-1.md",
  "input_folder": "<input_folder>",
  "extraction_type": "<extraction_type>"
}
```

Expected output:
```json
{
  "status": "complete",
  "report_path": "<SESSION_DIR>/01-initial-schema-analysis.md",
  "schema_summary": {
    "total_tables": 0,
    "total_fields": 0,
    "key_findings": []
  }
}
```

**Validation:**
- JSON parse succeeds
- `status` is "complete"
- `report_path` file exists
- `schema_summary` has required keys

### 3. Run Phase 2: Field Utilization Analysis

Spawn Phase 2 agent with:

```json
{
  "skill_dir": "<skill_dir>",
  "session_dir": "<SESSION_DIR>",
  "reference_path": "<skill_dir>/references/02-phase-2.md",
  "phase1_report_path": "<phase1_report_path>",
  "input_folder": "<input_folder>"
}
```

Expected output:
```json
{
  "status": "complete",
  "report_path": "<SESSION_DIR>/02-field-utilization-analysis.md",
  "utilization_summary": {
    "unused_fields": [],
    "low_utilization_fields": [],
    "recommendations": []
  }
}
```

### 4. Run Phase 3: Impact Assessment

Spawn Phase 3 agent with:

```json
{
  "skill_dir": "<skill_dir>",
  "session_dir": "<SESSION_DIR>",
  "reference_path": "<skill_dir>/references/03-phase-3.md",
  "phase1_report_path": "<phase1_report_path>",
  "phase2_report_path": "<phase2_report_path>",
  "input_folder": "<input_folder>"
}
```

Expected output:
```json
{
  "status": "complete",
  "report_path": "<SESSION_DIR>/03-impact-assessment.md",
  "impact_summary": {
    "high_risk_changes": [],
    "medium_risk_changes": [],
    "low_risk_changes": [],
    "estimated_savings": {}
  }
}
```

### 5. Run Phase 4: Verification with Script

Spawn Phase 4 agent with:

```json
{
  "skill_dir": "<skill_dir>",
  "session_dir": "<SESSION_DIR>",
  "reference_path": "<skill_dir>/references/04-phase-4-verify-with-script.md",
  "phase2_report_path": "<phase2_report_path>",
  "phase3_report_path": "<phase3_report_path>",
  "input_folder": "<input_folder>",
  "script_path": "<skill_dir>/scripts/analyze_field_utilization.sh",
  "output_folder_path": "<input_folder>"
}
```

Expected output:
```json
{
  "status": "complete",
  "report_path": "<SESSION_DIR>/04-field-utilization-verification.md",
  "verification_summary": {
    "files_analyzed": 0,
    "conclusions_confirmed": [],
    "conclusions_revised": [],
    "unexpected_findings": [],
    "revised_action_items": []
  }
}
```

### 6. Run Phase 5: Final Recommendations

Spawn Phase 5 agent with:

```json
{
  "skill_dir": "<skill_dir>",
  "session_dir": "<SESSION_DIR>",
  "reference_path": "<skill_dir>/references/05-phase-5.md",
  "phase1_report_path": "<phase1_report_path>",
  "phase2_report_path": "<phase2_report_path>",
  "phase3_report_path": "<phase3_report_path>",
  "phase4_report_path": "<phase4_report_path>"
}
```

Expected output:
```json
{
  "status": "complete",
  "report_path": "<SESSION_DIR>/05-final-recommendations.md",
  "recommendations_summary": {
    "priority_actions": [],
    "implementation_plan": [],
    "success_metrics": []
  }
}
```

## Output (JSON Only)

```json
{
  "status": "complete",
  "session_dir": "<SESSION_DIR>",
  "timestamp": "YYYY-MM-DD_HHMMSS",
  "phase_reports": {
    "phase1": "<SESSION_DIR>/01-initial-schema-analysis.md",
    "phase2": "<SESSION_DIR>/02-field-utilization-analysis.md",
    "phase3": "<SESSION_DIR>/03-impact-assessment.md",
    "phase4": "<SESSION_DIR>/04-field-utilization-verification.md",
    "phase5": "<SESSION_DIR>/05-final-recommendations.md"
  },
  "final_summary": {
    "total_tables": 0,
    "total_fields": 0,
    "unused_fields": 0,
    "optimization_opportunities": 0,
    "estimated_savings_pct": 0,
    "verification_status": "confirmed"
  }
}
```

## Error Handling

If any phase fails:
- Stop execution
- Return error status with phase details
- Preserve partial reports for debugging

```json
{
  "status": "error",
  "failed_phase": 3,
  "error_message": "Phase 3 agent failed validation",
  "session_dir": "<SESSION_DIR>",
  "completed_phases": ["phase1", "phase2"]
}
```

## Validation Rules

After each phase:
1. Parse returned JSON (fail if invalid)
2. Check `status` is "complete" (fail if not)
3. Verify `report_path` exists on disk (fail if not)
4. Validate phase-specific summary keys (fail if missing)

## Implementation Notes

- Use Task tool to spawn phase agents
- Pass exact file paths (no wildcards)
- Session directory must be absolute path
- All reports must be written before returning
- No terminal output except final JSON

## Example Usage

```
User: "Run schema optimization on my BigQuery export"

Claude: [Creates session directory]
Claude: [Spawns Phase 1 agent]
Claude: [Validates Phase 1 output]
Claude: [Spawns Phase 2 agent with Phase 1 report]
Claude: [... continues through Phase 5]
Claude: [Returns final JSON summary]
```

## Files Created Per Run

```
reports/runs/2025-01-15_143022/
├── 01-initial-schema-analysis.md
├── 02-field-utilization-analysis.md
├── 03-impact-assessment.md
├── 04-field-utilization-verification.md
└── 05-final-recommendations.md
```

Each file is evidence of work completed.
