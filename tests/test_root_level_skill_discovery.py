"""Regression tests for root-level SKILL.md discovery in the batch validator.

Covers the bug where `find_skill_files` and `validate_plugin` only walked the
legacy `plugins/<cat>/<name>/skills/<name>/SKILL.md` layout and missed the
Anthropic-spec layout where SKILL.md sits at the plugin root.

Bead: claude-guna. Audit: 000-docs/266. Decision: 000-docs/267.
"""

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import importlib.util

VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "validate-skills-schema.py"
)
spec = importlib.util.spec_from_file_location("validate_skills_schema", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


FIXTURE_SRC = Path(__file__).parent / "fixtures" / "root-level-skill-plugin"


def _stage_plugin(repo_root: Path, category: str, name: str) -> Path:
    """Copy the fixture into a synthetic plugins/<category>/<name>/ dir."""
    dest = repo_root / "plugins" / category / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURE_SRC, dest)
    return dest


def test_find_skill_files_picks_up_root_level_skill_md(tmp_path):
    """Root-level SKILL.md (Anthropic-spec layout) must appear in batch walk."""
    plugin_dir = _stage_plugin(tmp_path, "design", "fixture-root-level")
    expected = plugin_dir / "SKILL.md"

    results = validator.find_skill_files(tmp_path)

    assert expected in results, (
        f"find_skill_files missed root-level SKILL.md.\n"
        f"  expected: {expected}\n"
        f"  got: {results}"
    )


def test_find_skill_files_dedupes_when_both_layouts_present(tmp_path):
    """If a plugin has both root SKILL.md and skills/<name>/SKILL.md, no duplicates."""
    plugin_dir = _stage_plugin(tmp_path, "design", "fixture-both-layouts")
    nested_skill = plugin_dir / "skills" / "nested" / "SKILL.md"
    nested_skill.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(plugin_dir / "SKILL.md", nested_skill)

    results = validator.find_skill_files(tmp_path)
    resolved = [p.resolve() for p in results]

    assert len(resolved) == len(set(resolved)), (
        f"find_skill_files produced duplicates: {resolved}"
    )
    assert len(results) == 2, (
        f"expected 2 distinct SKILL.md files (root + nested), got {len(results)}: {results}"
    )


def test_find_skill_files_still_picks_up_legacy_nested_layout(tmp_path):
    """Regression: legacy skills/<name>/SKILL.md layout must keep working."""
    plugin_dir = tmp_path / "plugins" / "design" / "fixture-nested-only"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / ".claude-plugin").mkdir()
    shutil.copy(
        FIXTURE_SRC / ".claude-plugin" / "plugin.json",
        plugin_dir / ".claude-plugin" / "plugin.json",
    )
    nested = plugin_dir / "skills" / "thing" / "SKILL.md"
    nested.parent.mkdir(parents=True)
    shutil.copy(FIXTURE_SRC / "SKILL.md", nested)

    results = validator.find_skill_files(tmp_path)

    assert nested in results, f"legacy nested SKILL.md missed: {nested} not in {results}"


def test_validate_plugin_counts_root_level_skill(tmp_path):
    """validate_plugin must count root-level SKILL.md (Skills: 1, not 0)."""
    plugin_dir = _stage_plugin(tmp_path, "design", "fixture-validate-plugin")

    result = validator.validate_plugin(plugin_dir, tier=validator.TIER_MARKETPLACE)

    assert result.get("skill_count") == 1, (
        f"expected 1 skill from root-level SKILL.md, got {result.get('skill_count')}; "
        f"full result keys: {list(result.keys())}"
    )
