# Subagent Orchestration Pattern for Claude Skills

A comprehensive guide to building multi-phase workflows where each phase runs as an isolated subagent with its own context window, strict contracts, and verification gates.

-----

## Part 1: Why Subagent Orchestration

### The Problem with Monolithic Prompts

When you ask Claude to do something complex — "analyze this codebase and give me optimization recommendations" — you're cramming everything into one context window:

```
┌─────────────────────────────────────────────────────────────┐
│                  ONE MASSIVE CONTEXT                        │
│                                                             │
│  - System prompt (2k tokens)                                │
│  - All the code files (30k tokens)                          │
│  - Schema definitions (5k tokens)                           │
│  - Analysis instructions (3k tokens)                        │
│  - Intermediate reasoning (10k tokens)                      │
│  - Previous analysis notes (8k tokens)                      │
│  - Final recommendations (2k tokens)                        │
│                                                             │
│  TOTAL: 60k tokens, attention diluted across everything     │
└─────────────────────────────────────────────────────────────┘
```

Problems:

1. **Attention dilution** — The model is trying to attend to everything at once
1. **Context pollution** — Early reasoning artifacts stick around and influence later steps
1. **No isolation** — A mistake in step 2 propagates invisibly through steps 3-5
1. **No verification** — You can't check intermediate work
1. **No recovery** — If step 4 fails, you start over from scratch

### The Subagent Solution

Split the work into isolated phases. Each phase gets a fresh context with only what it needs:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   PHASE 1    │     │   PHASE 2    │     │   PHASE 3    │
│   8k tokens  │────▶│   10k tokens │────▶│   6k tokens  │
│              │     │              │     │              │
│ Fresh context│     │ Fresh context│     │ Fresh context│
│ Focused task │     │ Focused task │     │ Focused task │
│ Strict output│     │ Strict output│     │ Strict output│
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
   report_1.md          report_2.md          report_3.md
   + JSON summary       + JSON summary       + JSON summary
```

Benefits:

1. **Focused attention** — Each agent only sees relevant context
1. **Clean handoffs** — Structured JSON passes between phases
1. **Visible checkpoints** — Each phase produces a report you can inspect
1. **Fail fast** — Contract violations stop the pipeline immediately
1. **Partial recovery** — Failed at Phase 4? Restart from Phase 4, not Phase 1

### Context Budget Comparison

**Monolithic approach:**

- 60k tokens in one window
- Model tries to hold everything in attention
- Later steps have degraded quality

**Orchestrated approach:**

- Phase 1: 8k tokens (system + inputs + procedure)
- Phase 2: 10k tokens (system + Phase 1 output + new inputs + procedure)
- Phase 3: 6k tokens (system + Phase 2 output + procedure)
- Phase 4: 12k tokens (system + Phases 2-3 outputs + script results + procedure)
- Phase 5: 8k tokens (system + all summaries + procedure)

Each phase operates at peak attention. The orchestrator only passes forward what's needed.

-----

## Part 2: The Contract Pattern

### Why Strict Contracts Matter

Without contracts, subagents return whatever they feel like:

```
Phase 1 returns: "I found some tables. There were issues."
Phase 2 receives: ??? (What tables? What issues? Where's the data?)
```

With contracts, every phase has explicit:

- **Inputs**: What it receives
- **Outputs**: What it must produce (file + JSON)
- **Validation**: How the orchestrator checks success

### Anatomy of a Phase Contract

Every phase agent has three components:

```markdown
# Phase N: [Name]

## Input Contract
You will receive:
- `session_dir`: Absolute path where you write your report
- `input_folder`: Path to source data (if applicable)
- `previous_outputs`: JSON from prior phases (if applicable)

## Procedure
Read: `references/0N-phase-N.md`
Follow the step-by-step instructions exactly.

## Output Contract

### File Output
Write a markdown report to: `{session_dir}/0N-report-name.md`

Required sections:
- Summary
- Detailed Findings
- Key Takeaways

### JSON Return
Return exactly this structure:
```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/0N-report-name.md",
  "phase_data": {
    "key_metric_1": <value>,
    "key_metric_2": <value>,
    "findings": ["...", "..."]
  }
}
```

If you cannot complete the task, return:

```json
{
  "status": "failed",
  "error": "Description of what went wrong",
  "partial_work": "/path/to/partial/report/if/any"
}
```
```

### The Dual Output Pattern

Each phase produces TWO outputs:

1. **Human-readable report (Markdown file)**
   - Detailed narrative
   - Full context and reasoning
   - Can be reviewed by humans
   - Serves as audit trail

2. **Machine-readable summary (JSON)**
   - Structured data only
   - Passed to next phase
   - Validated by orchestrator
   - Enables automation

This separation is crucial. The report is for understanding. The JSON is for handoff.

### Validation Gates

The orchestrator validates after each phase:

```python
def validate_phase_output(phase_num, output):
    # 1. Is it valid JSON?
    try:
        data = json.loads(output)
    except:
        raise ValidationError(f"Phase {phase_num} returned invalid JSON")

    # 2. Required keys present?
    required = ["status", "report_path", "phase_data"]
    for key in required:
        if key not in data:
            raise ValidationError(f"Phase {phase_num} missing key: {key}")

    # 3. Status is success?
    if data["status"] != "complete":
        raise ValidationError(f"Phase {phase_num} failed: {data.get('error')}")

    # 4. Report file exists?
    if not os.path.exists(data["report_path"]):
        raise ValidationError(f"Phase {phase_num} report not found: {data['report_path']}")

    # 5. Phase-specific validation
    validate_phase_specific(phase_num, data["phase_data"])

    return data
```

If any validation fails, the entire pipeline stops. No silent failures.

-----

## Part 3: The Verification Pattern

### The Problem: LLMs Hallucinate Confidently

Phase 2 might say: "I found 23 unused fields with >95% null values."

But did it actually count? Or did it pattern-match and guess? You have no way to know.

### The Solution: Ground Truth Injection

Insert a phase that runs **deterministic code** and forces the LLM to reconcile its claims with actual data.

```
┌─────────────────────────────────────────────────────────────┐
│                    THE VERIFICATION PHASE                   │
│                                                             │
│  1. Read conclusions from prior LLM phases                  │
│  2. Run deterministic script on actual data                 │
│  3. Compare script output vs LLM conclusions                │
│  4. Produce reconciliation report:                          │
│     - CONFIRMED: Where script agrees with LLM               │
│     - REVISED: Where script shows different numbers         │
│     - UNEXPECTED: New findings LLM missed                   │
└─────────────────────────────────────────────────────────────┘
```

### Example: Schema Analysis Verification

**Phase 2 claimed:**

```json
{
  "unused_fields": [
    {"table": "users", "field": "legacy_id", "null_pct": 98.2},
    {"table": "users", "field": "temp_flag", "null_pct": 100.0},
    {"table": "orders", "field": "deprecated_status", "null_pct": 95.7}
  ],
  "total_unused": 23
}
```

**Phase 4 runs script:**

```bash
./analyze_field_utilization.sh ./schemas ./output
```

**Script produces:**

```json
{
  "files_analyzed": 42,
  "fields_analyzed": 367,
  "unused_fields": [
    {"table": "users", "field": "legacy_id", "null_pct": 98.1},
    {"table": "users", "field": "temp_flag", "null_pct": 100.0},
    {"table": "orders", "field": "old_status", "null_pct": 96.2}
  ],
  "total_unused": 21
}
```

**Phase 4 reconciles:**

```markdown
## Verification Results

### Confirmed (20 fields)
Script confirms these fields are unused as Phase 2 identified.

### Revised (2 fields)
- `users.legacy_id`: Phase 2 said 98.2%, script found 98.1% — minor difference, still unused
- `orders.deprecated_status`: Phase 2 identified this but script shows `orders.old_status` — naming mismatch, same field

### Not Found (1 field)
- Phase 2 claimed `events.archive_flag` was unused but script found 78% utilization — FALSE POSITIVE

### Unexpected (1 field)
- Script found `logs.debug_data` at 99.8% null — Phase 2 missed this

### Revised Totals
- Original claim: 23 unused fields
- Verified count: 21 unused fields
- Confidence: HIGH (script-verified)
```

### Why This Matters

1. **Catches hallucinations** — The LLM can't just make up numbers
1. **Builds trust** — You have ground truth backing the recommendations
1. **Improves accuracy** — Forces the LLM to be precise knowing it will be checked
1. **Creates audit trail** — The reconciliation report shows exactly what was verified

### What Can Be Verified

Any claim that can be checked programmatically:

| LLM Claim                       | Verification Script                  |
|---------------------------------|--------------------------------------|
| "23 fields are unused"          | Count null percentages in actual data|
| "This function is never called" | Static analysis / grep for references|
| "These 5 files are duplicates"  | Hash comparison                      |
| "API response time is 200ms"    | Actual HTTP request timing           |
| "This regex matches the pattern"| Run regex against test cases         |
| "Total cost is $5,000/month"    | Calculator script with actual prices |

### Writing Verification Scripts

Verification scripts should be:

1. **Deterministic** — Same input always produces same output
1. **Standalone** — Can be run outside the LLM pipeline for testing
1. **Simple** — Do one thing well, don't try to be clever
1. **Documented** — Clear usage, input format, output format

Example structure:

```bash
#!/bin/bash
# analyze_field_utilization.sh
#
# Analyzes JSON schema files for field utilization patterns.
#
# Usage: ./analyze_field_utilization.sh <input_folder> <output_folder>
#
# Input: Folder containing .json schema files
# Output: <output_folder>/field_utilization_report.json
#
# Exit codes:
#   0 - Success
#   1 - Invalid arguments
#   2 - Input folder not found
#   3 - No schema files found

set -euo pipefail

INPUT_FOLDER="${1:-}"
OUTPUT_FOLDER="${2:-}"

# Validate inputs
if [[ -z "$INPUT_FOLDER" ]] || [[ -z "$OUTPUT_FOLDER" ]]; then
    echo "Usage: $0 <input_folder> <output_folder>" >&2
    exit 1
fi

if [[ ! -d "$INPUT_FOLDER" ]]; then
    echo "Error: Input folder not found: $INPUT_FOLDER" >&2
    exit 2
fi

mkdir -p "$OUTPUT_FOLDER"

# Find schema files
SCHEMA_FILES=$(find "$INPUT_FOLDER" -name "*.json" -type f)
if [[ -z "$SCHEMA_FILES" ]]; then
    echo "Error: No .json files found in $INPUT_FOLDER" >&2
    exit 3
fi

# Analysis logic here...
# [Parse JSON, count fields, calculate null percentages]

# Write deterministic output
cat > "$OUTPUT_FOLDER/field_utilization_report.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "input_folder": "$INPUT_FOLDER",
  "files_analyzed": $FILES_ANALYZED,
  "fields_analyzed": $FIELDS_ANALYZED,
  "unused_fields": $UNUSED_FIELDS_JSON,
  "low_utilization_fields": $LOW_UTIL_FIELDS_JSON,
  "summary": {
    "total_unused": $TOTAL_UNUSED,
    "total_low_util": $TOTAL_LOW_UTIL,
    "estimated_savings_bytes": $SAVINGS_ESTIMATE
  }
}
EOF

echo "Analysis complete: $OUTPUT_FOLDER/field_utilization_report.json"
exit 0
```

-----

## Part 4: Building Your Own Orchestrated Skill

### Step 1: Define the Workflow

Before writing any code, map out your phases:

```
WORKFLOW: [Your Task Name]

Phase 1: [Name]
  Input: [What this phase receives]
  Does: [What computation/analysis happens]
  Output: [What it produces]

Phase 2: [Name]
  Input: [Phase 1 output + new data]
  Does: [What computation/analysis happens]
  Output: [What it produces]

...

Phase N: [Name] (VERIFICATION)
  Input: [Prior phase outputs]
  Does: [Run script, compare to LLM claims]
  Output: [Reconciliation report]

Phase N+1: [Name] (SYNTHESIS)
  Input: [All prior outputs]
  Does: [Combine into final recommendations]
  Output: [Final report + action items]
```

### Step 2: Create the Directory Structure

```
your-skill/
├── SKILL.md                    # Orchestrator
├── agents/
│   ├── phase_1.md              # Phase 1 system prompt + contract
│   ├── phase_2.md              # Phase 2 system prompt + contract
│   ├── phase_3.md              # Phase 3 system prompt + contract
│   ├── phase_4_verify.md       # Verification phase
│   └── phase_5_synthesize.md   # Synthesis phase
├── references/
│   ├── 01-phase-1-procedure.md # Step-by-step for Phase 1
│   ├── 02-phase-2-procedure.md # Step-by-step for Phase 2
│   ├── 03-phase-3-procedure.md # Step-by-step for Phase 3
│   ├── 04-verification.md      # How to run and interpret script
│   ├── 05-synthesis.md         # How to produce final recommendations
│   └── shared-best-practices.md # Cross-cutting docs for multiple phases
├── scripts/
│   └── verify_[domain].sh      # Verification script
└── reports/
    ├── _samples/               # Example outputs
    │   └── 2025-01-15_143022/
    └── [project-name]/         # Project-scoped sessions (see below)
        └── 2025-01-15_143022/
            ├── 01-phase-1-report.md
            ├── 02-phase-2-report.md
            ├── 03-phase-3-report.md
            ├── 04-verification-report.md
            └── 05-final-recommendations.md
```

#### Project-Scoped Reports Pattern

When running the same skill across multiple projects, scope sessions by project:

```
reports/
├── _samples/                    # Reference examples
├── client-alpha-api/            # Project 1
│   ├── 2025-01-10_091500/
│   └── 2025-01-15_143022/
├── internal-billing-service/    # Project 2
│   └── 2025-01-12_160000/
└── documenti_di_gara/           # Project 3
    ├── 2025-12-21_153000/
    └── 2025-12-21_155316/
```

Benefits:

- **Isolation**: Different projects never mix outputs
- **History**: Track multiple runs per project over time
- **Comparison**: Diff reports between runs to see what changed
- **Cleanup**: Archive or delete entire projects easily

Session path becomes: `reports/{project_name}/{timestamp}/`

Update your orchestrator to accept project name:

```markdown
## Session Management

Input: `{ project_name, input_folder, ... }`

Session directory: `reports/{project_name}/{timestamp}/`

```bash
PROJECT="client-alpha-api"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
SESSION_DIR="reports/$PROJECT/$TIMESTAMP"
mkdir -p "$SESSION_DIR"
```
```

#### Shared References Pattern

Not all references map 1:1 to phases. Include cross-cutting docs:

```
references/
├── 01-comprehension.md              # Phase 1 procedure
├── 02-json-analysis.md              # Phase 2 procedure
├── 03-schema-alignment.md           # Phase 3 procedure
├── 04-verification.md               # Phase 4 procedure
├── 05-remediation.md                # Phase 5 procedure
├── json-api-best-practices.md       # Shared: phases 2, 3 reference this
└── output-templates.md              # Shared: all phases use these templates
```

In phase agents, be explicit about which references to read:

```markdown
# Phase 2: JSON Analysis

## References to Read
Primary: `references/02-json-analysis.md`
Also consult: `references/json-api-best-practices.md` (for validation rules)

## Your Task
...
```

This keeps phase-specific procedures separate from shared knowledge.

*(Continued in next message due to length...)*
### Step 3: Write the Orchestrator (SKILL.md)

The orchestrator is your main entry point. It manages the entire pipeline, validates each phase, and handles errors gracefully.

**See**: [`schema-optimization/SKILL.md`](schema-optimization/SKILL.md) for complete working example

Key sections:
- Architecture overview with ASCII diagram
- Session management (timestamp-based directories)
- Phase spawning logic
- Validation gates between phases
- Error handling and recovery
- Context passing rules

### Step 4: Write Phase Agents

Each phase agent lives in `agents/` and defines the contract for that phase.

**See**: [`schema-optimization/agents/`](schema-optimization/agents/) for examples

Template structure:
```markdown
# Phase N: [Name]

You are a specialized agent for [specific task].

## Input Contract
[Exact JSON structure you receive]

## Procedure
Read: references/0N-[name].md
Follow step-by-step instructions exactly.

## Output Contract
File: {session_dir}/0N-report.md
JSON: { status, report_path, phase_data }

## Failure Protocol
If cannot complete: { status: "failed", error: "..." }
```

### Step 5: Write Reference Procedures

These are the actual step-by-step instructions each phase follows.

**See**: [`schema-optimization/references/`](schema-optimization/references/) for examples

Each procedure includes:
- Context (why this phase exists)
- Inputs available
- Step-by-step instructions with examples
- Output checklist
- Report template
- Common mistakes to avoid

### Step 6: Write the Verification Script

This is your ground truth. It must be deterministic and independent.

**See**: [`schema-optimization/scripts/analyze_field_utilization.sh`](schema-optimization/scripts/analyze_field_utilization.sh)

Requirements:
- Runs standalone (no LLM needed)
- Takes input/output paths
- Produces structured JSON
- Documents exit codes
- Includes usage help

### Step 7: Create Sample Outputs

Show users what success looks like.

**Location**: `reports/_samples/YYYY-MM-DD_HHMMSS/`

Include:
- Complete session directory with all 5 reports
- Realistic data (based on real runs)
- Demonstrates both successful and challenging cases
- Shows verification reconciliation clearly

### Step 8: Test End-to-End

Before deployment:

1. **Unit test each phase** in isolation
2. **Test verification script** standalone
3. **Integration test** full pipeline
4. **Failure test** with bad inputs
5. **Compare** actual outputs vs samples

-----

## Part 5: Advanced Patterns

### Pattern: Retry with Feedback

When a phase fails validation, retry with error context:

```markdown
Phase 2 attempt 1: Returns invalid JSON
    ↓
Orchestrator: Catches parse error
    ↓
Phase 2 attempt 2: Receives error message + retry instruction
    ↓
Phase 2 attempt 2: Returns valid JSON ✓
```

Limit retries (typically 2-3 max) to avoid infinite loops.

### Pattern: Parallel Phases

When phases don't depend on each other, run them simultaneously:

```
                    ┌─▶ Phase 2a: Code Analysis ──┐
Phase 1 ──┬─────────┼─▶ Phase 2b: Doc Analysis ───┼─▶ Phase 3
          │         └─▶ Phase 2c: Test Analysis ──┘
```

Wait for all to complete, then merge results in Phase 3.

### Pattern: Conditional Phases

Skip phases based on prior results:

```markdown
if phase_2_data["complexity"] == "low":
    skip Phase 3 (deep analysis)
    go directly to Phase 4
```

### Pattern: Human-in-the-Loop

Pause for approval at critical decision points:

```markdown
Phase 3 identifies HIGH RISK changes
    ↓
Orchestrator asks: "Proceed? [y/n]"
    ↓
If approved → Continue to Phase 4
If rejected → End with recommendations only
```

### Pattern: Checkpointing

Save state after each phase for recovery:

```json
{
  "checkpoint": "phase_3_complete",
  "completed_phases": [1, 2, 3],
  "phase_outputs": { ... },
  "timestamp": "2025-01-15T14:30:22Z"
}
```

On failure, resume from last checkpoint instead of starting over.

-----

## Part 6: Common Pitfalls & Solutions

### Pitfall 1: Over-Passing Context

❌ **Wrong**: Pass entire 5000-word reports to each phase

```json
{
  "phase_1_full_report": "[massive markdown blob]"
}
```

✅ **Right**: Pass summaries + file paths

```json
{
  "phase_1_summary": { "tables": 42, "fields": 367 },
  "phase_1_report_path": "/session/01-report.md"
}
```

Phases read full reports only if needed.

### Pitfall 2: Vague Contracts

❌ **Wrong**: "Return a JSON with your findings."

✅ **Right**: 
```json
{
  "status": "complete",
  "report_path": "/absolute/path.md",
  "phase_data": {
    "count": 23,
    "items": ["a", "b", "c"],
    "confidence": "high"
  }
}
```

Be explicit about types, required fields, structure.

### Pitfall 3: No Failure Path

❌ **Wrong**: "Complete the analysis and return results."

✅ **Right**: Define both success AND failure responses:

```json
Success: { "status": "complete", ... }
Failure: { "status": "failed", "error": "...", "partial_work": "..." }
```

### Pitfall 4: Verification Theater

❌ **Wrong**: Script just echoes what LLM said

```bash
echo '{"confirmed": true}'  # Useless
```

✅ **Right**: Script does independent computation

```bash
# Parse actual files
# Count actual occurrences
# Calculate actual percentages
# Output independently derived values
```

### Pitfall 5: Missing Session Isolation

❌ **Wrong**: All runs overwrite same files

```
reports/phase_1.md  # Gets overwritten each run
```

✅ **Right**: Unique timestamp-based sessions

```
reports/2025-01-15_143022/01-phase-1.md
reports/2025-01-15_150847/01-phase-1.md
```

-----

## Quick Reference Card

### Directory Structure

```
skill-name/
├── SKILL.md              # Orchestrator
├── agents/*.md           # Phase contracts
├── references/*.md       # Procedures + shared docs
├── scripts/*.sh          # Verification scripts
└── reports/
    ├── _samples/         # Example outputs
    └── {project}/        # Project-scoped sessions
        └── {timestamp}/  # Individual runs
```

### Phase Contract Template

```json
{
  "status": "complete|failed",
  "report_path": "/absolute/path/to/report.md",
  "error": "only if failed",
  "phase_data": {
    "key_metrics": "...",
    "findings": [...],
    "confidence": "high|medium|low"
  }
}
```

### Session Path Patterns

**Simple**: `reports/{YYYY-MM-DD_HHMMSS}/`

**Project-scoped**: `reports/{project_name}/{YYYY-MM-DD_HHMMSS}/`

### Reference Organization

```
references/
├── 01-phase-1.md         # Phase-specific
├── 02-phase-2.md         # Phase-specific
├── shared-standards.md   # Cross-cutting
└── output-templates.md   # Cross-cutting
```

### Validation Checklist

After each phase:
- [ ] Valid JSON?
- [ ] Status = "complete"?
- [ ] Report file exists?
- [ ] Required keys present?
- [ ] Types correct?
- [ ] Phase-specific validation passed?

### Context Passing Rule

> Pass summaries and paths, not full content.
> Each phase pulls what it needs from prior reports.

### The Verification Principle

> Any claim that can be checked programmatically, should be checked.
> Scripts provide ground truth. Reconciliation builds confidence.

### The Orchestration Equation

```
Monolithic Prompt (60k tokens, diluted attention)
    vs
5 Focused Phases (8-12k tokens each, peak attention)
    +
Empirical Verification (deterministic scripts)
    =
Production-Ready Agent System
```

-----

## Real-World Examples

### Example 1: Schema Optimization

**See**: [`schema-optimization/`](schema-optimization/)

Workflow:
1. Scan BigQuery schemas
2. Analyze field utilization patterns
3. Assess impact of removing fields
4. **Verify** with script that counts actual null percentages
5. Synthesize recommendations

Result: Reduces storage costs with confidence in recommendations.

### Example 2: Release Validation

Workflow:
1. Analyze git diff (what changed)
2. Predict test impact (which tests might fail)
3. Assess risk (breaking vs non-breaking changes)
4. **Verify** by running actual test suite
5. Go/no-go recommendation

Result: Automated release validation with empirical test evidence.

### Example 3: API Documentation Sync

Workflow:
1. Scan code for public APIs
2. Extract documented APIs
3. Compare code vs docs (gaps, stale docs)
4. **Verify** by running doc examples
5. Documentation update plan

Result: Keep docs synchronized with code reality.

-----

## Further Reading

- [GUIDE-00: Mental Model](GUIDE-00-START-HERE.md) - 5-minute introduction
- [GUIDE-01: Architecture Deep Dive](GUIDE-01-PATTERN-EXPLAINED.md) - 15-minute technical breakdown
- [GUIDE-02: Build Your Own](GUIDE-02-BUILDING-YOUR-OWN.md) - 30-minute adaptation guide
- [Reference Implementation](schema-optimization/SKILL.md) - Working 5-phase example
- [Visual Map](VISUAL-MAP.md) - Architecture diagrams

-----

**Pattern version**: 1.0.0  
**Last updated**: 2025-12-21  
**Maintained by**: intent solutions io

---

*This pattern transforms "LLM analyzed my code" into "LLM + script verified with evidence" — The foundation for production-ready agent systems.*
