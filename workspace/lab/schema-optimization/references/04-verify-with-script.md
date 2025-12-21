# Phase 4 Reference: Verify Field Utilization with Script

## Context

**This is the critical "make it real" phase.**

Phases 2-3 analyzed field utilization through manual analysis and made conclusions about unused/low-utilization fields. This phase runs a deterministic script to empirically validate those conclusions.

**Why this matters:**
- Manual analysis (LLM) can make mistakes or miss edge cases
- Script provides objective, reproducible evidence
- Comparing manual vs script catches errors early
- Builds trust in final recommendations (Phase 5)

## Inputs Available

- `skill_dir`: Absolute path to schema-optimization skill directory
- `session_dir`: Absolute path to this run's session directory
- `reference_path`: Path to this reference doc (for self-reference)
- `phase2_report_path`: Absolute path to Phase 2's report file
- `phase3_report_path`: Absolute path to Phase 3's report file
- `input_folder`: Path to schema export files
- `script_path`: Absolute path to verification script (`scripts/analyze_field_utilization.sh`)
- `output_folder_path`: Where script should write results

## Key Conclusions from Phase 2/3 to Verify

Before starting, you must extract the specific claims made in Phases 2-3.

**From Phase 2 (Field Utilization Analysis):**
Look for:
- List of "unused fields" (>90% null)
- List of "low utilization fields" (70-90% null)
- Null percentage estimates for specific fields
- Recommendations based on these findings

**From Phase 3 (Impact Assessment):**
Look for:
- Fields categorized as "safe to remove" (based on Phase 2 data)
- Storage savings estimates (based on field counts)
- Risk assessments (high/medium/low risk)

**Extract to a structured list:**

```
Claim 1: table.field is unused (100% null)
  Source: Phase 2, Section "Unused Fields"
  Evidence cited: "Analyzed 1000 rows, all NULL"

Claim 2: table.field2 is low utilization (85% null)
  Source: Phase 2, Section "Low Utilization"
  Evidence cited: "850/1000 rows are NULL"

Claim 3: Removing field X will save Y GB
  Source: Phase 3, Section "Storage Savings"
  Evidence cited: "Field is STRING(1000), unused in 100% of rows"
```

## Step-by-Step Procedure

### Step 1: Read Phase 2 and Phase 3 Reports

Open both report files:

```bash
cat <phase2_report_path>
cat <phase3_report_path>
```

**Extract conclusions manually or programmatically:**

If reports have "## Key Findings (Machine-Readable)" sections with JSON:
- Parse the JSON blocks
- Extract field lists and null percentages

If reports are plain markdown:
- Find tables or bullet lists of unused/low-util fields
- Extract field names and percentages manually

**Create a comparison checklist:**

```markdown
| Field | Manual Claim | Manual Null% | Script Null% | Status | Notes |
|-------|--------------|--------------|--------------|--------|-------|
| users.legacy_id | Unused | 100% | TBD | TBD | TBD |
| orders.notes | Low util | 85% | TBD | TBD | TBD |
```

### Step 2: Execute Verification Script

Run the script:

```bash
chmod +x <script_path>
<script_path> <input_folder> <output_folder_path>
```

**Expected behavior:**
- Script scans all JSON/CSV files in `input_folder`
- Calculates ACTUAL null percentages for each field
- Writes results to `<output_folder_path>/field_utilization_report.json`

**Monitor for errors:**
- Check exit code: `echo $?` (should be 0)
- Check output file exists: `ls -lh <output_folder_path>/field_utilization_report.json`

### Step 3: Parse Script Output

Read the script's JSON output:

```bash
cat <output_folder_path>/field_utilization_report.json | jq .
```

**Expected format:**
```json
{
  "files_analyzed": 42,
  "timestamp": "2025-01-15T14:30:22-06:00",
  "field_usage_breakdown": {
    "unused_fields": [
      {"table": "users", "field": "legacy_id", "null_pct": 100.0},
      {"table": "products", "field": "old_sku", "null_pct": 98.5}
    ],
    "low_utilization_fields": [
      {"table": "orders", "field": "internal_notes", "null_pct": 87.3}
    ],
    "high_utilization_fields": [...]
  },
  "summary": {
    "total_fields": 367,
    "unused_count": 23,
    "low_util_count": 15,
    "high_util_count": 329
  }
}
```

Extract:
- `files_analyzed` (verify matches expected input file count)
- `unused_fields` array (script's empirical findings)
- `low_utilization_fields` array
- Null percentages for each field

### Step 4: Compare Manual vs Script Results

For each claim from Phase 2/3, compare against script results.

**Comparison logic:**

```
For each field in manual conclusions:
  1. Find field in script output
  2. Compare null percentages
  3. Categorize result:

  If |manual_pct - script_pct| <= 5%:
    → CONFIRMED (close enough)
    Add to: conclusions_confirmed

  If |manual_pct - script_pct| > 5%:
    → REVISED (significant difference)
    Add to: conclusions_revised
    Note: "Manual: X%, Script: Y%"

  If field not in script output:
    → UNEXPECTED (script didn't find field)
    Add to: unexpected_findings
    Note: "Field not found in script analysis"
```

**For fields in script output NOT in manual analysis:**
```
  → UNEXPECTED (manual missed this)
  Add to: unexpected_findings
  Note: "Script found unused field not identified manually: table.field (Z% null)"
```

### Step 5: Update Action Items

Based on comparison results:

**Confirmed conclusions → Safe actions:**
```
"Remove users.legacy_id: SAFE (script confirmed 100% null, manual predicted 100%)"
```

**Revised conclusions → Risky actions:**
```
"Re-evaluate orders.notes: RISKY (manual predicted 85% null, script shows 68% null)"
```

**Unexpected findings → New actions:**
```
"Investigate products.deprecated_flag: NEW (script found 99% null, not in manual analysis)"
```

### Step 6: Write Verification Report

Save to: `{session_dir}/04-field-utilization-verification.md`

**Required sections:**

```markdown
# Phase 4: Field Utilization Verification

**Session:** <session_id>
**Generated:** <timestamp>
**Script Executed:** <script_path>
**Script Runtime:** X seconds

---

## Executive Summary

- Script analyzed N files
- Confirmed X/Y manual conclusions
- Revised Z conclusions based on empirical data
- Found W unexpected issues not in manual analysis
- Updated action items: A safe actions, B risky actions

---

## Original Conclusions (From Phase 2/3)

### Unused Fields (Manual Analysis)
1. `users.legacy_id` - Claimed 100% null
2. `orders.old_reference` - Claimed 98% null
3. ...

### Low Utilization Fields (Manual Analysis)
1. `products.internal_notes` - Claimed 85% null
2. ...

### Recommendations (From Phase 3)
- Remove 23 unused fields → save 45GB storage
- Archive 15 low-util fields → save 12GB storage

---

## Script Execution Results

### Script Metadata
- **Script:** analyze_field_utilization.sh v1.0.0
- **Input:** <input_folder>
- **Files Analyzed:** 42
- **Total Fields Scanned:** 367
- **Runtime:** 3.2 seconds

### Script Findings

#### Unused Fields (Script)
| Table | Field | Null % |
|-------|-------|--------|
| users | legacy_id | 100.0 |
| products | old_sku | 98.5 |
| ... | ... | ... |

#### Low Utilization Fields (Script)
| Table | Field | Null % |
|-------|-------|--------|
| orders | internal_notes | 68.2 |
| ... | ... | ... |

---

## Comparison Analysis

| Field | Manual Null% | Script Null% | Diff | Status | Notes |
|-------|--------------|--------------|------|--------|-------|
| users.legacy_id | 100% | 100% | 0% | ✅ CONFIRMED | Exact match |
| orders.old_reference | 98% | 97.8% | 0.2% | ✅ CONFIRMED | Within tolerance |
| products.internal_notes | 85% | 68.2% | 16.8% | ⚠️ REVISED | Significantly lower |
| orders.deprecated_flag | N/A | 99.1% | N/A | 🔍 UNEXPECTED | Manual analysis missed this |

### Summary
- **Confirmed:** 21/23 conclusions (91%)
- **Revised:** 2/23 conclusions (9%)
- **Unexpected findings:** 3 fields

---

## Detailed Comparison

### Conclusions Confirmed (21 fields)

1. **users.legacy_id**: Manual 100%, Script 100%
   - Action: Safe to remove ✅
   - Storage savings estimate: 2.3GB

2. **products.old_sku**: Manual 98%, Script 98.5%
   - Action: Safe to remove ✅
   - Storage savings estimate: 1.1GB

...

### Conclusions Revised (2 fields)

1. **products.internal_notes**: Manual 85%, Script 68.2%
   - Issue: Manual overestimated null percentage
   - Root cause: Manual sample size too small (1000 rows), script analyzed all data
   - Action: DO NOT remove (still 32% utilized) ⚠️
   - Updated recommendation: Monitor usage, consider keeping

2. **orders.metadata**: Manual 92%, Script 78.5%
   - Issue: Manual overestimated null percentage
   - Action: Downgrade from "safe to remove" to "needs investigation" ⚠️

### Unexpected Findings (3 fields)

1. **orders.deprecated_flag**: Script 99.1% null
   - Not identified in manual analysis
   - Action: Add to safe removal list ✅
   - Estimated savings: 0.5GB

2. **users.legacy_email**: Script 97.8% null
   - Not identified in manual analysis
   - Action: Add to safe removal list ✅
   - Estimated savings: 1.2GB

3. **products.temp_field**: Script 100% null
   - Not identified in manual analysis
   - Action: Immediate removal candidate ✅
   - Estimated savings: 0.8GB

---

## Revised Action Items

### High Priority (Safe - Confirmed by Script)

1. **Remove users.legacy_id** (100% null, confirmed)
   - Storage savings: 2.3GB
   - Risk: LOW
   - Dependencies: None found

2. **Remove products.old_sku** (98.5% null, confirmed)
   - Storage savings: 1.1GB
   - Risk: LOW
   - Dependencies: None found

... (21 total)

### Medium Priority (New - Found by Script)

1. **Remove orders.deprecated_flag** (99.1% null, unexpected finding)
   - Storage savings: 0.5GB
   - Risk: MEDIUM (manual analysis missed this - verify no code dependencies)

... (3 total)

### Low Priority (Revised - Needs Further Analysis)

1. **Monitor products.internal_notes** (68.2% null, not 85%)
   - Action: Do NOT remove
   - Next step: Analyze which teams/processes use this field

2. **Investigate orders.metadata** (78.5% null, not 92%)
   - Action: Needs manual review before deciding
   - Next step: Check query logs for usage patterns

---

## Updated Storage Savings Estimate

**Original estimate (Phase 3):**
- Remove 23 unused fields: 45GB savings
- Archive 15 low-util fields: 12GB savings
- **Total: 57GB**

**Revised estimate (after verification):**
- Remove 21 confirmed unused fields: 42.5GB savings
- Remove 3 newly found fields: 2.5GB savings
- Archive 13 low-util fields (removed 2): 10.2GB savings
- **Total: 55.2GB (-3% from original)**

**Confidence level:** HIGH (empirically validated)

---

## Verification Summary (Machine-Readable)

```json
{
  "script_metadata": {
    "script": "analyze_field_utilization.sh",
    "version": "1.0.0",
    "runtime_seconds": 3.2,
    "files_analyzed": 42
  },
  "comparison_results": {
    "total_claims": 23,
    "confirmed": 21,
    "revised": 2,
    "unexpected_findings": 3
  },
  "revised_storage_savings_gb": 55.2,
  "confidence_level": "high"
}
```

---

## Recommendations for Phase 5

- Prioritize the 21 confirmed safe removals (high confidence)
- Create investigation tasks for 2 revised fields (need manual review)
- Include 3 unexpected findings in removal plan (verify no dependencies first)
- Update risk scoring: downgrade revised fields to MEDIUM risk

---

*Generated by Phase 4 Agent*
*Report Path: 04-field-utilization-verification.md*
```

### Step 7: Return JSON

Return ONLY this JSON (no explanatory text):

```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/04-field-utilization-verification.md",
  "verification_summary": {
    "files_analyzed": 42,
    "conclusions_confirmed": [
      "users.legacy_id: 100% null (manual 100%, script 100%)",
      "products.old_sku: 98.5% null (manual 98%, script 98.5%)"
    ],
    "conclusions_revised": [
      "products.internal_notes: manual 85%, script 68.2% (16.8% difference)",
      "orders.metadata: manual 92%, script 78.5% (13.5% difference)"
    ],
    "unexpected_findings": [
      "orders.deprecated_flag: 99.1% null (not in manual analysis)",
      "users.legacy_email: 97.8% null (not in manual analysis)",
      "products.temp_field: 100% null (not in manual analysis)"
    ],
    "revised_action_items": [
      "SAFE: Remove 21 confirmed fields (42.5GB savings)",
      "NEW: Remove 3 unexpected fields (2.5GB savings)",
      "RISKY: Investigate 2 revised fields before deciding"
    ]
  }
}
```

**CRITICAL:**
- Execute script BEFORE writing report
- Write report file BEFORE returning JSON
- Include absolute path in report_path
- All arrays can be empty but must exist
- status must be "complete" or "error"

## Quality Checklist

Before returning JSON:
- [ ] Script executed successfully (exit code 0)
- [ ] Script output file exists and is valid JSON
- [ ] All manual conclusions were compared against script results
- [ ] Comparison table is complete and accurate
- [ ] Revised action items reflect empirical findings
- [ ] Report file written to disk
- [ ] JSON includes all required keys

## Error Handling

**Script execution fails:**
```json
{
  "status": "error",
  "error_message": "Script failed: <script_path> exited with code X",
  "report_path": null,
  "verification_summary": null
}
```

**Cannot parse script output:**
```json
{
  "status": "error",
  "error_message": "Script output is not valid JSON: <output_file>",
  "report_path": null,
  "verification_summary": null
}
```

**Cannot read Phase 2/3 reports:**
```json
{
  "status": "error",
  "error_message": "Failed to read phase2_report_path: <path>",
  "report_path": null,
  "verification_summary": null
}
```

---

**This is the critical phase that turns manual analysis into empirically validated work.**
