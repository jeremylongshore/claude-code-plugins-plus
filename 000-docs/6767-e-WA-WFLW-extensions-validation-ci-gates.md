# 6767-e-WA-WFLW-wa-stnd-extensions-validation-ci.md

**Document Type**: Workflow & Automation - Standard (WA-STND)
**Document ID**: 6767-e-WA-STND-extensions-validation-and-ci-gates
**Title**: Extensions Validation and CI Gates
**Version**: 3.0.0
**Status**: CANONICAL (Enterprise-Only)
**Date**: 2025-12-20
**Companion To**: 6767-c (Extensions Standard), 6767-d (Schema)
**Authority**: Intent Solutions (Enterprise Marketplace)

---

## TRUTH INVARIANTS (ENTERPRISE MODE)

**MODE**: ENTERPRISE MODE ALWAYS ON. No "Anthropic-minimum" fallback. All fields marked "REQUIRED" are REQUIRED.

**CORE RULES**:

1. **allowed-tools Format**:
   - ✅ CORRECT: CSV string → `allowed-tools: "Read,Write,Grep,Glob"`
   - ❌ WRONG: YAML array → `allowed-tools: [Read, Write, Grep]`
   - Violation: CRITICAL ERROR (`SKILL_022`)

2. **Bash Scoping**:
   - ✅ CORRECT: Scoped → `Bash(git:*)`, `Bash(npm:*)`, `Bash(python:*)`
   - ❌ WRONG: Unscoped → `Bash`
   - Violation: CRITICAL ERROR (`SKILL_024`)

3. **Path Portability**:
   - ✅ CORRECT: `${CLAUDE_PLUGIN_ROOT}/...` or `{baseDir}/...`
   - ❌ WRONG: `/home/user/...` or `~/...`
   - Violation: CRITICAL ERROR (`SKILL_103`, `SEC_005`)

4. **Naming Convention**:
   - Pattern: `^[a-z0-9-]+$` (kebab-case only)
   - Max length: 64 chars
   - Reserved words: NO "claude" or "anthropic"
   - Violation: CRITICAL ERROR (`NAMING_001`, `NAMING_002`, `NAMING_003`)

5. **Versioning**:
   - Format: SemVer `MAJOR.MINOR.PATCH` (3 parts)
   - Example: `1.0.0`, `2.3.1`
   - Violation: CRITICAL ERROR (`PLUGIN_012`, `SKILL_032`)

6. **Directory Structure**:
   - `.claude-plugin/` contains ONLY `plugin.json`
   - Component dirs (skills/, agents/, commands/) at plugin root, NOT inside `.claude-plugin/`
   - Violation: CRITICAL ERROR (`DIR_002`, `DIR_005`)

7. **Security**:
   - NO hardcoded secrets, API keys, .env files committed
   - Secrets via environment variables ONLY
   - Exemptions: ONLY `tests/fixtures/**` + known test patterns (EXAMPLE, DUMMY, test-)
   - Violation: CRITICAL ERROR (`SEC_001`, `SEC_002`, `SEC_003`, `SEC_004`)

8. **Context Hygiene**:
   - SKILL.md body ≤ 5,000 words / 500 lines / ~7,500 tokens
   - Heavy content in `references/` directory (loaded on-demand)
   - Violation: HIGH ERROR (`SKILL_100`, `SKILL_101`)

9. **Discoverability**:
   - Description MUST include "Use when..." phrase
   - Description MUST include 2-6 trigger phrases
   - Violation: HIGH ERROR (`SKILL_015`, `SKILL_016`)

10. **Required Fields (Enterprise)**:
    - Plugin: name, version, description, author (name + email), license, keywords
    - Skill: name, description, allowed-tools (CSV), version, author, license, tags
    - Violation: CRITICAL ERROR (various `PLUGIN_*`, `SKILL_*` codes)

**VALIDATION**:
- Validator runs in ENTERPRISE MODE ONLY
- CRITICAL/HIGH errors BLOCK PR merge
- Deterministic error codes (6767-d schema)

**NO EXCEPTIONS**: These rules apply to ALL plugins/skills, regardless of size or complexity.

---

## 1. Purpose

This specification defines **enforcement mechanisms** for Claude Code extensions:
- Validator implementation requirements
- CI/CD pipeline gates and workflows
- Auto-fix policies
- Compliance reporting

All rules herein operate in **ENTERPRISE MODE ONLY**. There is no Anthropic-minimum fallback.

---

## 2. Validator Requirements

### 2.1 Execution Modes

#### 2.1.1 Enterprise Mode (ONLY MODE)

**Command**:
```bash
python validate_standards.py --plugin-root /path/to/plugin
```

**Behavior**:
- Enforce ALL enterprise requirements from 6767-c and 6767-d
- No "Anthropic-minimum" fallback
- All fields marked "REQUIRED" in 6767-c are REQUIRED
- Exit code 1 on CRITICAL or HIGH errors
- Exit code 2 on MEDIUM or LOW warnings
- Exit code 0 on success

**Flags**:
- `--plugin-root PATH`: Plugin root directory (REQUIRED)
- `--verbose`: Detailed output
- `--json`: JSON report output
- `--fix`: Auto-fix simple issues (use with caution)

### 2.2 Validation Categories

| Category | Checks | Severity Range |
|----------|--------|----------------|
| **Manifest** | plugin.json schema, required fields, name/version format | CRITICAL |
| **Directory** | .claude-plugin/ ONLY plugin.json, components at root | CRITICAL |
| **Skills** | Frontmatter, CSV allowed-tools, body limits | CRITICAL - HIGH |
| **Agents** | Frontmatter, required fields | CRITICAL - HIGH |
| **Security** | Secrets, .env files, paths, Bash scoping | CRITICAL |
| **Naming** | Kebab-case, reserved words, max length | CRITICAL - HIGH |
| **Context** | Body size limits, progressive disclosure | HIGH - MEDIUM |

### 2.3 Required Checks (Comprehensive List)

#### 2.3.1 Plugin Manifest

- [ ] plugin.json exists at `.claude-plugin/plugin.json`
- [ ] JSON is valid (parseable)
- [ ] `name` field present, string, kebab-case, max 64 chars
- [ ] `name` does NOT contain "claude" or "anthropic"
- [ ] `version` field present, string, SemVer format `\d+\.\d+\.\d+`
- [ ] `description` field present, string, max 1024 chars
- [ ] `author` field present, object with `name` and `email`
- [ ] `author.name` present, string, min 1 char
- [ ] `author.email` present, string, valid email format
- [ ] `license` field present, string, min 1 char
- [ ] `keywords` field present, array, min 1 item
- [ ] `homepage` (if present) is valid URL
- [ ] `repository` (if present) is valid URL

#### 2.3.2 Directory Structure

- [ ] `.claude-plugin/` directory exists
- [ ] `.claude-plugin/` contains ONLY `plugin.json` (no other files)
- [ ] `plugin.json` exists at `.claude-plugin/plugin.json`
- [ ] Component dirs (skills/, agents/, commands/, hooks/) at plugin root (NOT in .claude-plugin/)
- [ ] No empty directories

#### 2.3.3 Skills (if present)

- [ ] Skills located at `skills/<skill-name>/SKILL.md`
- [ ] Frontmatter is valid YAML
- [ ] `name` present, string, kebab-case, max 64 chars, no reserved words
- [ ] `description` present, string, max 1024 chars
- [ ] `description` contains "Use when" phrase (case-insensitive)
- [ ] `description` contains trigger phrases
- [ ] `allowed-tools` present, **string** (NOT array)
- [ ] `allowed-tools` is CSV format (comma-separated)
- [ ] Bash tool (if present) is scoped: `Bash(command:*)` NOT just `Bash`
- [ ] `version` present, string, SemVer format
- [ ] `author` present, string, min 1 char
- [ ] `license` present, string, min 1 char
- [ ] `tags` present, array, min 1 item
- [ ] Body ≤ 5,000 words
- [ ] Body ≤ 500 lines
- [ ] No absolute paths in body (e.g., `/home/...`)
- [ ] Paths use `{baseDir}` for repo-relative references

#### 2.3.4 Agents (if present)

- [ ] Agents located at `agents/<agent-name>.md`
- [ ] Frontmatter is valid YAML
- [ ] `name` present, string
- [ ] `description` present, string
- [ ] `tools` (if present) is string (CSV format)

#### 2.3.5 Security

- [ ] No hardcoded secrets (API keys, AWS keys, SSH keys)
  - Exempt only `tests/fixtures/**` OR files with known test markers (EXAMPLE, DUMMY, test-)
- [ ] No `.env` files committed
- [ ] No absolute paths (e.g., `/home/`, `/usr/`)
- [ ] All paths use `${CLAUDE_PLUGIN_ROOT}` or `{baseDir}`
- [ ] Bash tool scoping enforced (no unscoped Bash)

#### 2.3.6 Naming

- [ ] Plugin name is kebab-case (`^[a-z0-9-]+$`)
- [ ] Skill names are kebab-case
- [ ] Agent names are kebab-case (recommended)
- [ ] No uppercase letters in names
- [ ] No underscores in names
- [ ] No reserved words (claude, anthropic)

---

## 3. CI/CD Workflows

### 3.1 PR Validation Workflow

**File**: `.github/workflows/pr.yml`

**Trigger**: Every pull request to `main` branch

**Purpose**: Block non-compliant code from merging

**Steps**:
```yaml
name: PR Validation

on:
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd plugins/my-plugin
          pip install -r scripts/requirements.txt

      - name: Validate standards compliance (ENTERPRISE MODE)
        run: |
          cd plugins/my-plugin
          python scripts/validate_standards.py --plugin-root . --verbose
        continue-on-error: false       # ← BLOCKING GATE

      - name: Run security tests
        run: |
          cd plugins/my-plugin
          pytest tests/test_security.py -v

      - name: Run component tests
        run: |
          cd plugins/my-plugin
          pytest tests/ -v

      - name: Lint check
        run: |
          cd plugins/my-plugin
          black --check src/ tests/
          isort --check-only src/ tests/
          flake8 src/ tests/ --count --statistics
```

**Blocking Behavior**:
- Validator runs FIRST (fail-fast)
- If validator exits with code 1 (CRITICAL/HIGH errors), PR is BLOCKED
- All other steps run only if validation passes
- Developer must fix errors locally and push again

**Expected Output (Success)**:
```
✓ Checkout code
✓ Set up Python 3.10
✓ Install dependencies
✓ Validate standards compliance (ENTERPRISE MODE)
  ✅ ALL VALIDATIONS PASSED!
✓ Run security tests
✓ Run component tests
✓ Lint check
```

**Expected Output (Failure)**:
```
✓ Checkout code
✓ Set up Python 3.10
✓ Install dependencies
✗ Validate standards compliance (ENTERPRISE MODE)
  [CRITICAL] skills/my-skill/SKILL.md
    Field: allowed-tools
    Expected: CSV string (e.g., "Read,Write,Grep")
    Actual: YAML array format
    Fix: Change frontmatter to: allowed-tools: "Read,Write,Grep"

  FAILED: 1 error found (1 CRITICAL)

  ❌ PR BLOCKED - Fix errors above and push again
```

### 3.2 Main Branch Workflow

**File**: `.github/workflows/main.yml`

**Trigger**: Every push to `main` branch (post-merge)

**Purpose**: Comprehensive validation + reporting

**Steps**:
```yaml
name: Main Branch CI

on:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd plugins/my-plugin
          pip install -r scripts/requirements.txt

      - name: Validate standards (ENTERPRISE MODE)
        run: |
          cd plugins/my-plugin
          python scripts/validate_standards.py --plugin-root . --verbose --json > validation-report.json

      - name: Run all tests with coverage
        run: |
          cd plugins/my-plugin
          pytest tests/ -v --cov=src --cov-report=term --cov-report=html

      - name: Lint and format check
        run: |
          cd plugins/my-plugin
          black --check src/ tests/
          isort --check-only src/ tests/
          flake8 src/ tests/ --count --statistics

      - name: Upload validation report
        uses: actions/upload-artifact@v4
        with:
          name: validation-report
          path: plugins/my-plugin/validation-report.json

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: plugins/my-plugin/htmlcov/
```

**Purpose**:
- Comprehensive validation (same rigor as PR)
- Generate coverage reports
- Archive validation artifacts
- Catch issues that might slip through PR review

---

## 4. Auto-Fix Policy

### 4.1 Safe Auto-Fixes (Allowed)

**Command**: `python validate_standards.py --plugin-root . --fix`

**Allowed Auto-Fixes**:

1. **Trailing whitespace removal**
   - Severity: LOW
   - Risk: None
   - Example: `"description": "...  "` → `"description": "..."`

2. **JSON/YAML formatting**
   - Severity: LOW
   - Risk: None (preserves semantics)
   - Example: Indent to 2 spaces, sort keys alphabetically

3. **SemVer normalization**
   - Severity: LOW
   - Risk: Low (only adds missing zeros)
   - Example: `"version": "1.0"` → `"version": "1.0.0"`

4. **Keyword de-duplication**
   - Severity: LOW
   - Risk: None
   - Example: `["test", "test", "demo"]` → `["test", "demo"]`

### 4.2 Unsafe Auto-Fixes (NEVER Automatic)

**NEVER auto-fix** (require manual intervention):

1. **allowed-tools YAML array → CSV string**
   - Risk: High (semantic change, may alter tool list)
   - Reason: Must verify tool list is correct
   - Action: Flag as CRITICAL, require developer fix

2. **Bash scoping**
   - Risk: Critical (security implications)
   - Reason: Cannot infer correct scope
   - Action: Flag as CRITICAL, require developer to scope

3. **Description content**
   - Risk: High (semantic change)
   - Reason: Cannot generate "Use when" or trigger phrases
   - Action: Flag as HIGH, require developer to enhance

4. **Secret removal**
   - Risk: Critical (may break functionality)
   - Reason: Unknown if secret is needed elsewhere
   - Action: Flag as CRITICAL, require developer to replace with env var

5. **Absolute path conversion**
   - Risk: High (may break paths)
   - Reason: Cannot infer correct relative path
   - Action: Flag as CRITICAL, require developer to fix

### 4.3 Auto-Fix Reporting

**Output Format**:
```
Running validator with --fix enabled...

✅ AUTO-FIXED:
  - plugins/my-plugin/plugin.json:
    Normalized version "1.0" → "1.0.0"
  - skills/my-skill/SKILL.md:
    Removed trailing whitespace (3 lines)

⚠️  CANNOT AUTO-FIX (manual intervention required):
  - [CRITICAL] skills/my-skill/SKILL.md
    Field: allowed-tools
    Issue: YAML array format
    Fix: Change frontmatter to: allowed-tools: "Read,Write,Grep"

SUMMARY: 2 auto-fixed, 1 requires manual fix
```

---

## 5. Compliance Reporting

### 5.1 JSON Report Schema

```json
{
  "validator_version": "3.0.0",
  "enterprise_mode": true,
  "plugin_root": "/path/to/plugin",
  "timestamp": "2025-12-20T10:00:00Z",
  "summary": {
    "total_checks": 42,
    "passed": 40,
    "failed": 2,
    "errors": {
      "critical": 1,
      "high": 1,
      "medium": 0,
      "low": 0
    }
  },
  "errors": [
    {
      "code": "SKILL_022",
      "severity": "CRITICAL",
      "category": "skills",
      "file": "skills/my-skill/SKILL.md",
      "line": 5,
      "field": "allowed-tools",
      "expected": "CSV string (e.g., \"Read,Write,Grep\")",
      "actual": "YAML array format",
      "fix": "Change frontmatter to: allowed-tools: \"Read,Write,Grep\"",
      "docs_url": "https://docs.example.com/6767-d#skill-allowed-tools"
    }
  ],
  "warnings": [],
  "passed_checks": [
    "PLUGIN_001: plugin.json exists",
    "PLUGIN_002: name field present",
    "PLUGIN_003: name is kebab-case",
    ...
  ]
}
```

### 5.2 Console Output (Human-Readable)

```
================================================================================
🔍 STANDARDS VALIDATOR (ENTERPRISE MODE)
================================================================================

🔍 Validating plugin at: /path/to/plugin
📋 Enterprise mode: ENABLED (no fallback)

📦 Validating plugin manifest...
  ✓ plugin.json exists
  ✓ name field present and valid
  ✓ version field present and valid (SemVer)
  ✓ author object complete (name + email)
  ✓ license field present
  ✓ keywords array present (3 items)

📁 Validating directory structure...
  ✓ .claude-plugin/ contains ONLY plugin.json
  ✓ No components inside .claude-plugin/

🎯 Validating skills (2 skills found)...
  ✓ skills/skill-1/SKILL.md frontmatter valid
  ✗ skills/skill-2/SKILL.md has errors (1 CRITICAL)

🔒 Running security scans...
  ✓ No hardcoded secrets detected
  ✓ No .env files committed
  ✓ All paths relative or use ${CLAUDE_PLUGIN_ROOT}

📝 Validating naming conventions...
  ✓ All names kebab-case
  ✓ No reserved words detected

================================================================================
📊 VALIDATION RESULTS
================================================================================

❌ 2 ERRORS FOUND:

[CRITICAL] skills/skill-2/SKILL.md
  Field: allowed-tools
  Expected: CSV string (e.g., "Read,Write,Grep")
  Actual: YAML array format
  Fix: Change frontmatter to: allowed-tools: "Read,Write,Grep"
  Docs: https://docs.example.com/6767-d#skill-allowed-tools

[HIGH] skills/skill-2/SKILL.md
  Field: description
  Expected: Must contain "Use when" phrase
  Actual: Missing usage scenarios
  Fix: Add "Use when [scenarios]" to description

================================================================================
Summary: 40 passed, 2 failed (1 CRITICAL, 1 HIGH)
================================================================================

❌ FAILED: Fix errors above before merging to main branch
```

---

## 6. Flat 000-docs/ Validation

### 6.1 Document Filing System Checks

**Applies to**: Plugins with `000-docs/` directory

**Checks**:
- [ ] `000-docs/` is flat (no subdirectories)
- [ ] All filenames match pattern: `NNN-CC-ABCD-short-description.ext`
- [ ] NNN are unique (no duplicates unless valid suffix: `005a`, `006-1`)
- [ ] CC codes valid (DR, RA, PP, AT, TQ, PM, AA, etc.)
- [ ] ABCD codes valid for their CC category
- [ ] Short descriptions 1-4 words, kebab-case

**Error Codes**:
- `DOC_001`: 000-docs/ is not flat (has subdirectories)
- `DOC_002`: Invalid filename pattern
- `DOC_003`: Duplicate NNN
- `DOC_004`: Invalid CC code
- `DOC_005`: Invalid ABCD for CC
- `DOC_006`: Short description too long or not kebab-case

**Severity**: CRITICAL (doc filing violations block PRs)

### 6.2 Example Validation

**Good**:
```
000-docs/
├── 001-DR-STND-document-filing-system.md      ✓
├── 002-RA-ANLY-canonical-ruleset.md           ✓
├── 003-AA-AACR-phase-1-cleanup.md             ✓
```

**Bad**:
```
000-docs/
├── planned-plugins/                            ✗ Subdirectory not allowed
│   └── README.md
├── 001-AA-TMPL-template.md                     ✗ TMPL is DR not AA
├── 001-DR-STND-another-doc.md                  ✗ Duplicate NNN 001
├── 002_REPORT_analysis.md                      ✗ Invalid pattern (underscores)
```

---

## 7. Integration with Development Workflow

### 7.1 Pre-Commit Hook (Recommended)

**File**: `.git/hooks/pre-commit`

```bash
#!/bin/bash

echo "Running standards validation..."
cd plugins/my-plugin
python scripts/validate_standards.py --plugin-root .

if [ $? -ne 0 ]; then
    echo "❌ Standards validation failed. Commit aborted."
    echo "Fix errors above and try again."
    exit 1
fi

echo "✅ Standards validation passed"
exit 0
```

**Installation**:
```bash
chmod +x .git/hooks/pre-commit
```

### 7.2 Pre-Push Hook (Alternative)

**File**: `.git/hooks/pre-push`

```bash
#!/bin/bash

echo "Running comprehensive standards validation..."
cd plugins/my-plugin
python scripts/validate_standards.py --plugin-root . --verbose

if [ $? -ne 0 ]; then
    echo "❌ Standards validation failed. Push aborted."
    exit 1
fi

echo "✅ All validations passed"
exit 0
```

### 7.3 IDE Integration (VS Code)

**File**: `.vscode/tasks.json`

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate Standards (Enterprise)",
      "type": "shell",
      "command": "cd plugins/my-plugin && python scripts/validate_standards.py --plugin-root . --verbose",
      "group": {
        "kind": "test",
        "isDefault": true
      },
      "presentation": {
        "reveal": "always",
        "panel": "new"
      },
      "problemMatcher": []
    }
  ]
}
```

**Usage**: `Ctrl+Shift+B` → Select "Validate Standards (Enterprise)"

---

## 8. Validator Test Suite

### 8.1 Required Test Coverage

Validator MUST have tests for:

1. **Manifest Validation**:
   - Valid plugin.json passes
   - Missing required fields fail (CRITICAL)
   - Invalid name pattern fails (CRITICAL)
   - Invalid version format fails (CRITICAL)
   - Missing author.email fails (CRITICAL)

2. **Directory Structure**:
   - .claude-plugin/ with ONLY plugin.json passes
   - Extra files in .claude-plugin/ fail (CRITICAL)
   - Components inside .claude-plugin/ fail (CRITICAL)

3. **Skills**:
   - Valid skill passes
   - YAML array allowed-tools fails (CRITICAL)
   - Unscoped Bash fails (CRITICAL)
   - Missing "Use when" fails (HIGH)
   - Body >5,000 words fails (HIGH)

4. **Security**:
   - Hardcoded API key fails (CRITICAL)
   - test/fixtures/ secret allowed (passes)
   - Known test pattern (EXAMPLE) allowed (passes)
   - Real secret in test file fails (CRITICAL)

5. **Naming**:
   - Kebab-case name passes
   - Uppercase in name fails (CRITICAL)
   - Reserved word fails (CRITICAL)

### 8.2 Test Pattern

```python
def test_allowed_tools_yaml_array_fails():
    """YAML array for allowed-tools should fail (CRITICAL)"""
    skill_path = create_temp_skill(frontmatter={
        'name': 'test-skill',
        'description': 'Test skill. Use when testing.',
        'allowed-tools': ['Read', 'Write', 'Bash'],  # ← YAML array (wrong)
        'version': '1.0.0',
        'author': 'Test <test@example.com>',
        'license': 'MIT',
        'tags': ['test']
    })

    errors, warnings = validate_skill_file(skill_path)

    assert len(errors) > 0
    assert any(e.code == 'SKILL_022' and e.severity == 'CRITICAL' for e in errors)
    assert 'CSV string' in str(errors[0].expected)
```

---

## 9. Rollout Strategy

### 9.1 Phase 1: Validator Creation

- [ ] Implement validator per 6767-d schema
- [ ] Add comprehensive test suite (>90% coverage)
- [ ] Validate against reference plugins (known good/bad)
- [ ] Document all error codes in README

### 9.2 Phase 2: Template Updates

- [ ] Update skill-template.md: `allowed-tools` → CSV string
- [ ] Update gemini-prompt-template.md: enterprise fields required
- [ ] Update generation-config.json: enterprise-only validation
- [ ] Regenerate any auto-generated skills

### 9.3 Phase 3: CI Integration

- [ ] Add PR workflow (.github/workflows/pr.yml)
- [ ] Add main workflow (.github/workflows/main.yml)
- [ ] Test on sample PRs
- [ ] Document workflow behavior in README

### 9.4 Phase 4: Enforcement

- [ ] Enable PR blocking (set `continue-on-error: false`)
- [ ] Monitor first week for false positives
- [ ] Adjust validator if needed
- [ ] Publish rollout AAR

---

## 10. Deprecation of Old Validators

### 10.1 Legacy Validators (Deprecated)

**Deprecated**:
- Any validator that supports "Anthropic-minimum" mode
- Any validator that treats `allowed-tools` YAML array as valid
- Any validator that doesn't enforce enterprise fields

**Action**: Update or replace with 6767-c/d/e compliant validator

### 10.2 Migration Path

**For existing plugins**:
1. Run new validator to identify violations
2. Fix CRITICAL errors first (blocking)
3. Fix HIGH errors next (important)
4. Address MEDIUM/LOW warnings over time
5. Update CI to use new validator

**Grace Period**: None (enterprise mode enforced immediately)

---

## 11. References

### 11.1 Related Standards

- **6767-c**: Extensions Standard (policy and rationale)
- **6767-d**: Extensions Schema (validation rules)
- **Document Filing System v4.2**: 000-docs/ structure

### 11.2 Tools

- **Validator Reference Implementation**: `/scripts/validate_standards.py`
- **CI Workflow Templates**: `.github/workflows/`
- **Pre-commit Hook Template**: Included in section 7.1

---

**END OF SPECIFICATION**

**Version**: 3.0.0
**Status**: CANONICAL (Enterprise-Only)
**Date**: 2025-12-20
