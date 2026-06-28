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


def _validate(tmp_path: Path, manifest: dict):
    pj = tmp_path / "plugin.json"
    pj.write_text(json.dumps(manifest), encoding="utf-8")
    return validator.validate_plugin_json(pj)


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


def test_genuinely_unknown_field_still_flagged(tmp_path):
    # NON-NEGOTIABLE #7 unchanged: a non-spec field is still reported (as today,
    # an error). This test pins that the GA additions did NOT silently widen the
    # allowlist to accept arbitrary keys.
    result = _validate(tmp_path, {"name": "demo", "totallyMadeUpField": 1})
    assert any("totallyMadeUpField" in e for e in result["errors"]), result
