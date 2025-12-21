# GUIDE 02: Building Your Own Workflow

**Read time:** 30 minutes
**Goal:** Adapt the test harness pattern for your specific use case

---

## Decision Tree: Do I Need This Pattern?

```
Start: I have a multi-step workflow

Q1: Does it involve more than 2 steps?
    No → Just use a simple prompt, no need for test harness
    Yes → Continue to Q2

Q2: Do I need to verify the work was actually done?
    No → Simple multi-turn conversation is fine
    Yes → Continue to Q3

Q3: Can I validate outputs programmatically?
    No → Test harness won't help (need human judgment)
    Yes → Continue to Q4

Q4: Is there a deterministic way to check conclusions?
    No → Consider adding one (script/tool), but pattern still useful
    Yes → USE TEST HARNESS PATTERN ✅

Example YES cases:
- Data pipeline validation
- Code review workflows
- Compliance audits
- Research synthesis with citation checking
- Security scans with tool verification

Example NO cases:
- Creative writing (no objective validation)
- Open-ended brainstorming (no right answer)
- Simple Q&A (single-turn)
- Purely subjective evaluations
```

---

## Step-by-Step: Adapt for Your Use Case

### Step 1: Define Your Workflow Phases

**Template:**
```
Phase 1: [Initial Analysis/Collection]
Purpose: Establish baseline, gather data
Output: Summary of what was found

Phase 2: [Deep Analysis]
Purpose: Analyze patterns, identify issues
Output: Detailed findings with evidence

Phase 3: [Risk/Impact Assessment]
Purpose: Evaluate consequences, prioritize
Output: Risk scores, impact estimates

Phase 4: [Verification]
Purpose: Empirically validate conclusions
Output: Confirmed vs revised findings

Phase 5: [Recommendations]
Purpose: Synthesize into action plan
Output: Prioritized recommendations
```

**Your workflow:**
1. Write down your end goal
2. Work backwards: what's the last step before that goal?
3. What needs to happen before that step?
4. Keep breaking down until you have 3-7 phases
5. Identify which phase can run a deterministic check (your "Phase 4")

**Examples:**

**Code Review Workflow:**
```
Phase 1: File Discovery - Find all changed files
Phase 2: Static Analysis - Run linters/formatters
Phase 3: Pattern Detection - Identify anti-patterns
Phase 4: Test Verification - Run test suite, compare coverage
Phase 5: Review Summary - Aggregate all findings
```

**Security Audit Workflow:**
```
Phase 1: Surface Scan - Identify entry points
Phase 2: Vulnerability Analysis - Check OWASP Top 10
Phase 3: Risk Scoring - Categorize by severity
Phase 4: Tool Verification - Run SAST/DAST, compare findings
Phase 5: Remediation Plan - Prioritize fixes
```

**Research Synthesis Workflow:**
```
Phase 1: Paper Collection - Gather relevant papers
Phase 2: Theme Extraction - Identify common themes
Phase 3: Gap Analysis - Find research gaps
Phase 4: Citation Verification - Run citation analysis, verify connections
Phase 5: Synthesis Report - Write literature review
```

### Step 2: Design Your Session Directory

**Pattern:**
```
reports/runs/<timestamp>/
├── 01-<phase1-name>.md
├── 02-<phase2-name>.md
├── 03-<phase3-name>.md
├── 04-<phase4-name>.md
└── 05-<phase5-name>.md
```

**Customization:**
- Rename `reports/` to match your domain (e.g., `audits/`, `reviews/`, `syntheses/`)
- Add phase-specific artifacts (e.g., `04-test-results.json`, `02-lint-output.txt`)
- Include metadata file (e.g., `_session-metadata.json`)

**Example: Code Review**
```
reviews/runs/2025-01-15_143022/
├── 01-file-discovery.md
├── 02-static-analysis.md
├── 02-lint-output.txt           # Linter raw output
├── 03-pattern-detection.md
├── 04-test-verification.md
├── 04-test-results.json         # Test suite JSON output
├── 05-review-summary.md
└── _metadata.json               # PR number, author, timestamp
```

### Step 3: Define JSON Contracts

**For each phase, specify:**

```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/report.md",
  "phase_summary": {
    // Phase-specific keys here
  }
}
```

**Phase 1 example (File Discovery):**
```json
{
  "status": "complete",
  "report_path": "/path/to/01-file-discovery.md",
  "phase_summary": {
    "files_changed": 12,
    "lines_added": 456,
    "lines_removed": 123,
    "languages": ["python", "javascript"]
  }
}
```

**Phase 4 example (Test Verification):**
```json
{
  "status": "complete",
  "report_path": "/path/to/04-test-verification.md",
  "verification_summary": {
    "tests_run": 145,
    "tests_passed": 143,
    "tests_failed": 2,
    "coverage_before": 78.5,
    "coverage_after": 82.3,
    "manual_predictions_confirmed": [
      "Predicted test_foo would fail: CONFIRMED"
    ],
    "manual_predictions_revised": [
      "Predicted test_bar would pass: REVISED (failed)"
    ]
  }
}
```

**Tip:** Phase 4 should always have:
- `conclusions_confirmed`: What manual analysis got right
- `conclusions_revised`: What needed correction
- `unexpected_findings`: What manual analysis missed

### Step 4: Write Reference Docs

**Template for each reference doc:**

```markdown
# Phase N: [Name]

## Context
[1-2 paragraphs: what this phase does, why it matters]

## Inputs Available

You have access to:
- `skill_dir`: [describe]
- `session_dir`: [describe]
- `input_folder`: [describe]
- `phaseX_report_path`: [describe prior phases]

## Step-by-Step Procedure

### Step 1: [Concrete Action]
[Detailed instructions]
[Example commands/code if applicable]

Expected output: [describe]

### Step 2: [Concrete Action]
[Detailed instructions]

Expected output: [describe]

### Step 3: [Concrete Action]
[Continue until work is complete]

## Report Format

Write to: `{session_dir}/0N-[name].md`

Required sections:
- ## Executive Summary (3-5 bullets)
- ## Methodology (how you did it)
- ## Findings (what you found, with evidence)
- ## [Phase-Specific Section]
- ## Next Steps (what Phase N+1 should focus on)

## Output Requirements

Return JSON only (no explanatory text):
```json
{
  "status": "complete",
  "report_path": "<absolute path>",
  "phase_summary": {
    "key1": "<value>",
    "key2": "<value>"
  }
}
```

## Quality Checklist
- [ ] All data sources documented in report
- [ ] Metrics include methodology
- [ ] Findings are evidence-based (not speculation)
- [ ] Report file exists on disk before returning JSON
- [ ] JSON includes all required keys
```

**Critical: Phase 4 Reference (Verification)**

```markdown
# Phase 4: [Name] Verification

## Context
Phases 2-3 made conclusions through manual analysis.
This phase runs deterministic tools to empirically validate those conclusions.

## Key Conclusions from Prior Phases to Verify

Read `phase2_report_path` and `phase3_report_path`.

Extract the following claims:
- [Specific claim type 1]
- [Specific claim type 2]
- [Specific claim type 3]

## Step-by-Step Procedure

### Step 1: Extract Manual Conclusions
From Phase 2/3 reports, create a structured list:
```
Claim 1: [description]
Evidence cited: [what Phase 2/3 based this on]

Claim 2: [description]
Evidence cited: [what Phase 2/3 based this on]
```

### Step 2: Execute Verification Tool
Run: `scripts/[your-verification-script.sh] <input> <output>`

This script must:
- Be deterministic (same inputs = same outputs)
- Produce structured output (JSON preferred)
- Complete quickly (<5 minutes)

### Step 3: Parse Tool Output
Read the script's output file.
Extract measurable facts (not opinions).

### Step 4: Compare Manual vs Empirical
For each claim from Phase 2/3:

If tool confirms (matches within tolerance):
→ Add to `conclusions_confirmed`

If tool differs significantly:
→ Add to `conclusions_revised` with explanation

If tool finds issues not in Phase 2/3:
→ Add to `unexpected_findings`

### Step 5: Update Action Items
Based on comparison:
- Keep actions based on confirmed conclusions
- Revise actions based on revised conclusions
- Add new actions based on unexpected findings

### Step 6: Write Verification Report
Save to: `{session_dir}/04-[name]-verification.md`

Required sections:
- ## Original Conclusions (from Phase 2/3)
- ## Tool Execution Results
- ## Comparison Analysis (table format)
  | Claim | Manual Analysis | Tool Result | Status | Notes |
  |-------|----------------|-------------|--------|-------|
  | ...   | ...            | ...         | ...    | ...   |
- ## Revised Action Items

### Step 7: Return JSON
```json
{
  "status": "complete",
  "report_path": "<absolute>",
  "verification_summary": {
    "tool_executed": "<script name>",
    "tool_runtime_seconds": N,
    "conclusions_confirmed": ["claim1: confirmed within 5% tolerance"],
    "conclusions_revised": ["claim2: was X, actually Y"],
    "unexpected_findings": ["claim3: tool found issue not in manual analysis"],
    "revised_action_items": ["action1: safe (confirmed)", "action2: needs review (revised)"]
  }
}
```
```

### Step 5: Create Verification Script

**Requirements:**
1. **Deterministic:** No randomness, no LLM calls, no API dependencies
2. **Fast:** Completes in seconds to minutes (not hours)
3. **Structured output:** JSON preferred, CSV acceptable
4. **Self-validating:** Checks inputs before processing
5. **Error handling:** Returns meaningful errors

**Template:**

```bash
#!/bin/bash
# [Your Verification Script]
# Purpose: [What it verifies]
# Inputs: [Describe]
# Outputs: [Describe]

set -euo pipefail  # Exit on error

# ===========================================
# Configuration
# ===========================================
SCRIPT_NAME=$(basename "$0")
VERSION="1.0.0"

# ===========================================
# Input Validation
# ===========================================
if [ $# -ne 2 ]; then
  echo "Usage: $SCRIPT_NAME <input_path> <output_path>"
  echo "  input_path: Directory or file to analyze"
  echo "  output_path: Where to write results"
  exit 1
fi

INPUT_PATH="$1"
OUTPUT_PATH="$2"

if [ ! -e "$INPUT_PATH" ]; then
  echo "Error: Input path does not exist: $INPUT_PATH"
  exit 1
fi

mkdir -p "$OUTPUT_PATH"

# ===========================================
# Main Analysis Logic
# ===========================================
echo "Starting analysis..."
START_TIME=$(date +%s)

# [Your analysis code here]
# Example: Parse files, calculate metrics, etc.

METRICS_CALCULATED=0
ISSUES_FOUND=0

for file in "$INPUT_PATH"/*; do
  if [ -f "$file" ]; then
    # Process file
    # Increment metrics
    METRICS_CALCULATED=$((METRICS_CALCULATED + 1))
  fi
done

END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))

# ===========================================
# Output Generation
# ===========================================
cat > "$OUTPUT_PATH/results.json" <<EOF
{
  "metadata": {
    "script": "$SCRIPT_NAME",
    "version": "$VERSION",
    "timestamp": "$(date -Iseconds)",
    "runtime_seconds": $RUNTIME
  },
  "input": {
    "path": "$INPUT_PATH",
    "files_processed": $METRICS_CALCULATED
  },
  "results": {
    "issues_found": $ISSUES_FOUND,
    "metrics": {
      "key1": "value1",
      "key2": "value2"
    }
  }
}
EOF

echo "Analysis complete: $OUTPUT_PATH/results.json"
echo "Runtime: ${RUNTIME}s"
exit 0
```

**Make it executable:**
```bash
chmod +x scripts/your-verification-script.sh
```

### Step 6: Build Orchestrator

**Copy and adapt:** `schema-optimization/SKILL.md`

**Key changes:**
1. Update phase names and counts
2. Update input schema (what your workflow needs)
3. Update JSON validation rules (match your phase summaries)
4. Update phase invocation (pass your specific inputs)

**Orchestrator checklist:**
- [ ] Creates timestamp-based session directory
- [ ] Spawns Phase 1 with initial inputs
- [ ] Validates Phase 1 JSON and report file
- [ ] Spawns Phase 2 with Phase 1 report path
- [ ] Validates each phase before continuing
- [ ] Spawns Phase 4 with script path and output folder
- [ ] Validates Phase 4 verification summary
- [ ] Aggregates final JSON output
- [ ] Handles errors gracefully (no partial runs)

### Step 7: Create Sample Outputs

**Purpose:** Show users what good looks like

**What to include:**
1. Complete session directory with all phase reports
2. Realistic data (not placeholders)
3. Proper formatting (follow your standards)
4. Phase 4 showing actual verification (script output vs manual)

**Tip:** Run the workflow once manually, save the outputs, clean them up, move to `_samples/`

---

## Real-World Examples

### Example 1: API Documentation Audit

**Goal:** Verify API docs match actual code

**Phases:**
1. **Discovery:** Find all API endpoints in code
2. **Doc Extraction:** Extract documented endpoints
3. **Gap Analysis:** Compare code vs docs
4. **Verification:** Run script to test each endpoint, verify responses match docs
5. **Remediation Plan:** Prioritize doc updates

**Phase 4 script:**
```bash
# test_api_endpoints.sh
# Calls each endpoint, compares response schema to documented schema
curl -X GET /api/users | jq . > actual-response.json
jq . docs/api/users.json > documented-response.json
diff actual-response.json documented-response.json
```

**Verification summary:**
```json
{
  "endpoints_tested": 42,
  "endpoints_matching_docs": 38,
  "endpoints_diverged": 4,
  "undocumented_endpoints": 2
}
```

### Example 2: Infrastructure Drift Detection

**Goal:** Verify Terraform state matches actual cloud resources

**Phases:**
1. **State Analysis:** Parse Terraform state files
2. **Resource Inventory:** List what should exist
3. **Risk Assessment:** Categorize by criticality
4. **Verification:** Run `terraform plan`, compare predicted drift vs actual
5. **Reconciliation Plan:** Steps to fix drift

**Phase 4 script:**
```bash
# verify_terraform_state.sh
terraform plan -detailed-exitcode -out=tfplan
terraform show -json tfplan > actual-plan.json
# Compare manual predictions vs terraform's actual plan
```

**Verification summary:**
```json
{
  "resources_checked": 156,
  "drift_predicted": 12,
  "drift_confirmed": 10,
  "drift_false_positives": 2,
  "unexpected_drift": 3
}
```

### Example 3: Dependency Security Audit

**Goal:** Verify manual security review matches automated scans

**Phases:**
1. **Dependency Tree:** Build complete dependency graph
2. **Manual Review:** Identify suspicious/outdated packages
3. **Risk Scoring:** Categorize by severity
4. **Verification:** Run `npm audit`, `safety check`, compare findings
5. **Remediation:** Prioritize updates

**Phase 4 script:**
```bash
# verify_dependencies.sh
npm audit --json > npm-audit-results.json
safety check --json > safety-results.json
# Compare manual findings vs automated scan results
```

**Verification summary:**
```json
{
  "packages_scanned": 234,
  "vulnerabilities_predicted": 8,
  "vulnerabilities_confirmed": 7,
  "vulnerabilities_revised": 1,
  "critical_unexpected": 2
}
```

---

## Common Adaptations

### Fewer Phases (3-Phase Workflow)

```
Phase 1: Initial Analysis
Phase 2: Verification with Tool (critical)
Phase 3: Recommendations
```

**When to use:** Simple workflows, quick audits

### More Phases (7-Phase Workflow)

```
Phase 1: Discovery
Phase 2: Collection
Phase 3: Analysis
Phase 4: Deep Dive
Phase 5: Verification 1 (Tool A)
Phase 6: Verification 2 (Tool B)
Phase 7: Synthesis
```

**When to use:** Complex workflows, multiple verification steps

### Parallel Verification Phases

```
Phase 4a: Linter Verification
Phase 4b: Test Suite Verification
Phase 4c: Security Scan Verification
Phase 5: Aggregate Verifications
```

**Implementation:** Orchestrator spawns 4a/4b/4c concurrently, waits for all, then Phase 5

---

## Checklist: Before You Deploy

**Pre-Deployment:**
- [ ] All phases return valid JSON (test manually)
- [ ] All report files are written before JSON return (verify)
- [ ] Verification script runs independently (test outside workflow)
- [ ] Orchestrator validates all required keys (test with missing keys)
- [ ] Session directories are created with timestamps (check naming)
- [ ] Reference docs are clear and actionable (have someone else read)
- [ ] Sample outputs demonstrate realistic workflow (not placeholders)
- [ ] Error handling works (test with bad inputs)

**Production Readiness:**
- [ ] Add logging (orchestrator logs each phase start/end)
- [ ] Add monitoring (track success rate, runtime)
- [ ] Add alerting (notify on failures)
- [ ] Add cleanup (old session directories)
- [ ] Document for ops team (how to run, how to debug)
- [ ] Load test (can it handle expected volume?)
- [ ] Security review (no secrets in logs, proper permissions)

---

## Next Steps

**Hands-on practice:**
Read `exercises/exercise-4-build-from-scratch.md` and build a 3-phase workflow.

**Debugging help:**
Read `GUIDE-03-DEBUGGING-TIPS.md` for common issues and solutions.

**Deploy to production:**
Move your workflow out of `workspace/lab/` into `.claude/skills/` and test with real data.

---

*Next: GUIDE-03-DEBUGGING-TIPS.md*
