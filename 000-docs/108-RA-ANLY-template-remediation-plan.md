# Template & Configuration Remediation Plan
**Phase 3 Preflight Analysis**

**Report ID**: 108-RA-ANLY-template-remediation-plan.md
**Date**: 2025-12-20
**Status**: ANALYSIS COMPLETE (No Files Modified)
**Based On**: 106-RA-ANLY-sources-and-invariants.md § 4 (Template Bugs)

---

## Executive Summary

This analysis identifies **3 CRITICAL template violations** that prevent proper skill generation and validation. These issues directly impact the 500-skill generation pipeline and must be remediated before batch processing begins.

### Severity Assessment

| Severity | Count | Impact |
|----------|-------|--------|
| CRITICAL | 3 | Pipeline breaks during validation |
| HIGH | 2 | Inconsistency between template & validator |
| MEDIUM | 1 | Documentation misalignment |

---

## Violation Details

### CRITICAL VIOLATIONS

#### Violation 1: allowed-tools YAML Format (Template)
**File**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/templates/skill-template.md`

**Current Issue** (Lines 7-10):
```yaml
allowed-tools:
  - Read
  - Write
  - Bash
```

**Problem**:
- Template shows YAML array format (lines 7-10)
- Validator accepts BOTH array and CSV string formats (validate-skill.js lines 94-96)
- Actual deployed skills use CSV STRING format (lines 8 in api-contract-generator/SKILL.md)
- Generator (Gemini) will produce array format from template, failing real-world validation

**Evidence**:
1. Template violation: Lines 7-10 show array with `-` list items
2. Validator flexibility: `validate-skill.js` lines 94-96 accept both formats
3. Live skill contradiction: `api-contract-generator/SKILL.md` line 8 uses CSV: `"allowed-tools: Read, Write, Edit, Grep, Glob, Bash(api:contract-)"`
4. Another live skill: `security-headers-analyzer/SKILL.md` lines 8-12 use array format

**Root Cause**: Template was not validated against actual deployed skill ecosystem. Standard library demonstrates mixed usage, but enterprise standard should enforce ONE format consistently.

**Required Fix**: Change template to CSV STRING format (single-line)
```yaml
allowed-tools: Read, Write, Edit, Bash
```

**Priority**: CRITICAL (blocks skill generation)
**Validator Check ID**: V001-allowed-tools-format
**Lines to Change**: 7-10

---

#### Violation 2: Enterprise Fields Incorrectly Marked Optional (Validator)
**File**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/scripts/validate-skill.js`

**Current Issue** (Lines 59-64):
```javascript
// Check enterprise fields
for (const field of ENTERPRISE_FIELDS) {
  if (!frontmatter[field]) {
    warnings.push(`Missing enterprise field: ${field}`);
  }
}
```

**Problem**:
- Validator treats `allowed-tools`, `version`, `author`, `license` as WARNINGS (optional)
- Status report & documentation mark them as REQUIRED (STATUS-2025-12-19.md lines 55-61)
- This contradicts generation-config.json validation spec (line 15)
- Skills missing enterprise fields pass validation but fail production deployment

**Evidence**:
1. Validator code (lines 59-64): Pushes to `warnings` array, not `errors`
2. Status document (lines 55-61): Lists them as "REQUIRED (Enterprise)"
3. Reference manual (lines 37-56): Shows enterprise fields as REQUIRED, not optional
4. Generation config (line 15): Lists enterprise fields in `required_fields` array
5. Test impact: Skills could pass CI but fail production use

**Root Cause**: Validation was implemented as "pass with warnings" rather than "fail on missing required fields". This allows incomplete skills to proceed.

**Required Fix**: Move enterprise fields from WARNINGS to ERRORS
```javascript
// Lines 59-64 should be:
// Check enterprise fields (REQUIRED for deployment)
for (const field of ENTERPRISE_FIELDS) {
  if (!frontmatter[field]) {
    errors.push(`Missing required enterprise field: ${field}`);  // Changed from warnings
  }
}
```

**Priority**: CRITICAL (allows defective skills to deploy)
**Validator Check ID**: V002-enterprise-fields-required
**Lines to Change**: 59-64 (change 3 `warnings.push` to `errors.push`)

---

#### Violation 3: Deprecated Mode References (Template Documentation)
**File**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/templates/gemini-prompt-template.md`

**Current Issue** (Line 5):
```markdown
You are an expert Claude Code Agent Skills author. Generate high-quality SKILL.md files following the Anthropic specification and Intent Solutions enterprise standards.
```

**Problem**:
- References are vague about "Anthropic specification"
- No mention of required vs optional fields distinction
- Line 12 says "`allowed-tools`: list of permitted tools" (passive, no format spec)
- Template does not clarify that CSV format is REQUIRED (not array)
- This leads Gemini to generate array format by default

**Evidence**:
1. Gemini prompt (line 12): Vague on format: "list of permitted tools"
2. Does not specify CSV STRING requirement
3. YAML semantics default to array when using `- item` syntax
4. Reference manual has correct info but prompt doesn't reference it

**Root Cause**: Prompt engineering was incomplete. Did not specify exact format requirements in machine-readable way.

**Required Fix**: Update prompt to be explicit about format
```markdown
- `allowed-tools`: CSV string (single-line), e.g., "Read, Write, Bash(scope:*)"
```

**Priority**: CRITICAL (causes generator to produce non-compliant output)
**Validator Check ID**: V003-prompt-clarity
**Lines to Change**: 12 (add clarification)

---

## HIGH PRIORITY VIOLATIONS

### Violation 4: Scoped Bash Tool Format Not in Template
**File**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/templates/skill-template.md`

**Current Issue** (Lines 7-10):
```yaml
allowed-tools:
  - Read
  - Write
  - Bash
```

**Problem**:
- Template shows generic `Bash` without scope notation
- Live skills use scoped format: `Bash(api:contract-*)`, `Bash(api:grpc-*)`, etc.
- Template does not demonstrate scope syntax
- Generated skills will omit scopes, reducing capability granularity

**Evidence**:
1. Template shows: `- Bash`
2. Live skills show: `Bash(api:contract-*)` (api-contract-generator/SKILL.md:8)
3. Reference manual (section 3) should cover scope notation but template doesn't demonstrate it

**Root Cause**: Template was created before scope notation was established. Not updated when scoping was added to live skills.

**Required Fix**: Update template to show scoped format
```yaml
allowed-tools: Read, Write, Bash(category:subcategory-*)
```

**Priority**: HIGH (reduces skill precision)
**Validator Check ID**: V004-scoped-bash-format
**Lines to Change**: 7-10 (plus add comment explaining scope notation)

---

### Violation 5: Reference Manual Not Linked in Prompt
**File**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/templates/gemini-prompt-template.md`

**Current Issue** (Lines 18-32):
```markdown
### Action Verbs (Use These)
- Data: Extract, analyze, parse, transform, convert, merge, split, validate
- Creation: Generate, create, build, produce, synthesize, compose
...
```

**Problem**:
- Prompt includes partial action verb list
- Full list is in SKILLS-REFERENCE-MANUAL.md (lines 87-96)
- Prompt lists 6 categories, manual has more granular definitions
- Generator will use incomplete list, producing less diverse descriptions

**Evidence**:
1. Prompt (lines 25-31): 6 action verb categories
2. Manual (lines 87-96): 8 categories with more verbs per category
3. Inconsistency causes Gemini to use limited vocabulary

**Root Cause**: Prompt was not updated when reference manual was expanded.

**Required Fix**: Link to reference manual or sync verb lists
```markdown
### Action Verbs (See SKILLS-REFERENCE-MANUAL.md § 2 for complete list)
- Data: Extract, analyze, parse, transform, convert, merge, split, validate, filter, aggregate
...
```

**Priority**: HIGH (reduces description quality)
**Validator Check ID**: V005-action-verb-completeness
**Lines to Change**: 25-31 (expand with full action verb list from manual)

---

## MEDIUM PRIORITY VIOLATIONS

### Violation 6: Documentation Gap - Enterprise Fields Not Explained in Template
**File**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/templates/skill-template.md`

**Current Issue** (Lines 1-17):
- Frontmatter shows fields but provides no explanation
- No distinction between Anthropic-required vs Enterprise-required
- No guidance on acceptable values

**Problem**:
- New skill authors don't understand why all fields are needed
- No reference to SKILLS-REFERENCE-MANUAL.md in template
- Template is self-contained but incomplete

**Evidence**:
1. Template lines 1-17: Just shows structure, not rationale
2. Actual documentation scattered across 3 files:
   - reference-manual.md (schema)
   - status-2025-12-19.md (implementation)
   - generation-config.json (validation rules)

**Required Fix**: Add comment block explaining each field
```markdown
---
# YAML Frontmatter for Anthropic + Enterprise Compliance
# See SKILLS-REFERENCE-MANUAL.md for complete field documentation

name: {{SKILL_NAME}}                    # REQUIRED (Anthropic) - kebab-case, max 64 chars
description: |                         # REQUIRED (Anthropic) - max 1024 chars, include triggers
  {{PRIMARY_ACTION_VERB}} {{CAPABILITY}}. {{SECONDARY_FEATURES}}.
  Use when {{TRIGGER_SCENARIOS}}.
  Trigger with "{{PHRASE_1}}", "{{PHRASE_2}}", "{{PHRASE_3}}".
allowed-tools: {{TOOLS}}               # REQUIRED (Enterprise) - CSV string format
version: 1.0.0                         # REQUIRED (Enterprise) - semver format
author: Jeremy Longshore <jeremy@intentsolutions.io>  # REQUIRED (Enterprise)
license: MIT                           # REQUIRED (Enterprise)
tags:                                  # RECOMMENDED - lowercase array
  - {{CATEGORY}}
  - {{SUBCATEGORY}}
---
```

**Priority**: MEDIUM (documentation only, doesn't break functionality)
**Validator Check ID**: V006-template-documentation
**Lines to Change**: 1-17 (add inline comments)

---

## Remediation Roadmap

### Phase 1: Critical Fixes (MUST do before batch generation)

| Fix ID | File | Lines | Change Type | Effort | Risk |
|--------|------|-------|-------------|--------|------|
| V001 | skill-template.md | 7-10 | Replace YAML array with CSV string | 5 min | LOW |
| V002 | validate-skill.js | 59-64 | Move enterprise fields to errors | 5 min | MEDIUM (may break existing workflows) |
| V003 | gemini-prompt-template.md | 12 | Add format specification | 5 min | LOW |

**Estimated Time**: 15 minutes
**Testing Required**:
1. Run validator against template (should pass)
2. Run Gemini with updated prompt on 5 test skills
3. Validate output against updated validator
4. Verify scopes are included

### Phase 2: High Priority Fixes (Before production deployment)

| Fix ID | File | Lines | Change Type | Effort | Risk |
|--------|------|-------|-------------|--------|------|
| V004 | skill-template.md | 7-10 | Add scope notation example | 10 min | LOW |
| V005 | gemini-prompt-template.md | 25-31 | Sync action verbs with manual | 10 min | LOW |

**Estimated Time**: 20 minutes
**Testing Required**:
1. Generate 10 sample skills
2. Verify scope notation is used appropriately
3. Verify action verb diversity in descriptions

### Phase 3: Medium Priority Fixes (Before v1.0.0 release)

| Fix ID | File | Lines | Change Type | Effort | Risk |
|--------|------|-------|-------------|--------|------|
| V006 | skill-template.md | 1-17 | Add inline documentation | 15 min | LOW |

**Estimated Time**: 15 minutes
**Testing Required**:
1. Code review for clarity
2. Verify comments don't break YAML parsing

---

## Validation Checks to Implement

### Check V001: allowed-tools Format Validation
**Purpose**: Ensure all skills use CSV STRING format, not YAML array
**Implementation Location**: `validate-skill.js` lines 92-104

```javascript
// Validate allowed-tools format (MUST be CSV string)
if (frontmatter['allowed-tools']) {
  const toolsValue = frontmatter['allowed-tools'];

  // REJECTED: Array format (old template style)
  if (Array.isArray(toolsValue)) {
    errors.push('allowed-tools must be CSV string format (e.g., "Read, Write, Bash"), not YAML array');
  }

  // ACCEPTED: CSV String format
  if (typeof toolsValue === 'string') {
    const tools = toolsValue.split(',').map(t => t.trim());
    // Validate each tool...
  }
}
```

**Check ID**: V001-allowed-tools-format

---

### Check V002: Enterprise Fields Required
**Purpose**: Ensure all skills have required enterprise fields
**Implementation Location**: `validate-skill.js` lines 59-64

```javascript
// Enforce enterprise fields as REQUIRED (not warnings)
for (const field of ENTERPRISE_FIELDS) {
  if (!frontmatter[field]) {
    errors.push(`Missing required enterprise field: ${field}. See SKILLS-REFERENCE-MANUAL.md`);
  }
}
```

**Check ID**: V002-enterprise-fields-required

---

### Check V003: Scoped Bash Validation
**Purpose**: Warn if Bash tool is used without scope notation
**Implementation Location**: `validate-skill.js` new section after line 104

```javascript
// Warn if Bash is used without scope (should be Bash(scope:pattern-*))
if (frontmatter['allowed-tools'] && typeof frontmatter['allowed-tools'] === 'string') {
  if (frontmatter['allowed-tools'].includes('Bash') && !frontmatter['allowed-tools'].includes('Bash(')) {
    warnings.push('Bash tool should use scope notation (e.g., Bash(api:*) or Bash(devops:*)). See SKILLS-REFERENCE-MANUAL.md § 3');
  }
}
```

**Check ID**: V003-scoped-bash-validation

---

## Impact Analysis

### Files Affected by These Violations

```
generation-pipeline.md
├── Template Issues (Template → Generator)
│   ├── skill-template.md (3 violations: V001, V004, V006)
│   └── gemini-prompt-template.md (2 violations: V003, V005)
│
├── Validator Issues (Generated Skills → Deployed Skills)
│   └── validate-skill.js (2 violations: V002, V003)
│
└── Configuration Issues (Generation Rules)
    └── generation-config.json (indirectly affected by V002)
```

### Ripple Effects

**If Left Unrepaired**:
1. V001 (allowed-tools array): Generated skills fail production validation
2. V002 (enterprise fields warnings): Incomplete skills deploy to production
3. V003 (prompt clarity): Gemini produces array format, fails validation
4. V004 (scoped Bash missing): Lost granularity in tool permissions
5. V005 (incomplete action verbs): Lower quality descriptions
6. V006 (no documentation): Higher onboarding friction

**Critical Path for Deployment**:
```
Fixes V001, V003 → Regenerate batch 001 → Validate with V002
→ Pass (all 3 critical fixes applied) → Proceed to batch 002
```

---

## Proposed Fixes (Diff Format)

### Fix 1: skill-template.md (V001, V004, V006)

**Location**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/templates/skill-template.md`

```diff
---
+ # YAML Frontmatter - Anthropic + Enterprise Required Fields
+ # See SKILLS-REFERENCE-MANUAL.md § 1 for complete schema documentation
+
 name: {{SKILL_NAME}}
 description: |
   {{PRIMARY_ACTION_VERB}} {{CAPABILITY}}. {{SECONDARY_FEATURES}}.
   Use when {{TRIGGER_SCENARIOS}}.
   Trigger with "{{PHRASE_1}}", "{{PHRASE_2}}", "{{PHRASE_3}}".
-allowed-tools:
-  - Read
-  - Write
-  - Bash
+allowed-tools: Read, Write, Edit, Bash(category:domain-*)
 version: 1.0.0
 author: Jeremy Longshore <jeremy@intentsolutions.io>
 license: MIT
 tags:
   - {{CATEGORY}}
   - {{SUBCATEGORY}}
+ # Note: allowed-tools is CSV string format, not YAML array.
+ # Scoped Bash tools use notation: Bash(api:*), Bash(devops:*), etc.
---
```

**Changes**:
- Line 1: Add documentation header
- Lines 8-11: Replace array format with CSV string including scope example
- Line 17: Add clarifying comment about scopes

---

### Fix 2: gemini-prompt-template.md (V003, V005)

**Location**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/templates/gemini-prompt-template.md`

```diff
 ### YAML Frontmatter (Required)
 - `name`: kebab-case, max 64 characters
 - `description`: max 1024 characters, includes action verbs and trigger phrases
-- `allowed-tools`: list of permitted tools
+- `allowed-tools`: CSV string of permitted tools (e.g., "Read, Write, Bash(api:*)")
 - `version`: semver format (1.0.0)
 - `author`: Jeremy Longshore <jeremy@intentsolutions.io>
 - `license`: MIT
 - `tags`: array of relevant tags

 ### Action Verbs (Use These)
-- Data: Extract, analyze, parse, transform, convert, merge, split, validate
-- Creation: Generate, create, build, produce, synthesize, compose
-- Modification: Edit, update, refactor, optimize, fix, enhance, migrate
-- Analysis: Review, audit, scan, inspect, diagnose, profile, assess
-- Operations: Deploy, execute, run, configure, install, setup, provision
-- Documentation: Document, explain, summarize, annotate, describe
+See SKILLS-REFERENCE-MANUAL.md § 2 for complete action verb reference.
+- Data: Extract, analyze, parse, transform, convert, merge, split, validate, filter, aggregate
+- Creation: Generate, create, build, produce, synthesize, compose, scaffold, initialize
+- Modification: Edit, update, refactor, optimize, fix, enhance, migrate, patch, upgrade
+- Analysis: Review, audit, scan, inspect, diagnose, profile, assess, evaluate, benchmark
+- Operations: Deploy, execute, run, configure, install, setup, provision, orchestrate
+- Documentation: Document, explain, summarize, annotate, describe, catalog, index
+- Testing: Test, verify, validate, check, assert, measure, monitor
+- Security: Secure, encrypt, authenticate, authorize, protect, harden, sanitize
```

**Changes**:
- Line 12: Add format specification for allowed-tools
- Lines 25-31: Expand action verbs to match SKILLS-REFERENCE-MANUAL.md and add reference link

---

### Fix 3: validate-skill.js (V002, V003)

**Location**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/scripts/validate-skill.js`

```diff
   // Check enterprise fields
   for (const field of ENTERPRISE_FIELDS) {
     if (!frontmatter[field]) {
-      warnings.push(`Missing enterprise field: ${field}`);
+      errors.push(`Missing required enterprise field: ${field}. See SKILLS-REFERENCE-MANUAL.md § 1`);
     }
   }

   // Validate allowed-tools
   if (frontmatter['allowed-tools']) {
-    const tools = Array.isArray(frontmatter['allowed-tools'])
-      ? frontmatter['allowed-tools']
-      : frontmatter['allowed-tools'].split(',').map(t => t.trim());
+    // REQUIRED: allowed-tools must be CSV string, not YAML array
+    if (Array.isArray(frontmatter['allowed-tools'])) {
+      errors.push('allowed-tools must be CSV string format (e.g., "Read, Write, Bash"), not YAML array');
+    } else if (typeof frontmatter['allowed-tools'] === 'string') {
+      const tools = frontmatter['allowed-tools'].split(',').map(t => t.trim());

-    for (const tool of tools) {
-      const baseTool = tool.split('(')[0];
-      if (!VALID_TOOLS.includes(baseTool)) {
-        warnings.push(`Unknown tool: ${tool}`);
-      }
-    }
+      for (const tool of tools) {
+        const baseTool = tool.split('(')[0];
+        if (!VALID_TOOLS.includes(baseTool)) {
+          errors.push(`Unknown tool: ${tool}. See SKILLS-REFERENCE-MANUAL.md § 3 for valid tools`);
+        }
+      }
+
+      // Warn if Bash is used without scope
+      if (frontmatter['allowed-tools'].includes('Bash') && !frontmatter['allowed-tools'].includes('Bash(')) {
+        warnings.push('Bash should use scope notation (e.g., Bash(api:*) or Bash(devops:*)). See SKILLS-REFERENCE-MANUAL.md § 3');
+      }
+    } else {
+      errors.push('allowed-tools must be a string, not other types');
+    }
   }
```

**Changes**:
- Line 62: Change warnings to errors for enterprise fields (V002)
- Lines 93-122: Add format validation for allowed-tools CSV string (V003)
- Add scope warning for Bash tool

---

## Testing & Validation Strategy

### Pre-Flight Checklist

- [ ] **Template Validation**: Run validator against skill-template.md (should not error)
- [ ] **Prompt Testing**: Send updated gemini-prompt-template.md to Gemini with 5 test cases
- [ ] **Output Validation**: Run validator against Gemini output (should pass 100%)
- [ ] **Scope Check**: Verify all generated skills have scoped Bash (or no Bash)
- [ ] **Enterprise Check**: Verify all skills have all 6 required fields

### Validator Test Cases

```bash
# Test 1: Array format (should FAIL with V001)
name: test-skill-1
allowed-tools:
  - Read
  - Bash
→ Expected: ERROR - array format not allowed

# Test 2: Missing enterprise fields (should FAIL with V002)
name: test-skill-2
description: Test
allowed-tools: Read
# Missing: version, author, license
→ Expected: ERROR - missing required fields

# Test 3: Scoped Bash (should PASS)
name: test-skill-3
allowed-tools: Read, Write, Bash(api:*)
version: 1.0.0
author: Test <test@example.com>
license: MIT
→ Expected: PASS

# Test 4: Unscoped Bash (should WARN with V003)
name: test-skill-4
allowed-tools: Read, Bash
version: 1.0.0
author: Test <test@example.com>
license: MIT
→ Expected: PASS + WARNING - Bash should be scoped
```

### Batch Generation Test Plan

1. **Batch 001 (10 test skills)**:
   - Template: updated skill-template.md
   - Prompt: updated gemini-prompt-template.md
   - Expected: 100% pass rate on validation

2. **Batch 002-020 (490 production skills)**:
   - Start only after Batch 001 passes
   - Monitor for compliance issues
   - Document any new violations

---

## Approval Gates

### Before Implementing Fixes

- [ ] This analysis reviewed by code owners
- [ ] Fixes reviewed for backward compatibility
- [ ] Risk assessment: Will moving enterprise fields to errors break existing skills?

### Before Batch Generation Resumes

- [ ] V001, V002, V003 fixes applied
- [ ] Validator tests pass (all 4 test cases)
- [ ] Gemini prompt test with 5 skills
- [ ] Batch 001 regenerated and validated
- [ ] CI/CD updated to enforce new checks

---

## Timeline Estimate

| Phase | Task | Time | Owner |
|-------|------|------|-------|
| P1 | Apply critical fixes (V001-V003) | 15 min | Code |
| P1 | Run validator test cases | 10 min | QA |
| P1 | Regenerate Batch 001 (10 skills) | 30 min | Gen |
| P1 | Validate Batch 001 | 10 min | QA |
| P2 | Apply high priority fixes (V004-V005) | 20 min | Code |
| P2 | Run full Batch 001 + 002 validation | 20 min | QA |
| P3 | Apply documentation (V006) | 15 min | Code |

**Total Elapsed Time**: ~2 hours
**Critical Path**: P1 (65 minutes)

---

## References

### Related Documents
- **106-RA-ANLY-sources-and-invariants.md**: Original conflict analysis (§ 4)
- **SKILLS-REFERENCE-MANUAL.md**: Authoritative schema and standards
- **STATUS-2025-12-19.md**: Implementation status and fixes applied
- **SKILLS-STANDARD-COMPLETE.md**: Enterprise requirements specification

### Violation Cross-Reference
| Check ID | Document Section | Severity |
|----------|------------------|----------|
| V001 | Violation 1 | CRITICAL |
| V002 | Violation 2 | CRITICAL |
| V003 | Violation 3 | CRITICAL |
| V004 | Violation 4 | HIGH |
| V005 | Violation 5 | HIGH |
| V006 | Violation 6 | MEDIUM |

---

## Sign-Off

**Analysis Complete**: 2025-12-20
**Files Analyzed**: 6
**Violations Found**: 6
**Fixes Proposed**: 6
**Estimated Remediation Time**: 90 minutes
**Status**: Ready for implementation (NO FILES MODIFIED YET)

**Next Steps**:
1. Review this analysis
2. Approve fixes in Violations 1-3 (critical path)
3. Apply diffs in remediation roadmap
4. Run validation test cases
5. Regenerate Batch 001
6. Proceed to batch 002+

---

**End of Report**
