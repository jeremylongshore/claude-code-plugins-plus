# 6767-d-AT-STND-claude-code-extensions-schema.md

**Document Type**: Architecture & Technical - Standard (AT-STND)
**Document ID**: 6767-d-AT-STND-claude-code-extensions-schema
**Title**: Claude Code Extensions Schema (Machine-Checkable)
**Version**: 3.0.0
**Status**: CANONICAL (Enterprise-Only)
**Date**: 2025-12-20
**Companion To**: 6767-c (Extensions Standard)
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

This specification defines the **machine-checkable schema** for Claude Code extensions. It provides formal validation rules, data types, constraints, and error codes that validators MUST implement.

**Relationship to 6767-c**:
- 6767-c: Human-readable standard (policy, rationale, examples)
- 6767-d: Machine-readable schema (types, validators, error codes)

All rules herein operate in **ENTERPRISE MODE ONLY**.

---

## 2. Naming Patterns (Regex)

### 2.1 Kebab-Case Pattern

```regex
^[a-z0-9-]+$
```

**Rules**:
- Lowercase letters (a-z)
- Numbers (0-9)
- Hyphens (-) allowed
- NO uppercase, NO underscores, NO spaces

**Error Code**: `NAMING_001`
**Severity**: CRITICAL

### 2.2 Reserved Word Ban

**Banned Substrings** (case-insensitive):
- `claude`
- `anthropic`

**Pattern** (for detection):
```regex
(claude|anthropic)
```

**Error Code**: `NAMING_002`
**Severity**: CRITICAL

### 2.3 Max Length

| Component | Max Length | Error Code | Severity |
|-----------|------------|------------|----------|
| Plugin name | 64 chars | `NAMING_003` | CRITICAL |
| Skill name | 64 chars | `NAMING_004` | CRITICAL |
| Description | 1024 chars | `NAMING_005` | HIGH |

---

## 3. Plugin Manifest Schema (plugin.json)

### 3.1 JSON Schema (Formal)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "version", "description", "author", "license", "keywords"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z0-9-]+$",
      "minLength": 1,
      "maxLength": 64,
      "not": { "pattern": "(claude|anthropic)" }
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "description": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1024
    },
    "author": {
      "type": "object",
      "required": ["name", "email"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "email": { "type": "string", "format": "email" },
        "url": { "type": "string", "format": "uri" }
      }
    },
    "license": {
      "type": "string",
      "minLength": 1
    },
    "keywords": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1
    },
    "homepage": { "type": "string", "format": "uri" },
    "repository": { "type": "string", "format": "uri" },
    "commands": {
      "oneOf": [
        { "type": "string" },
        { "type": "array", "items": { "type": "string" } }
      ]
    },
    "agents": {
      "oneOf": [
        { "type": "string" },
        { "type": "array", "items": { "type": "string" } }
      ]
    },
    "skills": {
      "oneOf": [
        { "type": "string" },
        { "type": "array", "items": { "type": "string" } }
      ]
    },
    "hooks": {
      "oneOf": [
        { "type": "string" },
        { "type": "object" }
      ]
    },
    "mcpServers": {
      "type": "object",
      "patternProperties": {
        "^[a-z0-9-]+$": {
          "type": "object",
          "required": ["command"],
          "properties": {
            "command": { "type": "string" },
            "args": { "type": "array", "items": { "type": "string" } },
            "env": { "type": "object" }
          }
        }
      }
    }
  }
}
```

### 3.2 Field Validation Rules

#### 3.2.1 name

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `PLUGIN_001` | CRITICAL |
| Required | true | `PLUGIN_002` | CRITICAL |
| Pattern | `^[a-z0-9-]+$` | `PLUGIN_003` | CRITICAL |
| Min length | 1 | `PLUGIN_004` | CRITICAL |
| Max length | 64 | `PLUGIN_005` | CRITICAL |
| Ban reserved | No "claude" or "anthropic" | `PLUGIN_006` | CRITICAL |

#### 3.2.2 version

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `PLUGIN_010` | CRITICAL |
| Required | true | `PLUGIN_011` | CRITICAL |
| Pattern | `^\\d+\\.\\d+\\.\\d+$` (SemVer) | `PLUGIN_012` | CRITICAL |

**Valid**: `1.0.0`, `2.3.1`, `0.1.0`
**Invalid**: `v1.0`, `1.0`, `1` (missing parts)

#### 3.2.3 description

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `PLUGIN_020` | CRITICAL |
| Required | true | `PLUGIN_021` | CRITICAL |
| Min length | 1 | `PLUGIN_022` | CRITICAL |
| Max length | 1024 | `PLUGIN_023` | HIGH |

#### 3.2.4 author

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | object | `PLUGIN_030` | CRITICAL |
| Required | true | `PLUGIN_031` | CRITICAL |
| Required fields | name, email | `PLUGIN_032` | CRITICAL |
| name type | string, min 1 char | `PLUGIN_033` | CRITICAL |
| email type | string, valid email | `PLUGIN_034` | CRITICAL |

#### 3.2.5 license

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `PLUGIN_040` | CRITICAL |
| Required | true | `PLUGIN_041` | CRITICAL |
| Min length | 1 | `PLUGIN_042` | CRITICAL |

**Recommended**: SPDX identifiers (MIT, Apache-2.0, Proprietary, etc.)

#### 3.2.6 keywords

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | array of strings | `PLUGIN_050` | CRITICAL |
| Required | true | `PLUGIN_051` | CRITICAL |
| Min items | 1 | `PLUGIN_052` | CRITICAL |

---

## 4. Skill Frontmatter Schema (YAML)

### 4.1 Required Fields (Enterprise)

```yaml
name: string                           # REQUIRED
description: string                    # REQUIRED
allowed-tools: string                  # REQUIRED (CSV, NOT array)
version: string                        # REQUIRED
author: string                         # REQUIRED
license: string                        # REQUIRED
tags: array                            # REQUIRED
```

### 4.2 Field Validation Rules

#### 4.2.1 name

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `SKILL_001` | CRITICAL |
| Required | true | `SKILL_002` | CRITICAL |
| Pattern | `^[a-z0-9-]+$` | `SKILL_003` | CRITICAL |
| Min length | 1 | `SKILL_004` | CRITICAL |
| Max length | 64 | `SKILL_005` | CRITICAL |
| Ban reserved | No "claude" or "anthropic" | `SKILL_006` | CRITICAL |

#### 4.2.2 description

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `SKILL_010` | CRITICAL |
| Required | true | `SKILL_011` | CRITICAL |
| Min length | 1 | `SKILL_012` | CRITICAL |
| Max length | 1024 | `SKILL_013` | HIGH |
| Voice | Third-person | `SKILL_014` | MEDIUM |
| MUST contain | "Use when" phrase | `SKILL_015` | HIGH |
| MUST contain | Trigger phrases | `SKILL_016` | HIGH |

**Pattern for "Use when"**:
```regex
[Uu]se\s+when
```

#### 4.2.3 allowed-tools (CRITICAL: CSV String NOT YAML Array)

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | **string** (NOT array) | `SKILL_020` | CRITICAL |
| Required | true | `SKILL_021` | CRITICAL |
| Format | CSV (comma-separated) | `SKILL_022` | CRITICAL |
| Min length | 1 | `SKILL_023` | CRITICAL |

**CORRECT** (CSV string):
```yaml
allowed-tools: "Read,Write,Grep,Glob,Bash(git:*)"
```

**WRONG** (YAML array):
```yaml
allowed-tools:              # ❌ TYPE ERROR
  - Read
  - Write
```

**Validation**:
```python
import yaml

frontmatter = yaml.safe_load(content)
allowed_tools = frontmatter.get('allowed-tools')

if isinstance(allowed_tools, list):
    raise ValidationError(
        code='SKILL_022',
        severity='CRITICAL',
        message='allowed-tools MUST be CSV string, not YAML array',
        expected='allowed-tools: "Read,Write,Grep"',
        actual='allowed-tools: [Read, Write, Grep]',
        fix='Convert YAML array to comma-separated string'
    )
```

**Bash Scoping Validation**:

Pattern: `Bash\([^)]+\)`

**Unscoped Bash** (CRITICAL error):
```yaml
allowed-tools: "Read,Write,Bash"     # ❌ Unscoped Bash
```

**Error Code**: `SKILL_024`
**Severity**: CRITICAL
**Fix**: Scope to specific commands: `Bash(git:*)`, `Bash(npm:*)`, etc.

#### 4.2.4 version

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `SKILL_030` | CRITICAL |
| Required | true | `SKILL_031` | CRITICAL |
| Pattern | `^\\d+\\.\\d+\\.\\d+$` | `SKILL_032` | CRITICAL |

#### 4.2.5 author

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `SKILL_040` | CRITICAL |
| Required | true | `SKILL_041` | CRITICAL |
| Format | "Name <email>" or "Name" | `SKILL_042` | HIGH |
| Min length | 1 | `SKILL_043` | CRITICAL |

**Recommended Pattern**:
```regex
^[^<]+\s*(<[^>]+>)?$
```

#### 4.2.6 license

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `SKILL_050` | CRITICAL |
| Required | true | `SKILL_051` | CRITICAL |
| Min length | 1 | `SKILL_052` | CRITICAL |

#### 4.2.7 tags

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | array of strings | `SKILL_060` | CRITICAL |
| Required | true | `SKILL_061` | CRITICAL |
| Min items | 1 | `SKILL_062` | CRITICAL |

### 4.3 Body Constraints

| Constraint | Limit | Error Code | Severity |
|------------|-------|------------|----------|
| Max words | 5,000 | `SKILL_100` | HIGH |
| Max lines | 500 | `SKILL_101` | HIGH |
| Max tokens | ~7,500 | `SKILL_102` | MEDIUM |
| Path format | `{baseDir}/...` (no absolute) | `SKILL_103` | CRITICAL |
| Reference depth | 1 level | `SKILL_104` | MEDIUM |

**Path Validation**:
```python
import re

# Detect absolute paths (CRITICAL error)
absolute_path_pattern = re.compile(r'(?:^|[^{])/(?:home|usr|opt|var|etc)/')
if absolute_path_pattern.search(body):
    raise ValidationError(
        code='SKILL_103',
        severity='CRITICAL',
        message='Absolute paths not allowed in skill body',
        fix='Use {baseDir}/... for repo-relative paths'
    )
```

---

## 5. Agent Frontmatter Schema (YAML)

### 5.1 Required Fields (Enterprise)

```yaml
name: string                           # REQUIRED
description: string                    # REQUIRED
```

### 5.2 Optional Fields

```yaml
tools: string                          # OPTIONAL (CSV string, inherits all if omitted)
model: string                          # OPTIONAL (inherit, sonnet, opus, haiku)
permissionMode: string                 # OPTIONAL
skills: string                         # OPTIONAL (CSV string)
```

### 5.3 Field Validation Rules

#### 5.3.1 name

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `AGENT_001` | CRITICAL |
| Required | true | `AGENT_002` | CRITICAL |
| Min length | 1 | `AGENT_003` | CRITICAL |

#### 5.3.2 description

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string | `AGENT_010` | CRITICAL |
| Required | true | `AGENT_011` | CRITICAL |
| Min length | 1 | `AGENT_012` | CRITICAL |

#### 5.3.3 tools (optional)

| Rule | Value | Error Code | Severity |
|------|-------|------------|----------|
| Type | string (CSV) | `AGENT_020` | HIGH |
| Required | false | N/A | N/A |
| Format | CSV (comma-separated) | `AGENT_021` | HIGH |

---

## 6. Directory Structure Validation

### 6.1 Critical Rules

| Rule | Error Code | Severity |
|------|------------|----------|
| `.claude-plugin/` MUST exist | `DIR_001` | CRITICAL |
| `.claude-plugin/` MUST contain ONLY `plugin.json` | `DIR_002` | CRITICAL |
| `plugin.json` MUST exist at `.claude-plugin/plugin.json` | `DIR_003` | CRITICAL |
| Component dirs (skills/, agents/, commands/) MUST be at plugin root | `DIR_004` | CRITICAL |
| Component dirs MUST NOT be inside `.claude-plugin/` | `DIR_005` | CRITICAL |
| No empty directories | `DIR_006` | MEDIUM |

### 6.2 Validation Logic

```python
def validate_directory_structure(plugin_root: Path):
    claude_plugin_dir = plugin_root / '.claude-plugin'

    # Check .claude-plugin/ exists
    if not claude_plugin_dir.exists():
        raise ValidationError('DIR_001', 'CRITICAL', '.claude-plugin/ does not exist')

    # Check ONLY plugin.json in .claude-plugin/
    files_in_claude_plugin = list(claude_plugin_dir.iterdir())
    if len(files_in_claude_plugin) != 1 or files_in_claude_plugin[0].name != 'plugin.json':
        raise ValidationError(
            'DIR_002',
            'CRITICAL',
            '.claude-plugin/ MUST contain ONLY plugin.json',
            expected='ONLY plugin.json',
            actual=f'Found: {[f.name for f in files_in_claude_plugin]}',
            fix='Remove all files except plugin.json from .claude-plugin/'
        )

    # Check component dirs NOT inside .claude-plugin/
    for component_dir in ['skills', 'agents', 'commands', 'hooks']:
        if (claude_plugin_dir / component_dir).exists():
            raise ValidationError(
                'DIR_005',
                'CRITICAL',
                f'{component_dir}/ MUST be at plugin root, NOT inside .claude-plugin/',
                expected=f'{component_dir}/ at plugin root',
                actual=f'{component_dir}/ inside .claude-plugin/',
                fix=f'Move .claude-plugin/{component_dir}/ to plugin root'
            )
```

---

## 7. Security Validation

### 7.1 Secret Detection Patterns

```python
import re

SECRET_PATTERNS = [
    (re.compile(r'["\']?API_KEY["\']?\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})'), "API key"),
    (re.compile(r'["\']?SECRET["\']?\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})'), "Secret"),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), "OpenAI API key"),
    (re.compile(r'AKIA[A-Z0-9]{16}'), "AWS access key"),
    (re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----'), "Private key"),
]
```

### 7.2 Exemption Rules (Minimal Allowlist)

**Exempt Paths**:
- `tests/fixtures/**` (explicit fixtures directory only)

**Exempt Content Patterns**:
```python
TEST_FIXTURE_MARKERS = [
    'EXAMPLE',
    'TEST-',
    'DUMMY-',
    'AKIAIOSFODNN7EXAMPLE',  # AWS example key
]

def is_test_fixture(content: str) -> bool:
    content_upper = content.upper()
    return any(marker in content_upper for marker in TEST_FIXTURE_MARKERS)
```

### 7.3 Security Error Codes

| Error Code | Severity | Description |
|------------|----------|-------------|
| `SEC_001` | CRITICAL | Hardcoded API key detected |
| `SEC_002` | CRITICAL | Hardcoded AWS key detected |
| `SEC_003` | CRITICAL | Hardcoded SSH private key detected |
| `SEC_004` | CRITICAL | .env file committed |
| `SEC_005` | CRITICAL | Absolute path detected |
| `SEC_006` | CRITICAL | Unscoped Bash tool |

---

## 8. Error Schema

### 8.1 ValidationError Structure

```python
class ValidationError:
    def __init__(
        self,
        code: str,           # Error code (e.g., 'SKILL_022')
        severity: str,       # CRITICAL | HIGH | MEDIUM | LOW
        message: str,        # Human-readable error message
        file_path: str,      # Path to file with error
        field: str,          # Field/rule violated
        expected: str,       # What was expected
        actual: str,         # What was found
        fix: str             # How to remediate
    ):
        self.code = code
        self.severity = severity
        self.message = message
        self.file_path = file_path
        self.field = field
        self.expected = expected
        self.actual = actual
        self.fix = fix
```

### 8.2 Exit Codes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| `0` | All validations passed | ✅ Proceed |
| `1` | CRITICAL or HIGH errors | ❌ Block (CI fails) |
| `2` | MEDIUM or LOW warnings | ⚠️  Warn (can proceed, should fix) |

---

## 9. Validator Implementation Requirements

### 9.1 Required Checks

Every validator MUST implement:

1. **Manifest Validation**:
   - plugin.json exists at `.claude-plugin/plugin.json`
   - All enterprise required fields present
   - Name pattern `^[a-z0-9-]+$`, max 64 chars
   - Version pattern `^\d+\.\d+\.\d+$` (SemVer)
   - Author has name + email
   - Keywords array has ≥1 item

2. **Directory Structure Validation**:
   - `.claude-plugin/` contains ONLY `plugin.json`
   - No component dirs inside `.claude-plugin/`
   - All component dirs at plugin root

3. **Skill Validation**:
   - Skills at `skills/<skill-name>/SKILL.md`
   - Frontmatter has all enterprise required fields
   - `allowed-tools` is CSV string (NOT array)
   - Unscoped Bash flagged as CRITICAL
   - Description contains "Use when" + trigger phrases
   - Body ≤5,000 words / 500 lines

4. **Security Validation**:
   - Scan all files for hardcoded secrets
   - Exempt only `tests/fixtures/**` + known test patterns
   - Flag .env files as CRITICAL
   - Detect absolute paths
   - Validate Bash scoping

5. **Naming Validation**:
   - All names kebab-case
   - No reserved words (claude, anthropic)
   - Max length enforcement

### 9.2 Validation Flow

```python
def validate_all(plugin_root: Path) -> Tuple[List[ValidationError], List[ValidationError]]:
    errors = []
    warnings = []

    # 1. Manifest
    errors.extend(validate_plugin_manifest(plugin_root))

    # 2. Directory Structure
    errors.extend(validate_directory_structure(plugin_root))

    # 3. Skills
    errors.extend(validate_skills(plugin_root))

    # 4. Agents (if present)
    errors.extend(validate_agents(plugin_root))

    # 5. Security
    errors.extend(validate_security(plugin_root))

    # 6. Naming
    errors.extend(validate_naming(plugin_root))

    # Separate by severity
    critical_or_high = [e for e in errors if e.severity in ['CRITICAL', 'HIGH']]
    medium_or_low = [e for e in errors if e.severity in ['MEDIUM', 'LOW']]

    return (critical_or_high, medium_or_low)
```

---

## 10. Test Patterns

### 10.1 Test Fixture Allowlist

**Allowed in `tests/fixtures/**`**:
- Example API keys (containing "EXAMPLE")
- Dummy credentials (containing "DUMMY")
- Test keys (containing "test-")
- AWS example key: `AKIAIOSFODNN7EXAMPLE`

**Example**:
```python
# tests/fixtures/test_keys.py
EXAMPLE_API_KEY = "sk_test_1234567890abcdefghijklmnopqrs"  # ✅ Allowed (contains "test")
AWS_EXAMPLE_KEY = "AKIAIOSFODNN7EXAMPLE"                   # ✅ Allowed (known pattern)
```

**Real Secrets** (CRITICAL error even in tests):
```python
# tests/test_auth.py
API_KEY = "sk_live_abcd1234..."  # ❌ CRITICAL (real key in test file)
```

### 10.2 Test Pattern Detection

```python
def is_allowed_test_secret(content: str, file_path: Path) -> bool:
    # Only exempt files in tests/fixtures/
    if 'tests' in file_path.parts and 'fixtures' in file_path.parts:
        return True

    # Or files with known test markers
    content_upper = content.upper()
    return any(marker in content_upper for marker in [
        'EXAMPLE', 'TEST-', 'DUMMY-', 'AKIAIOSFODNN7EXAMPLE'
    ])
```

---

## 11. Compliance Reporting

### 11.1 Report Format (JSON)

```json
{
  "validator_version": "3.0.0",
  "plugin_root": "/path/to/plugin",
  "enterprise_mode": true,
  "timestamp": "2025-12-20T10:00:00Z",
  "summary": {
    "total_errors": 2,
    "critical": 1,
    "high": 1,
    "medium": 0,
    "low": 0
  },
  "errors": [
    {
      "code": "SKILL_022",
      "severity": "CRITICAL",
      "file": "skills/my-skill/SKILL.md",
      "field": "allowed-tools",
      "expected": "CSV string (e.g., \"Read,Write,Grep\")",
      "actual": "YAML array format",
      "fix": "Change frontmatter to: allowed-tools: \"Read,Write,Grep\""
    }
  ],
  "warnings": [],
  "passed": false
}
```

### 11.2 Exit Behavior

```python
def main():
    errors, warnings = validate_all(plugin_root)

    print_summary(errors, warnings)

    if errors:  # CRITICAL or HIGH
        sys.exit(1)  # Block CI
    elif warnings:  # MEDIUM or LOW
        sys.exit(2)  # Warn (can proceed)
    else:
        sys.exit(0)  # Success
```

---

## 12. References

### 12.1 Related Standards

- **6767-c**: Extensions Standard (human-readable policy)
- **6767-e**: Validation and CI Gates (enforcement specification)

### 12.2 External Standards

- **JSON Schema**: http://json-schema.org/draft-07/schema#
- **YAML 1.2**: https://yaml.org/spec/1.2/spec.html
- **Semantic Versioning**: https://semver.org/
- **SPDX Licenses**: https://spdx.org/licenses/

---

**END OF SPECIFICATION**

**Version**: 3.0.0
**Status**: CANONICAL (Enterprise-Only)
**Date**: 2025-12-20
