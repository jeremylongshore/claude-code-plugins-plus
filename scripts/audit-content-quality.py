#!/usr/bin/env python3
"""
Content Quality Audit for Claude Code Plugins
Detects boilerplate, duplicates, stub content, and empty shells across all plugins.

Report-only — no auto-fix. Complements validate-skills-schema.py (structural validation)
with deeper content-quality analysis.

Usage:
    python3 scripts/audit-content-quality.py                       # Full audit, text report
    python3 scripts/audit-content-quality.py --json                # JSON output
    python3 scripts/audit-content-quality.py --severity CRITICAL   # Only worst offenders
    python3 scripts/audit-content-quality.py --top 20              # Top 20 worst
    python3 scripts/audit-content-quality.py --summary-only        # Dashboard only
    python3 scripts/audit-content-quality.py --category saas-packs # Single category

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ─── Constants ───────────────────────────────────────────────────────────────

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_LABELS = list(SEVERITY_ORDER.keys())

RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
CODE_FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")
HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s+")

EXCLUDED_DIRS = {
    "archive", "backups", "backup", ".git", "node_modules",
    "__pycache__", ".venv", "010-archive", "002-workspaces",
    "templates", "examples",
}

# ─── Boilerplate patterns ────────────────────────────────────────────────────

# CRITICAL: Exact template boilerplate (openrouter-pack and similar saas-packs)
BOILERPLATE_CRITICAL = [
    # 5-step generic instructions block
    re.compile(
        r"Follow these steps to implement this skill:\s*\n"
        r"\s*1\.\s+\*\*Verify Prerequisites\*\*.*?Ensure all prerequisites",
        re.DOTALL,
    ),
    # Generic output section
    re.compile(
        r"Successful execution produces:\s*\n"
        r"[-*]\s*Working .+ integration\s*\n"
        r"[-*]\s*Verified API connectivity\s*\n"
        r"[-*]\s*Example responses demonstrating functionality",
    ),
]

# HIGH: Generic template language
BOILERPLATE_HIGH = [
    re.compile(r"Follow these steps to implement this skill", re.IGNORECASE),
    re.compile(r"Verify Prerequisites.*Ensure all prerequisites listed above are met", re.IGNORECASE | re.DOTALL),
    re.compile(r"Review the Implementation.*Study the code examples", re.IGNORECASE | re.DOTALL),
    re.compile(r"Adapt to Your Environment.*Modify configuration values", re.IGNORECASE | re.DOTALL),
    re.compile(r"Test the Integration.*Run the verification steps", re.IGNORECASE | re.DOTALL),
    re.compile(r"Monitor in Production.*Set up appropriate logging", re.IGNORECASE | re.DOTALL),
    re.compile(r"This skill provides automated assistance for", re.IGNORECASE),
    re.compile(r"This skill enables Claude to", re.IGNORECASE),
]

# ─── Reference placeholder patterns ─────────────────────────────────────────

REFERENCE_PLACEHOLDER_CRITICAL = [
    re.compile(r"Example usage patterns will be demonstrated in context", re.IGNORECASE),
    re.compile(r"See code examples in sections above for complete,?\s*runnable implementations", re.IGNORECASE),
]

REFERENCE_PLACEHOLDER_HIGH = [
    re.compile(r"^#\s+\w+\s*$", re.MULTILINE),  # heading-only file (caught by length check too)
    re.compile(r"Refer to the main SKILL\.md for", re.IGNORECASE),
    re.compile(r"\bTODO\b:?\s*(add|write|fill|complete)", re.IGNORECASE),
]

# ─── Stub script patterns ────────────────────────────────────────────────────

STUB_PYTHON_PATTERNS = [
    re.compile(r"^\s*pass\s*$", re.MULTILINE),
    re.compile(r'^\s*print\(["\'](?:hello|test|placeholder|TODO)', re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*raise NotImplementedError", re.MULTILINE),
    re.compile(r'^\s*"""TODO', re.MULTILINE),
]

STUB_BASH_PATTERNS = [
    re.compile(r"^\s*echo\s+['\"](?:hello|test|placeholder|TODO)", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*exit\s+0\s*$", re.MULTILINE),
]

STUB_JS_PATTERNS = [
    re.compile(r"^\s*console\.log\(['\"](?:hello|test|placeholder|TODO)", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*throw new Error\(['\"]not implemented", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*// TODO", re.MULTILINE),
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """Parse YAML frontmatter, return (frontmatter_dict, body_text)."""
    m = RE_FRONTMATTER.match(content)
    if not m:
        return {}, content
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, content
    if not isinstance(data, dict):
        return {}, content
    return data, m.group(2)


def strip_code_fences(text: str) -> str:
    """Remove fenced code blocks from text."""
    lines = text.splitlines()
    result = []
    in_fence = False
    for line in lines:
        if CODE_FENCE_PATTERN.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            result.append(line)
    return "\n".join(result)


def strip_headings(text: str) -> str:
    """Remove markdown headings."""
    return "\n".join(
        line for line in text.splitlines()
        if not HEADING_PATTERN.match(line)
    )


def prose_word_count(text: str) -> int:
    """Count prose words after stripping code fences and headings."""
    cleaned = strip_code_fences(text)
    cleaned = strip_headings(cleaned)
    # Also strip list markers and blank lines
    words = cleaned.split()
    return len(words)


def extract_sections(body: str) -> Dict[str, str]:
    """Extract markdown sections by heading. Returns {heading: content}."""
    sections: Dict[str, str] = {}
    current_heading = "__preamble__"
    current_lines: List[str] = []

    for line in body.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = heading_match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_heading] = "\n".join(current_lines).strip()
    return sections


def normalize_whitespace(text: str) -> str:
    """Collapse whitespace for comparison."""
    return re.sub(r"\s+", " ", text).strip().lower()


def hash_body_sections(body: str) -> str:
    """Hash the body sections after Overview (sections 3-7ish) for duplicate detection."""
    sections = extract_sections(body)
    # Skip preamble and Overview — hash the instructional core
    skip_headings = {"__preamble__", "Overview"}
    parts = []
    for heading, content in sections.items():
        if heading not in skip_headings:
            parts.append(normalize_whitespace(content))
    combined = "|".join(parts)
    return hashlib.md5(combined.encode()).hexdigest()


def trigram_set(text: str) -> Set[str]:
    """Generate character trigram set for near-duplicate detection."""
    normalized = normalize_whitespace(text)
    if len(normalized) < 3:
        return set()
    return {normalized[i:i+3] for i in range(len(normalized) - 2)}


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def find_skill_files(root: Path, category: Optional[str] = None) -> List[Path]:
    """Find all SKILL.md files."""
    results = []
    plugins_dir = root / "plugins"
    if not plugins_dir.exists():
        return results

    if category:
        search_dir = plugins_dir / category
        if not search_dir.exists():
            return results
        for p in search_dir.rglob("skills/*/SKILL.md"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    else:
        for p in plugins_dir.rglob("skills/*/SKILL.md"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    return sorted(results)


def find_reference_files(root: Path, category: Optional[str] = None) -> List[Path]:
    """Find all reference files under skills/*/references/."""
    results = []
    plugins_dir = root / "plugins"
    if not plugins_dir.exists():
        return results

    if category:
        search_dir = plugins_dir / category
        if not search_dir.exists():
            return results
        for p in search_dir.rglob("skills/*/references/*"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    else:
        for p in plugins_dir.rglob("skills/*/references/*"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    return sorted(results)


def find_script_files(root: Path, category: Optional[str] = None) -> List[Path]:
    """Find all script files under skills/*/scripts/."""
    results = []
    plugins_dir = root / "plugins"
    if not plugins_dir.exists():
        return results

    if category:
        search_dir = plugins_dir / category
        if not search_dir.exists():
            return results
        for p in search_dir.rglob("skills/*/scripts/*"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    else:
        for p in plugins_dir.rglob("skills/*/scripts/*"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    return sorted(results)


def find_command_files(root: Path, category: Optional[str] = None) -> List[Path]:
    """Find all command markdown files."""
    results = []
    plugins_dir = root / "plugins"
    if not plugins_dir.exists():
        return results

    if category:
        search_dir = plugins_dir / category
        if not search_dir.exists():
            return results
        for p in search_dir.rglob("commands/*.md"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    else:
        for p in plugins_dir.rglob("commands/*.md"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    return sorted(results)


def find_agent_files(root: Path, category: Optional[str] = None) -> List[Path]:
    """Find all agent markdown files."""
    results = []
    plugins_dir = root / "plugins"
    if not plugins_dir.exists():
        return results

    if category:
        search_dir = plugins_dir / category
        if not search_dir.exists():
            return results
        for p in search_dir.rglob("agents/*.md"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    else:
        for p in plugins_dir.rglob("agents/*.md"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p)
    return sorted(results)


def find_plugin_dirs(root: Path, category: Optional[str] = None) -> List[Path]:
    """Find all plugin directories (those with .claude-plugin/plugin.json)."""
    results = []
    plugins_dir = root / "plugins"
    if not plugins_dir.exists():
        return results

    if category:
        search_dir = plugins_dir / category
        if not search_dir.exists():
            return results
        for p in search_dir.rglob(".claude-plugin/plugin.json"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p.parent.parent)
    else:
        for p in plugins_dir.rglob(".claude-plugin/plugin.json"):
            if p.is_file() and not _is_excluded(p, root):
                results.append(p.parent.parent)
    return sorted(set(results))


def _is_excluded(path: Path, root: Path) -> bool:
    """Check if a path is in an excluded directory."""
    parts = path.relative_to(root).parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    if any(part.startswith("skills-backup-") for part in parts):
        return True
    return False


def get_plugin_pack(path: Path, root: Path) -> Optional[str]:
    """Extract the plugin pack name from a path (e.g. 'openrouter-pack')."""
    try:
        rel = path.relative_to(root / "plugins")
    except ValueError:
        return None
    parts = rel.parts
    # plugins/<category>/<pack-name>/skills/<skill>/SKILL.md
    if len(parts) >= 2:
        return parts[1]  # pack name
    return None


# ─── Finding dataclass ──────────────────────────────────────────────────────

class Finding:
    """A single audit finding."""

    def __init__(self, path: Path, check: str, severity: str, message: str,
                 detail: str = "", context: str = ""):
        self.path = path
        self.check = check
        self.severity = severity
        self.message = message
        self.detail = detail
        self.context = context  # e.g. "skill", "reference", "script", "plugin"

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "path": str(self.path),
            "check": self.check,
            "severity": self.severity,
            "message": self.message,
        }
        if self.detail:
            d["detail"] = self.detail
        if self.context:
            d["context"] = self.context
        return d

    def sort_key(self) -> Tuple[int, str, str]:
        return (SEVERITY_ORDER.get(self.severity, 99), self.check, str(self.path))


# ─── Check 1: Body Substance ────────────────────────────────────────────────

def check_body_substance(root: Path, skill_files: List[Path]) -> List[Finding]:
    """Check SKILL.md files for minimal prose content."""
    findings = []
    for path in skill_files:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        _, body = parse_frontmatter(content)
        wc = prose_word_count(body)

        if wc < 50:
            findings.append(Finding(
                path.relative_to(root), "body-substance", "CRITICAL",
                f"Skill body has only {wc} prose words (minimum: 50)",
                context="skill",
            ))
        elif wc < 100:
            findings.append(Finding(
                path.relative_to(root), "body-substance", "HIGH",
                f"Skill body has only {wc} prose words (recommended: 100+)",
                context="skill",
            ))
    return findings


# ─── Check 2: Section Emptiness ──────────────────────────────────────────────

def check_section_emptiness(root: Path, skill_files: List[Path]) -> List[Finding]:
    """Check for top-level (##) sections with minimal real content.

    Only flags ## sections — sub-sections (###, ####) are naturally short.
    Reference pointers are LOW severity (legitimate progressive disclosure).
    """
    # Major sections we expect to have substance
    MAJOR_SECTIONS = {
        "overview", "instructions", "prerequisites", "output",
        "error handling", "examples", "resources",
    }
    findings = []
    for path in skill_files:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        _, body = parse_frontmatter(content)

        # Only extract ## headings (top-level sections), skip ### and deeper
        current_heading = None
        current_lines: List[str] = []
        sections: Dict[str, str] = {}

        for line in body.splitlines():
            m = re.match(r"^(##)\s+(.*)", line)  # Only ## level
            if m:
                if current_heading is not None:
                    sections[current_heading] = "\n".join(current_lines).strip()
                current_heading = m.group(2).strip()
                current_lines = []
            elif current_heading is not None:
                current_lines.append(line)
        if current_heading is not None:
            sections[current_heading] = "\n".join(current_lines).strip()

        for heading, section_content in sections.items():
            prose = strip_code_fences(section_content).strip()

            # Reference pointer → skip (this is valid progressive disclosure)
            if re.search(r"See `\$\{CLAUDE_SKILL_DIR\}", prose):
                continue

            heading_key = heading.lower().strip()
            is_major = heading_key in MAJOR_SECTIONS

            if len(prose) < 10 and is_major:
                findings.append(Finding(
                    path.relative_to(root), "section-emptiness", "HIGH",
                    f"Section '{heading}' is effectively empty ({len(prose)} chars)",
                    context="skill",
                ))
    return findings


# ─── Check 3: Boilerplate Detection ─────────────────────────────────────────

def check_boilerplate(root: Path, skill_files: List[Path]) -> List[Finding]:
    """Detect generic template boilerplate in SKILL.md files."""
    findings = []
    for path in skill_files:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        _, body = parse_frontmatter(content)

        # Critical boilerplate (exact template patterns)
        critical_matches = []
        for pattern in BOILERPLATE_CRITICAL:
            m = pattern.search(body)
            if m:
                snippet = m.group(0)[:60].replace("\n", " ").strip()
                critical_matches.append(f'"{snippet}..."')
        if critical_matches:
            findings.append(Finding(
                path.relative_to(root), "boilerplate", "CRITICAL",
                f"Contains template boilerplate ({len(critical_matches)} pattern(s))",
                detail="; ".join(critical_matches[:3]),
                context="skill",
            ))
            continue  # Don't double-report HIGH if already CRITICAL

        # High boilerplate (generic language)
        high_matches = []
        for pattern in BOILERPLATE_HIGH:
            m = pattern.search(body)
            if m:
                snippet = m.group(0)[:50].replace("\n", " ").strip()
                high_matches.append(f'"{snippet}"')
        if len(high_matches) >= 3:
            findings.append(Finding(
                path.relative_to(root), "boilerplate", "HIGH",
                f"Contains generic template language ({len(high_matches)} patterns)",
                detail="; ".join(high_matches[:2]),
                context="skill",
            ))
        elif len(high_matches) >= 1:
            findings.append(Finding(
                path.relative_to(root), "boilerplate", "MEDIUM",
                f"Contains some template language ({len(high_matches)} pattern(s))",
                detail="; ".join(high_matches[:2]),
                context="skill",
            ))
    return findings


# ─── Check 4: Duplicate Bodies ───────────────────────────────────────────────

def check_duplicate_bodies(root: Path, skill_files: List[Path]) -> List[Finding]:
    """Detect skills with identical body sections (hash-based + Jaccard near-duplicate)."""
    findings = []

    # --- Tier 1: Hash-based exact duplicate detection (O(n)) ---
    hash_groups: Dict[str, List[Path]] = defaultdict(list)
    body_cache: Dict[Path, str] = {}

    for path in skill_files:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        _, body = parse_frontmatter(content)
        body_cache[path] = body
        h = hash_body_sections(body)
        hash_groups[h].append(path)

    reported_paths: Set[Path] = set()
    for h, paths in hash_groups.items():
        if len(paths) >= 2:
            rel_paths = [p.relative_to(root) for p in paths]
            pack_name = get_plugin_pack(paths[0], root)
            group_label = f" (in {pack_name})" if pack_name else ""
            for path in paths:
                reported_paths.add(path)
                others = [str(r) for r in rel_paths if r != path.relative_to(root)]
                findings.append(Finding(
                    path.relative_to(root), "duplicate-body", "CRITICAL",
                    f"Identical body with {len(others)} other skill(s){group_label}",
                    detail=f"Duplicates: {', '.join(others[:5])}" + ("..." if len(others) > 5 else ""),
                    context="skill",
                ))

    # --- Tier 2: Jaccard near-duplicate detection (within same pack) ---
    pack_groups: Dict[str, List[Tuple[Path, Set[str]]]] = defaultdict(list)
    for path in skill_files:
        if path in reported_paths:
            continue
        body = body_cache.get(path)
        if body is None:
            continue
        pack = get_plugin_pack(path, root)
        if pack:
            sections = extract_sections(body)
            skip = {"__preamble__", "Overview"}
            combined = " ".join(
                normalize_whitespace(c) for h, c in sections.items() if h not in skip
            )
            tgrams = trigram_set(combined)
            if tgrams:
                pack_groups[pack].append((path, tgrams))

    for pack, items in pack_groups.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                sim = jaccard_similarity(items[i][1], items[j][1])
                if sim > 0.85:
                    path_a, path_b = items[i][0], items[j][0]
                    if path_a not in reported_paths:
                        reported_paths.add(path_a)
                        findings.append(Finding(
                            path_a.relative_to(root), "near-duplicate", "HIGH",
                            f"Near-duplicate body (Jaccard={sim:.2f}) with {path_b.relative_to(root)}",
                            detail=f"Within pack: {pack}",
                            context="skill",
                        ))
                    if path_b not in reported_paths:
                        reported_paths.add(path_b)
                        findings.append(Finding(
                            path_b.relative_to(root), "near-duplicate", "HIGH",
                            f"Near-duplicate body (Jaccard={sim:.2f}) with {path_a.relative_to(root)}",
                            detail=f"Within pack: {pack}",
                            context="skill",
                        ))

    return findings


# ─── Check 5: Reference File Stubs ──────────────────────────────────────────

def check_reference_stubs(root: Path, reference_files: List[Path]) -> List[Finding]:
    """Detect placeholder and stub reference files."""
    findings = []
    for path in reference_files:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        content_stripped = content.strip()
        if not content_stripped:
            findings.append(Finding(
                path.relative_to(root), "reference-stub", "CRITICAL",
                "Reference file is empty",
                context="reference",
            ))
            continue

        # Check critical placeholder patterns
        for pattern in REFERENCE_PLACEHOLDER_CRITICAL:
            if pattern.search(content):
                findings.append(Finding(
                    path.relative_to(root), "reference-stub", "CRITICAL",
                    "Reference file contains placeholder text",
                    detail=pattern.pattern[:60],
                    context="reference",
                ))
                break
        else:
            # Check high placeholder patterns
            for pattern in REFERENCE_PLACEHOLDER_HIGH:
                if pattern.search(content):
                    # Only flag heading-only if the file is very short
                    if pattern.pattern.startswith("^#"):
                        if len(content_stripped) < 50:
                            findings.append(Finding(
                                path.relative_to(root), "reference-stub", "HIGH",
                                "Reference file is heading-only or near-empty",
                                detail=f"{len(content_stripped)} chars total",
                                context="reference",
                            ))
                    else:
                        findings.append(Finding(
                            path.relative_to(root), "reference-stub", "HIGH",
                            "Reference file contains stub/TODO content",
                            detail=pattern.pattern[:50],
                            context="reference",
                        ))
                    break
            else:
                # Length check for very short reference files
                if len(content_stripped) < 50:
                    findings.append(Finding(
                        path.relative_to(root), "reference-stub", "HIGH",
                        f"Reference file too short ({len(content_stripped)} chars)",
                        context="reference",
                    ))

    return findings


# ─── Check 6: Stub Scripts ──────────────────────────────────────────────────

def check_stub_scripts(root: Path, script_files: List[Path]) -> List[Finding]:
    """Detect stub/placeholder scripts."""
    findings = []
    for path in script_files:
        # Exempt __init__.py — empty is idiomatic Python
        if path.name == "__init__.py":
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        suffix = path.suffix.lower()
        name = path.name.lower()

        # Determine file type and patterns
        patterns = []
        if suffix == ".py" or name.endswith(".py"):
            patterns = STUB_PYTHON_PATTERNS
        elif suffix in (".sh", ".bash") or name.endswith(".sh"):
            patterns = STUB_BASH_PATTERNS
        elif suffix in (".js", ".ts", ".mjs") or name.endswith((".js", ".ts")):
            patterns = STUB_JS_PATTERNS

        if not patterns:
            continue

        # Strip comments and blank lines for substance check
        lines = [
            l for l in content.splitlines()
            if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("//")
        ]
        # Exclude shebang
        lines = [l for l in lines if not l.startswith("#!")]

        # Exempt large scripts (>20 substantive lines) — clearly not stubs
        if len(lines) > 20:
            continue

        if len(lines) <= 2:
            findings.append(Finding(
                path.relative_to(root), "stub-script", "HIGH",
                f"Script has only {len(lines)} substantive line(s)",
                context="script",
            ))
            continue

        match_count = sum(1 for p in patterns if p.search(content))
        if match_count >= 2:
            findings.append(Finding(
                path.relative_to(root), "stub-script", "HIGH",
                f"Script matches {match_count} stub patterns",
                context="script",
            ))

    return findings


# ─── Check 7: Empty Shell Plugins ───────────────────────────────────────────

def check_empty_shells(root: Path, plugin_dirs: List[Path]) -> List[Finding]:
    """Detect plugins with plugin.json + README but no skills/commands/agents."""
    findings = []
    for plugin_dir in plugin_dirs:
        has_skills = list(plugin_dir.rglob("skills/*/SKILL.md"))
        has_commands = list(plugin_dir.rglob("commands/*.md"))
        has_agents = list(plugin_dir.rglob("agents/*.md"))

        # MCP plugins with src/ or servers/ are OK
        has_src = (plugin_dir / "src").exists()
        has_servers = (plugin_dir / "servers").exists()

        # Hooks-based plugins (e.g. prettier-markdown-hook) are OK
        has_hooks = (plugin_dir / "hooks").exists()

        if not has_skills and not has_commands and not has_agents and not has_src and not has_servers and not has_hooks:
            has_readme = (plugin_dir / "README.md").exists()
            has_plugin_json = (plugin_dir / ".claude-plugin" / "plugin.json").exists()
            if has_readme or has_plugin_json:
                findings.append(Finding(
                    plugin_dir.relative_to(root), "empty-shell", "CRITICAL",
                    "Plugin has plugin.json/README but no skills, commands, agents, or src/",
                    context="plugin",
                ))

    return findings


# ─── Report Formatting ──────────────────────────────────────────────────────

def format_text_report(findings: List[Finding], summary_only: bool = False) -> str:
    """Format findings as a human-readable text report."""
    lines: List[str] = []

    if not summary_only:
        # Group by severity
        by_severity: Dict[str, List[Finding]] = defaultdict(list)
        for f in findings:
            by_severity[f.severity].append(f)

        for sev in SEVERITY_LABELS:
            group = by_severity.get(sev, [])
            if not group:
                continue
            lines.append(f"\n{'=' * 72}")
            lines.append(f"  {sev} ({len(group)} findings)")
            lines.append(f"{'=' * 72}")

            # Group by check within severity
            by_check: Dict[str, List[Finding]] = defaultdict(list)
            for f in group:
                by_check[f.check].append(f)

            for check, check_findings in sorted(by_check.items()):
                lines.append(f"\n  [{check}] ({len(check_findings)} items)")
                lines.append(f"  {'-' * 50}")
                for f in check_findings:
                    lines.append(f"    {f.path}")
                    lines.append(f"      {f.message}")
                    if f.detail:
                        lines.append(f"      Detail: {f.detail}")

    # Summary dashboard
    lines.append(f"\n{'=' * 72}")
    lines.append("  SUMMARY DASHBOARD")
    lines.append(f"{'=' * 72}")

    # Count by context and severity
    contexts = ["skill", "reference", "script", "plugin"]
    context_labels = {"skill": "Skills", "reference": "References", "script": "Scripts", "plugin": "Plugins"}

    by_ctx_sev: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for f in findings:
        ctx = f.context or "other"
        by_ctx_sev[ctx][f.severity] += 1

    # Header
    header = f"  {'':20s}"
    for sev in SEVERITY_LABELS:
        header += f"  {sev:>8s}"
    header += f"  {'TOTAL':>8s}"
    lines.append(header)
    lines.append(f"  {'-' * 64}")

    for ctx in contexts:
        row = f"  {context_labels.get(ctx, ctx):20s}"
        total = 0
        for sev in SEVERITY_LABELS:
            count = by_ctx_sev[ctx][sev]
            total += count
            row += f"  {count:>8d}"
        row += f"  {total:>8d}"
        if total > 0:
            lines.append(row)

    # Grand total
    grand_total = len(findings)
    lines.append(f"  {'-' * 64}")
    grand_row = f"  {'TOTAL':20s}"
    for sev in SEVERITY_LABELS:
        sev_total = sum(1 for f in findings if f.severity == sev)
        grand_row += f"  {sev_total:>8d}"
    grand_row += f"  {grand_total:>8d}"
    lines.append(grand_row)

    return "\n".join(lines)


def format_json_report(findings: List[Finding]) -> str:
    """Format findings as JSON."""
    data = {
        "findings": [f.to_dict() for f in findings],
        "summary": {
            "total": len(findings),
            "by_severity": {},
            "by_check": {},
        },
    }
    for sev in SEVERITY_LABELS:
        data["summary"]["by_severity"][sev] = sum(1 for f in findings if f.severity == sev)
    checks: Dict[str, int] = defaultdict(int)
    for f in findings:
        checks[f.check] += 1
    data["summary"]["by_check"] = dict(sorted(checks.items()))

    return json.dumps(data, indent=2)


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Content quality audit for Claude Code plugins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--severity", choices=SEVERITY_LABELS, help="Filter by minimum severity")
    parser.add_argument("--top", type=int, help="Show only top N findings")
    parser.add_argument("--summary-only", action="store_true", help="Show only summary dashboard")
    parser.add_argument("--category", type=str, help="Audit single plugin category")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    plugins_dir = root / "plugins"
    if not plugins_dir.exists():
        print(f"ERROR: plugins directory not found at {plugins_dir}", file=sys.stderr)
        return 1

    # Discover files
    if args.verbose:
        print("Discovering files...", file=sys.stderr)

    skill_files = find_skill_files(root, args.category)
    reference_files = find_reference_files(root, args.category)
    script_files = find_script_files(root, args.category)
    plugin_dirs = find_plugin_dirs(root, args.category)

    if args.verbose:
        print(
            f"Found: {len(skill_files)} skills, {len(reference_files)} references, "
            f"{len(script_files)} scripts, {len(plugin_dirs)} plugins",
            file=sys.stderr,
        )

    # Run all checks
    findings: List[Finding] = []

    if args.verbose:
        print("Running checks...", file=sys.stderr)

    findings.extend(check_body_substance(root, skill_files))
    findings.extend(check_section_emptiness(root, skill_files))
    findings.extend(check_boilerplate(root, skill_files))
    findings.extend(check_duplicate_bodies(root, skill_files))
    findings.extend(check_reference_stubs(root, reference_files))
    findings.extend(check_stub_scripts(root, script_files))
    findings.extend(check_empty_shells(root, plugin_dirs))

    # Apply filters
    if args.severity:
        max_sev = SEVERITY_ORDER[args.severity]
        findings = [f for f in findings if SEVERITY_ORDER.get(f.severity, 99) <= max_sev]

    # Sort: severity first, then check name, then path
    findings.sort(key=lambda f: f.sort_key())

    if args.top:
        findings = findings[:args.top]

    # Output
    if args.json:
        print(format_json_report(findings))
    else:
        if not args.summary_only:
            print(f"CONTENT QUALITY AUDIT")
            print(f"Found: {len(skill_files)} skills, {len(reference_files)} references, "
                  f"{len(script_files)} scripts, {len(plugin_dirs)} plugins")
        print(format_text_report(findings, summary_only=args.summary_only))

    # Exit code: 0 for clean, 1 for CRITICAL findings
    critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
