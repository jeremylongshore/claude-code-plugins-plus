"""Regression tests for scripts/validate-skills-schema.py frontmatter checks.

Covers review findings f-ccp-validator-1 and f-ccp-validator-2 (2026-06-11):

  * f-ccp-validator-1 — validate_tool_permission always returned True and the
    caller dropped its diagnostic messages, so malformed or misspelled
    allowed-tools entries passed without any output.
  * f-ccp-validator-2 — a SKILL.md missing `name` at standard tier produced
    zero field-presence diagnostics despite STANDARD_REQUIRED = {name,
    description}.

All new diagnostics are WARNING-level by design: escalating them to errors
would be an error-vs-warning semantics change, which is architectural per
000-docs/SCHEMA_CHANGELOG.md NON-NEGOTIABLE #7 and needs prior approval.
The marketplace-tier guard tests at the bottom pin NON-NEGOTIABLES #1-#2
(missing ALWAYS_REQUIRED fields stay ERRORS at marketplace tier).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate-skills-schema.py"
_spec = importlib.util.spec_from_file_location("validate_skills_schema", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validator)

# A description long enough (>20 chars) and bland enough to avoid unrelated
# length / voice / discoverability diagnostics muddying assertions.
GOOD_DESC = "Validate skill frontmatter fields against the published schema registry."

SKILL_PATH = Path("plugins/testing/my-skill/skills/my-skill/SKILL.md")


def _frontmatter(fm: dict, tier: str):
    return validator.validate_frontmatter(SKILL_PATH, fm, tier=tier)


# =========================================================================
# f-ccp-validator-1 — validate_tool_permission unit behavior
# =========================================================================


def test_known_bare_tools_are_valid_with_no_message():
    for tool in ("Read", "Write", "Edit", "Bash", "Grep", "Glob", "Skill"):
        valid, msg = validator.validate_tool_permission(tool)
        assert valid is True, tool
        assert msg == "", (tool, msg)


def test_scoped_colon_form_is_valid():
    valid, msg = validator.validate_tool_permission("Bash(git:*)")
    assert valid is True
    assert msg == ""


def test_scoped_space_form_is_valid_per_anthropic_canonical_example():
    # code.claude.com/docs/en/skills canonical example: Bash(git add *)
    valid, msg = validator.validate_tool_permission("Bash(git add *)")
    assert valid is True
    assert msg == "", msg


def test_mcp_tool_reference_is_valid():
    valid, msg = validator.validate_tool_permission("mcp__database-explorer__query_database")
    assert valid is True
    assert msg == "", msg


def test_misspelled_tool_name_yields_advisory_with_suggestion():
    valid, msg = validator.validate_tool_permission("Reads")
    assert valid is True  # well-formed, just unknown — advisory, not malformed
    assert "Reads" in msg
    assert "Read" in msg  # did-you-mean suggestion


def test_unclosed_paren_is_malformed():
    valid, msg = validator.validate_tool_permission("Bash(git add *")
    assert valid is False
    assert "parenthes" in msg.lower()


def test_stray_close_paren_is_malformed():
    valid, msg = validator.validate_tool_permission("wc:*)")
    assert valid is False
    assert msg


def test_empty_scope_is_malformed():
    valid, msg = validator.validate_tool_permission("Bash()")
    assert valid is False
    assert "scope" in msg.lower()


def test_empty_entry_is_malformed():
    valid, msg = validator.validate_tool_permission("   ")
    assert valid is False
    assert msg


# =========================================================================
# f-ccp-validator-1 — caller routing inside validate_frontmatter
# =========================================================================


def test_misspelled_allowed_tool_surfaces_warning_not_error():
    fm = {"name": "my-skill", "description": GOOD_DESC, "allowed-tools": "Reads, Write"}
    errors, warnings, _infos = _frontmatter(fm, validator.TIER_STANDARD)
    assert any("allowed-tools" in w and "Reads" in w for w in warnings), warnings
    assert not any("allowed-tools" in e for e in errors), errors


def test_malformed_wildcard_surfaces_warning_not_error():
    # YAML-list form so the comma-free truncated entry survives parsing intact.
    fm = {"name": "my-skill", "description": GOOD_DESC, "allowed-tools": ["Bash(git add *", "Read"]}
    errors, warnings, _infos = _frontmatter(fm, validator.TIER_STANDARD)
    assert any("allowed-tools" in w and "parenthes" in w.lower() for w in warnings), warnings
    assert not any("allowed-tools" in e for e in errors), errors


def test_clean_allowed_tools_produce_no_tool_diagnostics():
    fm = {"name": "my-skill", "description": GOOD_DESC, "allowed-tools": "Read, Write, Bash(git:*)"}
    errors, warnings, _infos = _frontmatter(fm, validator.TIER_STANDARD)
    assert not any("Unknown tool" in w or "Malformed" in w for w in warnings), warnings
    assert not any("allowed-tools" in e for e in errors), errors


# =========================================================================
# f-ccp-validator-2 — standard tier missing-name diagnostic
# =========================================================================


def test_standard_tier_missing_name_emits_warning():
    fm = {"description": GOOD_DESC}
    errors, warnings, _infos = _frontmatter(fm, validator.TIER_STANDARD)
    assert any("'name'" in w and "Missing" in w for w in warnings), (
        f"standard tier must diagnose a missing 'name' field; got warnings={warnings}"
    )
    # Warning-level only — promoting to error is gated by NON-NEGOTIABLE #7.
    assert not any("'name'" in e and "Missing" in e for e in errors), errors


def test_standard_tier_missing_description_still_warns():
    fm = {"name": "my-skill"}
    _errors, warnings, _infos = _frontmatter(fm, validator.TIER_STANDARD)
    assert any("'description'" in w and "Missing" in w for w in warnings), warnings


def test_standard_tier_complete_minimal_frontmatter_has_no_presence_warnings():
    fm = {"name": "my-skill", "description": GOOD_DESC}
    errors, warnings, _infos = _frontmatter(fm, validator.TIER_STANDARD)
    assert not errors, errors
    assert not any("Missing required field" in w or "Missing recommended field" in w for w in warnings), warnings


# =========================================================================
# NON-NEGOTIABLES #1-#2 guard — marketplace tier still ERRORS on the 8-field set
# =========================================================================


def test_marketplace_tier_missing_always_required_fields_are_errors():
    fm = {"name": "my-skill", "description": GOOD_DESC}
    errors, _warnings, _infos = _frontmatter(fm, validator.TIER_MARKETPLACE)
    for field in ("allowed-tools", "version", "author", "license", "compatibility", "tags"):
        assert any(f"'{field}'" in e and "Missing required field" in e for e in errors), (
            f"marketplace tier must ERROR on missing '{field}' (NON-NEGOTIABLE #2); got errors={errors}"
        )


def test_always_required_is_the_is_enterprise_8_field_set():
    # NON-NEGOTIABLE #1 — pin the canonical set so accidental reduction fails loudly.
    assert validator.ALWAYS_REQUIRED == {
        "name",
        "description",
        "allowed-tools",
        "version",
        "author",
        "license",
        "compatibility",
        "tags",
    }
