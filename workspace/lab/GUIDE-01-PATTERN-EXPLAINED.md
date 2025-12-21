# GUIDE 01: Pattern Explained - Deep Dive

**Read time:** 15 minutes
**Goal:** Understand every component and why it exists

---

## The Architecture (Component Breakdown)

```
schema-optimization/
├── SKILL.md                    # Orchestrator (the conductor)
├── agents/                     # Phase subagents (the workers)
│   ├── phase_1.md              # "What I do, what I return"
│   ├── phase_2.md
│   ├── phase_3.md
│   ├── phase_4.md
│   └── phase_5.md
├── references/                 # Instructions (the playbook)
│   ├── 01-phase-1.md           # "Step-by-step: do this"
│   ├── 02-phase-2.md
│   ├── 03-phase-3.md
│   ├── 04-verify-with-script.md
│   └── 05-phase-5.md
├── scripts/                    # Deterministic tools (the lab equipment)
│   └── analyze_field_utilization.sh
└── reports/                    # Evidence (the paper trail)
    ├── runs/                   # Session directories
    │   └── 2025-01-15_143022/  # One workflow run
    │       ├── 01-*.md         # Phase outputs
    │       ├── 02-*.md
    │       ├── 03-*.md
    │       ├── 04-*.md
    │       └── 05-*.md
    └── _samples/               # Examples of good outputs
```

---

## 1. The Orchestrator (SKILL.md)

**Role:** Conductor of the workflow
**Responsibilities:**
- Create session directory with timestamp
- Spawn phases in sequence
- Pass context between phases
- Validate outputs before continuing
- Aggregate final results

**Key Sections:**

### A. Input Schema
```yaml
inputs:
  skill_dir: "/absolute/path/to/this/skill"
  input_folder: "/path/to/data"
  extraction_type: "bigquery_json"
  session_dir_base: "reports/runs"  # optional
```

**Why:** Orchestrator needs to know where things are and what to process.

### B. Session Directory Creation
```bash
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
SESSION_DIR="${session_dir_base}/${TIMESTAMP}"
mkdir -p "${SESSION_DIR}"
```

**Why:** Isolation. Each run is independent. Can compare runs. Evidence persists.

### C. Phase Invocation Pattern
```markdown
For Phase 1:
- Call agent with inputs: {skill_dir, session_dir, reference_path, input_folder, extraction_type}
- Expect JSON: {status, report_path, schema_summary}
- Validate: JSON valid? status="complete"? report_path exists? schema_summary has keys?
- If valid: store phase1_report_path for Phase 2
- If invalid: STOP and return error
```

**Why:** Fail-fast. Don't waste time on downstream phases if upstream fails.

### D. Phase Chaining
```markdown
Phase 2 inputs = Phase 1 inputs + {phase1_report_path}
Phase 3 inputs = Phase 1 inputs + {phase1_report_path, phase2_report_path}
Phase 4 inputs = Phase 1 inputs + {phase2_report_path, phase3_report_path, script_path}
Phase 5 inputs = Phase 1 inputs + {phase1_report_path, phase2_report_path, phase3_report_path, phase4_report_path}
```

**Why:** Context accumulation. Later phases build on validated earlier work.

### E. Validation Rules
```markdown
After each phase:
1. Parse returned JSON (fail if invalid)
2. Check status="complete" (fail if error or missing)
3. Verify report_path file exists on disk (fail if not)
4. Validate phase-specific summary keys (fail if missing)
```

**Why:** Machine-checkable gates. No human judgment needed.

### F. Final Output
```json
{
  "status": "complete",
  "session_dir": "/absolute/path",
  "timestamp": "2025-01-15_143022",
  "phase_reports": {
    "phase1": "...",
    "phase2": "...",
    ...
  },
  "final_summary": {
    "total_tables": 42,
    "total_fields": 367,
    "unused_fields": 23,
    "optimization_opportunities": 21,
    "estimated_savings_pct": 15,
    "verification_status": "confirmed"
  }
}
```

**Why:** Machine-readable summary of entire workflow. Can be logged, graphed, alerted on.

---

## 2. Phase Agents (agents/*.md)

**Role:** Workers that execute one step
**Pattern:** All phase agents follow same contract

### Standard Phase Agent Structure

```markdown
# Phase N Agent: [Name]

## Inputs (JSON)
{
  "skill_dir": "...",
  "session_dir": "...",
  "reference_path": "...",
  "phaseX_report_path": "...",  # from prior phases
  ...
}

## Task Instructions
1. Read reference document at reference_path
2. Read prior phase reports (if applicable)
3. Execute analysis/work
4. Write report to: <session_dir>/NN-[name].md
5. Return JSON only (no terminal text)

## Output Format (JSON Only)
{
  "status": "complete",
  "report_path": "/absolute/path",
  "phase_summary": {
    "key1": "value1",
    ...
  }
}

## Validation Requirements
- status must be "complete"
- report_path must exist
- phase_summary must have required keys

## Error Handling
If work fails, return:
{
  "status": "error",
  "error_message": "...",
  "report_path": null,
  "phase_summary": null
}
```

**Why this structure:**
- **Inputs section:** Clear contract of what's provided
- **Task instructions:** High-level overview (details in reference doc)
- **Output format:** Exact JSON schema expected
- **Validation requirements:** What orchestrator will check
- **Error handling:** Graceful failure mode

### Phase-Specific Variations

**Phase 1: Initial Analysis**
- No prior phase inputs
- Establishes baseline metrics
- Summary: `{total_tables, total_fields, key_findings}`

**Phase 2-3: Analysis Phases**
- Read Phase 1 report for context
- Build on established baseline
- Summary: Domain-specific metrics

**Phase 4: Verification (CRITICAL)**
- Reads Phase 2-3 conclusions
- **RUNS REAL SCRIPT** (`analyze_field_utilization.sh`)
- Compares script output vs manual analysis
- Summary: `{files_analyzed, conclusions_confirmed, conclusions_revised, unexpected_findings, revised_action_items}`

**Phase 5: Synthesis**
- Reads ALL prior phase reports
- Aggregates validated findings
- Summary: `{priority_actions, implementation_plan, success_metrics}`

---

## 3. Reference Docs (references/*.md)

**Role:** The playbook - step-by-step instructions
**Why separate from agent contract:** Agent knows WHAT to return, reference knows HOW to do work

### Anatomy of a Reference Doc

```markdown
# Phase N: [Name]

## Context
[What this phase accomplishes in the bigger picture]

## Inputs Available to You
- skill_dir: ...
- session_dir: ...
- input_folder: ...
- phaseX_report_path: ...

## Step-by-Step Procedure

### Step 1: [Action]
[Detailed instructions]
[Example commands if applicable]

### Step 2: [Action]
[Detailed instructions]

...

## Report Format

Write to: {session_dir}/NN-[name].md

Required sections:
- ## Summary
- ## Methodology
- ## Findings
- ## Recommendations

## Output Requirements

Return JSON:
{
  "status": "complete",
  "report_path": "<absolute path>",
  "phase_summary": {
    "key1": "...",
    "key2": "..."
  }
}

## Quality Checklist
- [ ] All data sources documented
- [ ] Metrics include methodology
- [ ] Findings are evidence-based
- [ ] Recommendations are actionable
```

**Key difference from agent contract:**
- **Agent contract:** "Return JSON with these keys"
- **Reference doc:** "Calculate metrics using this methodology"

### Example: Phase 4 Reference (The Critical One)

```markdown
# Phase 4: Verify Field Utilization with Script

## Context
Phases 2-3 made conclusions about unused fields through manual analysis.
This phase runs a deterministic script to empirically validate those conclusions.

## Key Conclusions from Phase 2/3 to Verify
Read phase2_report_path and phase3_report_path.
Extract:
- Fields marked as "unused" (>90% null)
- Fields marked as "low utilization" (70-90% null)
- Estimated storage savings

## Step-by-Step Procedure

### Step 1: Extract Conclusions
From Phase 2/3 reports, create a list:
- table.field: conclusion (e.g., "users.legacy_id: unused, 100% null")

### Step 2: Execute Verification Script
Run: scripts/analyze_field_utilization.sh <input_folder> <output_folder>

This script:
- Scans all JSON/CSV files in input_folder
- Calculates ACTUAL null percentages
- Produces: <output_folder>/field_utilization_report.json

### Step 3: Parse Script Output
Read: <output_folder>/field_utilization_report.json
Extract:
- files_analyzed
- field_usage_breakdown

### Step 4: Compare Script vs Manual
For each conclusion from Phase 2/3:
- If script confirms (within 5% tolerance): add to "conclusions_confirmed"
- If script differs (>5% difference): add to "conclusions_revised"
- If script finds new issues: add to "unexpected_findings"

### Step 5: Update Action Items
Based on comparison:
- Keep safe actions (script confirmed)
- Revise risky actions (script showed different data)
- Add new actions (script found unexpected issues)

### Step 6: Write Report
Save to: {session_dir}/04-field-utilization-verification.md

Required sections:
- ## Original Conclusions (from Phase 2/3)
- ## Script Execution Results
- ## Comparison Analysis (table)
- ## Revised Action Items

### Step 7: Return JSON
{
  "status": "complete",
  "report_path": "<absolute>",
  "verification_summary": {
    "files_analyzed": N,
    "conclusions_confirmed": ["table.field: ..."],
    "conclusions_revised": ["table.field: was X%, actually Y%"],
    "unexpected_findings": ["table.field: script found issue"],
    "revised_action_items": ["Safe: Remove field X", "Risky: Monitor field Y"]
  }
}
```

**Why this is powerful:**
- Forces empirical validation (script doesn't lie)
- Documents discrepancies (revised conclusions)
- Updates recommendations based on evidence
- Produces audit trail (can see what changed and why)

---

## 4. Scripts (scripts/*.sh)

**Role:** Deterministic computation (the lab equipment)
**Why:** Remove LLM variability for objective calculations

### Characteristics of Good Verification Scripts

**1. Deterministic**
- Same inputs = same outputs (always)
- No randomness, no API calls, no LLM usage

**2. Fast**
- Runs in seconds, not minutes
- Optimized for local execution

**3. Self-Contained**
- No external dependencies (or minimal)
- Validates its own inputs

**4. Structured Output**
- Produces JSON (machine-readable)
- Clear schema

**5. Error Handling**
- Validates inputs before processing
- Returns meaningful error messages

### Example: analyze_field_utilization.sh

```bash
#!/bin/bash
# Deterministic field utilization analyzer
# No LLM usage - pure computation

set -euo pipefail  # Fail on errors

# ============================================
# Input Validation
# ============================================
if [ $# -ne 2 ]; then
  echo "Usage: $0 <input_folder> <output_folder>"
  exit 1
fi

INPUT_FOLDER="$1"
OUTPUT_FOLDER="$2"

if [ ! -d "$INPUT_FOLDER" ]; then
  echo "Error: Input folder does not exist: $INPUT_FOLDER"
  exit 1
fi

mkdir -p "$OUTPUT_FOLDER"

# ============================================
# Analysis
# ============================================
FILES_ANALYZED=0
UNUSED_FIELDS=()
LOW_UTIL_FIELDS=()
HIGH_UTIL_FIELDS=()

for file in "$INPUT_FOLDER"/*.json "$INPUT_FOLDER"/*.csv; do
  if [ -f "$file" ]; then
    FILES_ANALYZED=$((FILES_ANALYZED + 1))

    # Parse file and calculate null percentages
    # (Implementation: jq for JSON, awk for CSV)
    # For each field:
    #   - Count total rows
    #   - Count null rows
    #   - Calculate null_pct = (null_rows / total_rows) * 100
    #   - Categorize: >90% = unused, 70-90% = low, <70% = high

    # Placeholder (replace with real parsing):
    # field_null_pct=$(...)
    # if [ $field_null_pct -gt 90 ]; then
    #   UNUSED_FIELDS+=("$file:$field:$field_null_pct")
    # elif [ $field_null_pct -gt 70 ]; then
    #   LOW_UTIL_FIELDS+=("$file:$field:$field_null_pct")
    # else
    #   HIGH_UTIL_FIELDS+=("$file:$field:$field_null_pct")
    # fi
  fi
done

# ============================================
# Output JSON
# ============================================
cat > "$OUTPUT_FOLDER/field_utilization_report.json" <<EOF
{
  "files_analyzed": $FILES_ANALYZED,
  "timestamp": "$(date -Iseconds)",
  "field_usage_breakdown": {
    "unused_fields": $(printf '%s\n' "${UNUSED_FIELDS[@]}" | jq -R . | jq -s .),
    "low_utilization_fields": $(printf '%s\n' "${LOW_UTIL_FIELDS[@]}" | jq -R . | jq -s .),
    "high_utilization_fields": $(printf '%s\n' "${HIGH_UTIL_FIELDS[@]}" | jq -R . | jq -s .)
  },
  "summary": {
    "total_fields": $((${#UNUSED_FIELDS[@]} + ${#LOW_UTIL_FIELDS[@]} + ${#HIGH_UTIL_FIELDS[@]})),
    "unused_count": ${#UNUSED_FIELDS[@]},
    "low_util_count": ${#LOW_UTIL_FIELDS[@]},
    "high_util_count": ${#HIGH_UTIL_FIELDS[@]}
  }
}
EOF

echo "Analysis complete: $OUTPUT_FOLDER/field_utilization_report.json"
exit 0
```

**Why this works:**
- Validates inputs before processing
- Pure computation (no LLM guessing)
- Structured JSON output
- Can be tested independently
- Fast and deterministic

---

## 5. Session Directories (reports/runs/)

**Role:** Evidence repository
**Pattern:** One directory per workflow execution

### Structure

```
reports/runs/
├── 2025-01-15_143022/          # Timestamp = session ID
│   ├── 01-initial-schema-analysis.md
│   ├── 02-field-utilization-analysis.md
│   ├── 03-impact-assessment.md
│   ├── 04-field-utilization-verification.md
│   └── 05-final-recommendations.md
├── 2025-01-15_151435/          # Another run (different data or config)
│   ├── 01-*.md
│   └── ...
└── 2025-01-16_092314/          # Next day's run
    ├── 01-*.md
    └── ...
```

**Benefits:**
1. **Audit Trail:** Can review exactly what was analyzed
2. **Debugging:** If Phase 4 failed, read Phase 1-3 reports to understand context
3. **Comparison:** Compare runs across time
4. **Evidence:** Proves work was actually done
5. **Rollback:** If new run is bad, refer to previous run

### Report Format Standards

Each report should include:

```markdown
# Phase N: [Name]

**Session:** 2025-01-15_143022
**Generated:** 2025-01-15 14:30:45 CST
**Input:** /path/to/data

---

## Executive Summary
[3-5 bullet points of key findings]

---

## Methodology
[How the analysis was performed]

---

## Findings

### [Category 1]
[Detailed findings with evidence]

### [Category 2]
[Detailed findings with evidence]

---

## Data

| Metric | Value |
|--------|-------|
| Total Tables | 42 |
| Total Fields | 367 |
| ... | ... |

---

## Recommendations
- [Actionable recommendation 1]
- [Actionable recommendation 2]

---

## Next Steps
[What Phase N+1 should focus on based on these findings]

---

*Generated by Phase N Agent*
*Report Path: 0N-[name].md*
```

**Why this structure:**
- **Metadata:** Know when/where this came from
- **Executive Summary:** TL;DR for stakeholders
- **Methodology:** Reproducibility and trust
- **Findings:** Evidence-based details
- **Data:** Structured metrics (can be graphed)
- **Recommendations:** Actionable outputs
- **Next Steps:** Guide for next phase

---

## 6. Sample Outputs (reports/_samples/)

**Role:** Reference examples
**Why:** Show what good outputs look like

### What to Include

1. **Complete session directory** with all 5 phase reports
2. **Realistic data** (not "lorem ipsum")
3. **Actual verification** (Phase 4 shows script output)
4. **Proper formatting** (demonstrates report standards)

### Learning Value

New users can:
- See what finished workflow produces
- Understand report quality standards
- Learn Phase 4 verification pattern
- Copy structure for their own reports

---

## The Critical Phase 4 Pattern (Deep Dive)

**Why Phase 4 is the "money shot":**

Most LLM workflows are all narrative:
1. Agent analyzes → writes text
2. Agent concludes → writes text
3. Agent recommends → writes text

**Problem:** No empirical validation. Just LLM's opinion.

**Phase 4 solution:**
1. Phases 2-3 make conclusions (LLM analysis)
2. Phase 4 runs SCRIPT (deterministic computation)
3. Phase 4 compares: LLM conclusions vs script facts
4. Phase 4 revises: "Was 95% null, actually 87% null"
5. Phase 4 updates: "Can't safely remove, need monitoring"

**This is the pattern that turns** "chatbot output" **into** "validated engineering work"

### How to Adapt for Your Use Case

**Code review workflow:**
- Phases 1-3: LLM analyzes code, suggests improvements
- Phase 4: Run linter/formatter/tests, compare LLM suggestions vs actual tool output
- Phase 5: Recommendations based on validated issues only

**Security audit workflow:**
- Phases 1-3: LLM analyzes for vulnerabilities
- Phase 4: Run SAST/DAST tools, compare LLM findings vs scanner results
- Phase 5: Prioritize confirmed vulnerabilities only

**Research synthesis workflow:**
- Phases 1-3: LLM summarizes papers, identifies themes
- Phase 4: Run citation analysis script, verify LLM's claimed connections
- Phase 5: Synthesis based on validated citation network

**Pattern:** Always include one phase that runs deterministic tools to validate LLM conclusions.

---

## Design Principles Summary

1. **Evidence-Based**
   - Every phase writes a file
   - Can't claim work without artifact

2. **Machine-Checkable**
   - JSON outputs can be validated programmatically
   - No human judgment needed for gates

3. **Fail-Fast**
   - Orchestrator stops on first validation failure
   - Don't waste time on downstream work

4. **Composable**
   - Phases are independent
   - Can reuse in other workflows

5. **Debuggable**
   - Clear failure points
   - Structured outputs
   - Session directories preserve state

6. **Repeatable**
   - Deterministic scripts
   - Same inputs = same outputs

7. **Auditable**
   - Timestamp-based sessions
   - Complete paper trail
   - Can review past runs

---

## Next Steps

**To see it in action:**
Read `exercises/exercise-1-run-workflow.md` and execute the reference implementation.

**To build your own:**
Read `GUIDE-02-BUILDING-YOUR-OWN.md` for step-by-step adaptation guide.

**To debug issues:**
Read `GUIDE-03-DEBUGGING-TIPS.md` for common pitfalls and solutions.

---

*Next: GUIDE-02-BUILDING-YOUR-OWN.md*
