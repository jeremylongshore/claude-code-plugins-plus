#!/usr/bin/env python3
"""
Skill Validator v5.0 - Two-Tier Validation + 100-Point Grading

Validates SKILL.md files against:
  - Standard tier: AgentSkills.io minimum (name + description required)
  - Enterprise tier (DEFAULT): Standard + identity fields, scoped tools, sections, disclosure
  - 100-Point grading: Intent Solutions marketplace rubric (--grade flag)

Usage:
    python validate-skill.py path/to/SKILL.md              # Enterprise (default)
    python validate-skill.py --standard path/to/SKILL.md    # Standard only
    python validate-skill.py --grade path/to/SKILL.md       # 100-point grading
    python validate-skill.py --grade --json path/to/SKILL.md # JSON grade output
    python validate-skill.py --json path/to/SKILL.md        # JSON output
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# === CONSTANTS ===

VALID_TOOLS = {
    "Read", "Write", "Edit", "Bash", "Glob", "Grep",
    "WebFetch", "WebSearch", "Task", "NotebookEdit",
    "AskUserQuestion", "Skill",
}

KNOWN_FRONTMATTER_FIELDS = {
    # AgentSkills.io spec
    "name", "description", "license", "compatibility", "metadata", "allowed-tools",
    # Top-level identity fields (marketplace standard)
    "version", "author", "compatible-with", "tags",
    # Claude Code extensions
    "argument-hint", "disable-model-invocation", "user-invocable", "model",
    "context", "agent", "hooks",
}

DEPRECATED_FIELDS = {
    "when_to_use": "Move content to description",
    "mode": "Use disable-model-invocation instead",
}

VALID_PLATFORMS = {
    "claude-code", "codex", "openclaw", "aider", "continue", "cursor", "windsurf",
}

RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
RE_FIRST_PERSON = re.compile(r"\b(I can|I will|I'm going to|I help|I'm)\b", re.IGNORECASE)
RE_SECOND_PERSON = re.compile(r"\b(You can|You should|You will)\b", re.IGNORECASE)
RE_HARDCODED_MODEL = re.compile(r"claude-[\w]+-\d{8}")
RE_CONSECUTIVE_HYPHENS = re.compile(r"--")
RE_WINDOWS_PATH = re.compile(r"[A-Za-z]:\\\\", re.IGNORECASE)
RE_ARGUMENTS = re.compile(r"\$ARGUMENTS|\$\d+|\$ARGUMENTS\[\d+\]")
RE_DYNAMIC_CONTEXT = re.compile(r"!`[^`]+`")

ABSOLUTE_PATH_PATTERNS = [
    (re.compile(r"/home/\w+/"), "/home/..."),
    (re.compile(r"/Users/\w+/"), "/Users/..."),
    (re.compile(r"[A-Za-z]:\\\\Users\\\\", re.IGNORECASE), "C:\\Users\\..."),
]


def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """Parse YAML frontmatter from SKILL.md content."""
    m = RE_FRONTMATTER.match(content)
    if not m:
        raise ValueError("Invalid or absent YAML frontmatter (missing --- delimiters)")
    front_str, body = m.groups()
    try:
        data = yaml.safe_load(front_str) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error: {e}")
    return data, body


def validate_name(fm: dict, path: Path) -> Tuple[List[str], List[str]]:
    """Validate the name field."""
    errors, warnings = [], []
    if "name" not in fm:
        errors.append("Missing required field: 'name'")
        return errors, warnings

    name = str(fm["name"]).strip()
    if not name:
        errors.append("'name' must be non-empty")
        return errors, warnings

    if len(name) > 64:
        errors.append(f"'name' exceeds 64 characters ({len(name)})")

    if not re.match(r"^[a-z]([a-z0-9-]*[a-z0-9])?$", name):
        errors.append(f"'name' must be kebab-case (lowercase, hyphens): '{name}'")
    elif RE_CONSECUTIVE_HYPHENS.search(name):
        errors.append(f"'name' has consecutive hyphens: '{name}'")

    if name.startswith("-") or name.endswith("-"):
        errors.append(f"'name' must not start or end with hyphen: '{name}'")

    if name != path.parent.name:
        warnings.append(f"'name' '{name}' differs from directory '{path.parent.name}'")

    return errors, warnings


def validate_description(fm: dict) -> Tuple[List[str], List[str]]:
    """Validate the description field."""
    errors, warnings = [], []
    if "description" not in fm:
        errors.append("Missing required field: 'description'")
        return errors, warnings

    desc = str(fm["description"]).strip()
    if not desc:
        errors.append("'description' must be non-empty")
        return errors, warnings

    if len(desc) > 1024:
        errors.append(f"'description' exceeds 1024 characters ({len(desc)})")
    if len(desc) < 20:
        warnings.append(f"'description' is very short ({len(desc)} chars) - add keywords for discovery")
    if len(desc) > 500:
        warnings.append(f"'description' is long ({len(desc)} chars) - impacts token budget")

    if RE_FIRST_PERSON.search(desc):
        errors.append("'description' must not use first person (I can, I will, I'm, I help)")
    if RE_SECOND_PERSON.search(desc):
        errors.append("'description' must not use second person (You can, You should, You will)")

    return errors, warnings


def validate_tools(fm: dict, enterprise: bool) -> Tuple[List[str], List[str]]:
    """Validate allowed-tools field."""
    errors, warnings = [], []
    if "allowed-tools" not in fm:
        if enterprise:
            warnings.append("'allowed-tools' not set (Enterprise recommends scoped tools)")
        return errors, warnings

    tools_val = fm["allowed-tools"]
    if isinstance(tools_val, list):
        tools = [str(t).strip() for t in tools_val]
    else:
        raw = str(tools_val)
        tools = re.findall(r"[A-Za-z_][\w-]*(?:\([^)]*\))?", raw)

    if not tools or tools == [""]:
        errors.append("'allowed-tools' is empty")
        return errors, warnings

    for tool in tools:
        if ":" in tool and "(" not in tool:
            continue  # MCP tool reference
        base_tool = tool.split("(")[0].strip()
        if base_tool not in VALID_TOOLS:
            errors.append(f"Unknown tool: '{base_tool}'")
        if "(" in tool and not tool.endswith(")"):
            errors.append(f"Invalid tool scope syntax: '{tool}'")

    if "Bash" in tools:
        if enterprise:
            errors.append("Unscoped 'Bash' forbidden in Enterprise tier - use Bash(git:*) etc.")
        else:
            warnings.append("Unscoped 'Bash' - consider scoping: Bash(git:*), Bash(npm:*)")

    return errors, warnings


def validate_optional_fields(fm: dict) -> Tuple[List[str], List[str]]:
    """Validate optional and extension fields."""
    errors, warnings = [], []

    # Model validation
    if "model" in fm:
        model = str(fm["model"]).strip()
        valid_models = {"inherit", "sonnet", "haiku", "opus"}
        if model not in valid_models and not model.startswith("claude-"):
            warnings.append(f"'model' value '{model}' - expected: inherit, sonnet, haiku, opus, or claude-* ID")
        if RE_HARDCODED_MODEL.match(model):
            warnings.append(f"Hardcoded model ID '{model}' - prefer 'inherit' or short names (sonnet, opus)")

    # Context + agent validation
    if "context" in fm:
        if str(fm["context"]) != "fork":
            errors.append("'context' must be 'fork' if set")
    if "agent" in fm and "context" not in fm:
        warnings.append("'agent' set without 'context: fork' - agent requires fork context")

    # Boolean fields
    for field in ("disable-model-invocation", "user-invocable"):
        if field in fm and not isinstance(fm[field], bool):
            errors.append(f"'{field}' must be boolean, got: {type(fm[field]).__name__}")

    # Conflicting invocation controls
    if fm.get("disable-model-invocation") is True and fm.get("user-invocable") is False:
        errors.append(
            "Conflicting: 'disable-model-invocation: true' + 'user-invocable: false' "
            "makes skill unreachable by both user and model"
        )

    # Compatibility length
    if "compatibility" in fm:
        compat = str(fm["compatibility"]).strip()
        if len(compat) > 500:
            errors.append(f"'compatibility' exceeds 500 characters ({len(compat)})")

    # compatible-with validation
    if "compatible-with" in fm:
        compat_with = fm["compatible-with"]
        if isinstance(compat_with, str):
            platforms = [p.strip() for p in compat_with.split(",")]
        elif isinstance(compat_with, list):
            platforms = [str(p).strip() for p in compat_with]
        else:
            platforms = []
            warnings.append("'compatible-with' should be a comma-separated string or list")
        for p in platforms:
            if p and p not in VALID_PLATFORMS:
                warnings.append(f"Unknown platform in compatible-with: '{p}'")

    # tags validation
    if "tags" in fm:
        tags = fm["tags"]
        if not isinstance(tags, list):
            warnings.append("'tags' should be an array/list of strings")

    # Version validation (top-level)
    if "version" in fm:
        version = str(fm["version"]).strip()
        if version and not re.match(r"^\d+\.\d+\.\d+", version):
            warnings.append(f"Version should be semver (X.Y.Z): '{version}'")

    # Author validation (top-level)
    if "author" in fm:
        author = str(fm["author"]).strip()
        if not author:
            warnings.append("'author' is empty")
        elif "@" not in author:
            warnings.append("'author' should include email (Name <email>)")

    # Deprecated fields
    for field, msg in DEPRECATED_FIELDS.items():
        if field in fm:
            warnings.append(f"Deprecated field '{field}': {msg}")

    # Check if author/version are nested in metadata (warn to move top-level)
    metadata = fm.get("metadata", {})
    if isinstance(metadata, dict):
        for field in ("author", "version", "license", "tags"):
            if field in metadata and field not in fm:
                warnings.append(
                    f"'{field}' found in metadata block - move to top-level for marketplace scoring"
                )

    # Unknown fields
    all_known = KNOWN_FRONTMATTER_FIELDS | DEPRECATED_FIELDS.keys()
    for field in fm:
        if field not in all_known:
            warnings.append(f"Unknown frontmatter field: '{field}'")

    return errors, warnings


def validate_enterprise_metadata(fm: dict) -> Tuple[List[str], List[str]]:
    """Enterprise tier: check author and version at top-level (or metadata fallback)."""
    errors, warnings = [], []
    metadata = fm.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    # Check author (top-level preferred, metadata fallback accepted with warning)
    has_author = "author" in fm
    has_author_meta = "author" in metadata
    if not has_author and not has_author_meta:
        warnings.append("Enterprise: 'author' recommended (top-level field)")
    elif has_author_meta and not has_author:
        warnings.append("'author' in metadata block - move to top-level for marketplace scoring")

    # Check version (top-level preferred, metadata fallback accepted with warning)
    has_version = "version" in fm
    has_version_meta = "version" in metadata
    if not has_version and not has_version_meta:
        warnings.append("Enterprise: 'version' recommended (top-level field)")
    elif has_version_meta and not has_version:
        warnings.append("'version' in metadata block - move to top-level for marketplace scoring")

    # Check license
    if "license" not in fm:
        warnings.append("Enterprise: 'license' recommended (top-level field)")

    return errors, warnings


def validate_body(body: str, path: Path, enterprise: bool) -> Tuple[List[str], List[str], List[str]]:
    """Validate SKILL.md body content."""
    errors, warnings, info = [], [], []
    lines = body.splitlines()
    line_count = len(lines)
    word_count = len(body.split())

    if line_count > 500:
        errors.append(f"Body has {line_count} lines (max 500)")
    elif line_count > 400:
        warnings.append(f"Body has {line_count} lines (approaching 500 limit)")

    if word_count > 5000:
        warnings.append(f"Body has {word_count} words - consider splitting to references/")

    # Strip code blocks for path checks
    body_no_code = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    body_no_code = re.sub(r"`[^`]+`", "", body_no_code)

    for pattern, desc in ABSOLUTE_PATH_PATTERNS:
        if pattern.search(body_no_code):
            errors.append(f"Contains absolute path ({desc}) - use ${{CLAUDE_SKILL_DIR}}")

    if RE_WINDOWS_PATH.search(body_no_code):
        errors.append("Contains Windows-style path - use Unix paths or ${CLAUDE_SKILL_DIR}")

    if not re.search(r"^# \S", body, re.MULTILINE):
        if enterprise:
            warnings.append("Missing H1 title (# Title)")

    if enterprise:
        instruction_headings = ("## Instructions", "## Steps", "## Your task", "## Usage", "## Workflow")
        has_instructions = any(h in body for h in instruction_headings)
        if not has_instructions:
            warnings.append("Missing '## Instructions' section (or ## Steps/Your task/Usage/Workflow)")
        else:
            instr_match = re.search(
                r"## (?:Instructions|Steps|Your task|Usage|Workflow)(.*?)(?=\n## |\Z)", body, re.DOTALL
            )
            if instr_match:
                instr = instr_match.group(1)
                has_steps = (
                    re.search(r"(?m)^\s*\d+\.\s+", instr)
                    or re.search(r"(?mi)^\s*#{2,6}\s*step\s*\d+", instr)
                )
                if not has_steps:
                    warnings.append("Instructions should have numbered steps or ### Step N headings")

        if "## Examples" not in body and "## Example" not in body:
            warnings.append("Missing '## Examples' section")

        if "## Error" not in body and "error" not in body.lower():
            info.append("Consider adding error handling documentation")

        skill_dir = path.parent.resolve()
        refs_dir = skill_dir / "references"
        if line_count > 300 and not refs_dir.exists():
            warnings.append(
                f"SKILL.md is {line_count} lines with no references/ directory - "
                "consider splitting heavy content"
            )

    if "{baseDir}/../" in body:
        errors.append("Path escape detected: {baseDir}/../ - references must stay within skill directory")

    nested_refs = re.findall(r"\{baseDir\}/references/\S+/\S+/", body)
    if nested_refs:
        warnings.append(f"Deeply nested reference paths detected: {nested_refs[0]} - keep references one level deep")

    dynamic_cmds = RE_DYNAMIC_CONTEXT.findall(body)
    if dynamic_cmds:
        info.append(f"Dynamic context injection detected ({len(dynamic_cmds)} command(s))")

    if RE_ARGUMENTS.search(body):
        try:
            content = path.read_text(encoding="utf-8")
            if "argument-hint" not in content.split("---")[1]:
                info.append("Uses $ARGUMENTS but no 'argument-hint' in frontmatter")
        except Exception:
            pass

    return errors, warnings, info


def validate_resources(body: str, path: Path) -> List[str]:
    """Validate that referenced resources exist."""
    errors = []
    skill_dir = path.parent.resolve()

    for subdir in ("scripts", "references", "templates", "assets"):
        # Check both ${CLAUDE_SKILL_DIR} and {baseDir} references
        for pattern in [
            rf"\$\{{CLAUDE_SKILL_DIR\}}/{subdir}/([\w\-./]+)",
            rf"\{{baseDir\}}/{subdir}/([\w\-./]+)",
        ]:
            for match in re.finditer(pattern, body):
                rel_path = match.group(1)
                full_path = skill_dir / subdir / rel_path
                if not full_path.exists():
                    errors.append(f"Resource not found: {subdir}/{rel_path}")

    return errors


def calculate_disclosure_score(fm: dict, body: str, path: Path) -> int:
    """Calculate progressive disclosure score (0-6)."""
    score = 0
    lines = len(body.splitlines())
    skill_dir = path.parent.resolve()

    if lines < 200:
        score += 2
    elif lines < 400:
        score += 1

    desc = str(fm.get("description", ""))
    if len(desc) < 200:
        score += 1

    if (skill_dir / "references").exists():
        score += 1
    if (skill_dir / "scripts").exists():
        score += 1
    if lines <= 500:
        score += 1

    return min(score, 6)


# === 100-POINT GRADING RUBRIC ===
#
# Ported from marketplace validator (scripts/validate-skills-schema.py)
# Grade Scale:
#   A (90-100): Production-ready
#   B (80-89):  Good, minor improvements needed
#   C (70-79):  Adequate, has gaps
#   D (60-69):  Needs significant work
#   F (<60):    Major revision required


def score_progressive_disclosure(path: Path, body: str, fm: dict) -> dict:
    """Progressive Disclosure Architecture (30 pts max)."""
    breakdown = {}
    lines = len(body.splitlines())
    skill_dir = path.parent

    # Token Economy (10 pts)
    if lines <= 150:
        breakdown["token_economy"] = (10, f"Excellent: {lines} lines")
    elif lines <= 300:
        breakdown["token_economy"] = (7, f"Good: {lines} lines (target <=150)")
    elif lines <= 500:
        breakdown["token_economy"] = (4, f"Acceptable: {lines} lines (target <=150)")
    else:
        breakdown["token_economy"] = (0, f"Too long: {lines} lines (target <=150)")

    # Layered Structure (10 pts)
    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        ref_files = list(refs_dir.glob("*.md"))
        if ref_files:
            breakdown["layered_structure"] = (10, f"Has references/ with {len(ref_files)} files")
        else:
            breakdown["layered_structure"] = (3, "references/ exists but empty")
    else:
        if lines <= 100:
            breakdown["layered_structure"] = (8, "No references/ (acceptable for short skill)")
        elif lines <= 200:
            breakdown["layered_structure"] = (4, "No references/ (should extract content)")
        else:
            breakdown["layered_structure"] = (0, "No references/ (long skill needs extraction)")

    # Reference Depth (5 pts)
    if refs_dir.exists():
        nested_dirs = [d for d in refs_dir.iterdir() if d.is_dir()]
        if not nested_dirs:
            breakdown["reference_depth"] = (5, "References are flat (good)")
        else:
            breakdown["reference_depth"] = (2, f"Nested dirs in references/: {len(nested_dirs)}")
    else:
        breakdown["reference_depth"] = (5, "N/A - no references/")

    # Navigation Signals (5 pts)
    has_toc = bool(re.search(r"(?mi)^##?\s*(table of contents|contents|toc)\b", body))
    has_nav_links = bool(re.search(r"\[.*?\]\(#.*?\)", body))
    if lines <= 100:
        breakdown["navigation_signals"] = (5, "Short file, TOC optional")
    elif has_toc or has_nav_links:
        breakdown["navigation_signals"] = (5, "Has navigation/TOC")
    else:
        breakdown["navigation_signals"] = (0, "Long file needs TOC/navigation")

    total = sum(v[0] for v in breakdown.values())
    return {"score": total, "max": 30, "breakdown": breakdown}


def score_ease_of_use(path: Path, body: str, fm: dict) -> dict:
    """Ease of Use (25 pts max)."""
    breakdown = {}
    desc = str(fm.get("description", "")).lower()

    # Metadata Quality (10 pts)
    meta_score = 0
    meta_notes = []
    if fm.get("name"):
        meta_score += 2
    else:
        meta_notes.append("missing name")
    if fm.get("description") and len(str(fm.get("description", ""))) >= 50:
        meta_score += 3
    else:
        meta_notes.append("description too short")
    if fm.get("version"):
        meta_score += 2
    else:
        meta_notes.append("missing version")
    if fm.get("allowed-tools"):
        meta_score += 2
    else:
        meta_notes.append("missing allowed-tools")
    if fm.get("author") and "@" in str(fm.get("author", "")):
        meta_score += 1
    breakdown["metadata_quality"] = (meta_score, ", ".join(meta_notes) if meta_notes else "Complete metadata")

    # Discoverability (6 pts)
    disc_score = 0
    disc_notes = []
    if "use when" in desc:
        disc_score += 3
        disc_notes.append("has 'Use when'")
    if "trigger with" in desc or "trigger phrase" in desc:
        disc_score += 3
        disc_notes.append("has trigger phrases")
    if not disc_notes:
        disc_notes.append("missing discovery cues")
    breakdown["discoverability"] = (disc_score, ", ".join(disc_notes))

    # Terminology Consistency (4 pts)
    name = str(fm.get("name", ""))
    folder = path.parent.name
    term_score = 4
    term_notes = []
    if name and name != folder:
        term_score -= 2
        term_notes.append("name differs from folder")
    if any(w.isupper() and len(w) > 3 for w in str(fm.get("description", "")).split()):
        term_score -= 1
        term_notes.append("inconsistent casing")
    breakdown["terminology"] = (max(0, term_score), ", ".join(term_notes) if term_notes else "Consistent terminology")

    # Workflow Clarity (5 pts)
    workflow_score = 0
    workflow_notes = []
    if re.search(r"(?m)^\s*1\.\s+", body):
        workflow_score += 3
        workflow_notes.append("has numbered steps")
    section_count = len(re.findall(r"(?m)^##\s+", body))
    if section_count >= 5:
        workflow_score += 2
        workflow_notes.append(f"{section_count} sections")
    elif section_count >= 3:
        workflow_score += 1
        workflow_notes.append(f"{section_count} sections (add more)")
    if not workflow_notes:
        workflow_notes.append("unclear workflow")
    breakdown["workflow_clarity"] = (workflow_score, ", ".join(workflow_notes))

    total = sum(v[0] for v in breakdown.values())
    return {"score": total, "max": 25, "breakdown": breakdown}


def score_utility(path: Path, body: str, fm: dict) -> dict:
    """Utility (20 pts max)."""
    breakdown = {}
    body_lower = body.lower()

    # Problem Solving Power (8 pts)
    problem_score = 0
    problem_notes = []
    if "## overview" in body_lower:
        overview_match = re.search(r"## overview\s*\n(.*?)(?=\n##|\Z)", body, re.IGNORECASE | re.DOTALL)
        if overview_match and len(overview_match.group(1).strip()) > 50:
            problem_score += 4
            problem_notes.append("has overview")
    if "## prerequisites" in body_lower:
        problem_score += 2
        problem_notes.append("has prerequisites")
    if "## output" in body_lower:
        problem_score += 2
        problem_notes.append("has output spec")
    if not problem_notes:
        problem_notes.append("unclear problem/solution")
    breakdown["problem_solving"] = (problem_score, ", ".join(problem_notes))

    # Degrees of Freedom (5 pts)
    freedom_score = 0
    freedom_notes = []
    if re.search(r"(?i)(optional|configur|parameter|argument|flag|option)", body):
        freedom_score += 2
        freedom_notes.append("has options")
    if re.search(r"(?i)(alternatively|or use|another approach|you can also)", body):
        freedom_score += 2
        freedom_notes.append("shows alternatives")
    if re.search(r"(?i)(extend|customize|modify|adapt)", body):
        freedom_score += 1
        freedom_notes.append("extensible")
    if not freedom_notes:
        freedom_notes.append("rigid implementation")
    breakdown["degrees_of_freedom"] = (freedom_score, ", ".join(freedom_notes))

    # Feedback Loops (4 pts)
    feedback_score = 0
    feedback_notes = []
    if "## error handling" in body_lower:
        feedback_score += 2
        feedback_notes.append("has error handling")
    if re.search(r"(?i)(validate|verify|check|test|confirm)", body):
        feedback_score += 1
        feedback_notes.append("has validation")
    if re.search(r"(?i)(troubleshoot|debug|diagnose|fix)", body):
        feedback_score += 1
        feedback_notes.append("has troubleshooting")
    if not feedback_notes:
        feedback_notes.append("no feedback mechanisms")
    breakdown["feedback_loops"] = (feedback_score, ", ".join(feedback_notes))

    # Examples & Templates (3 pts)
    examples_score = 0
    examples_notes = []
    if "## examples" in body_lower or "**example" in body_lower:
        examples_score += 2
        examples_notes.append("has examples")
    if "```" in body:
        code_blocks = len(re.findall(r"```", body)) // 2
        if code_blocks >= 2:
            examples_score += 1
            examples_notes.append(f"{code_blocks} code blocks")
    if not examples_notes:
        examples_notes.append("no examples")
    breakdown["examples"] = (examples_score, ", ".join(examples_notes))

    total = sum(v[0] for v in breakdown.values())
    return {"score": total, "max": 20, "breakdown": breakdown}


def score_spec_compliance(path: Path, body: str, fm: dict) -> dict:
    """Spec Compliance (15 pts max)."""
    breakdown = {}
    name = str(fm.get("name", ""))
    desc = str(fm.get("description", ""))

    # Frontmatter Validity (5 pts)
    fm_score = 5
    fm_notes = []
    required = {"name", "description", "allowed-tools", "version", "author", "license"}
    missing = required - set(fm.keys())
    if missing:
        fm_score -= min(len(missing), 4)
        fm_notes.append(f"missing: {', '.join(sorted(missing))}")
    if not fm_notes:
        fm_notes.append("valid frontmatter")
    breakdown["frontmatter_validity"] = (max(0, fm_score), ", ".join(fm_notes))

    # Name Conventions (4 pts)
    name_score = 4
    name_notes = []
    if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", name) and len(name) > 1:
        name_score -= 2
        name_notes.append("not kebab-case")
    if len(name) > 64:
        name_score -= 1
        name_notes.append("name too long")
    if name != path.parent.name:
        name_score -= 1
        name_notes.append("name/folder mismatch")
    if not name_notes:
        name_notes.append("proper naming")
    breakdown["name_conventions"] = (max(0, name_score), ", ".join(name_notes))

    # Description Quality (4 pts)
    desc_score = 4
    desc_notes = []
    if len(desc) < 50:
        desc_score -= 2
        desc_notes.append("too short")
    if len(desc) > 1024:
        desc_score -= 2
        desc_notes.append("too long")
    desc_lower = desc.lower()
    if "i can" in desc_lower or "i will" in desc_lower:
        desc_score -= 1
        desc_notes.append("uses first person")
    if "you can" in desc_lower or "you should" in desc_lower:
        desc_score -= 1
        desc_notes.append("uses second person")
    if not desc_notes:
        desc_notes.append("good description")
    breakdown["description_quality"] = (max(0, desc_score), ", ".join(desc_notes))

    # Optional Fields (2 pts)
    opt_score = 2
    opt_notes = []
    if "model" in fm:
        model = fm["model"]
        if model not in ["inherit", "sonnet", "haiku", "opus"] and not str(model).startswith("claude-"):
            opt_score -= 1
            opt_notes.append("invalid model value")
    if not opt_notes:
        opt_notes.append("optional fields ok")
    breakdown["optional_fields"] = (opt_score, ", ".join(opt_notes))

    total = sum(v[0] for v in breakdown.values())
    return {"score": total, "max": 15, "breakdown": breakdown}


def score_writing_style(path: Path, body: str, fm: dict) -> dict:
    """Writing Style (10 pts max)."""
    breakdown = {}

    # Voice & Tense (4 pts)
    voice_score = 4
    voice_notes = []
    imperative_verbs = ["create", "use", "run", "execute", "configure", "set", "add", "remove", "check", "verify"]
    has_imperative = any(re.search(rf"(?m)^\s*\d+\.\s*{v}", body, re.IGNORECASE) for v in imperative_verbs)
    if not has_imperative:
        voice_score -= 2
        voice_notes.append("use imperative voice")
    if not voice_notes:
        voice_notes.append("good voice")
    breakdown["voice_tense"] = (voice_score, ", ".join(voice_notes))

    # Objectivity (3 pts)
    obj_score = 3
    obj_notes = []
    body_lower = body.lower()
    if "you should" in body_lower or "you can" in body_lower or "you will" in body_lower:
        obj_score -= 1
        obj_notes.append("has second person")
    if " i " in body_lower or "i can" in body_lower or "i'll" in body_lower:
        obj_score -= 1
        obj_notes.append("has first person")
    if not obj_notes:
        obj_notes.append("objective")
    breakdown["objectivity"] = (max(0, obj_score), ", ".join(obj_notes))

    # Conciseness (3 pts)
    conc_score = 3
    conc_notes = []
    word_count = len(body.split())
    lines = len(body.splitlines())
    if word_count > 3000:
        conc_score -= 2
        conc_notes.append(f"verbose ({word_count} words)")
    elif word_count > 2000:
        conc_score -= 1
        conc_notes.append(f"lengthy ({word_count} words)")
    if lines > 400:
        conc_score -= 1
        conc_notes.append(f"many lines ({lines})")
    if not conc_notes:
        conc_notes.append("concise")
    breakdown["conciseness"] = (max(0, conc_score), ", ".join(conc_notes))

    total = sum(v[0] for v in breakdown.values())
    return {"score": total, "max": 10, "breakdown": breakdown}


def calculate_modifiers(path: Path, body: str, fm: dict) -> dict:
    """Modifiers (-5 to +5 pts)."""
    modifiers = {}
    name = str(fm.get("name", ""))
    desc = str(fm.get("description", ""))
    lines = len(body.splitlines())

    # Bonuses
    if name.endswith("ing") or any(name.endswith(f"-{s}") for s in ["ing"]):
        modifiers["gerund_name"] = (+1, "gerund-style name")

    sections = len(re.findall(r"(?m)^##\s+", body))
    if sections >= 7:
        modifiers["grep_friendly"] = (+1, "grep-friendly structure")

    example_count = len(re.findall(r"(?i)\*\*example[:\s]", body))
    if example_count >= 3:
        modifiers["exemplary_examples"] = (+2, f"{example_count} labeled examples")

    if "## resources" in body.lower():
        external_links = len(re.findall(r"\[.*?\]\(https?://", body))
        if external_links >= 2:
            modifiers["external_resources"] = (+1, f"{external_links} external links")

    # Penalties
    desc_lower = desc.lower()
    if "i can" in desc_lower or "i will" in desc_lower or "you can" in desc_lower or "you should" in desc_lower:
        modifiers["person_in_desc"] = (-2, "first/second person in description")

    has_toc = bool(re.search(r"(?mi)^##?\s*(table of contents|contents|toc)\b", body))
    if lines > 150 and not has_toc:
        modifiers["missing_toc"] = (-2, "long file needs TOC")

    if "<" in body and ">" in body and re.search(r"<[a-z]+>", body):
        modifiers["xml_tags"] = (-1, "XML-like tags in body")

    total = sum(v[0] for v in modifiers.values())
    total = max(-5, min(5, total))
    return {"score": total, "max_bonus": 5, "max_penalty": -5, "items": modifiers}


def grade_skill(path: Path, body: str, fm: dict) -> dict:
    """Calculate Intent Solutions 100-point grade."""
    pda = score_progressive_disclosure(path, body, fm)
    ease = score_ease_of_use(path, body, fm)
    utility = score_utility(path, body, fm)
    spec = score_spec_compliance(path, body, fm)
    style = score_writing_style(path, body, fm)
    mods = calculate_modifiers(path, body, fm)

    base_score = pda["score"] + ease["score"] + utility["score"] + spec["score"] + style["score"]
    total_score = max(0, min(100, base_score + mods["score"]))

    if total_score >= 90:
        grade = "A"
    elif total_score >= 80:
        grade = "B"
    elif total_score >= 70:
        grade = "C"
    elif total_score >= 60:
        grade = "D"
    else:
        grade = "F"

    # Generate improvement suggestions
    improvements = []
    desc_lower = str(fm.get("description", "")).lower()
    if "use when" not in desc_lower:
        improvements.append('Add "Use when" to description (+3 pts)')
    if "trigger with" not in desc_lower:
        improvements.append('Add "Trigger with" to description (+3 pts)')
    body_lower = body.lower()
    if "## overview" not in body_lower:
        improvements.append("Add ## Overview section (+4 pts)")
    if "## prerequisites" not in body_lower:
        improvements.append("Add ## Prerequisites section (+2 pts)")
    if "## output" not in body_lower:
        improvements.append("Add ## Output section (+2 pts)")
    if "## error handling" not in body_lower:
        improvements.append("Add ## Error Handling section (+2 pts)")
    if "## examples" not in body_lower:
        improvements.append("Add ## Examples section (+2 pts)")
    if not fm.get("version"):
        improvements.append("Add version field (+2 pts)")
    if not fm.get("author"):
        improvements.append("Add author field (+1 pt)")
    if not fm.get("allowed-tools"):
        improvements.append("Add allowed-tools field (+2 pts)")

    return {
        "score": total_score,
        "grade": grade,
        "improvements": improvements,
        "breakdown": {
            "progressive_disclosure": pda,
            "ease_of_use": ease,
            "utility": utility,
            "spec_compliance": spec,
            "writing_style": style,
            "modifiers": mods,
        },
    }


def validate_skill(path: Path, enterprise: bool = True) -> Dict[str, Any]:
    """Validate a SKILL.md file."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"fatal": f"Cannot read file: {e}"}

    try:
        fm, body = parse_frontmatter(content)
    except Exception as e:
        return {"fatal": str(e)}

    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []

    name_e, name_w = validate_name(fm, path)
    errors.extend(name_e)
    warnings.extend(name_w)

    desc_e, desc_w = validate_description(fm)
    errors.extend(desc_e)
    warnings.extend(desc_w)

    tools_e, tools_w = validate_tools(fm, enterprise)
    errors.extend(tools_e)
    warnings.extend(tools_w)

    opt_e, opt_w = validate_optional_fields(fm)
    errors.extend(opt_e)
    warnings.extend(opt_w)

    if enterprise:
        meta_e, meta_w = validate_enterprise_metadata(fm)
        errors.extend(meta_e)
        warnings.extend(meta_w)

    body_e, body_w, body_i = validate_body(body, path, enterprise)
    errors.extend(body_e)
    warnings.extend(body_w)
    info.extend(body_i)

    resource_errors = validate_resources(body, path)
    errors.extend(resource_errors)

    word_count = len(body.split())
    line_count = len(body.splitlines())
    token_estimate = int(word_count * 1.3)
    disclosure_score = calculate_disclosure_score(fm, body, path)

    return {
        "valid": len(errors) == 0,
        "tier": "Enterprise" if enterprise else "Standard",
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "stats": {
            "word_count": word_count,
            "line_count": line_count,
            "token_estimate": token_estimate,
            "disclosure_score": disclosure_score,
        },
    }


def print_result(result: Dict[str, Any], path: Path) -> None:
    """Print validation result in human-readable format."""
    if "fatal" in result:
        print(f"FATAL: {result['fatal']}")
        sys.exit(1)

    tier = result["tier"]
    stats = result["stats"]

    print(f"\n{'=' * 60}")
    print(f"SKILL VALIDATION: {path.name} [{tier} tier]")
    print(f"{'=' * 60}\n")

    if result["errors"]:
        print("ERRORS:")
        for e in result["errors"]:
            print(f"  x {e}")
        print()

    if result["warnings"]:
        print("WARNINGS:")
        for w in result["warnings"]:
            print(f"  ! {w}")
        print()

    if result["info"]:
        print("INFO:")
        for i in result["info"]:
            print(f"  - {i}")
        print()

    print(f"Stats:")
    print(f"  Words: {stats['word_count']}")
    print(f"  Lines: {stats['line_count']}")
    print(f"  Tokens (est.): {stats['token_estimate']}")
    print(f"  Disclosure Score: {stats['disclosure_score']}/6")
    print()

    if result["valid"]:
        print("PASSED")
    else:
        print(f"FAILED ({len(result['errors'])} errors)")


def print_grade(grade_result: Dict[str, Any], path: Path) -> None:
    """Print 100-point grade report."""
    bd = grade_result["breakdown"]

    print(f"\n{'=' * 60}")
    print(f"SKILL GRADE: {path.name}")
    print(f"{'=' * 60}\n")

    print(f"Grade: {grade_result['grade']} ({grade_result['score']}/100)\n")

    # Print each pillar
    pillars = [
        ("Progressive Disclosure", "progressive_disclosure"),
        ("Ease of Use", "ease_of_use"),
        ("Utility", "utility"),
        ("Spec Compliance", "spec_compliance"),
        ("Writing Style", "writing_style"),
    ]

    for label, key in pillars:
        pillar = bd[key]
        sub_scores = ", ".join(f"{k}={v[0]}" for k, v in pillar["breakdown"].items())
        print(f"  {label + ':':28s} {pillar['score']:2d}/{pillar['max']}  [{sub_scores}]")

    # Modifiers
    mods = bd["modifiers"]
    mod_items = ", ".join(f"{k}={v[0]:+d}" for k, v in mods["items"].items()) if mods["items"] else "none"
    sign = "+" if mods["score"] >= 0 else ""
    print(f"  {'Modifiers:':28s} {sign}{mods['score']}     [{mod_items}]")
    print()

    # Improvements
    if grade_result["improvements"]:
        print("Improvements:")
        for imp in grade_result["improvements"]:
            print(f"  - {imp}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md files (Enterprise tier by default)"
    )
    parser.add_argument("path", help="Path to SKILL.md file")
    parser.add_argument(
        "--standard",
        action="store_true",
        help="Use Standard tier (AgentSkills.io minimum) instead of Enterprise",
    )
    parser.add_argument("--grade", action="store_true", help="Run 100-point grading rubric")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    enterprise = not args.standard

    if args.grade:
        try:
            content = path.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(content)
        except Exception as e:
            print(f"FATAL: {e}", file=sys.stderr)
            sys.exit(1)

        grade_result = grade_skill(path, body, fm)

        if args.json:
            # Serialize breakdown for JSON (convert tuples to dicts)
            output = {
                "score": grade_result["score"],
                "grade": grade_result["grade"],
                "improvements": grade_result["improvements"],
                "breakdown": {},
            }
            for pillar_key, pillar_data in grade_result["breakdown"].items():
                if pillar_key == "modifiers":
                    output["breakdown"]["modifiers"] = {
                        "score": pillar_data["score"],
                        "items": {k: {"points": v[0], "reason": v[1]} for k, v in pillar_data["items"].items()},
                    }
                else:
                    output["breakdown"][pillar_key] = {
                        "score": pillar_data["score"],
                        "max": pillar_data["max"],
                        "breakdown": {k: {"points": v[0], "reason": v[1]} for k, v in pillar_data["breakdown"].items()},
                    }
            print(json.dumps(output, indent=2))
        else:
            print_grade(grade_result, path)

        sys.exit(0 if grade_result["score"] >= 60 else 1)

    # Standard validation
    result = validate_skill(path, enterprise=enterprise)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_result(result, path)

    sys.exit(0 if result.get("valid", False) else 1)


if __name__ == "__main__":
    main()
