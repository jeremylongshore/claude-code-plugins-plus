# GUIDE 03: Debugging Tips - Common Issues and Solutions

**Read time:** 15 minutes
**Goal:** Quickly diagnose and fix issues when workflows fail

---

## Debugging Strategy

```
Workflow fails
      ↓
1. Which phase failed?
   → Check orchestrator output
      ↓
2. What was the error?
   → Read phase output (JSON or error message)
      ↓
3. Was report file created?
   → Check session directory
      ↓
4. Is JSON valid?
   → Parse with jq or Python
      ↓
5. Are required keys present?
   → Compare against contract
      ↓
6. Did verification script run?
   → Check script exit code
      ↓
7. Fix the issue
   → Apply solution from this guide
```

---

## Common Issues and Solutions

### Issue 1: Phase Returns Text Instead of JSON

**Symptoms:**
```
Error: Failed to parse JSON from Phase 2
Output: "I analyzed the data and found 23 unused fields. Here's the JSON: {...}"
```

**Root cause:** Agent added explanatory text before/after JSON

**Solution 1: Update Reference Doc**
```markdown
## CRITICAL: Output Requirements

Return ONLY the JSON object below.
Do NOT add explanatory text.
Do NOT say "Here's the JSON" or similar.

Return EXACTLY this and nothing else:
```json
{
  "status": "complete",
  ...
}
```
```

**Solution 2: Update Agent Contract**
```markdown
## Output Format (JSON ONLY - NO TEXT)

**IMPORTANT:** Your ENTIRE response must be valid JSON.
Do not write any text before or after the JSON.

❌ WRONG:
I found 23 fields. Here's the JSON:
{"status": "complete"}

✅ CORRECT:
{"status": "complete", "report_path": "..."}
```

**Solution 3: Add JSON Extraction to Orchestrator**
```bash
# If agent adds text, extract JSON block
agent_output=$(spawn_phase_2)
json_only=$(echo "$agent_output" | sed -n '/^{/,/^}/p')
```

### Issue 2: Report File Not Created

**Symptoms:**
```
Error: Phase 3 validation failed
report_path file does not exist: /path/to/03-impact-assessment.md
```

**Root cause:** Agent returned JSON but didn't actually write file

**Solution 1: Update Reference Doc**
```markdown
## CRITICAL: File Writing

You MUST write the report file BEFORE returning JSON.

Steps:
1. Write complete report to {session_dir}/03-impact-assessment.md
2. Verify file exists on disk
3. Only then return JSON with report_path

If file writing fails, return:
{"status": "error", "error_message": "Failed to write report file"}
```

**Solution 2: Add Verification to Agent Prompt**
```markdown
## Pre-Flight Checklist

Before returning JSON, verify:
- [ ] Report file written to disk
- [ ] File path is correct
- [ ] File contains all required sections

If ANY check fails, return error status.
```

**Solution 3: Orchestrator Double-Check**
```bash
# After receiving JSON, immediately check file
if [ ! -f "$report_path" ]; then
  echo "ERROR: Phase 3 claimed file exists, but it doesn't: $report_path"
  exit 1
fi
```

### Issue 3: Verification Script Fails

**Symptoms:**
```
Error: Phase 4 script execution failed
Exit code: 1
Script: analyze_field_utilization.sh
```

**Root cause:** Script dependency missing, bad inputs, or logic error

**Solution 1: Test Script Standalone**
```bash
# Run script manually to see actual error
cd scripts/
./analyze_field_utilization.sh /path/to/input /path/to/output

# Check exit code
echo $?

# Check output
cat /path/to/output/results.json
```

**Solution 2: Add Debug Mode to Script**
```bash
#!/bin/bash
set -euo pipefail

# Add debug flag
DEBUG=${DEBUG:-0}
if [ "$DEBUG" -eq 1 ]; then
  set -x  # Print each command
fi

# Add verbose logging
log() {
  if [ "$DEBUG" -eq 1 ]; then
    echo "[DEBUG] $*" >&2
  fi
}

log "Starting analysis with input: $INPUT_PATH"
```

**Run with debug:**
```bash
DEBUG=1 ./analyze_field_utilization.sh input/ output/
```

**Solution 3: Add Input Validation**
```bash
#!/bin/bash

# Validate before processing
validate_inputs() {
  if [ ! -d "$INPUT_FOLDER" ]; then
    echo "ERROR: Input folder does not exist: $INPUT_FOLDER"
    exit 1
  fi

  if [ ! -w "$OUTPUT_FOLDER" ]; then
    echo "ERROR: Output folder not writable: $OUTPUT_FOLDER"
    exit 1
  fi

  # Check dependencies
  if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is required but not installed"
    exit 1
  fi
}

validate_inputs
# ... rest of script
```

### Issue 4: JSON Missing Required Keys

**Symptoms:**
```
Error: Phase 2 validation failed
Missing required key: utilization_summary.unused_fields
Received: {"status": "complete", "report_path": "...", "utilization_summary": {}}
```

**Root cause:** Agent didn't populate all summary fields

**Solution 1: Explicit Key Requirements in Reference**
```markdown
## Output Requirements

The JSON MUST include ALL of these keys:
- status (string: "complete" or "error")
- report_path (string: absolute path)
- utilization_summary (object with ALL of:)
  - unused_fields (array, can be empty: [])
  - low_utilization_fields (array, can be empty: [])
  - recommendations (array, can be empty: [])

Even if a category is empty, include it with an empty array.

❌ WRONG:
{"utilization_summary": {}}

✅ CORRECT:
{"utilization_summary": {"unused_fields": [], "low_utilization_fields": [], "recommendations": []}}
```

**Solution 2: Orchestrator Key Validation**
```python
# Python example
def validate_phase2_output(json_output):
    required_keys = {
        "status": str,
        "report_path": str,
        "utilization_summary": {
            "unused_fields": list,
            "low_utilization_fields": list,
            "recommendations": list
        }
    }

    def check_keys(data, schema, path=""):
        for key, expected_type in schema.items():
            if key not in data:
                raise ValueError(f"Missing required key: {path}{key}")

            if isinstance(expected_type, dict):
                check_keys(data[key], expected_type, f"{path}{key}.")
            elif not isinstance(data[key], expected_type):
                raise TypeError(f"Key {path}{key} should be {expected_type}, got {type(data[key])}")

    check_keys(json_output, required_keys)
    return True
```

### Issue 5: Session Directory Not Created

**Symptoms:**
```
Error: Cannot write report to /path/to/reports/runs/2025-01-15_143022/01-analysis.md
No such file or directory
```

**Root cause:** Orchestrator didn't create session directory before spawning phases

**Solution 1: Create Directory in Orchestrator**
```bash
# BEFORE spawning any phases
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
SESSION_DIR="${SKILL_DIR}/reports/runs/${TIMESTAMP}"
mkdir -p "$SESSION_DIR"

# Verify creation
if [ ! -d "$SESSION_DIR" ]; then
  echo "ERROR: Failed to create session directory: $SESSION_DIR"
  exit 1
fi

echo "Session directory created: $SESSION_DIR"
```

**Solution 2: Pass Absolute Path**
```bash
# Convert to absolute path before passing to phases
SESSION_DIR=$(realpath "$SESSION_DIR")

# Pass to Phase 1
spawn_phase_1 --session_dir="$SESSION_DIR"
```

### Issue 6: Phase 4 Can't Compare Conclusions

**Symptoms:**
```
Phase 4 report shows:
conclusions_confirmed: []
conclusions_revised: []
unexpected_findings: []
```

**Root cause:** Phase 4 couldn't extract structured conclusions from Phase 2/3 reports

**Solution 1: Standardize Phase 2/3 Report Format**
```markdown
# Phase 2 Reference: Add Structured Section

## Conclusions (Machine-Readable)

```json
{
  "unused_fields": [
    {"table": "users", "field": "legacy_id", "null_pct": 100.0},
    {"table": "orders", "field": "deprecated_flag", "null_pct": 98.5}
  ],
  "low_utilization_fields": [
    {"table": "products", "field": "internal_notes", "null_pct": 87.3}
  ]
}
```

This JSON block is extracted by Phase 4 for verification.
```

**Solution 2: Update Phase 4 Reference to Parse Markdown**
```markdown
## Step 1: Extract Conclusions from Phase 2/3

Read phase2_report_path.
Find the section: "## Conclusions (Machine-Readable)"
Extract the JSON block between ```json and ```
Parse as JSON to get structured conclusions.

If JSON block not found:
- Fall back to parsing markdown tables
- Or return error: "Phase 2 report missing machine-readable conclusions"
```

**Solution 3: Add JSON Artifacts**
```markdown
# Phase 2 should write TWO files:
1. {session_dir}/02-field-utilization-analysis.md (human-readable)
2. {session_dir}/02-conclusions.json (machine-readable)

# Phase 4 reads:
- phase2_report_path (markdown)
- phase2_conclusions_path (JSON)
```

### Issue 7: Orchestrator Doesn't Stop on Failure

**Symptoms:**
```
Phase 2 failed but Phase 3/4/5 still ran
Final output shows partial results
```

**Root cause:** Orchestrator not checking status before continuing

**Solution: Add Validation Gates**
```bash
# After each phase
phase2_output=$(spawn_phase_2)

# Parse JSON
phase2_status=$(echo "$phase2_output" | jq -r '.status')

# Check status
if [ "$phase2_status" != "complete" ]; then
  echo "ERROR: Phase 2 failed"
  echo "$phase2_output" | jq .

  # Return partial results
  cat <<EOF
{
  "status": "error",
  "failed_phase": 2,
  "error_message": "$(echo "$phase2_output" | jq -r '.error_message')",
  "session_dir": "$SESSION_DIR",
  "completed_phases": ["phase1"]
}
EOF
  exit 1
fi

# If we get here, Phase 2 succeeded
# Extract report path for Phase 3
phase2_report=$(echo "$phase2_output" | jq -r '.report_path')
```

### Issue 8: Timestamps Collide (Multiple Runs)

**Symptoms:**
```
Error: Session directory already exists
Cannot create: /path/to/reports/runs/2025-01-15_143022
```

**Root cause:** Two workflow runs started in same second

**Solution 1: Add Milliseconds to Timestamp**
```bash
# Instead of:
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)

# Use:
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S-%3N)  # Linux
# or
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)-$(date +%N | cut -c1-3)
```

**Solution 2: Add Random Suffix**
```bash
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
RANDOM_SUFFIX=$(head -c 4 /dev/urandom | xxd -p)
SESSION_DIR="reports/runs/${TIMESTAMP}-${RANDOM_SUFFIX}"
```

**Solution 3: Check and Increment**
```bash
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
SESSION_DIR="reports/runs/${TIMESTAMP}"
COUNTER=0

while [ -d "$SESSION_DIR" ]; do
  COUNTER=$((COUNTER + 1))
  SESSION_DIR="reports/runs/${TIMESTAMP}-${COUNTER}"
done

mkdir -p "$SESSION_DIR"
```

### Issue 9: Large Reports Exceed Token Limits

**Symptoms:**
```
Phase 5 fails when trying to read all prior reports
Error: Context too long
```

**Root cause:** Phase 5 reads all 4 prior reports, exceeds LLM context

**Solution 1: Pass Summaries Instead of Full Reports**
```bash
# Phase 1 returns: schema_summary
# Phase 2 returns: utilization_summary
# Phase 3 returns: impact_summary
# Phase 4 returns: verification_summary

# Phase 5 receives:
# - phase1_summary (JSON object)
# - phase2_summary (JSON object)
# - phase3_summary (JSON object)
# - phase4_summary (JSON object)
# - phase1_report_path (for reference if needed)

# Phase 5 can synthesize from summaries (small)
# Only read full reports if clarification needed
```

**Solution 2: Chunked Reading**
```markdown
# Phase 5 Reference:

## Step 1: Read Executive Summaries Only
For each prior phase report:
- Read ONLY the "## Executive Summary" section (first 10 lines)
- Skip detailed findings

This gives you the gist without full context.
```

**Solution 3: Aggregate Report**
```bash
# Orchestrator creates aggregate.json before Phase 5
cat > "$SESSION_DIR/_aggregate.json" <<EOF
{
  "phase1": $(echo "$phase1_output" | jq '.phase_summary'),
  "phase2": $(echo "$phase2_output" | jq '.phase_summary'),
  "phase3": $(echo "$phase3_output" | jq '.phase_summary'),
  "phase4": $(echo "$phase4_output" | jq '.verification_summary')
}
EOF

# Phase 5 only reads this file (much smaller)
```

### Issue 10: Verification Script Is Non-Deterministic

**Symptoms:**
```
Run 1: Script finds 10 issues
Run 2: Script finds 12 issues (same data)
```

**Root cause:** Script has randomness or external dependencies

**Common causes:**
- Using `find` without `-sorted` (order varies)
- Network calls (API responses change)
- Timestamps in output (changes each run)
- Parallel processing without deterministic ordering

**Solution 1: Deterministic Ordering**
```bash
# Instead of:
for file in $(find . -name "*.json"); do
  process "$file"
done

# Use:
for file in $(find . -name "*.json" | sort); do
  process "$file"
done
```

**Solution 2: Remove Timestamps from Comparisons**
```bash
# When comparing script output to manual predictions:
# Strip timestamp fields before comparison

jq 'del(.timestamp, .metadata.generated_at)' script-output.json > normalized.json
```

**Solution 3: Seed Randomness (If Needed)**
```bash
# If script uses random sampling:
RANDOM_SEED=${RANDOM_SEED:-42}
export RANDOM_SEED

# In script:
# Python: random.seed(int(os.environ['RANDOM_SEED']))
# Bash: RANDOM=$RANDOM_SEED
```

---

## Debugging Tools

### 1. Validate JSON Output

```bash
# Test if output is valid JSON
echo "$phase_output" | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "ERROR: Invalid JSON"
  echo "$phase_output"
  exit 1
fi
```

### 2. Extract Specific Keys

```bash
# Get specific key from JSON
status=$(echo "$phase_output" | jq -r '.status')
report_path=$(echo "$phase_output" | jq -r '.report_path')

# Check if key exists
if [ "$(echo "$phase_output" | jq 'has("phase_summary")')" != "true" ]; then
  echo "ERROR: Missing phase_summary"
  exit 1
fi
```

### 3. Diff Expected vs Actual

```bash
# Save expected output
cat > expected.json <<EOF
{
  "status": "complete",
  "report_path": "/path/to/report.md",
  "phase_summary": {
    "key1": "value1"
  }
}
EOF

# Compare
diff <(jq -S . expected.json) <(jq -S . actual.json)
```

### 4. Test Script in Isolation

```bash
# Create test input directory
mkdir -p test-input
echo '{"test": "data"}' > test-input/sample.json

# Run script
./scripts/analyze_field_utilization.sh test-input test-output

# Verify output
cat test-output/results.json | jq .

# Check exit code
echo "Exit code: $?"
```

### 5. Trace Orchestrator Execution

```bash
# Add verbose logging to orchestrator
set -x  # Print each command

# Or selective logging:
log() {
  echo "[$(date -Iseconds)] $*" >&2
}

log "Creating session directory: $SESSION_DIR"
mkdir -p "$SESSION_DIR"
log "Spawning Phase 1"
phase1_output=$(spawn_phase_1)
log "Phase 1 complete. Status: $(echo "$phase1_output" | jq -r '.status')"
```

---

## Prevention Checklist

**Before running workflow:**
- [ ] All reference docs have explicit JSON requirements
- [ ] All agents are instructed: "Return JSON only, no text"
- [ ] All report file paths are absolute (not relative)
- [ ] Session directory creation is verified
- [ ] Verification script tested standalone
- [ ] All JSON schemas documented
- [ ] Validation gates after each phase
- [ ] Error handling for all failure modes

**After first successful run:**
- [ ] Save outputs as reference (`_samples/`)
- [ ] Document any manual fixes needed
- [ ] Update reference docs with lessons learned
- [ ] Add to regression tests

---

## When to Ask for Help

**You've debugged for >1 hour and:**
- JSON parsing fails inexplicably
- Script works standalone but fails in workflow
- Orchestrator spawning mechanism unclear
- Context limits hit despite optimizations
- Non-deterministic failures

**What to provide:**
1. Exact error message
2. Phase that failed
3. JSON output (sanitized)
4. Reference doc for that phase
5. What you've tried
6. Minimal reproduction case

---

## Quick Reference: Common Fixes

| Issue | Quick Fix |
|-------|-----------|
| Text before JSON | Update reference: "Return JSON only" |
| Missing report file | Add pre-flight check: file exists before JSON |
| Invalid JSON | Test with `jq .` |
| Script fails | Run standalone with debug mode |
| Missing keys | List ALL required keys in reference |
| Dir not created | `mkdir -p` before first phase |
| Phase 4 empty results | Add machine-readable section to Phase 2/3 |
| Doesn't stop on fail | Check `status` after each phase |
| Timestamp collision | Add milliseconds or random suffix |
| Context too long | Pass summaries, not full reports |

---

**Next:** Put it all together with hands-on exercises in `exercises/`

---

*End of debugging guide. You should now be able to diagnose and fix most workflow issues.*
