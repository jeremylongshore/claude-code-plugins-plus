"""Regression coverage for Freshie's run-wide stub classifier."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validator", ROOT / "scripts" / "validate-skills-schema.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def record(path, pack, body, grade="F"):
    return {"path": Path(path), "pack": Path(pack), "body": body, "grade": grade}


def test_flags_three_normalized_duplicates_but_protects_a_grade(tmp_path):
    pack = tmp_path / "pack"
    paths = [pack / "skills" / name / "SKILL.md" for name in ("a", "b", "c")]
    rows = [record(path, pack, "# Same\n\nbody", "A" if i == 0 else "F") for i, path in enumerate(paths)]
    flags = validator.deterministic_stub_flags(rows)
    assert str(paths[0]) not in flags
    assert str(paths[1]) in flags and str(paths[2]) in flags


def test_flags_missing_in_pack_reference_but_exempts_templates(tmp_path):
    pack = tmp_path / "pack"
    skill = pack / "skills" / "a" / "SKILL.md"
    templated = pack / "templates" / "a" / "SKILL.md"
    flags = validator.deterministic_stub_flags([
        record(skill, pack, "See [missing](../../references/nope.md)"),
        record(templated, pack, "See [missing](../../references/nope.md)"),
    ])
    assert str(skill) in flags
    assert str(templated) not in flags


def test_duplicate_hashes_do_not_cross_pack_boundaries(tmp_path):
    body = "# Shared\n\nThis identical body is only a finding within one pack."
    first = tmp_path / "first"
    second = tmp_path / "second"
    rows = [
        record(first / "skills" / name / "SKILL.md", first, body)
        for name in ("a", "b")
    ] + [record(second / "skills" / "c" / "SKILL.md", second, body)]
    assert validator.deterministic_stub_flags(rows) == {}


def test_existing_in_pack_reference_is_not_a_dangling_pointer(tmp_path):
    pack = tmp_path / "pack"
    skill = pack / "skills" / "a" / "SKILL.md"
    target = pack / "references" / "real.md"
    target.parent.mkdir(parents=True)
    target.write_text("present", encoding="utf-8")
    rows = [record(skill, pack, "See [real](../../references/real.md)")]
    assert validator.deterministic_stub_flags(rows) == {}
