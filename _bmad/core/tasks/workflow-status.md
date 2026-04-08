# Workflow Status Task

## Purpose
Check current BMAD project status and recommend next steps.

## Steps

1. Scan `_bmad-output/` for completed artifacts
2. Determine current phase (0-4)
3. Identify any incomplete or missing artifacts
4. Recommend the next workflow or action

## Phase Detection

- **Level 0**: No artifacts found → Recommend analysis
- **Level 1**: Analysis docs present → Recommend PRD creation
- **Level 2**: PRD present → Recommend architecture design
- **Level 3**: Architecture present → Recommend sprint planning
- **Level 4**: Stories present → Recommend implementation

## Output
- Current phase and level
- Completed artifacts list
- Next recommended action
