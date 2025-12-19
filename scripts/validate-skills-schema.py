#!/usr/bin/env python3
"""
Validates all SKILL.md files comply with Anthropic's official Claude Code Skills spec
plus Intent Solutions enterprise standards.

Based on:
- https://code.claude.com/docs/en/skills (Official Anthropic docs)
- https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/
- Intent Solutions Enterprise Standards

Required fields (per Anthropic spec):
- name (required) - Skill identifier, lowercase + hyphens, max 64 chars
- description (required) - Brief summary for Claude's skill selection, max 1024 chars

Enterprise standard fields (Intent Solutions):
- allowed-tools - Tool permissions for security
- version - Semantic versioning (e.g., 1.0.0)
- author - Creator attribution
- license - License (MIT recommended)

Optional fields (per Anthropic spec):
- model - Model override ("inherit" or specific model ID)
- disable-model-invocation - Boolean; manual-only invocation
- mode - Boolean; categorizes as mode command
- tags - Categorization keywords

Deprecated/Avoid:
- when_to_use - Undocumented, possibly deprecated
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Valid tools per Claude Code spec
VALID_TOOLS = {
    'Read', 'Write', 'Edit', 'Bash', 'Glob', 'Grep',
    'WebFetch', 'WebSearch', 'Task', 'TodoWrite',
    'NotebookEdit', 'AskUserQuestion', 'Skill'
}

# Fields per Anthropic spec
REQUIRED_FIELDS = {'name', 'description'}

# Enterprise standard fields (Intent Solutions) - required for marketplace
ENTERPRISE_REQUIRED = {'allowed-tools', 'version', 'author', 'license'}

# Optional fields per Anthropic spec
OPTIONAL_FIELDS = {'model', 'disable-model-invocation', 'mode', 'tags', 'metadata'}

DEPRECATED_FIELDS = {'when_to_use'}

# Default author for Intent Solutions skills
DEFAULT_AUTHOR = "Jeremy Longshore <jeremy@intentsolutions.io>"
DEFAULT_LICENSE = "MIT"


def parse_yaml_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """Parse YAML frontmatter using proper YAML parser"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return {'_parse_error': str(e)}


def parse_allowed_tools(tools_value: Any) -> List[str]:
    """Parse allowed-tools which can be string or list"""
    if isinstance(tools_value, list):
        return tools_value
    elif isinstance(tools_value, str):
        # Handle comma-separated string
        return [t.strip() for t in tools_value.split(',')]
    return []


def validate_tool_permission(tool: str) -> Tuple[bool, str]:
    """Validate a single tool permission including wildcards like Bash(git:*)"""
    # Extract base tool name (before parentheses)
    base_tool = tool.split('(')[0].strip()

    if base_tool not in VALID_TOOLS:
        return False, f"Unknown tool: {base_tool}"

    # Validate wildcard syntax if present
    if '(' in tool:
        if not tool.endswith(')'):
            return False, f"Invalid wildcard syntax: {tool}"
        # Pattern like Bash(git:*) or Bash(npm install:*)
        inner = tool[tool.index('(')+1:-1]
        if ':' not in inner:
            return False, f"Wildcard missing colon: {tool}"

    return True, ""


def check_hardcoded_paths(content: str) -> List[str]:
    """Check for hardcoded paths that should use {baseDir}"""
    issues = []

    # Only check in frontmatter and direct instructions, not code examples
    # Split out code blocks to avoid false positives
    content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    content_no_code = re.sub(r'`[^`]+`', '', content_no_code)

    # Patterns that indicate hardcoded paths (in non-code content)
    path_patterns = [
        (r'/home/\w+/', '/home/user/'),
        (r'/Users/\w+/', '/Users/user/'),
        (r'C:\\Users\\', 'C:\\Users\\'),
    ]

    for pattern, desc in path_patterns:
        if re.search(pattern, content_no_code):
            issues.append(f"Hardcoded path detected (use {{baseDir}}): {desc}")

    return issues


def estimate_word_count(content: str) -> int:
    """Estimate word count for content length check"""
    # Remove frontmatter
    content_body = re.sub(r'^---\n.*?\n---\n?', '', content, flags=re.DOTALL)
    return len(content_body.split())


def validate_skill(file_path: Path) -> Dict[str, Any]:
    """Validate a single SKILL.md file against Claude Code spec"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {'fatal': f'Cannot read file: {e}'}

    frontmatter = parse_yaml_frontmatter(content)

    if not frontmatter:
        return {'fatal': 'No YAML frontmatter found'}

    if '_parse_error' in frontmatter:
        return {'fatal': f"YAML parse error: {frontmatter['_parse_error']}"}

    errors = []
    warnings = []
    info = []

    # === REQUIRED FIELDS ===

    # name field
    if 'name' not in frontmatter:
        errors.append('Missing required field: name')
    else:
        name = frontmatter['name']
        # Check name matches folder name (marketplace standard, not Anthropic requirement)
        # Anthropic says this is best practice, not enforced at runtime
        folder_name = file_path.parent.name
        if name != folder_name:
            # INFO level - not an error per official spec, but recommended
            info.append(f"name '{name}' differs from folder '{folder_name}' (best practice: match them)")

        # Check name format (kebab-case)
        if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
            warnings.append(f"name should be kebab-case: {name}")

        if len(name) > 64:
            errors.append('name exceeds 64 characters')

    # description field
    if 'description' not in frontmatter:
        errors.append('Missing required field: description')
    else:
        desc = str(frontmatter['description'])
        if len(desc) < 20:
            warnings.append('description too short (< 20 chars) - may not trigger well')
        if len(desc) > 1024:
            errors.append('description exceeds 1024 characters')

        # Check for imperative language (best practice)
        imperative_starts = ['analyze', 'create', 'generate', 'build', 'debug',
                           'optimize', 'validate', 'test', 'deploy', 'monitor',
                           'fix', 'review', 'extract', 'convert', 'implement',
                           'this skill', 'use this', 'activates when']
        desc_lower = desc.lower()
        has_imperative = any(desc_lower.startswith(v) or v in desc_lower
                           for v in imperative_starts)
        if not has_imperative:
            info.append('Consider using imperative language in description')

    # === ENTERPRISE REQUIRED FIELDS (Intent Solutions Standard) ===

    # allowed-tools (enterprise required)
    if 'allowed-tools' in frontmatter:
        tools = parse_allowed_tools(frontmatter['allowed-tools'])
        for tool in tools:
            valid, msg = validate_tool_permission(tool)
            if not valid:
                errors.append(msg)

        # Info about over-permissioning (best practice)
        if len(tools) > 6:
            info.append(f'Many tools permitted ({len(tools)}) - consider limiting')
    else:
        warnings.append('Missing enterprise field: allowed-tools')

    # version (enterprise required)
    if 'version' not in frontmatter:
        warnings.append('Missing enterprise field: version (use semver e.g., 1.0.0)')
    else:
        version = str(frontmatter['version'])
        if not re.match(r'^\d+\.\d+\.\d+', version):
            warnings.append(f'version should be semver format: {version}')

    # author (enterprise required)
    if 'author' not in frontmatter:
        warnings.append('Missing enterprise field: author')

    # license (enterprise required)
    if 'license' not in frontmatter:
        warnings.append('Missing enterprise field: license (use MIT)')

    # === OPTIONAL FIELDS ===

    # model
    if 'model' in frontmatter:
        model = frontmatter['model']
        if model not in ['inherit', 'sonnet', 'haiku'] and not model.startswith('claude-'):
            warnings.append(f"Unknown model value: {model}")

    # === DEPRECATED FIELDS ===

    for field in DEPRECATED_FIELDS:
        if field in frontmatter:
            warnings.append(f"Deprecated field used: {field}")

    # === NON-SPEC FIELDS ===

    known_fields = REQUIRED_FIELDS | ENTERPRISE_REQUIRED | OPTIONAL_FIELDS | DEPRECATED_FIELDS
    unknown_fields = set(frontmatter.keys()) - known_fields
    for field in unknown_fields:
        info.append(f"Non-spec field: {field}")

    # === CONTENT CHECKS ===

    # Check for hardcoded paths
    path_issues = check_hardcoded_paths(content)
    for issue in path_issues:
        errors.append(issue)

    # Check content length (5000 word limit)
    word_count = estimate_word_count(content)
    if word_count > 5000:
        warnings.append(f'Content exceeds 5000 words ({word_count}) - may overwhelm context')
    elif word_count > 3500:
        info.append(f'Content is lengthy ({word_count} words) - consider using references/')

    # Check for second-person phrasing (should use imperative)
    if re.search(r'\byou should\b|\byou can\b|\byou will\b', content, re.IGNORECASE):
        info.append('Consider imperative language instead of "you should/can/will"')

    return {
        'errors': errors,
        'warnings': warnings,
        'info': info,
        'word_count': word_count,
        'has_allowed_tools': 'allowed-tools' in frontmatter
    }


def main():
    plugins_dir = Path(__file__).parent.parent / 'plugins'
    skill_files = list(plugins_dir.rglob('skills/*/SKILL.md'))

    # Also check for standalone skills
    standalone_skills_dir = Path(__file__).parent.parent / 'skills'
    if standalone_skills_dir.exists():
        skill_files.extend(standalone_skills_dir.rglob('*/SKILL.md'))

    total_errors = 0
    total_warnings = 0
    total_files = len(skill_files)

    files_with_errors = []
    files_with_warnings = []
    files_compliant = []

    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    print(f"🔍 CLAUDE CODE SKILLS VALIDATOR")
    print(f"   Based on: leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/")
    print(f"{'=' * 70}\n")

    for skill_file in skill_files:
        result = validate_skill(skill_file)
        rel_path = skill_file.relative_to(plugins_dir) if plugins_dir in skill_file.parents else skill_file

        if 'fatal' in result:
            print(f"❌ {rel_path}: {result['fatal']}")
            total_errors += 1
            files_with_errors.append(str(rel_path))
            continue

        has_issues = False

        if result['errors']:
            print(f"❌ {rel_path}:")
            for error in result['errors']:
                print(f"   ERROR: {error}")
            total_errors += len(result['errors'])
            files_with_errors.append(str(rel_path))
            has_issues = True

        if result['warnings']:
            if not has_issues:
                print(f"⚠️  {rel_path}:")
            for warning in result['warnings']:
                print(f"   WARN: {warning}")
            total_warnings += len(result['warnings'])
            if str(rel_path) not in files_with_errors:
                files_with_warnings.append(str(rel_path))
            has_issues = True

        if verbose and result['info']:
            if not has_issues:
                print(f"ℹ️  {rel_path}:")
            for info in result['info']:
                print(f"   INFO: {info}")

        if not result['errors'] and not result['warnings']:
            files_compliant.append(str(rel_path))

    # Summary
    print(f"\n{'=' * 70}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total skills validated: {total_files}")
    print(f"✅ Fully compliant: {len(files_compliant)}")
    print(f"⚠️  Warnings only: {len(files_with_warnings)}")
    print(f"❌ With errors: {len(files_with_errors)}")
    print(f"{'=' * 70}")

    # Stats
    compliant_pct = (len(files_compliant) / total_files * 100) if total_files > 0 else 0
    print(f"\n📈 Compliance rate: {compliant_pct:.1f}%")

    if total_errors > 0:
        print(f"\n❌ Validation FAILED with {total_errors} errors")
        return 1
    elif total_warnings > 0:
        print(f"\n⚠️  Validation PASSED with {total_warnings} warnings")
        return 0
    else:
        print(f"\n✅ All skills fully compliant!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
