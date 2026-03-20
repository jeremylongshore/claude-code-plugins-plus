#!/usr/bin/env python3
"""
Claude Code Plugin Validator v4.0 (Two-Tier: Standard + Enterprise)

Unified validator for all Claude Code plugin content:
- SKILL.md files (Agent Skills)
- commands/*.md files (Slash Commands)
- agents/*.md files (Custom Agents)

Two-tier validation system:
- Standard (DEFAULT): Anthropic spec only. No required fields. description recommended.
  Body has no required format. "Use when"/"Trigger with" are INFO only.
- Enterprise: Intent Solutions marketplace. 100-point rubric. version/author/license/
  allowed-tools scored as WARNINGS (not errors). Body sections scored as WARNINGS.
- Auto-detect: if CI=true or GITHUB_ACTIONS=true → enterprise by default.

Combines:
- Anthropic 2026 Skills Specification (code.claude.com/docs/en/skills)
- Lee Han Chung Deep Dive (leehanchung.github.io)
- Intent Solutions 100-Point Grading Rubric

Usage:
    python scripts/validate-skills-schema.py [--verbose|-v]              # Standard tier (default)
    python scripts/validate-skills-schema.py --enterprise [--verbose]    # Enterprise tier
    python scripts/validate-skills-schema.py --standard [--verbose]      # Explicit standard
    python scripts/validate-skills-schema.py --skills-only
    python scripts/validate-skills-schema.py --commands-only
    python scripts/validate-skills-schema.py --agents-only
    python scripts/validate-skills-schema.py path/to/SKILL.md           # Single-file mode

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 4.0.0
"""

import argparse
import json as json_module
import os
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

# Validation tiers
TIER_STANDARD = 'standard'
TIER_ENTERPRISE = 'enterprise'

# Valid tools per Claude Code spec (2026)
VALID_TOOLS = {
    'Read', 'Write', 'Edit', 'Bash', 'Glob', 'Grep',
    'WebFetch', 'WebSearch', 'Task', 'TodoWrite',
    'NotebookEdit', 'AskUserQuestion', 'Skill'
}

# Two-tier field definitions (Anthropic spec alignment)
# Standard tier: NO required fields per Anthropic spec (all are optional)
STANDARD_REQUIRED = set()
STANDARD_RECOMMENDED = {'description'}

# Enterprise tier: scored fields (warnings, not errors)
ENTERPRISE_RECOMMENDED = {'name', 'description', 'allowed-tools', 'version', 'author', 'license'}

# Legacy aliases for backward compat in grading functions
ANTHROPIC_REQUIRED = set()  # Nothing required per spec
ENTERPRISE_REQUIRED = set()  # Now warnings, not requirements
REQUIRED_FIELDS = set()  # Empty — nothing is a hard requirement

# Optional fields per Anthropic spec + AgentSkills.io
OPTIONAL_FIELDS = {
    'name', 'description', 'allowed-tools', 'version', 'author', 'license',
    'model', 'disable-model-invocation', 'mode', 'tags', 'metadata', 'compatible-with',
    'argument-hint', 'context', 'agent', 'user-invocable', 'hooks', 'compatibility',
}

# Deprecated fields (warn but don't error)
DEPRECATED_FIELDS = {'when_to_use'}

# Recommended sections (best practices, not mandated by any published standard)
RECOMMENDED_SECTIONS = [
    "# ",  # title line
    "## Overview",
    "## Prerequisites",
    "## Instructions",
    "## Output",
    "## Error Handling",
    "## Examples",
    "## Resources",
]

# Backward compat aliases
ENTERPRISE_SECTIONS = RECOMMENDED_SECTIONS
REQUIRED_SECTIONS = RECOMMENDED_SECTIONS

# Regex patterns
RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
RE_DESCRIPTION_USE_WHEN = re.compile(r"\bUse when\b", re.IGNORECASE)
RE_DESCRIPTION_TRIGGER_WITH = re.compile(r"\bTrigger with\b", re.IGNORECASE)
RE_SKILLDIR_SCRIPTS = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/scripts/([\w\-./]+)")
RE_SKILLDIR_REFERENCES = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/references/([\w\-./]+)")
RE_SKILLDIR_ASSETS = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/assets/([\w\-./]+)")
RE_RELATIVE_MD_LINK = re.compile(r"\[([^\]]*)\]\(((?!https?://|#)[^)]+)\)")
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

# Skill list token budget (Lee Han Chung deep dive): total descriptions are aggregated.
# NOTE: This repo hosts many skills; the "installed set" varies by user/workflow.
# This check is optional via --check-description-budget.
TOTAL_DESCRIPTION_BUDGET_WARN = 12_000
TOTAL_DESCRIPTION_BUDGET_ERROR = 15_000


# === INTENT SOLUTIONS 100-POINT GRADING RUBRIC ===
#
# Based on:
# - Anthropic Official Best Practices (platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
# - Lee Han Chung Deep Dive (leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
# - Intent Solutions production grading at scale
#
# Grade Scale:
#   A (90-100): Production-ready
#   B (80-89):  Good, minor improvements needed
#   C (70-79):  Adequate, has gaps
#   D (60-69):  Needs significant work
#   F (<60):    Major revision required


def calculate_grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'


def score_progressive_disclosure(path: Path, body: str, fm: dict) -> dict:
    """
    Progressive Disclosure Architecture (30 pts max)
    - Token Economy (10): SKILL.md line count
    - Layered Structure (10): Has references/ directory with content
    - Reference Depth (5): References are one level deep only
    - Navigation Signals (5): Well-structured sections for navigability
    """
    breakdown = {}
    lines = len(body.splitlines())
    skill_dir = path.parent

    # Token Economy (10 pts) - Per Anthropic: SKILL.md should be concise
    # ≤150=10, 151-300=7, 301-500=4, >500=0
    if lines <= 150:
        breakdown['token_economy'] = (10, "Excellent: ≤150 lines")
    elif lines <= 300:
        breakdown['token_economy'] = (7, f"Good: {lines} lines (target ≤150)")
    elif lines <= 500:
        breakdown['token_economy'] = (4, f"Acceptable: {lines} lines (target ≤150)")
    else:
        breakdown['token_economy'] = (0, f"Too long: {lines} lines (target ≤150)")

    # Layered Structure (10 pts) - Has references/ with markdown files
    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        ref_files = list(refs_dir.glob("*.md"))
        if ref_files:
            breakdown['layered_structure'] = (10, f"Has references/ with {len(ref_files)} files")
        else:
            breakdown['layered_structure'] = (3, "references/ exists but empty")
    else:
        # Penalty scales with file length - short files don't need references
        if lines <= 100:
            breakdown['layered_structure'] = (8, "No references/ (acceptable for short skill)")
        elif lines <= 200:
            breakdown['layered_structure'] = (4, "No references/ (should extract content)")
        else:
            breakdown['layered_structure'] = (0, "No references/ (long skill needs extraction)")

    # Info note: dynamic injection + references/ = sophisticated progressive disclosure
    has_dynamic_injection = bool(re.search(r'(?m)^!\`[^`]+\`\s*$', body))
    if has_dynamic_injection and refs_dir.exists() and refs_dir.glob("*.md"):
        score, msg = breakdown['layered_structure']
        breakdown['layered_structure'] = (score, msg + " + dynamic injection")

    # Reference Depth (5 pts) - One level deep only (no nested subdirs in references/)
    if refs_dir.exists():
        nested_dirs = [d for d in refs_dir.iterdir() if d.is_dir()]
        if not nested_dirs:
            breakdown['reference_depth'] = (5, "References are flat (good)")
        else:
            breakdown['reference_depth'] = (2, f"Nested dirs in references/: {len(nested_dirs)}")
    else:
        breakdown['reference_depth'] = (5, "N/A - no references/")

    # Navigation Signals (5 pts) - Well-structured sections for navigability
    # Note: No published standard mandates specific sections. Scoring is softened
    # to reflect that these are best practices, not requirements.
    sections = len(re.findall(r'(?m)^##\s+', body))
    if lines <= 100:
        breakdown['navigation_signals'] = (5, "Short file, navigation implicit")
    elif sections >= 7:
        breakdown['navigation_signals'] = (5, f"Well-structured: {sections} section headers")
    elif sections >= 4:
        breakdown['navigation_signals'] = (4, f"Adequate structure: {sections} sections (7+ ideal)")
    elif sections >= 2:
        breakdown['navigation_signals'] = (2, f"Minimal structure: {sections} sections (4+ recommended)")
    else:
        breakdown['navigation_signals'] = (0, f"Poor structure: only {sections} sections")

    total = sum(v[0] for v in breakdown.values())
    return {'score': total, 'max': 30, 'breakdown': breakdown}


def score_ease_of_use(path: Path, body: str, fm: dict) -> dict:
    """
    Ease of Use (25 pts max)
    - Metadata Quality (10): Complete, well-formed frontmatter
    - Discoverability (6): Has trigger phrases, "Use when"
    - Terminology Consistency (4): Consistent naming
    - Workflow Clarity (5): Clear step-by-step instructions
    """
    breakdown = {}
    desc = str(fm.get('description', '')).lower()

    # Metadata Quality (10 pts)
    meta_score = 0
    meta_notes = []
    if fm.get('name'):
        meta_score += 2
    else:
        meta_notes.append("missing name")
    if fm.get('description') and len(str(fm.get('description', ''))) >= 50:
        meta_score += 3
    else:
        meta_notes.append("description too short")
    if fm.get('version'):
        meta_score += 2
    else:
        meta_notes.append("missing version")
    if fm.get('allowed-tools'):
        meta_score += 2
    else:
        meta_notes.append("missing allowed-tools")
    if fm.get('author') and '@' in str(fm.get('author', '')):
        meta_score += 1
    breakdown['metadata_quality'] = (meta_score, ", ".join(meta_notes) if meta_notes else "Complete metadata")

    # Discoverability (6 pts)
    disc_score = 0
    disc_notes = []
    if 'use when' in desc:
        disc_score += 3
        disc_notes.append("has 'Use when'")
    if 'trigger with' in desc or 'trigger phrase' in desc:
        disc_score += 3
        disc_notes.append("has trigger phrases")
    if not disc_notes:
        disc_notes.append("missing discovery cues")
    breakdown['discoverability'] = (disc_score, ", ".join(disc_notes))

    # Terminology Consistency (4 pts)
    # Check for consistent naming patterns in the skill
    name = str(fm.get('name', ''))
    folder = path.parent.name
    term_score = 4  # Start with full score
    term_notes = []
    if name and name != folder:
        term_score -= 2
        term_notes.append("name differs from folder")
    # Check for mixed case in description
    if any(w.isupper() and len(w) > 3 for w in str(fm.get('description', '')).split()):
        term_score -= 1
        term_notes.append("inconsistent casing")
    breakdown['terminology'] = (max(0, term_score), ", ".join(term_notes) if term_notes else "Consistent terminology")

    # Workflow Clarity (5 pts)
    workflow_score = 0
    workflow_notes = []
    # Check for numbered steps
    if re.search(r'(?m)^\s*1\.\s+', body):
        workflow_score += 3
        workflow_notes.append("has numbered steps")
    # Check for clear section headers
    section_count = len(re.findall(r'(?m)^##\s+', body))
    if section_count >= 5:
        workflow_score += 2
        workflow_notes.append(f"{section_count} sections")
    elif section_count >= 3:
        workflow_score += 1
        workflow_notes.append(f"{section_count} sections (add more)")
    if not workflow_notes:
        workflow_notes.append("unclear workflow")
    breakdown['workflow_clarity'] = (workflow_score, ", ".join(workflow_notes))

    total = sum(v[0] for v in breakdown.values())
    return {'score': total, 'max': 25, 'breakdown': breakdown}


def score_utility(path: Path, body: str, fm: dict) -> dict:
    """
    Utility (20 pts max)
    - Problem Solving Power (8): Clear use cases, practical value
    - Degrees of Freedom (5): Flexible, configurable
    - Feedback Loops (4): Error handling, validation
    - Examples & Templates (3): Has working examples
    """
    breakdown = {}
    body_lower = body.lower()

    # Problem Solving Power (8 pts)
    problem_score = 0
    problem_notes = []
    # Check for Overview section with substance
    if '## overview' in body_lower:
        overview_match = re.search(r'## overview\s*\n(.*?)(?=\n##|\Z)', body, re.IGNORECASE | re.DOTALL)
        if overview_match and len(overview_match.group(1).strip()) > 50:
            problem_score += 4
            problem_notes.append("has overview")
    # Check for Prerequisites (shows understanding of requirements)
    if '## prerequisites' in body_lower:
        problem_score += 2
        problem_notes.append("has prerequisites")
    # Check for Output section
    if '## output' in body_lower:
        problem_score += 2
        problem_notes.append("has output spec")
    if not problem_notes:
        problem_notes.append("unclear problem/solution")
    breakdown['problem_solving'] = (problem_score, ", ".join(problem_notes))

    # Degrees of Freedom (5 pts)
    freedom_score = 0
    freedom_notes = []
    # Check for configuration options
    if re.search(r'(?i)(optional|configur|parameter|argument|flag|option)', body):
        freedom_score += 2
        freedom_notes.append("has options")
    # Check for multiple approaches
    if re.search(r'(?i)(alternatively|or use|another approach|you can also)', body):
        freedom_score += 2
        freedom_notes.append("shows alternatives")
    # Check for extensibility hints
    if re.search(r'(?i)(extend|customize|modify|adapt)', body):
        freedom_score += 1
        freedom_notes.append("extensible")
    if not freedom_notes:
        freedom_notes.append("rigid implementation")
    breakdown['degrees_of_freedom'] = (freedom_score, ", ".join(freedom_notes))

    # Feedback Loops (4 pts)
    feedback_score = 0
    feedback_notes = []
    if '## error handling' in body_lower:
        feedback_score += 2
        feedback_notes.append("has error handling")
    if re.search(r'(?i)(validate|verify|check|test|confirm)', body):
        feedback_score += 1
        feedback_notes.append("has validation")
    if re.search(r'(?i)(troubleshoot|debug|diagnose|fix)', body):
        feedback_score += 1
        feedback_notes.append("has troubleshooting")
    if not feedback_notes:
        feedback_notes.append("no feedback mechanisms")
    breakdown['feedback_loops'] = (feedback_score, ", ".join(feedback_notes))

    # Examples & Templates (3 pts)
    examples_score = 0
    examples_notes = []
    if '## examples' in body_lower or '**example' in body_lower:
        examples_score += 2
        examples_notes.append("has examples")
    if '```' in body:
        code_blocks = len(re.findall(r'```', body)) // 2
        if code_blocks >= 2:
            examples_score += 1
            examples_notes.append(f"{code_blocks} code blocks")
    if not examples_notes:
        examples_notes.append("no examples")
    breakdown['examples'] = (examples_score, ", ".join(examples_notes))

    total = sum(v[0] for v in breakdown.values())
    return {'score': total, 'max': 20, 'breakdown': breakdown}


def score_spec_compliance(path: Path, body: str, fm: dict) -> dict:
    """
    Spec Compliance (15 pts max)
    - Frontmatter Validity (5): Valid YAML, no parse errors
    - Name Conventions (4): Kebab-case, proper length
    - Description Quality (4): Proper length, no forbidden words
    - Optional Fields (2): Proper use of optional fields
    """
    breakdown = {}
    name = str(fm.get('name', ''))
    desc = str(fm.get('description', ''))

    # Frontmatter Validity (5 pts)
    fm_score = 5  # Start with full score
    fm_notes = []
    required = {'name', 'description', 'allowed-tools', 'version', 'author', 'license'}
    missing = required - set(fm.keys())
    if missing:
        fm_score -= min(len(missing), 4)
        fm_notes.append(f"missing: {', '.join(missing)}")
    if not fm_notes:
        fm_notes.append("valid frontmatter")
    breakdown['frontmatter_validity'] = (max(0, fm_score), ", ".join(fm_notes))

    # Name Conventions (4 pts)
    name_score = 4
    name_notes = []
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
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
    breakdown['name_conventions'] = (max(0, name_score), ", ".join(name_notes))

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
    if 'i can' in desc_lower or 'i will' in desc_lower:
        desc_score -= 1
        desc_notes.append("uses first person")
    if 'you can' in desc_lower or 'you should' in desc_lower:
        desc_score -= 1
        desc_notes.append("uses second person")
    if not desc_notes:
        desc_notes.append("good description")
    breakdown['description_quality'] = (max(0, desc_score), ", ".join(desc_notes))

    # Optional Fields (2 pts)
    opt_score = 2
    opt_notes = []
    if 'model' in fm:
        model = fm['model']
        if model not in ['inherit', 'sonnet', 'haiku', 'opus'] and not str(model).startswith('claude-'):
            opt_score -= 1
            opt_notes.append("invalid model value")
    if not opt_notes:
        opt_notes.append("optional fields ok")
    breakdown['optional_fields'] = (opt_score, ", ".join(opt_notes))

    total = sum(v[0] for v in breakdown.values())
    return {'score': total, 'max': 15, 'breakdown': breakdown}


def score_writing_style(path: Path, body: str, fm: dict) -> dict:
    """
    Writing Style (10 pts max)
    - Voice & Tense (4): Imperative voice, present tense
    - Objectivity (3): No first/second person in body
    - Conciseness (3): Not overly verbose
    """
    breakdown = {}

    # Voice & Tense (4 pts)
    voice_score = 4
    voice_notes = []
    # Check for imperative language (good)
    imperative_verbs = ['create', 'use', 'run', 'execute', 'configure', 'set', 'add', 'remove', 'check', 'verify']
    has_imperative = any(re.search(rf'(?m)^\s*\d+\.\s*{v}', body, re.IGNORECASE) for v in imperative_verbs)
    if not has_imperative:
        voice_score -= 2
        voice_notes.append("use imperative voice")
    if not voice_notes:
        voice_notes.append("good voice")
    breakdown['voice_tense'] = (voice_score, ", ".join(voice_notes))

    # Objectivity (3 pts)
    obj_score = 3
    obj_notes = []
    body_lower = body.lower()
    if 'you should' in body_lower or 'you can' in body_lower or 'you will' in body_lower:
        obj_score -= 1
        obj_notes.append("has second person")
    if ' i ' in body_lower or 'i can' in body_lower or "i'll" in body_lower:
        obj_score -= 1
        obj_notes.append("has first person")
    if not obj_notes:
        obj_notes.append("objective")
    breakdown['objectivity'] = (max(0, obj_score), ", ".join(obj_notes))

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
    breakdown['conciseness'] = (max(0, conc_score), ", ".join(conc_notes))

    total = sum(v[0] for v in breakdown.values())
    return {'score': total, 'max': 10, 'breakdown': breakdown}


def calculate_modifiers(path: Path, body: str, fm: dict) -> dict:
    """
    Modifiers (±15 pts)
    Bonuses: gerund name, grep-friendly, exemplary examples
    Penalties: first/second person description, unnecessary TOC
    """
    modifiers = {}
    name = str(fm.get('name', ''))
    desc = str(fm.get('description', ''))
    lines = len(body.splitlines())

    # Bonuses (up to +5)
    # Gerund-style name (verb-ing pattern) +1
    gerund_suffixes = ['ing', 'tion', 'ment', 'ness']
    if any(name.endswith(f'-{s}') or name.endswith(s) for s in ['ing']):
        modifiers['gerund_name'] = (+1, "gerund-style name")

    # Grep-friendly structure (clear section markers) +1
    sections = len(re.findall(r'(?m)^##\s+', body))
    if sections >= 7:
        modifiers['grep_friendly'] = (+1, "grep-friendly structure")

    # Exemplary examples (multiple labeled examples) +2
    example_count = len(re.findall(r'(?i)\*\*example[:\s]', body))
    if example_count >= 3:
        modifiers['exemplary_examples'] = (+2, f"{example_count} labeled examples")

    # Resources section with external links +1
    if '## resources' in body.lower():
        external_links = len(re.findall(r'\[.*?\]\(https?://', body))
        if external_links >= 2:
            modifiers['external_resources'] = (+1, f"{external_links} external links")

    # Penalties (up to -5)
    # First/second person in description -2
    desc_lower = desc.lower()
    if 'i can' in desc_lower or 'i will' in desc_lower or 'you can' in desc_lower or 'you should' in desc_lower:
        modifiers['person_in_desc'] = (-2, "first/second person in description")

    # TOC wastes tokens — Anthropic spec doesn't require it, progressive disclosure does
    has_toc = bool(re.search(r'(?mi)^##?\s*(table of contents|contents|toc)\b', body))
    if has_toc:
        modifiers['unnecessary_toc'] = (-1, "TOC wastes tokens — use clear section headers instead")

    # Dynamic context injection (Anthropic spec feature) +1
    has_dynamic_injection = bool(re.search(r'(?m)^!\`[^`]+\`\s*$', body))
    if has_dynamic_injection:
        injection_count = len(re.findall(r'(?m)^!\`[^`]+\`\s*$', body))
        modifiers['dynamic_injection'] = (+1, f"Uses preprocessing injection ({injection_count} directives)")

    # XML tags in body (anti-pattern) -1
    if '<' in body and '>' in body and re.search(r'<[a-z]+>', body):
        modifiers['xml_tags'] = (-1, "XML-like tags in body")

    total = sum(v[0] for v in modifiers.values())
    # Cap modifiers at ±15
    total = max(-15, min(15, total))
    return {'score': total, 'max_bonus': 5, 'max_penalty': -5, 'items': modifiers}


def grade_skill(path: Path, body: str, fm: dict) -> dict:
    """
    Calculate Intent Solutions 100-point grade for a skill.

    Returns dict with:
    - score: total points (0-100)
    - grade: letter grade (A-F)
    - breakdown: per-pillar scores
    """
    pda = score_progressive_disclosure(path, body, fm)
    ease = score_ease_of_use(path, body, fm)
    utility = score_utility(path, body, fm)
    spec = score_spec_compliance(path, body, fm)
    style = score_writing_style(path, body, fm)
    mods = calculate_modifiers(path, body, fm)

    base_score = pda['score'] + ease['score'] + utility['score'] + spec['score'] + style['score']
    total_score = base_score + mods['score']

    # Clamp to 0-100
    total_score = max(0, min(100, total_score))

    return {
        'score': total_score,
        'grade': calculate_grade(total_score),
        'breakdown': {
            'progressive_disclosure': pda,
            'ease_of_use': ease,
            'utility': utility,
            'spec_compliance': spec,
            'writing_style': style,
            'modifiers': mods,
        }
    }


# === COMMAND VALIDATION ===

# Valid categories for commands
VALID_CMD_CATEGORIES = [
    'git', 'deployment', 'security', 'testing', 'documentation',
    'database', 'api', 'frontend', 'backend', 'devops', 'forecasting',
    'analytics', 'migration', 'monitoring', 'other'
]

VALID_DIFFICULTIES = ['beginner', 'intermediate', 'advanced', 'expert']


def find_command_files(root: Path) -> List[Path]:
    """Find all command markdown files in plugins/."""
    results = []
    plugins_dir = root / "plugins"
    if plugins_dir.exists():
        for cmd_file in plugins_dir.rglob("commands/*.md"):
            if cmd_file.is_file():
                results.append(cmd_file)
    return results


def validate_command(path: Path) -> Dict[str, Any]:
    """Validate a command markdown file."""
    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        return {'fatal': f'Cannot read file: {e}'}

    # Extract frontmatter
    m = RE_FRONTMATTER.match(content)
    if not m:
        return {'fatal': 'No frontmatter found'}

    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return {'fatal': f'Invalid YAML: {e}'}

    errors: List[str] = []
    warnings: List[str] = []

    # Required: name
    if 'name' not in fm:
        errors.append("[command] Missing required field: name")
    else:
        name = str(fm['name'])
        if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
            warnings.append("[command] 'name' should be kebab-case")
        if name != path.stem:
            warnings.append(f"[command] 'name' '{name}' should match filename '{path.stem}.md'")

    # Required: description
    if 'description' not in fm:
        errors.append("[command] Missing required field: description")
    else:
        desc = str(fm['description'])
        if len(desc) < 10:
            errors.append("[command] 'description' must be at least 10 characters")
        if len(desc) > 80:
            warnings.append("[command] 'description' should be 80 characters or less")

    # Optional: shortcut
    if 'shortcut' in fm:
        shortcut = str(fm['shortcut'])
        if len(shortcut) < 1 or len(shortcut) > 4:
            warnings.append("[command] 'shortcut' should be 1-4 characters")
        elif not shortcut.islower():
            warnings.append("[command] 'shortcut' should be lowercase")
        elif not shortcut.isalpha():
            warnings.append("[command] 'shortcut' should contain only letters")

    # Optional: category
    if 'category' in fm:
        if fm['category'] not in VALID_CMD_CATEGORIES:
            warnings.append(f"[command] Unknown category: {fm['category']}")

    # Optional: difficulty
    if 'difficulty' in fm:
        if fm['difficulty'] not in VALID_DIFFICULTIES:
            warnings.append(f"[command] Unknown difficulty: {fm['difficulty']}")

    return {'errors': errors, 'warnings': warnings, 'type': 'command'}


# === AGENT VALIDATION ===

VALID_EXPERTISE = ['intermediate', 'advanced', 'expert']
VALID_PRIORITIES = ['low', 'medium', 'high', 'critical']
VALID_EFFORT_LEVELS = ['low', 'medium', 'high']


def find_agent_files(root: Path) -> List[Path]:
    """Find all agent markdown files in plugins/."""
    results = []
    plugins_dir = root / "plugins"
    if plugins_dir.exists():
        for agent_file in plugins_dir.rglob("agents/*.md"):
            if agent_file.is_file():
                results.append(agent_file)
    return results


def validate_agent(path: Path) -> Dict[str, Any]:
    """Validate an agent markdown file."""
    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        return {'fatal': f'Cannot read file: {e}'}

    # Extract frontmatter
    m = RE_FRONTMATTER.match(content)
    if not m:
        return {'fatal': 'No frontmatter found'}

    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return {'fatal': f'Invalid YAML: {e}'}

    errors: List[str] = []
    warnings: List[str] = []

    # Required: name
    if 'name' not in fm:
        errors.append("[agent] Missing required field: name")
    else:
        name = str(fm['name'])
        if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
            warnings.append("[agent] 'name' should be kebab-case")

    # Required: description (20 chars min for agents)
    if 'description' not in fm:
        errors.append("[agent] Missing required field: description")
    else:
        desc = str(fm['description'])
        if len(desc) < 20:
            errors.append("[agent] 'description' must be at least 20 characters")
        if len(desc) > 200:
            warnings.append("[agent] 'description' should be 200 characters or less")

    # Recommended: capabilities
    if 'capabilities' not in fm:
        warnings.append("[agent] Missing recommended field: capabilities")
    elif not isinstance(fm['capabilities'], list):
        warnings.append("[agent] 'capabilities' should be an array")
    else:
        caps = fm['capabilities']
        if len(caps) < 2:
            warnings.append("[agent] 'capabilities' should have at least 2 items")
        if len(caps) > 10:
            warnings.append("[agent] 'capabilities' should have 10 or fewer items")
        for i, cap in enumerate(caps):
            if not isinstance(cap, str):
                errors.append(f"[agent] 'capabilities[{i}]' must be a string")

    # Optional: expertise_level
    if 'expertise_level' in fm:
        if fm['expertise_level'] not in VALID_EXPERTISE:
            warnings.append(f"[agent] Unknown expertise_level: {fm['expertise_level']}")

    # Optional: activation_priority
    if 'activation_priority' in fm:
        if fm['activation_priority'] not in VALID_PRIORITIES:
            warnings.append(f"[agent] Unknown activation_priority: {fm['activation_priority']}")

    # Optional: effort (v2.1.78+ — controls model reasoning effort per turn)
    if 'effort' in fm:
        if fm['effort'] not in VALID_EFFORT_LEVELS:
            warnings.append(f"[agent] Unknown effort level: {fm['effort']}. Must be one of: {', '.join(VALID_EFFORT_LEVELS)}")

    # Optional: maxTurns (v2.1.78+ — caps agentic loop iterations)
    if 'maxTurns' in fm:
        if not isinstance(fm['maxTurns'], int) or fm['maxTurns'] < 1:
            errors.append("[agent] 'maxTurns' must be a positive integer")

    # Optional: disallowedTools (v2.1.78+ — denylist for agent tool access)
    if 'disallowedTools' in fm:
        if not isinstance(fm['disallowedTools'], list):
            errors.append("[agent] 'disallowedTools' must be an array of strings")
        else:
            for i, tool in enumerate(fm['disallowedTools']):
                if not isinstance(tool, str):
                    errors.append(f"[agent] 'disallowedTools[{i}]' must be a string")

    return {'errors': errors, 'warnings': warnings, 'type': 'agent'}


# === UTILITY FUNCTIONS ===

def find_skill_files(root: Path) -> List[Path]:
    """Find all SKILL.md files in plugins/ and skills/ directories."""
    excluded_dirs = {
        "archive",
        "backups",
        "backup",
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "010-archive",
        "000-docs",
        "002-workspaces",
    }
    results = []

    # Search in plugins directory
    plugins_dir = root / "plugins"
    if plugins_dir.exists():
        for p in plugins_dir.rglob("skills/*/SKILL.md"):
            if p.is_file():
                parts = p.relative_to(root).parts
                if any(part in excluded_dirs for part in parts):
                    continue
                if any(part.startswith("skills-backup-") for part in parts):
                    continue
                results.append(p)

    # Search in standalone skills directory
    skills_dir = root / "skills"
    if skills_dir.exists():
        for p in skills_dir.rglob("*/SKILL.md"):
            if p.is_file():
                parts = p.relative_to(root).parts
                if any(part in excluded_dirs for part in parts):
                    continue
                results.append(p)

    # Nixtla-compatible: search in 003-skills directory
    nixtla_skills = root / "003-skills"
    if nixtla_skills.exists():
        for p in nixtla_skills.rglob("*/SKILL.md"):
            if p.is_file():
                parts = p.relative_to(root).parts
                if any(part in excluded_dirs for part in parts):
                    continue
                results.append(p)

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
    """Parse allowed-tools as a CSV string (Anthropic + enterprise standard)."""
    if isinstance(tools_value, str):
        return [t.strip() for t in tools_value.split(',') if t.strip()]
    return []


def validate_tool_permission(tool: str) -> Tuple[bool, str]:
    """Validate a single tool permission including wildcards like Bash(git:*)."""
    base_tool = tool.split('(')[0].strip()

    # Handle malformed scopes like "mysql:*)" - extract actual tool name
    if ':' in base_tool:
        base_tool = base_tool.split(':')[0].strip()

    if base_tool not in VALID_TOOLS:
        # Warn instead of error for unknown patterns (may be valid Bash commands)
        return True, f"Unknown tool pattern: {tool} (assuming Bash command)"

    # Validate wildcard syntax if present - warn instead of error
    if '(' in tool:
        if not tool.endswith(')'):
            return True, f"Malformed wildcard syntax: {tool}"
        inner = tool[tool.index('(')+1:-1]
        if ':' not in inner:
            return True, f"Wildcard should use cmd:* format: {tool}"

    return True, ""


def estimate_word_count(content: str) -> int:
    """Estimate word count for content length check."""
    # Remove frontmatter
    content_body = re.sub(r'^---\n.*?\n---\n?', '', content, flags=re.DOTALL)
    return len(content_body.split())


# === VALIDATION FUNCTIONS ===

def validate_frontmatter(path: Path, fm: dict, tier: str = TIER_STANDARD) -> Tuple[List[str], List[str], List[str]]:
    """
    Validate SKILL.md frontmatter.
    Returns: (errors, warnings, infos)
    """
    errors: List[str] = []
    warnings: List[str] = []
    infos: List[str] = []

    # === FIELD PRESENCE CHECKS (tier-aware) ===
    # Standard tier: no required fields per Anthropic spec. description is recommended (WARNING).
    # Enterprise tier: enterprise fields scored as WARNINGS (not errors).

    metadata = fm.get('metadata', {}) if isinstance(fm.get('metadata'), dict) else {}

    if tier == TIER_ENTERPRISE:
        for key in ENTERPRISE_RECOMMENDED:
            if key not in fm:
                if key in ('author', 'version', 'license') and key in metadata:
                    continue  # Found in metadata block — valid per spec
                warnings.append(f"[frontmatter] Missing recommended field: '{key}' (enterprise)")
    else:
        # Standard tier: only description is recommended
        if 'description' not in fm:
            warnings.append("[frontmatter] Missing recommended field: 'description' (recommended by Anthropic spec)")

    # === FIELD-SPECIFIC VALIDATION ===

    # name field
    if 'name' in fm:
        name = str(fm['name']).strip()
        if not name:
            errors.append("[frontmatter] 'name' must be non-empty")
        else:
            # Kebab-case check (WARN for now - some skills use human-readable names)
            if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
                warnings.append(f"[frontmatter] 'name' should be kebab-case (lowercase + hyphens): {name}")

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

            # Discoverability checks (tier-aware)
            if not RE_DESCRIPTION_USE_WHEN.search(desc):
                if tier == TIER_ENTERPRISE:
                    warnings.append("[frontmatter] 'description' should include 'Use when ...' phrase for model discoverability (enterprise)")
                else:
                    infos.append("[frontmatter] Consider adding 'Use when ...' phrase to description for better discoverability")

            if not RE_DESCRIPTION_TRIGGER_WITH.search(desc):
                if tier == TIER_ENTERPRISE:
                    warnings.append("[frontmatter] 'description' should include 'Trigger with ...' phrase for user discoverability (enterprise)")
                else:
                    infos.append("[frontmatter] Consider adding 'Trigger with ...' phrase to description")

            # Voice checks (tier-aware)
            if RE_FIRST_PERSON.search(desc):
                if tier == TIER_ENTERPRISE:
                    warnings.append("[frontmatter] 'description' should NOT use first person (I can / I will / etc.) - use third person")
                else:
                    warnings.append("[frontmatter] 'description' uses first person - third person recommended")

            if RE_SECOND_PERSON.search(desc):
                if tier == TIER_ENTERPRISE:
                    warnings.append("[frontmatter] 'description' should NOT use second person (You can / You should) - use third person")
                else:
                    warnings.append("[frontmatter] 'description' uses second person - third person recommended")

            # Reserved words (WARN - legitimate in AI/Claude product context)
            desc_lower = desc.lower()
            for bad in FORBIDDEN_WORDS:
                if bad in desc_lower:
                    warnings.append(f"[frontmatter] 'description' contains reserved word: '{bad}' (ok for Claude/AI context)")

            # Imperative language check (best practice)
            imperative_starts = [
                'analyze', 'audit', 'build', 'compare', 'configure', 'convert', 'create',
                'debug', 'deploy', 'detect', 'extract', 'fix', 'forecast', 'generate',
                'implement', 'log', 'manage', 'migrate', 'monitor', 'optimize',
                'process', 'review', 'route', 'scan', 'set up', 'setup', 'test',
                'track', 'transform', 'validate',
            ]
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

        # Unscoped Bash check (tier-aware)
        if 'Bash' in tools:
            if tier == TIER_ENTERPRISE:
                errors.append("[frontmatter] allowed-tools: unscoped 'Bash' is not allowed - use scoped Bash(git:*), Bash(npm:*), etc.")
            else:
                warnings.append("[frontmatter] allowed-tools: unscoped 'Bash' - consider scoping (Bash(git:*), Bash(npm:*), etc.)")

        # Info about over-permissioning
        # Count unique base tools (Bash scopes like Bash(git:*) should not inflate the tool count).
        def _base_tool(tool: str) -> str:
            base = tool.split('(')[0].strip()
            if ':' in base:
                base = base.split(':')[0].strip()
            return base

        unique_tool_count = len({_base_tool(t) for t in tools})
        if unique_tool_count > 6:
            warnings.append(
                f"[frontmatter] Many tools permitted ({unique_tool_count}) - consider limiting for security"
            )

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

    # === COMPATIBLE-WITH FIELD ===
    VALID_PLATFORMS = {'claude-code', 'codex', 'openclaw', 'aider', 'continue', 'cursor', 'windsurf'}

    if 'compatible-with' in fm:
        compat = fm['compatible-with']
        if isinstance(compat, str):
            # CSV string
            platforms = [p.strip().lower() for p in compat.split(',')]
        elif isinstance(compat, list):
            platforms = [str(p).strip().lower() for p in compat]
        else:
            errors.append(f"[frontmatter] 'compatible-with' must be CSV string or array, got: {type(compat).__name__}")
            platforms = []

        for p in platforms:
            if p and p not in VALID_PLATFORMS:
                warnings.append(f"[frontmatter] 'compatible-with' unknown platform: '{p}' (known: {', '.join(sorted(VALID_PLATFORMS))})")

    # === NEW CLAUDE CODE SPEC FIELDS ===

    # context field (fork for subagent execution)
    if 'context' in fm:
        ctx = fm['context']
        if ctx not in ('fork',):
            warnings.append(f"[frontmatter] 'context' value '{ctx}' not standard (use: fork)")

    # agent field (subagent type)
    if 'agent' in fm:
        agent_val = str(fm['agent']).strip()
        if not agent_val:
            errors.append("[frontmatter] 'agent' must be non-empty if specified")

    # user-invocable field (boolean)
    if 'user-invocable' in fm:
        ui = fm['user-invocable']
        if not isinstance(ui, bool):
            errors.append(f"[frontmatter] 'user-invocable' must be boolean, got: {type(ui).__name__}")

    # argument-hint field (string autocomplete hint)
    if 'argument-hint' in fm:
        hint = str(fm['argument-hint']).strip()
        if len(hint) > 200:
            warnings.append("[frontmatter] 'argument-hint' exceeds 200 chars - keep hints concise")

    # hooks field (skill-scoped lifecycle hooks)
    if 'hooks' in fm:
        hooks_val = fm['hooks']
        if not isinstance(hooks_val, dict):
            errors.append(f"[frontmatter] 'hooks' must be a mapping, got: {type(hooks_val).__name__}")

    # compatibility field (AgentSkills.io environment requirements)
    if 'compatibility' in fm:
        compat_str = str(fm['compatibility']).strip()
        if len(compat_str) > 500:
            warnings.append("[frontmatter] 'compatibility' exceeds 500 chars")

    # === DEPRECATED FIELDS ===

    for field in DEPRECATED_FIELDS:
        if field in fm:
            warnings.append(f"[frontmatter] Deprecated field '{field}' - use detailed 'description' instead")

    # === UNKNOWN FIELDS ===

    known_fields = OPTIONAL_FIELDS | DEPRECATED_FIELDS
    unknown_fields = set(fm.keys()) - known_fields
    for field in unknown_fields:
        warnings.append(f"[frontmatter] Non-standard field: '{field}'")

    return errors, warnings, infos


def validate_body(path: Path, body: str, tier: str = TIER_STANDARD, fm: dict = None) -> Tuple[List[str], List[str], List[str]]:
    """
    Validate SKILL.md body content.
    Returns: (errors, warnings, infos)
    """
    errors: List[str] = []
    warnings: List[str] = []
    infos: List[str] = []
    if fm is None:
        fm = {}
    lines = body.splitlines()

    # === LENGTH CHECKS ===

    # Line limit (WARN in both tiers)
    if len(lines) > 500:
        warnings.append(f"[body] SKILL.md body has {len(lines)} lines (max 500). Use progressive disclosure (extract to references/)")

    # Word count check
    word_count = len(body.split())
    if word_count > 5000:
        warnings.append(f"[body] Content exceeds 5000 words ({word_count}) - may overwhelm context")
    elif word_count > 3500:
        warnings.append(f"[body] Content is lengthy ({word_count} words) - consider references/ directory")

    # === SECTION CHECKS (enterprise tier only) ===
    # IMPORTANT: Detect headings outside fenced code blocks to avoid false positives from examples.

    def iter_non_code_lines(text: str):
        in_code_block = False
        for raw in text.splitlines():
            if CODE_FENCE_PATTERN.match(raw):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            yield raw

    def has_markdown_h1(text: str) -> bool:
        for raw in iter_non_code_lines(text):
            if re.match(r"^#\s+\S", raw) and not raw.startswith("## "):
                return True
        return False

    def has_heading_line(text: str, heading: str) -> bool:
        target = heading.strip().lower()
        for raw in iter_non_code_lines(text):
            if raw.strip().lower() == target:
                return True
        return False

    if tier == TIER_ENTERPRISE:
        for sec in RECOMMENDED_SECTIONS:
            if sec == "# ":
                if not has_markdown_h1(body):
                    warnings.append(f"[body] Recommended section missing: '{sec}' (best practice, not spec-mandated)")
            else:
                if not has_heading_line(body, sec):
                    warnings.append(f"[body] Recommended section missing: '{sec}' (best practice, not spec-mandated)")

    # === LEE HAN CHUNG: SECTION CONTENT MUST BE NON-EMPTY ===

    def _section_body(section_heading: str) -> str:
        """
        Grab content between this heading and the next heading of same or higher level.
        Headings inside code fences are ignored.
        """
        m_heading = re.match(r"^(#+)\s+", section_heading.strip())
        if not m_heading:
            return ""
        level = len(m_heading.group(1))
        target = section_heading.strip().lower()

        found = False
        collected: List[str] = []

        in_code = False
        for raw in body.splitlines():
            if CODE_FENCE_PATTERN.match(raw):
                in_code = not in_code
                continue
            if in_code:
                continue

            if not found:
                if raw.strip().lower() == target:
                    found = True
                continue

            m_next = re.match(r"^\s*(#{1,6})\s+", raw)
            if m_next:
                next_level = len(m_next.group(1))
                if next_level <= level:
                    break

            collected.append(raw)

        return "\n".join(collected).strip()

    if tier == TIER_ENTERPRISE:
        for section, min_chars, level in [
            ("## Instructions", 40, "WARN"),
            ("## Output", 20, "WARN"),
            ("## Error Handling", 20, "WARN"),
            ("## Examples", 20, "WARN"),
            ("## Resources", 20, "WARN"),
        ]:
            content = _section_body(section)
            # Ignore empty sections that only contain code fences/whitespace
            content_no_code = re.sub(r"```.*?```", "", content, flags=re.DOTALL).strip()
            if len(content_no_code) < min_chars:
                msg = f"[body] Section '{section}' looks empty/too short (enterprise quality standard)"
                if level == "ERROR":
                    errors.append(msg)
                else:
                    warnings.append(msg)

        # === LEE HAN CHUNG: INSTRUCTIONS MUST BE STEP-BY-STEP ===

        instructions = _section_body("## Instructions")
        if instructions:
            has_numbered = bool(re.search(r"(?m)^\s*1\.\s+\S+", instructions))
            has_step_heading = bool(re.search(r"(?mi)^\s*#{2,6}\s*step\s*\d+", instructions))
            has_step_label = bool(re.search(r"(?mi)^\s*step\s*\d+[:\-]", instructions))
            if not (has_numbered or has_step_heading or has_step_label):
                warnings.append("[body] '## Instructions' should include step-by-step steps (numbered list or Step headings) (enterprise)")

    # === LEE HAN CHUNG: PURPOSE STATEMENT (1-2 sentences near top) ===

    def _sentence_count(text: str) -> int:
        cleaned = re.sub(r"\s+", " ", text.strip())
        if not cleaned:
            return 0
        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        return len([p for p in parts if p.strip()])

    def _extract_first_paragraph(after_line_idx: int) -> str:
        paragraph: List[str] = []
        in_code = False
        for raw in lines[after_line_idx:]:
            if CODE_FENCE_PATTERN.match(raw):
                in_code = not in_code
                continue
            if in_code:
                continue
            if HEADING_PATTERN.match(raw):
                break
            if not raw.strip():
                if paragraph:
                    break
                continue
            # Skip list items to avoid counting bullets as purpose text.
            if raw.lstrip().startswith(("-", "*", "+")):
                if paragraph:
                    break
                continue
            paragraph.append(raw.strip())
        return " ".join(paragraph).strip()

    # Find first H1 title line
    title_idx: Optional[int] = None
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title_idx = i
            break

    purpose_text = ""
    purpose_location: Optional[int] = None

    # Prefer explicit "## Purpose" section if present
    for i, line in enumerate(lines):
        if line.strip().lower() == "## purpose":
            purpose_text = _extract_first_paragraph(i + 1)
            purpose_location = i + 1
            break

    # Fallback: first paragraph after title
    if not purpose_text and title_idx is not None:
        purpose_text = _extract_first_paragraph(title_idx + 1)
        purpose_location = title_idx + 1
        if not purpose_text:
            # Common layout: title followed immediately by a section heading (e.g., ## Overview).
            for i, line in enumerate(lines):
                if line.strip().lower() == "## overview":
                    purpose_text = _extract_first_paragraph(i + 1)
                    purpose_location = i + 1
                    break

    if tier == TIER_ENTERPRISE:
        if not purpose_text:
            warnings.append("[body] Missing purpose statement near the top (enterprise quality standard)")
        else:
            sc = _sentence_count(purpose_text)
            if sc == 0:
                warnings.append("[body] Purpose statement is empty (enterprise quality standard)")
            elif sc > 2:
                warnings.append(f"[body] Purpose statement is {sc} sentences (recommended 1-2)")
            if len(purpose_text) > 400:
                warnings.append("[body] Purpose statement is long (>400 chars) - keep it crisp")
            if purpose_location is not None and purpose_location > 120:
                warnings.append("[body] Purpose statement appears late in the document - keep it near the top")

    # === LEE HAN CHUNG: AVOID HUGE EMBEDDED BLOCKS ===

    in_code_block = False
    code_block_lines = 0
    for raw in lines:
        if CODE_FENCE_PATTERN.match(raw):
            if in_code_block:
                if code_block_lines >= 200:
                    warnings.append(
                        f"[body] Large embedded code block ({code_block_lines} lines) - prefer scripts/ or references/ (Lee Han Chung)"
                    )
                code_block_lines = 0
            in_code_block = not in_code_block
            continue
        if in_code_block:
            code_block_lines += 1

    # === PATH CHECKS ===
    # Remove all code blocks and inline code BEFORE scanning
    # This eliminates false positives from code examples

    body_no_code = re.sub(r'```.*?```', '', body, flags=re.DOTALL)  # Remove fenced code blocks
    body_no_code = re.sub(r'`[^`]+`', '', body_no_code)  # Remove inline code

    # Now check for absolute paths in the cleaned content
    for i, line in enumerate(body_no_code.splitlines(), start=1):
        # Absolute paths forbidden
        for pattern, desc in ABSOLUTE_PATH_PATTERNS:
            if pattern.search(line):
                errors.append(
                    f"[body] Line {i}: contains absolute/OS-specific path ({desc}) - use '${{CLAUDE_SKILL_DIR}}/...'"
                )
                break

        # Backslashes forbidden
        if "\\scripts\\" in line or "\\\\" in line:
            errors.append(f"[body] Line {i}: uses backslashes in path - use forward slashes")

    # === TIME-SENSITIVE INFORMATION ===
    # Check for date-specific logic that will become stale
    time_patterns = [
        (r'\b(before|after|until|since)\s+20\d{2}\b', "date-specific logic"),
        (r'\bas of\s+20\d{2}\b', "date-specific reference"),
        (r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+20\d{2}\b', "specific date"),
        (r'\bQ[1-4]\s+20\d{2}\b', "quarter reference"),
        (r'\bdeprecated\s+(in|since)\s+v?\d', "version deprecation note"),
    ]
    for pattern, desc in time_patterns:
        matches = list(re.finditer(pattern, body, re.IGNORECASE))
        for m in matches:
            warnings.append(f"[body] Time-sensitive information found: '{m.group()}' ({desc}) - may become stale")

    # === SCRIPT QUALITY CHECKS ===
    # Check embedded scripts for error handling
    code_blocks = re.findall(r'```(?:bash|sh|python|py)?\n(.*?)```', body, re.DOTALL | re.IGNORECASE)
    for i, block in enumerate(code_blocks):
        # Check for error handling in bash scripts (only for substantial scripts, not examples)
        if 'set -e' not in block and '|| ' not in block and 'if [' not in block:
            if len(block.strip().splitlines()) > 15:  # Only warn for substantial scripts
                if re.search(r'\b(rm|mv|cp|curl|wget|pip|npm)\b', block):
                    warnings.append(f"[scripts] Code block {i+1}: Consider adding error handling (set -e or || exit)")

        # Check for unexplained magic numbers (voodoo constants)
        # Whitelist well-known HTTP status codes and common port numbers
        KNOWN_NUMBERS = {
            '200', '201', '204', '301', '302', '304', '307', '308',
            '400', '401', '403', '404', '405', '408', '409', '422', '429',
            '500', '502', '503', '504',
            '3000', '5000', '8000', '8080', '8443', '9090',  # common ports
        }
        magic_numbers = re.findall(r'(?<![.\d])\b(?:(?:[2-9]\d{2,})|(?:1\d{3,}))\b(?![.\d])', block)
        for num in magic_numbers[:3]:  # Limit warnings
            if num in KNOWN_NUMBERS:
                continue
            if not re.search(rf'#.*{num}', block):  # No comment explaining it
                warnings.append(f"[scripts] Code block {i+1}: Magic number '{num}' - add comment explaining why")

    # === STRING SUBSTITUTION CHECKS ===
    # Detect $ARGUMENTS / $ARGUMENTS[N] / $0-$9 usage and validate argument-hint presence
    has_arguments = bool(re.search(r'\$ARGUMENTS', body))
    has_positional = bool(re.search(r'\$[0-9]', body))
    if (has_arguments or has_positional) and 'argument-hint' not in fm:
        infos.append("[body] Uses $ARGUMENTS/$N but 'argument-hint' frontmatter is missing — "
                     "add argument-hint for autocomplete support (per official docs)")

    # === VOICE CHECKS ===

    if re.search(r'\byou should\b|\byou can\b|\byou will\b', body, re.IGNORECASE):
        warnings.append("[body] Consider imperative language instead of 'you should/can/will'")

    return errors, warnings, infos


def validate_scripts_exist(path: Path, body: str) -> Tuple[List[str], List[str]]:
    """
    Validate that all ${CLAUDE_SKILL_DIR}/scripts/... references point to real files.
    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []
    skill_dir = path.parent.resolve()

    referenced = set(m.group(1) for m in RE_SKILLDIR_SCRIPTS.finditer(body))

    for rel in sorted(referenced):
        script_path = (skill_dir / "scripts" / rel).resolve()

        # Ensure path doesn't escape skill directory
        try:
            script_path.relative_to(skill_dir)
        except ValueError:
            errors.append(f"[scripts] Reference escapes skill directory: {rel}")
            continue

        if not script_path.exists():
            warnings.append(
                f"[scripts] Referenced script not found: '${{CLAUDE_SKILL_DIR}}/scripts/{rel}' "
                f"(expected at {skill_dir.name}/scripts/{rel})"
            )

    return errors, warnings


def validate_resource_files_exist(path: Path, body: str) -> Tuple[List[str], List[str]]:
    """
    Validate that all ${CLAUDE_SKILL_DIR}/references/... and ${CLAUDE_SKILL_DIR}/assets/... references point to real files.
    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []
    skill_dir = path.parent.resolve()

    for rel in sorted(set(m.group(1) for m in RE_SKILLDIR_REFERENCES.finditer(body))):
        target = (skill_dir / "references" / rel).resolve()
        try:
            target.relative_to(skill_dir)
        except ValueError:
            errors.append(f"[resources] Reference escapes skill directory: references/{rel}")
            continue
        if not target.exists():
            warnings.append(
                f"[resources] Referenced file not found: '${{CLAUDE_SKILL_DIR}}/references/{rel}' "
                f"(expected at {skill_dir.name}/references/{rel})"
            )

    for rel in sorted(set(m.group(1) for m in RE_SKILLDIR_ASSETS.finditer(body))):
        target = (skill_dir / "assets" / rel).resolve()
        try:
            target.relative_to(skill_dir)
        except ValueError:
            errors.append(f"[resources] Reference escapes skill directory: assets/{rel}")
            continue
        if not target.exists():
            warnings.append(
                f"[resources] Referenced file not found: '${{CLAUDE_SKILL_DIR}}/assets/{rel}' "
                f"(expected at {skill_dir.name}/assets/{rel})"
            )

    return errors, warnings


def validate_relative_links(path: Path, body: str) -> Tuple[List[str], List[str]]:
    """
    Validate that relative markdown links in SKILL.md point to existing files.
    Per Anthropic docs, [text](relative-path) is the official pattern for supporting files.
    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []
    skill_dir = path.parent.resolve()

    # Skip links inside code blocks and inline code
    in_code_block = False
    filtered_lines = []
    for line in body.splitlines():
        if CODE_FENCE_PATTERN.match(line):
            in_code_block = not in_code_block
        if not in_code_block:
            # Strip inline code spans to avoid matching example links
            filtered_lines.append(re.sub(r'`[^`]+`', '', line))
    filtered_body = "\n".join(filtered_lines)

    for match in RE_RELATIVE_MD_LINK.finditer(filtered_body):
        link_text = match.group(1)
        link_target = match.group(2)

        # Skip anchors, mailto, and template variables
        if link_target.startswith(("#", "mailto:", "${")):
            continue

        target_path = (skill_dir / link_target).resolve()

        # Ensure path doesn't escape skill directory
        try:
            target_path.relative_to(skill_dir)
        except ValueError:
            errors.append(f"[relative-link] Link escapes skill directory: [{link_text}]({link_target})")
            continue

        if not target_path.exists():
            warnings.append(
                f"[relative-link] Linked file not found: [{link_text}]({link_target}) "
                f"(expected at {skill_dir.name}/{link_target})"
            )

    return errors, warnings


# === CONTENT QUALITY VALIDATION (Phase 4: Hightower Feedback) ===
#
# These functions catch content quality issues that structural validation misses:
# - Files listed in README.md but don't exist
# - Python scripts that are stubs (only contain 'pass')
# - Placeholder text like REPLACE_ME, {variable}
# - Generic boilerplate descriptions

# Patterns for detecting stub scripts
STUB_SCRIPT_PATTERNS = [
    re.compile(r'def\s+\w+\([^)]*\):\s*\n\s*pass\s*$', re.MULTILINE),  # Function with only pass
    re.compile(r'Add processing logic here', re.IGNORECASE),
    re.compile(r'This is a template', re.IGNORECASE),
    re.compile(r'Customize based on', re.IGNORECASE),
    re.compile(r'#\s*TODO:\s*implement', re.IGNORECASE),
    re.compile(r'raise NotImplementedError'),
]

# Patterns for detecting placeholder text
PLACEHOLDER_PATTERNS = [
    re.compile(r'\{[a-z_]+\}'),           # {table_name}, {database}, etc.
    re.compile(r'REPLACE_ME', re.IGNORECASE),
    re.compile(r'\[YOUR_[A-Z_]+\]'),      # [YOUR_API_KEY], etc.
    re.compile(r'<insert\s+.+>', re.IGNORECASE),  # <insert description here>
    re.compile(r'\bTBD\b'),
    re.compile(r'\bFIXME\b'),
    re.compile(r'to be determined', re.IGNORECASE),
    re.compile(r'\bplaceholder\b', re.IGNORECASE),
]

# Patterns for detecting generic boilerplate
BOILERPLATE_PATTERNS = [
    re.compile(r'This skill provides automated assistance for \[?\w*\]? tasks', re.IGNORECASE),
    re.compile(r'This skill enables Claude to', re.IGNORECASE),
    re.compile(r'Step \d+: Assess Current State\s*$', re.MULTILINE | re.IGNORECASE),
    re.compile(r'Step \d+: Design Solution\s*$', re.MULTILINE | re.IGNORECASE),
    re.compile(r'Step \d+: Implement Changes\s*$', re.MULTILINE | re.IGNORECASE),
    re.compile(r'This is a template that can be customized', re.IGNORECASE),
    re.compile(r'Customize based on your requirements', re.IGNORECASE),
]


def validate_references_readme(skill_path: Path) -> Tuple[List[str], List[str]]:
    """
    Parse references/README.md for checkbox file lists.
    Verify each listed file actually exists.
    Returns (errors, warnings).

    Catches issues like:
    - references/README.md lists "postgresql_best_practices.md" but file doesn't exist
    """
    errors: List[str] = []
    warnings: List[str] = []
    skill_dir = skill_path.parent.resolve()

    # Check references/README.md
    refs_readme = skill_dir / "references" / "README.md"
    if refs_readme.exists():
        try:
            content = refs_readme.read_text(encoding='utf-8')
            # Match checkbox patterns: - [x] filename.md or - [ ] filename.md
            checkbox_pattern = re.compile(r'-\s*\[[ xX]\]\s*([^\s:]+\.(?:md|yaml|json|py|sh))')
            matches = checkbox_pattern.findall(content)

            for filename in matches:
                file_path = skill_dir / "references" / filename
                if not file_path.exists():
                    warnings.append(
                        f"[content-quality] references/README.md lists '{filename}' but file doesn't exist"
                    )
        except Exception as e:
            warnings.append(f"[content-quality] Could not parse references/README.md: {e}")

    # Check assets/README.md
    assets_readme = skill_dir / "assets" / "README.md"
    if assets_readme.exists():
        try:
            content = assets_readme.read_text(encoding='utf-8')
            checkbox_pattern = re.compile(r'-\s*\[[ xX]\]\s*([^\s:]+\.(?:md|yaml|json|py|sh|template))')
            matches = checkbox_pattern.findall(content)

            for filename in matches:
                file_path = skill_dir / "assets" / filename
                if not file_path.exists():
                    warnings.append(
                        f"[content-quality] assets/README.md lists '{filename}' but file doesn't exist"
                    )
        except Exception as e:
            warnings.append(f"[content-quality] Could not parse assets/README.md: {e}")

    return errors, warnings


def detect_stub_scripts(skill_path: Path) -> Tuple[List[str], List[str]]:
    """
    Scan Python scripts for stub patterns:
    - Functions with only 'pass' in body
    - "Add processing logic here"
    - "This is a template"
    - TODO/FIXME without implementation
    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []
    skill_dir = skill_path.parent.resolve()
    scripts_dir = skill_dir / "scripts"

    if not scripts_dir.exists():
        return errors, warnings

    for script in scripts_dir.glob("*.py"):
        try:
            content = script.read_text(encoding='utf-8')
            script_name = script.name

            # Check for stub patterns
            for pattern in STUB_SCRIPT_PATTERNS:
                if pattern.search(content):
                    warnings.append(
                        f"[content-quality] scripts/{script_name} appears to be a stub (contains placeholder code)"
                    )
                    break  # One warning per file is enough

            # Additional check: file is mostly empty or just imports
            lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith('#')]
            non_import_lines = [l for l in lines if not l.startswith(('import ', 'from '))]
            if len(non_import_lines) < 5 and len(lines) > 0:
                warnings.append(
                    f"[content-quality] scripts/{script_name} has minimal implementation ({len(non_import_lines)} non-import lines)"
                )

        except Exception as e:
            warnings.append(f"[content-quality] Could not read scripts/{script.name}: {e}")

    return errors, warnings


def detect_placeholder_text(skill_path: Path) -> Tuple[List[str], List[str]]:
    """
    Scan SKILL.md, templates, and config for placeholder patterns:
    - REPLACE_ME, {table_name}, {PLACEHOLDER}
    - TBD, TODO, FIXME in prose (not code comments)
    - "to be determined", "placeholder"
    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []
    skill_dir = skill_path.parent.resolve()

    # Files to scan (exclude code files where placeholders might be intentional)
    files_to_scan = [
        skill_path,  # SKILL.md
    ]

    # Add templates and config files
    for pattern in ['assets/*.yaml', 'assets/*.yml', 'config/*.yaml', 'config/*.yml']:
        files_to_scan.extend(skill_dir.glob(pattern))

    for file_path in files_to_scan:
        if not file_path.exists():
            continue

        try:
            content = file_path.read_text(encoding='utf-8')
            rel_path = file_path.relative_to(skill_dir)

            # Skip checking inside code blocks for SKILL.md
            if file_path.name == 'SKILL.md':
                # Remove code blocks before checking
                content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
            else:
                content_no_code = content

            for pattern in PLACEHOLDER_PATTERNS:
                matches = pattern.findall(content_no_code)
                if matches:
                    # Limit to first 3 unique matches per file
                    unique_matches = list(set(matches))[:3]
                    warnings.append(
                        f"[content-quality] {rel_path} contains placeholder text: {', '.join(unique_matches)}"
                    )
                    break  # One warning per file

        except Exception as e:
            warnings.append(f"[content-quality] Could not scan {file_path.name}: {e}")

    return errors, warnings


def detect_boilerplate(skill_path: Path) -> Tuple[List[str], List[str]]:
    """
    Detect generic boilerplate phrases in SKILL.md:
    - "This skill provides automated assistance for"
    - "This skill enables Claude to"
    - Generic step descriptions without specifics
    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []

    try:
        content = skill_path.read_text(encoding='utf-8')

        for pattern in BOILERPLATE_PATTERNS:
            if pattern.search(content):
                match = pattern.search(content)
                if match:
                    # Truncate long matches
                    matched_text = match.group()[:60] + ('...' if len(match.group()) > 60 else '')
                    warnings.append(
                        f"[content-quality] SKILL.md contains generic boilerplate: '{matched_text}'"
                    )

    except Exception as e:
        warnings.append(f"[content-quality] Could not scan SKILL.md for boilerplate: {e}")

    return errors, warnings


# === STRUCTURAL ADVISORS (suggest architecture improvements) ===

RE_OPERATION_HEADER = re.compile(r'^##\s+[\w-]+(?:\s*\(.*\))?\s*$', re.MULTILINE)


def advise_split_to_commands(path: Path, body: str) -> List[str]:
    """
    Detect multiple distinct operation sections that would be better as
    individual commands/*.md files. Looks for 3+ ## headers that follow
    step/operation naming patterns (## verb-noun, ## Step N: name, ## N. name).
    Returns info-level suggestions.
    """
    infos: List[str] = []
    skill_dir = path.parent.resolve()

    # Walk up to find the plugin root (directory containing .claude-plugin/)
    plugin_dir = None
    for parent in skill_dir.parents:
        if (parent / ".claude-plugin").exists():
            plugin_dir = parent
            break

    # Find ## headers that look like distinct user-invocable operations
    # Only matches kebab-case names (## verb-noun) — the clearest signal
    operation_pattern = re.compile(
        r'^##\s+(?:\d+\.\s+)?([\w]+-[\w]+(?:-[\w]+)*)\s*$', re.MULTILINE
    )
    operations = operation_pattern.findall(body)

    if len(operations) >= 3:
        # Check if plugin already has commands/ directory
        has_commands = plugin_dir and (plugin_dir / "commands").exists()

        if not has_commands:
            op_list = ", ".join(operations[:5])
            infos.append(
                f"[advisor] Found {len(operations)} operation sections ({op_list}). "
                f"Consider splitting into individual commands/*.md files for independent invocation."
            )

    return infos


def advise_offload_to_references(path: Path, body: str) -> List[str]:
    """
    Identify body sections >20 lines that could be offloaded to references/.
    Returns info-level suggestions.
    """
    infos: List[str] = []
    skill_dir = path.parent.resolve()
    refs_dir = skill_dir / "references"

    # Split body by ## headers
    sections: List[Tuple[str, int]] = []
    current_header = ""
    current_lines = 0

    for line in body.splitlines():
        if line.startswith("## "):
            if current_header and current_lines > 0:
                sections.append((current_header, current_lines))
            current_header = line.strip("# ").strip()
            current_lines = 0
        else:
            current_lines += 1

    if current_header and current_lines > 0:
        sections.append((current_header, current_lines))

    # Flag sections >20 lines that are good candidates for references
    offload_candidates = ["Output", "Error Handling", "Examples", "Resources",
                          "Reference", "API", "Configuration", "Schema"]
    for header, line_count in sections:
        if line_count > 20:
            is_candidate = any(kw.lower() in header.lower() for kw in offload_candidates)
            if is_candidate and not refs_dir.exists():
                infos.append(
                    f"[advisor] Section '## {header}' is {line_count} lines. "
                    f"Consider offloading to references/{header.lower().replace(' ', '-')}.md "
                    f"with a relative link: [details](references/{header.lower().replace(' ', '-')}.md)"
                )

    return infos


def advise_dci_opportunities(path: Path, body: str) -> List[str]:
    """
    Detect patterns where DCI (dynamic context injection) would save tool calls.
    Returns info-level suggestions.
    """
    infos: List[str] = []

    # Already has DCI? Skip.
    has_dci = bool(re.search(r'(?m)^!\`[^`]+\`\s*$', body))
    if has_dci:
        return infos

    # Patterns that suggest DCI would help
    dci_triggers = [
        (r'(?i)check if .+ exists', "file existence check",
         '!`[ -f FILE ] && echo "exists" || echo "not found"`'),
        (r'(?i)read .+\.md', "file reading at start",
         '!`[ -f FILE ] && head -5 FILE || echo "not found"`'),
        (r'(?i)git status|git log|git branch', "git state discovery",
         '!`git status --short 2>/dev/null || echo "not a git repo"`'),
        (r'(?i)check (?:which |if )?(?:node|python|docker|terraform|npm|pnpm)', "tool version check",
         '!`command -v TOOL 2>/dev/null && TOOL --version 2>/dev/null || echo "not installed"`'),
    ]

    for pattern, desc, example in dci_triggers:
        if re.search(pattern, body):
            infos.append(
                f"[advisor] Skill performs {desc} — consider DCI to auto-detect at activation: "
                f"`{example}`"
            )
            break  # One suggestion is enough

    return infos


def validate_skill(path: Path, tier: str = TIER_STANDARD) -> Dict[str, Any]:
    """
    Validate a single SKILL.md file.
    Returns dict with errors, warnings, infos, and metadata.
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
    infos: List[str] = []

    # Frontmatter size budget (local, per-file)
    m = RE_FRONTMATTER.match(content)
    if m:
        front_str, _body = m.groups()
        front_len = len(front_str)
        if front_len > 15_000:
            errors.append(f"[frontmatter] Frontmatter is {front_len} chars (max 15000)")
        elif front_len >= 12_000:
            warnings.append(f"[frontmatter] Frontmatter is {front_len} chars (warn at 12000)")

    # Validate frontmatter
    fm_errors, fm_warnings, fm_infos = validate_frontmatter(path, fm, tier)
    errors.extend(fm_errors)
    warnings.extend(fm_warnings)
    infos.extend(fm_infos)

    # Validate body
    body_errors, body_warnings, body_infos = validate_body(path, body, tier, fm)
    errors.extend(body_errors)
    warnings.extend(body_warnings)
    infos.extend(body_infos)

    # Validate scripts
    script_errors, script_warnings = validate_scripts_exist(path, body)
    errors.extend(script_errors)
    warnings.extend(script_warnings)

    # Validate referenced resources/templates
    resource_errors, resource_warnings = validate_resource_files_exist(path, body)
    errors.extend(resource_errors)
    warnings.extend(resource_warnings)

    # Validate relative markdown links (Anthropic-recommended pattern)
    link_errors, link_warnings = validate_relative_links(path, body)
    errors.extend(link_errors)
    warnings.extend(link_warnings)

    # === CONTENT QUALITY VALIDATION (Hightower feedback) ===
    # Validate files listed in references/README.md and assets/README.md actually exist
    readme_errors, readme_warnings = validate_references_readme(path)
    errors.extend(readme_errors)
    warnings.extend(readme_warnings)

    # Detect stub Python scripts
    stub_errors, stub_warnings = detect_stub_scripts(path)
    errors.extend(stub_errors)
    warnings.extend(stub_warnings)

    # Detect placeholder text (REPLACE_ME, {variable}, etc.)
    placeholder_errors, placeholder_warnings = detect_placeholder_text(path)
    errors.extend(placeholder_errors)
    warnings.extend(placeholder_warnings)

    # Detect generic boilerplate
    boilerplate_errors, boilerplate_warnings = detect_boilerplate(path)
    errors.extend(boilerplate_errors)
    warnings.extend(boilerplate_warnings)

    # === STRUCTURAL ADVISORS (enterprise tier only) ===
    if tier == TIER_ENTERPRISE:
        infos.extend(advise_split_to_commands(path, body))
        infos.extend(advise_offload_to_references(path, body))
        infos.extend(advise_dci_opportunities(path, body))

    description = str(fm.get("description") or "")

    # Calculate Intent Solutions grade
    grade_result = grade_skill(path, body, fm)

    return {
        'errors': errors,
        'warnings': warnings,
        'infos': infos,
        'word_count': estimate_word_count(content),
        'line_count': len(body.splitlines()),
        'description_length': len(description),
        'grade': grade_result,
    }


# === MAIN ===

def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-file OK lines and grades")
    parser.add_argument(
        "--standard",
        action="store_true",
        help="Use standard tier (Anthropic spec only, no required fields). This is the default.",
    )
    parser.add_argument(
        "--enterprise",
        action="store_true",
        help="Use enterprise tier (Intent Solutions marketplace, 100-point rubric). Auto-enabled in CI.",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Treat warnings as errors (enterprise strict mode).",
    )
    parser.add_argument(
        "--check-description-budget",
        action="store_true",
        help="Warn if total skill description chars exceed token budget guidance.",
    )
    parser.add_argument(
        "--min-grade",
        type=str,
        default=None,
        choices=['A', 'B', 'C', 'D'],
        help="Fail if any skill scores below this grade (e.g., --min-grade B)",
    )
    parser.add_argument(
        "--show-low-grades",
        action="store_true",
        help="Show skills with D or F grades even without verbose mode",
    )
    parser.add_argument(
        "--skills-only",
        action="store_true",
        help="Only validate SKILL.md files",
    )
    parser.add_argument(
        "--commands-only",
        action="store_true",
        help="Only validate command files",
    )
    parser.add_argument(
        "--agents-only",
        action="store_true",
        help="Only validate agent files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON with per-skill scoring data",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to a single SKILL.md file to validate (optional)",
    )
    args, _unknown = parser.parse_known_args()
    verbose = args.verbose

    # Determine validation tier
    # Priority: explicit flag > auto-detect > default (standard)
    if args.enterprise and args.standard:
        print("ERROR: Cannot use both --standard and --enterprise", file=sys.stderr)
        return 1
    elif args.enterprise:
        tier = TIER_ENTERPRISE
    elif args.standard:
        tier = TIER_STANDARD
    elif os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true':
        tier = TIER_ENTERPRISE  # Auto-detect CI
    else:
        tier = TIER_STANDARD

    # Single-file mode: validate just one SKILL.md
    if args.path:
        target = Path(args.path).resolve()
        if not target.exists():
            print(f"ERROR: File not found: {args.path}", file=sys.stderr)
            return 1
        if target.name != 'SKILL.md' and not target.name.endswith('.md'):
            print(f"ERROR: Expected a SKILL.md or .md file: {args.path}", file=sys.stderr)
            return 1

        print(f"🔍 CLAUDE CODE PLUGIN VALIDATOR v4.0 ({tier} tier)")
        print(f"   Single-file mode: {target}")
        print(f"{'=' * 70}\n")

        if target.name == 'SKILL.md':
            result = validate_skill(target, tier)
            if 'fatal' in result:
                print(f"❌ FATAL: {result['fatal']}")
                return 1

            grade_info = result.get('grade', {})
            score = grade_info.get('score', 0)
            letter = grade_info.get('grade', 'F')

            if result['errors']:
                for error in result['errors']:
                    print(f"   ERROR: {error}")
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"   WARN: {warning}")
            if result.get('infos'):
                for info in result['infos']:
                    print(f"   INFO: {info}")

            # Always show grade in single-file mode
            print(f"\n{'=' * 70}")
            print(f"📊 GRADE: {letter} ({score}/100)")
            print(f"{'=' * 70}")
            breakdown = grade_info.get('breakdown', {})
            for pillar_name, pillar_data in breakdown.items():
                if pillar_name == 'modifiers':
                    mod_score = pillar_data.get('score', 0)
                    print(f"  {'Modifiers':<30} {mod_score:+d}")
                    for item_name, (pts, note) in pillar_data.get('items', {}).items():
                        print(f"    {item_name:<28} {pts:+d} - {note}")
                else:
                    pil_score = pillar_data.get('score', 0)
                    pil_max = pillar_data.get('max', 0)
                    print(f"  {pillar_name.replace('_', ' ').title():<30} {pil_score}/{pil_max}")
                    for item_name, (pts, note) in pillar_data.get('breakdown', {}).items():
                        print(f"    {item_name:<28} {pts} - {note}")
            print(f"{'=' * 70}")

            return 1 if result['errors'] else 0
        else:
            # Command or agent file
            if '/commands/' in str(target):
                result = validate_command(target)
            elif '/agents/' in str(target):
                result = validate_agent(target)
            else:
                print(f"Cannot determine file type for: {target}")
                print("File must be in a commands/ or agents/ directory, or named SKILL.md")
                return 1

            if 'fatal' in result:
                print(f"❌ FATAL: {result['fatal']}")
                return 1
            if result.get('errors'):
                for error in result['errors']:
                    print(f"   ERROR: {error}")
                return 1
            if result.get('warnings'):
                for warning in result['warnings']:
                    print(f"   WARN: {warning}")
            print(f"\n✅ Validation passed")
            return 0

    # Determine what to validate
    validate_skills = not args.commands_only and not args.agents_only
    validate_commands = not args.skills_only and not args.agents_only
    validate_agents = not args.skills_only and not args.commands_only

    # Find files based on what we're validating
    skills = find_skill_files(repo_root) if validate_skills else []
    commands = find_command_files(repo_root) if validate_commands else []
    agents = find_agent_files(repo_root) if validate_agents else []

    total_files = len(skills) + len(commands) + len(agents)
    if total_files == 0:
        print("No files found to validate.")
        return 0

    if not args.json:
        print(f"🔍 CLAUDE CODE PLUGIN VALIDATOR v4.0 ({tier} tier)")
        if tier == TIER_ENTERPRISE:
            print(f"   Intent Solutions Standard (100-Point Grading)")
        else:
            print(f"   Anthropic Spec Standard (no required fields)")
        print(f"{'=' * 70}\n")
        if validate_skills:
            print(f"Found {len(skills)} SKILL.md files")
        if validate_commands:
            print(f"Found {len(commands)} command files")
        if validate_agents:
            print(f"Found {len(agents)} agent files")
        print()

    total_errors = 0
    total_warnings = 0
    total_description_chars = 0
    files_with_errors = []
    files_with_warnings = []
    files_compliant = []

    # Grade tracking
    grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    grade_scores = []  # For average calculation
    low_grade_skills = []  # Skills with D or F
    below_min_grade = []  # Skills below --min-grade threshold

    grade_thresholds = {'A': 90, 'B': 80, 'C': 70, 'D': 60}
    json_skill_results = []  # Collected for --json output

    for skill in skills:
        rel = skill.relative_to(repo_root)
        result = validate_skill(skill, tier)

        if 'fatal' in result:
            if not args.json:
                print(f"❌ {rel}: FATAL - {result['fatal']}")
            total_errors += 1
            files_with_errors.append(str(rel))
            json_skill_results.append({
                'path': str(rel),
                'fatal': result['fatal'],
            })
            continue

        has_issues = False

        # Track grade
        grade_info = result.get('grade', {})
        score = grade_info.get('score', 0)
        letter = grade_info.get('grade', 'F')
        grade_counts[letter] += 1
        grade_scores.append(score)

        json_skill_results.append({
            'path': str(rel),
            'score': score,
            'grade': letter,
            'errors': len(result.get('errors', [])),
            'warnings': len(result.get('warnings', [])),
        })

        # Check min-grade threshold
        if args.min_grade:
            min_threshold = grade_thresholds.get(args.min_grade, 0)
            if score < min_threshold:
                below_min_grade.append((str(rel), score, letter))

        # Track low grades
        if letter in ['D', 'F']:
            low_grade_skills.append((str(rel), score, letter, grade_info.get('breakdown', {})))

        if result['errors']:
            if not args.json:
                print(f"❌ {rel}:")
                for error in result['errors']:
                    print(f"   ERROR: {error}")
            total_errors += len(result['errors'])
            files_with_errors.append(str(rel))
            has_issues = True

        if result['warnings']:
            if not args.json:
                if not has_issues:
                    print(f"⚠️  {rel}:")
                for warning in result['warnings']:
                    print(f"   WARN: {warning}")
            total_warnings += len(result['warnings'])
            if str(rel) not in files_with_errors:
                files_with_warnings.append(str(rel))
            has_issues = True

        if result.get('infos') and verbose and not args.json:
            if not has_issues:
                print(f"💡 {rel}:")
            for info in result['infos']:
                print(f"   INFO: {info}")

        if verbose and not has_issues and not result.get('infos') and not args.json:
            print(f"✅ {rel} - {letter} ({score}/100) ({result['word_count']} words, {result['line_count']} lines)")

        if not result['errors'] and not result['warnings']:
            files_compliant.append(str(rel))

        total_description_chars += int(result.get("description_length") or 0)

    # JSON output mode: emit machine-readable results and exit
    if args.json:
        print(json_module.dumps(json_skill_results))
        return 0

    # Validate commands
    for cmd in commands:
        rel = cmd.relative_to(repo_root)
        result = validate_command(cmd)

        if 'fatal' in result:
            print(f"❌ {rel} (command): FATAL - {result['fatal']}")
            total_errors += 1
            files_with_errors.append(str(rel))
            continue

        if result['errors']:
            print(f"❌ {rel} (command):")
            for error in result['errors']:
                print(f"   ERROR: {error}")
            total_errors += len(result['errors'])
            files_with_errors.append(str(rel))
        elif result['warnings']:
            print(f"⚠️  {rel} (command):")
            for warning in result['warnings']:
                print(f"   WARN: {warning}")
            total_warnings += len(result['warnings'])
            files_with_warnings.append(str(rel))
        else:
            files_compliant.append(str(rel))
            if verbose:
                print(f"✅ {rel} (command) - OK")

    # Validate agents
    for agent in agents:
        rel = agent.relative_to(repo_root)
        result = validate_agent(agent)

        if 'fatal' in result:
            print(f"❌ {rel} (agent): FATAL - {result['fatal']}")
            total_errors += 1
            files_with_errors.append(str(rel))
            continue

        if result['errors']:
            print(f"❌ {rel} (agent):")
            for error in result['errors']:
                print(f"   ERROR: {error}")
            total_errors += len(result['errors'])
            files_with_errors.append(str(rel))
        elif result['warnings']:
            print(f"⚠️  {rel} (agent):")
            for warning in result['warnings']:
                print(f"   WARN: {warning}")
            total_warnings += len(result['warnings'])
            files_with_warnings.append(str(rel))
        else:
            files_compliant.append(str(rel))
            if verbose:
                print(f"✅ {rel} (agent) - OK")

    # Show low grade skills if requested
    if args.show_low_grades and low_grade_skills:
        print(f"\n{'=' * 70}")
        print(f"📉 LOW GRADE SKILLS (D or F)")
        print(f"{'=' * 70}")
        for path, score, letter, breakdown in low_grade_skills:
            print(f"\n{letter} ({score}/100): {path}")
            if 'progressive_disclosure' in breakdown:
                pda = breakdown['progressive_disclosure']
                print(f"   PDA: {pda['score']}/{pda['max']}")
                for key, (pts, note) in pda.get('breakdown', {}).items():
                    print(f"      {key}: {pts} pts - {note}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    total_validated = len(skills) + len(commands) + len(agents)
    if skills:
        print(f"Skills validated: {len(skills)}")
    if commands:
        print(f"Commands validated: {len(commands)}")
    if agents:
        print(f"Agents validated: {len(agents)}")
    print(f"Total files: {total_validated}")
    print(f"✅ Fully compliant: {len(files_compliant)}")
    print(f"⚠️  Warnings only: {len(files_with_warnings)}")
    print(f"❌ With errors: {len(files_with_errors)}")
    print(f"{'=' * 70}")

    # Compliance rate
    compliant_pct = (len(files_compliant) / total_validated * 100) if total_validated else 0
    print(f"\n📈 Compliance rate: {compliant_pct:.1f}%")

    # Grade Distribution
    print(f"\n{'=' * 70}")
    print(f"📊 INTENT SOLUTIONS GRADE REPORT")
    print(f"{'=' * 70}")

    avg_score = sum(grade_scores) / len(grade_scores) if grade_scores else 0
    avg_grade = calculate_grade(int(avg_score))
    print(f"Average Score: {avg_score:.1f}/100 ({avg_grade})")
    print()
    print("Grade Distribution:")
    for letter in ['A', 'B', 'C', 'D', 'F']:
        count = grade_counts[letter]
        pct = (count / len(skills) * 100) if skills else 0
        bar = '█' * int(pct / 2)
        emoji = {'A': '🏆', 'B': '✅', 'C': '⚠️', 'D': '📉', 'F': '❌'}[letter]
        print(f"  {emoji} {letter}: {count:4d} ({pct:5.1f}%) {bar}")

    # Quality metrics
    print()
    a_b_count = grade_counts['A'] + grade_counts['B']
    a_b_pct = (a_b_count / len(skills) * 100) if skills else 0
    print(f"Production Ready (A+B): {a_b_count} ({a_b_pct:.1f}%)")

    d_f_count = grade_counts['D'] + grade_counts['F']
    d_f_pct = (d_f_count / len(skills) * 100) if skills else 0
    print(f"Needs Work (D+F): {d_f_count} ({d_f_pct:.1f}%)")

    print(f"{'=' * 70}")

    if args.check_description_budget and total_description_chars >= TOTAL_DESCRIPTION_BUDGET_WARN:
        msg = (
            f"\n⚠️  Skill description budget: {total_description_chars} chars "
            f"(warn at {TOTAL_DESCRIPTION_BUDGET_WARN}, cap {TOTAL_DESCRIPTION_BUDGET_ERROR})"
        )
        print(msg)
        total_warnings += 1

    # Check min-grade violations
    if args.min_grade and below_min_grade:
        print(f"\n❌ {len(below_min_grade)} skill(s) below minimum grade {args.min_grade}:")
        for path, score, letter in below_min_grade[:10]:  # Show first 10
            print(f"   {letter} ({score}/100): {path}")
        if len(below_min_grade) > 10:
            print(f"   ... and {len(below_min_grade) - 10} more")
        return 1

    if total_errors > 0:
        print(f"\n❌ Validation FAILED with {total_errors} errors ({tier} tier)")
        if tier == TIER_ENTERPRISE:
            print("\nTo fix: Address errors above. Enterprise fields are now warnings, not errors.")
            print("Use --standard for Anthropic-spec-only validation (no required fields).")
        return 1
    elif total_warnings > 0 and args.fail_on_warn:
        print(f"\n❌ Validation FAILED due to {total_warnings} warning(s) (--fail-on-warn)")
        return 1
    elif total_warnings > 0:
        print(f"\n⚠️  Validation PASSED with {total_warnings} warnings ({tier} tier)")
        print("(Warnings are best practices - not blocking)")
        return 0
    else:
        print(f"\n✅ All skills fully compliant! ({tier} tier)")
        if tier == TIER_ENTERPRISE:
            print("   - Anthropic 2026 spec ✓")
            print("   - Intent Solutions standard ✓")
            print("   - 100-point grading ✓")
        else:
            print("   - Anthropic 2026 spec ✓")
        return 0


if __name__ == '__main__':
    sys.exit(main())
