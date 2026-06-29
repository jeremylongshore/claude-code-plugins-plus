"""Regression tests for plugin.json GA-field acceptance in validate-skills-schema.py.

SCHEMA 3.12.0 (2026-06-28): the Anthropic plugin.json manifest gained GA fields
(displayName, defaultEnabled, dependencies, userConfig, channels, $schema,
experimental). PLUGIN_JSON_FIELDS previously listed only the pre-GA 15, so the
validator hard-rejected valid current Anthropic plugins as
"Unknown field: '<x>' — not in Anthropic spec". These tests pin that the GA
fields are accepted and type-checked.

Source of truth verified against code.claude.com/docs/en/plugins-reference
§ "Plugin manifest schema". Additive spec-compliance fix (SCHEMA_CHANGELOG
NON-NEGOTIABLE #6 — adding missing documented fields). The unknown-field
error-vs-warning policy is deliberately UNCHANGED here (NON-NEGOTIABLE #7).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate-skills-schema.py"
_spec = importlib.util.spec_from_file_location("validate_skills_schema", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validator)

GA_FIELDS = (
    "displayName",
    "defaultEnabled",
    "dependencies",
    "userConfig",
    "channels",
    "$schema",
    "experimental",
)


def _validate(tmp_path: Path, manifest: dict, strict: bool = False):
    pj = tmp_path / "plugin.json"
    pj.write_text(json.dumps(manifest), encoding="utf-8")
    return validator.validate_plugin_json(pj, strict=strict)


def test_ga_fields_are_in_the_allowlist():
    for field in GA_FIELDS:
        assert field in validator.PLUGIN_JSON_FIELDS, f"{field} missing from PLUGIN_JSON_FIELDS"


def test_manifest_using_every_ga_field_has_no_errors(tmp_path):
    manifest = {
        "name": "demo-plugin",
        "displayName": "Demo Plugin",
        "version": "1.0.0",
        "description": "A plugin exercising the GA manifest fields.",
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        "defaultEnabled": True,
        "userConfig": {"apiKey": {"type": "string", "sensitive": True}},
        "channels": [{"server": "notifier"}],
        "dependencies": [{"name": "secrets-vault", "version": "~2.1.0"}],
        "experimental": {"themes": "./themes", "monitors": "./monitors"},
    }
    result = _validate(tmp_path, manifest)
    assert result["errors"] == [], result["errors"]


def test_default_enabled_accepts_boolean(tmp_path):
    result = _validate(tmp_path, {"name": "demo", "defaultEnabled": False})
    assert result["errors"] == [], result["errors"]


def test_default_enabled_rejects_non_boolean(tmp_path):
    # boolean is now in TYPE_MAP, so a string value is a real type error.
    result = _validate(tmp_path, {"name": "demo", "defaultEnabled": "yes"})
    assert any("defaultEnabled" in e for e in result["errors"]), result


def test_name_is_still_the_only_required_field(tmp_path):
    result = _validate(tmp_path, {"displayName": "No Name Here"})
    assert any("name" in e.lower() for e in result["errors"]), result


def test_unknown_field_is_a_warning_not_an_error_by_default(tmp_path):
    # SCHEMA 3.13.0 (NON-NEGOTIABLE #7, approved): unrecognized fields warn,
    # matching `claude plugin validate`. A plugin with only such warnings passes.
    result = _validate(tmp_path, {"name": "demo", "totallyMadeUpField": 1})
    assert result["errors"] == [], result["errors"]
    assert any("totallyMadeUpField" in w for w in result["warnings"]), result


def test_unknown_field_becomes_error_under_strict(tmp_path):
    result = _validate(tmp_path, {"name": "demo", "totallyMadeUpField": 1}, strict=True)
    assert any("totallyMadeUpField" in e for e in result["errors"]), result


def test_near_miss_field_gets_a_did_you_mean_hint(tmp_path):
    result = _validate(tmp_path, {"name": "demo", "displayNam": "Typo"})
    assert any("did you mean 'displayName'" in w for w in result["warnings"]), result


def test_wrong_type_is_always_an_error_even_without_strict(tmp_path):
    # Anthropic fails wrong-type fields regardless of --strict; so do we.
    result = _validate(tmp_path, {"name": "demo", "keywords": "should-be-an-array"})
    assert any("keywords" in e for e in result["errors"]), result


# --- L2 consumer-cutover (schema 3.14.0): kernel plugin-manifest drift gate ---


def test_kernel_plugin_shadow_is_in_sync():
    """PLUGIN_JSON_FIELDS must match the kernel's current (authoring/v2)
    plugin-manifest field surface. If this fails with `stale=[...]`, the kernel
    captured an upstream field CCPI hasn't adopted — add it to PLUGIN_JSON_FIELDS.
    Skips only if the kernel isn't installed (needs @intentsolutions/core>=0.9.0).
    """
    pj = validator.kernel_shadow_report().get("plugin_manifest", {})
    if not pj.get("available"):
        import pytest

        pytest.skip(f"kernel plugin-manifest v2 unavailable: {pj.get('note')}")
    assert pj["fields_match"], (
        f"PLUGIN_JSON_FIELDS drifted from kernel v2 plugin-manifest — "
        f"stale (missing): {pj['stale_missing_from_hand_authored']}, "
        f"extra: {pj['only_in_hand_authored']}"
    )


def test_kernel_plugin_surface_carries_the_ga_fields():
    """Sanity: the kernel surface we gate against is the CURRENT one (v2), i.e.
    it actually contains the GA fields — guards against silently gating against
    the stale v1 fold."""
    pj = validator.load_kernel_plugin_fields()
    if not pj.get("available"):
        import pytest

        pytest.skip(f"kernel plugin-manifest v2 unavailable: {pj.get('reason')}")
    for ga in ("displayName", "defaultEnabled", "userConfig", "channels", "dependencies", "experimental"):
        assert ga in pj["properties"], f"kernel v2 surface missing GA field {ga!r}"
