#!/usr/bin/env python3
"""
Jeremy Plugin Tool - Nixtla-Grade Validator v2.0

Combines:
- Anthropic 2025 Skills Specification (code.claude.com/docs/en/skills)
- Intent Solutions Enterprise Standard (6767-c v3.0.0)
- Nixtla Quality Standards (strict mode)

Adapted from: /home/jeremy/000-projects/nixtla/004-scripts/validate_skills_v2.py

Usage:
    python validate_plugin_nixtla.py [plugin_path] [--verbose|-v]

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# === CONSTANTS ===

# Valid tools per Claude Code spec (2025)
VALID_TOOLS = {
    'Read', 'Write', 'Edit', 'Bash', 'Glob', 'Grep',
    'WebFetch', 'WebSearch', 'Task', 'TodoWrite',
    'NotebookEdit', 'AskUserQuestion', 'Skill'
}

# Anthropic required fields (minimum spec)
ANTHROPIC_REQUIRED = {'name', 'description'}

# Enterprise required fields (Intent Solutions marketplace)
ENTERPRISE_REQUIRED = {'allowed-tools', 'version', 'author', 'license'}

# All required fields (Anthropic + Enterprise)
REQUIRED_FIELDS = ANTHROPIC_REQUIRED | ENTERPRISE_REQUIRED

# Optional fields per Anthropic spec
OPTIONAL_FIELDS = {'model', 'disable-model-invocation', 'mode', 'tags', 'metadata'}

# Deprecated fields (warn but don't error)
DEPRECATED_FIELDS = {'when_to_use'}

# Nixtla required sections (strict quality mode)
REQUIRED_SECTIONS = [
    "# ",  # title line
    "## Overview",
    "## Prerequisites",
    "## Instructions",
    "## Output",
    "## Error Handling",
    "## Examples",
    "## Resources",
]

# Regex patterns
RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
RE_DESCRIPTION_USE_WHEN = re.compile(r"\bUse when\b", re.IGNORECASE)
RE_DESCRIPTION_TRIGGER_WITH = re.compile(r"\bTrigger with\b", re.IGNORECASE)
RE_BASEDIR_SCRIPTS = re.compile(r"{baseDir}/scripts/([\w\-./]+)")
RE_BASEDIR_REFERENCES = re.compile(r"{baseDir}/references/([\w\-./]+)")
RE_BASEDIR_ASSETS = re.compile(r"{baseDir}/assets/([\w\-./]+)")
RE_FIRST_PERSON = re.compile(r"\b(I can|I will|I'm going to|I help)\b", re.IGNORECASE)
RE_SECOND_PERSON = re.compile(r"\b(You can|You should|You will)\b", re.IGNORECASE)
FORBIDDEN_WORDS = ("anthropic", "claude")
CODE_FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")
HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s+")
ABSOLUTE_PATH_PATTERNS = [
    (re.compile(r"/home/\w+/"), "/home/..."),
    (re.compile(r"/Users/\w+/"), "/Users/..."),
    (re.compile(r"[A-Za-z]:\\\\Users\\\\", re.IGNORECASE), "C:\\\\Users\\\\..."),
]

# Defaults
DEFAULT_AUTHOR = "Jeremy Longshore <jeremy@intentsolutions.io>"
DEFAULT_LICENSE = "MIT"

# Skill list token budget (Lee Han Chung deep dive)
TOTAL_DESCRIPTION_BUDGET_WARN = 12_000
TOTAL_DESCRIPTION_BUDGET_ERROR = 15_000


# === UTILITY FUNCTIONS ===

def find_skill_files(plugin_path: Path) -> List[Path]:
    """
    Find all SKILL.md files in a plugin directory.
    Adapted for claude-code-plugins structure.
    """
    # Exclude backup/archive directories
    excluded_dirs = {
        "archive", "backups", "backup", ".git", "node_modules",
        "__pycache__", ".venv", "skills-backup-"
    }

    results = []

    # Check if this is a single plugin directory
    if (plugin_path / ".claude-plugin").exists():
        # Single plugin mode - find skills in this plugin
        skills_dir = plugin_path / "skills"
        if skills_dir.exists():
            for skill_md in skills_dir.rglob("SKILL.md"):
                if skill_md.is_file():
                    parts = skill_md.relative_to(plugin_path).parts
                    if not any(part in excluded_dirs or part.startswith("skills-backup-") for part in parts):
                        results.append(skill_md)
    else:
        # Repository root mode - find all plugin skills
        plugins_dir = plugin_path / "plugins"
        if plugins_dir.exists():
            for skill_md in plugins_dir.rglob("SKILL.md"):
                if skill_md.is_file():
                    parts = skill_md.relative_to(plugin_path).parts
                    if not any(part in excluded_dirs or part.startswith("skills-backup-") for part in parts):
                        if "skills" in parts:  # Must be in a skills/ directory
                            results.append(skill_md)

    return results


def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """Parse YAML frontmatter from SKILL.md content."""
    m = RE_FRONTMATTER.match(content)
    if not m:
        raise ValueError("Invalid or absent YAML frontmatter block at top of SKILL.md")
    front_str, body = m.groups()
    try:
        data = yaml.safe_load(front_str) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error: {e}")
    if not isinstance(data, dict):
        raise ValueError("Frontmatter is not a YAML mapping")
    return data, body


def parse_allowed_tools(tools_value: Any) -> List[str]:
    """Parse allowed-tools as a CSV string (Claude Code standard)."""
    if isinstance(tools_value, str):
        return [t.strip() for t in tools_value.split(',') if t.strip()]
    return []


def validate_tool_permission(tool: str) -> Tuple[bool, str]:
    """Validate a single tool permission including wildcards like Bash(git:*)."""
    base_tool = tool.split('(')[0].strip()

    if base_tool not in VALID_TOOLS:
        return False, f"Unknown tool: {base_tool}"

    # Validate wildcard syntax if present
    if '(' in tool:
        if not tool.endswith(')'):
            return False, f"Invalid wildcard syntax (missing closing paren): {tool}"
        inner = tool[tool.index('(')+1:-1]
        if ':' not in inner:
            return False, f"Wildcard missing colon (use cmd:*): {tool}"

    return True, ""


def estimate_word_count(content: str) -> int:
    """Estimate word count for content length check."""
    # Remove frontmatter
    content_body = re.sub(r'^---\n.*?\n---\n?', '', content, flags=re.DOTALL)
    return len(content_body.split())


# === VALIDATION FUNCTIONS ===

def validate_frontmatter(path: Path, fm: dict) -> Tuple[List[str], List[str]]:
    """
    Validate SKILL.md frontmatter.
    Returns: (errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    # === REQUIRED FIELDS (Anthropic + Enterprise) ===

    for key in REQUIRED_FIELDS:
        if key not in fm:
            errors.append(f"[frontmatter] Missing required field: '{key}'")

    # === FIELD-SPECIFIC VALIDATION ===

    # name field
    if 'name' in fm:
        name = str(fm['name']).strip()
        if not name:
            errors.append("[frontmatter] 'name' must be non-empty")
        else:
            # Kebab-case check
            if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
                errors.append(f"[frontmatter] 'name' must be kebab-case (lowercase + hyphens): {name}")

            # Length check
            if len(name) > 64:
                errors.append("[frontmatter] 'name' exceeds 64 characters")

            # Reserved words
            name_lower = name.lower()
            if 'anthropic' in name_lower or 'claude' in name_lower:
                errors.append(f"[frontmatter] 'name' contains reserved word: {name}")

            # Folder match check (best practice, not error)
            folder_name = path.parent.name
            if name != folder_name:
                warnings.append(f"[frontmatter] 'name' '{name}' differs from folder '{folder_name}' (best practice: match them)")

    # description field
    if 'description' in fm:
        desc = str(fm['description']).strip()

        if not desc:
            errors.append("[frontmatter] 'description' must be non-empty")
        else:
            # Length checks
            if len(desc) < 20:
                warnings.append("[frontmatter] 'description' too short (< 20 chars) - may not trigger well")
            if len(desc) > 1024:
                errors.append("[frontmatter] 'description' exceeds 1024 characters")

            # Nixtla strict quality checks (ERRORS in strict mode)
            if not RE_DESCRIPTION_USE_WHEN.search(desc):
                errors.append("[frontmatter] 'description' must include 'Use when ...' phrase (nixtla quality standard)")

            if not RE_DESCRIPTION_TRIGGER_WITH.search(desc):
                errors.append("[frontmatter] 'description' must include 'Trigger with ...' phrase (nixtla quality standard)")

            # Voice checks (nixtla strict mode)
            if RE_FIRST_PERSON.search(desc):
                errors.append("[frontmatter] 'description' must NOT use first person (I can / I will / etc.) - use third person")

            if RE_SECOND_PERSON.search(desc):
                errors.append("[frontmatter] 'description' must NOT use second person (You can / You should) - use third person")

            # Reserved words
            desc_lower = desc.lower()
            for bad in FORBIDDEN_WORDS:
                if bad in desc_lower:
                    errors.append(f"[frontmatter] 'description' contains reserved word: '{bad}'")

            # Imperative language check (best practice)
            imperative_starts = ['analyze', 'create', 'generate', 'build', 'debug',
                               'optimize', 'validate', 'test', 'deploy', 'monitor',
                               'fix', 'review', 'extract', 'convert', 'implement',
                               'detect', 'forecast', 'transform', 'compare']
            has_imperative = any(v in desc_lower for v in imperative_starts)
            if not has_imperative:
                warnings.append("[frontmatter] Consider using action verbs (analyze, detect, forecast, etc.)")

    # allowed-tools field
    if 'allowed-tools' in fm:
        raw_tools = fm['allowed-tools']
        tools_type_error = False
        if isinstance(raw_tools, list):
            errors.append(
                "[frontmatter] 'allowed-tools' must be a comma-separated string (CSV), not a YAML array "
                '(example: allowed-tools: "Read, Write, Bash(git:*)")'
            )
            tools_type_error = True
            tools: List[str] = []
        elif isinstance(raw_tools, str):
            tools = parse_allowed_tools(raw_tools)
        else:
            errors.append(
                "[frontmatter] 'allowed-tools' must be a comma-separated string (CSV) "
                '(example: allowed-tools: "Read, Write, Bash(git:*)")'
            )
            tools_type_error = True
            tools = []

        if not tools and not tools_type_error:
            errors.append("[frontmatter] 'allowed-tools' is empty - must list at least one tool")

        for tool in tools:
            valid, msg = validate_tool_permission(tool)
            if not valid:
                errors.append(f"[frontmatter] allowed-tools: {msg}")

        # Nixtla strict mode: forbid unscoped Bash
        if 'Bash' in tools:
            errors.append("[frontmatter] allowed-tools: unscoped 'Bash' forbidden - use scoped Bash(git:*) or Bash(npm:*)")

        # Info about over-permissioning
        if len(tools) > 6:
            warnings.append(f"[frontmatter] Many tools permitted ({len(tools)}) - consider limiting for security")

    # version field
    if 'version' in fm:
        version = str(fm['version'])
        if not re.match(r'^\d+\.\d+\.\d+', version):
            errors.append(f"[frontmatter] 'version' should be semver format (X.Y.Z): {version}")

    # author field
    if 'author' in fm:
        author = str(fm['author']).strip()
        if not author:
            errors.append("[frontmatter] 'author' must be non-empty")
        # Recommend email format
        if '@' not in author:
            warnings.append("[frontmatter] 'author' best practice: include email (Name <email>)")

    # license field
    if 'license' in fm:
        license_val = str(fm['license']).strip()
        if not license_val:
            errors.append("[frontmatter] 'license' must be non-empty")

    # === OPTIONAL FIELDS ===

    # model field
    if 'model' in fm:
        model = fm['model']
        valid_models = ['inherit', 'sonnet', 'haiku', 'opus']
        if model not in valid_models and not str(model).startswith('claude-'):
            warnings.append(f"[frontmatter] 'model' value '{model}' not standard (use: inherit, sonnet, haiku, opus, or claude-*)")

    # disable-model-invocation field
    if 'disable-model-invocation' in fm:
        dmi = fm['disable-model-invocation']
        if not isinstance(dmi, bool):
            errors.append(f"[frontmatter] 'disable-model-invocation' must be boolean, got: {type(dmi).__name__}")

    # mode field
    if 'mode' in fm:
        mode = fm['mode']
        if not isinstance(mode, bool):
            errors.append(f"[frontmatter] 'mode' must be boolean, got: {type(mode).__name__}")

    # tags field
    if 'tags' in fm:
        tags = fm['tags']
        if not isinstance(tags, list):
            errors.append(f"[frontmatter] 'tags' must be array of strings, got: {type(tags).__name__}")
        elif not all(isinstance(t, str) for t in tags):
            errors.append("[frontmatter] 'tags' must contain only strings")

    # === DEPRECATED FIELDS ===

    for field in DEPRECATED_FIELDS:
        if field in fm:
            warnings.append(f"[frontmatter] Deprecated field '{field}' - use detailed 'description' instead")

    # === UNKNOWN FIELDS ===

    known_fields = REQUIRED_FIELDS | OPTIONAL_FIELDS | DEPRECATED_FIELDS
    unknown_fields = set(fm.keys()) - known_fields
    for field in unknown_fields:
        warnings.append(f"[frontmatter] Non-standard field: '{field}'")

    return errors, warnings


def validate_body(path: Path, body: str) -> Tuple[List[str], List[str]]:
    """
    Validate SKILL.md body content.
    Returns: (errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []
    lines = body.splitlines()

    # === LENGTH CHECKS ===

    # Nixtla strict mode: 500 line limit
    if len(lines) > 500:
        errors.append(f"[body] SKILL.md body has {len(lines)} lines (max 500). Use progressive disclosure (extract to references/)")

    # Source of truth: word count check
    word_count = len(body.split())
    if word_count > 5000:
        warnings.append(f"[body] Content exceeds 5000 words ({word_count}) - may overwhelm context")
    elif word_count > 3500:
        warnings.append(f"[body] Content is lengthy ({word_count} words) - consider references/ directory")

    # === REQUIRED SECTIONS (Nixtla strict mode) ===

    for sec in REQUIRED_SECTIONS:
        if sec not in body:
            errors.append(f"[body] Required section missing: '{sec}' (nixtla quality standard)")

    # === SECTION CONTENT VALIDATION ===

    def _section_body(section_heading: str) -> str:
        m_heading = re.match(r"^(#+)\s+", section_heading.strip())
        if not m_heading:
            return ""
        level = len(m_heading.group(1))

        lower = body.lower()
        idx = lower.find(section_heading.lower())
        if idx == -1:
            return ""

        after = body[idx + len(section_heading):]
        stop = None
        for m in re.finditer(r"^\s*(#{1,6})\s+", after, flags=re.M):
            next_level = len(m.group(1))
            if next_level <= level:
                stop = m.start()
                break

        if stop is not None:
            after = after[:stop]

        return after.strip()

    for section, min_chars, level in [
        ("## Instructions", 40, "ERROR"),
        ("## Output", 20, "WARN"),
        ("## Error Handling", 20, "WARN"),
        ("## Examples", 20, "WARN"),
        ("## Resources", 20, "WARN"),
    ]:
        content = _section_body(section)
        content_no_code = re.sub(r"```.*?```", "", content, flags=re.DOTALL).strip()
        if len(content_no_code) < min_chars:
            msg = f"[body] Section '{section}' looks empty/too short (nixtla standard)"
            if level == "ERROR":
                errors.append(msg)
            else:
                warnings.append(msg)

    # === INSTRUCTIONS MUST BE STEP-BY-STEP ===

    instructions = _section_body("## Instructions")
    if instructions:
        has_numbered = bool(re.search(r"(?m)^\s*1\.\s+\S+", instructions))
        has_step_heading = bool(re.search(r"(?mi)^\s*#{2,6}\s*step\s*\d+", instructions))
        has_step_label = bool(re.search(r"(?mi)^\s*step\s*\d+[:\-]", instructions))
        if not (has_numbered or has_step_heading or has_step_label):
            errors.append("[body] '## Instructions' must include step-by-step steps (numbered list or Step headings)")

    # === PATH CHECKS ===

    body_no_code = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
    body_no_code = re.sub(r'`[^`]+`', '', body_no_code)

    for i, line in enumerate(body_no_code.splitlines(), start=1):
        for pattern, desc in ABSOLUTE_PATH_PATTERNS:
            if pattern.search(line):
                errors.append(f"[body] Line {i}: contains absolute/OS-specific path ({desc}) - use '{{baseDir}}/...'")
                break

        if "\\scripts\\" in line:
            errors.append(f"[body] Line {i}: uses backslashes in path - use forward slashes")

    # === VOICE CHECKS ===

    if re.search(r'\byou should\b|\byou can\b|\byou will\b', body, re.IGNORECASE):
        warnings.append("[body] Consider imperative language instead of 'you should/can/will'")

    return errors, warnings


def validate_scripts_exist(path: Path, body: str) -> List[str]:
    """Validate that all {baseDir}/scripts/... references point to real files."""
    errors: List[str] = []
    skill_dir = path.parent.resolve()

    referenced = set(m.group(1) for m in RE_BASEDIR_SCRIPTS.finditer(body))

    for rel in sorted(referenced):
        script_path = (skill_dir / "scripts" / rel).resolve()

        try:
            script_path.relative_to(skill_dir)
        except ValueError:
            errors.append(f"[scripts] Reference escapes skill directory: {rel}")
            continue

        if not script_path.exists():
            errors.append(f"[scripts] Referenced script not found: '{{baseDir}}/scripts/{rel}'")

    return errors


def validate_resource_files_exist(path: Path, body: str) -> List[str]:
    """Validate that all {baseDir}/references/... and {baseDir}/assets/... references exist."""
    errors: List[str] = []
    skill_dir = path.parent.resolve()

    for rel in sorted(set(m.group(1) for m in RE_BASEDIR_REFERENCES.finditer(body))):
        target = (skill_dir / "references" / rel).resolve()
        try:
            target.relative_to(skill_dir)
        except ValueError:
            errors.append(f"[resources] Reference escapes skill directory: references/{rel}")
            continue
        if not target.exists():
            errors.append(f"[resources] Referenced file not found: '{{baseDir}}/references/{rel}'")

    for rel in sorted(set(m.group(1) for m in RE_BASEDIR_ASSETS.finditer(body))):
        target = (skill_dir / "assets" / rel).resolve()
        try:
            target.relative_to(skill_dir)
        except ValueError:
            errors.append(f"[resources] Reference escapes skill directory: assets/{rel}")
            continue
        if not target.exists():
            errors.append(f"[resources] Referenced file not found: '{{baseDir}}/assets/{rel}'")

    return errors


def validate_skill(path: Path) -> Dict[str, Any]:
    """
    Validate a single SKILL.md file.
    Returns dict with errors, warnings, and metadata.
    """
    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        return {'fatal': f'Cannot read file: {e}'}

    try:
        fm, body = parse_frontmatter(content)
    except Exception as e:
        return {'fatal': str(e)}

    errors: List[str] = []
    warnings: List[str] = []

    # Frontmatter size budget check
    m = RE_FRONTMATTER.match(content)
    if m:
        front_str, _body = m.groups()
        front_len = len(front_str)
        if front_len > 15_000:
            errors.append(f"[frontmatter] Frontmatter is {front_len} chars (max 15000 per token budget)")
        elif front_len >= 12_000:
            warnings.append(f"[frontmatter] Frontmatter is {front_len} chars (warn at 12000 per token budget)")

    # Validate frontmatter
    fm_errors, fm_warnings = validate_frontmatter(path, fm)
    errors.extend(fm_errors)
    warnings.extend(fm_warnings)

    # Validate body
    body_errors, body_warnings = validate_body(path, body)
    errors.extend(body_errors)
    warnings.extend(body_warnings)

    # Validate scripts
    script_errors = validate_scripts_exist(path, body)
    errors.extend(script_errors)

    # Validate referenced resources
    resource_errors = validate_resource_files_exist(path, body)
    errors.extend(resource_errors)

    description = str(fm.get("description") or "")
    return {
        'errors': errors,
        'warnings': warnings,
        'word_count': estimate_word_count(content),
        'line_count': len(body.splitlines()),
        'description_length': len(description),
    }


# === MAIN ===

def main() -> int:
    parser = argparse.ArgumentParser(description="Jeremy Plugin Tool - Nixtla-Grade Validator")
    parser.add_argument("plugin_path", nargs="?", default=".", help="Plugin directory or repository root")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-file OK lines")
    parser.add_argument("--fail-on-warn", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    plugin_path = Path(args.plugin_path).resolve()
    if not plugin_path.exists():
        print(f"ERROR: Path does not exist: {plugin_path}", file=sys.stderr)
        return 1

    skills = find_skill_files(plugin_path)

    if not skills:
        print("No SKILL.md files found in plugin.")
        return 0

    print(f"🔍 JEREMY PLUGIN TOOL - NIXTLA-GRADE VALIDATOR v2.0")
    print(f"   Enterprise + Nixtla Strict Quality Mode")
    print(f"{'=' * 70}\n")
    print(f"Found {len(skills)} SKILL.md file(s) to validate.\n")

    total_errors = 0
    total_warnings = 0
    total_description_chars = 0
    files_compliant = []

    for skill in skills:
        rel = skill.relative_to(plugin_path) if plugin_path.is_dir() else skill.name
        result = validate_skill(skill)

        if 'fatal' in result:
            print(f"❌ {rel}: FATAL - {result['fatal']}")
            total_errors += 1
            continue

        has_issues = False

        if result['errors']:
            print(f"❌ {rel}:")
            for error in result['errors']:
                print(f"   ERROR: {error}")
            total_errors += len(result['errors'])
            has_issues = True

        if result['warnings']:
            if not has_issues:
                print(f"⚠️  {rel}:")
            for warning in result['warnings']:
                print(f"   WARN: {warning}")
            total_warnings += len(result['warnings'])
            has_issues = True

        if args.verbose and not has_issues:
            print(f"✅ {rel} - OK ({result['word_count']} words, {result['line_count']} lines)")

        if not result['errors'] and not result['warnings']:
            files_compliant.append(str(rel))

        total_description_chars += int(result.get("description_length") or 0)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total skills validated: {len(skills)}")
    print(f"✅ Fully compliant: {len(files_compliant)}")
    print(f"❌ With errors: {len(skills) - len(files_compliant)}")
    print(f"{'=' * 70}")

    # Compliance rate
    compliant_pct = (len(files_compliant) / len(skills) * 100) if skills else 0
    print(f"\n📈 Compliance rate: {compliant_pct:.1f}%")

    if total_description_chars >= TOTAL_DESCRIPTION_BUDGET_WARN:
        msg = f"\n⚠️  Description budget: {total_description_chars} chars (warn at {TOTAL_DESCRIPTION_BUDGET_WARN})"
        if total_description_chars > TOTAL_DESCRIPTION_BUDGET_ERROR:
            print(msg.replace("⚠️", "❌"))
            total_errors += 1
        else:
            print(msg)
            total_warnings += 1

    if total_errors > 0:
        print(f"\n❌ Validation FAILED with {total_errors} errors")
        return 1
    elif total_warnings > 0 and args.fail_on_warn:
        print(f"\n❌ Validation FAILED due to {total_warnings} warning(s) (--fail-on-warn)")
        return 1
    elif total_warnings > 0:
        print(f"\n⚠️  Validation PASSED with {total_warnings} warnings")
        return 0
    else:
        print(f"\n✅ All skills fully compliant!")
        print("   - Anthropic 2025 spec ✓")
        print("   - Enterprise standard ✓")
        print("   - Nixtla quality standards ✓")
        return 0


if __name__ == '__main__':
    sys.exit(main())
