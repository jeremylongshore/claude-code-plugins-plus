"""Tests for the shared lib/finding.py module.

The Finding schema and Severity enum are load-bearing for the entire pack —
every skill emits findings through this contract. These tests pin the
behaviour every downstream skill depends on.
"""

from __future__ import annotations

import json

import pytest


def test_severity_enum_values():
    from lib.finding import Severity

    assert Severity.CRITICAL.value == "critical"
    assert Severity.HIGH.value == "high"
    assert Severity.MEDIUM.value == "medium"
    assert Severity.LOW.value == "low"
    assert Severity.INFO.value == "info"


def test_severity_numeric_ordering():
    from lib.finding import Severity

    assert Severity.CRITICAL.numeric > Severity.HIGH.numeric
    assert Severity.HIGH.numeric > Severity.MEDIUM.numeric
    assert Severity.MEDIUM.numeric > Severity.LOW.numeric
    assert Severity.LOW.numeric > Severity.INFO.numeric


@pytest.mark.parametrize(
    "cvss_score, expected",
    [
        (9.5, "critical"),
        (9.0, "critical"),
        (8.9, "high"),
        (7.0, "high"),
        (6.9, "medium"),
        (4.0, "medium"),
        (3.9, "low"),
        (0.1, "low"),
        (0.0, "info"),
    ],
)
def test_severity_from_cvss(cvss_score, expected):
    from lib.finding import Severity

    assert Severity.from_cvss(cvss_score).value == expected


@pytest.mark.parametrize(
    "npm_level, expected",
    [
        ("critical", "critical"),
        ("high", "high"),
        ("moderate", "medium"),
        ("low", "low"),
        ("info", "info"),
        ("CRITICAL", "critical"),  # case-insensitive
        ("unknown-flavor", "info"),  # unknown maps to info
    ],
)
def test_severity_from_npm_audit(npm_level, expected):
    from lib.finding import Severity

    assert Severity.from_npm_audit(npm_level).value == expected


def test_severity_from_bandit():
    from lib.finding import Severity

    assert Severity.from_bandit("HIGH") == Severity.HIGH
    assert Severity.from_bandit("MEDIUM") == Severity.MEDIUM
    assert Severity.from_bandit("LOW") == Severity.LOW
    assert Severity.from_bandit("UNKNOWN") == Severity.INFO


def test_finding_required_fields():
    from lib.finding import Finding, Severity

    f = Finding(
        skill_id="test-skill",
        title="Test finding",
        severity=Severity.HIGH,
        target="example.com",
        detail="Test detail",
        remediation="Test remediation",
    )
    assert f.skill_id == "test-skill"
    assert f.severity == Severity.HIGH
    assert f.references == ()
    assert f.evidence == ()


def test_finding_to_dict_round_trip():
    from lib.finding import Finding, Severity, from_json

    original = Finding(
        skill_id="test-skill",
        title="Test finding",
        severity=Severity.CRITICAL,
        target="example.com",
        detail="Test detail",
        remediation="Test remediation",
        cve_id="CVE-2026-1234",
        cwe_id="CWE-79",
        cvss_score=9.5,
        references=("https://example.com/advisory",),
        evidence=(("key", "value"),),
    )
    serialized = original.to_dict()
    restored = from_json(serialized)
    assert restored.skill_id == original.skill_id
    assert restored.title == original.title
    assert restored.severity == original.severity
    assert restored.cve_id == original.cve_id
    assert restored.cvss_score == original.cvss_score
    assert restored.references == original.references


def test_finding_fingerprint_is_stable():
    from lib.finding import Finding, Severity

    f1 = Finding(
        skill_id="test-skill",
        title="Same title",
        severity=Severity.HIGH,
        target="example.com",
        detail="Detail A",
        remediation="Fix A",
    )
    f2 = Finding(
        skill_id="test-skill",
        title="Same title",
        severity=Severity.HIGH,
        target="example.com",
        detail="Detail B",  # different
        remediation="Fix B",  # different
    )
    # Same (skill_id, title, target) → same fingerprint regardless of detail
    assert f1.fingerprint() == f2.fingerprint()


def test_finding_fingerprint_changes_with_target():
    from lib.finding import Finding, Severity

    f1 = Finding(
        skill_id="test",
        title="X",
        severity=Severity.HIGH,
        target="example.com",
        detail="d",
        remediation="r",
    )
    f2 = Finding(
        skill_id="test",
        title="X",
        severity=Severity.HIGH,
        target="other.com",
        detail="d",
        remediation="r",
    )
    assert f1.fingerprint() != f2.fingerprint()


def test_finding_to_dict_keys():
    """Pin the JSON output shape — downstream skills depend on it."""
    from lib.finding import Finding, Severity

    f = Finding(
        skill_id="t",
        title="T",
        severity=Severity.HIGH,
        target="x",
        detail="d",
        remediation="r",
    )
    d = f.to_dict()
    expected_keys = {
        "skill_id",
        "title",
        "severity",
        "target",
        "detail",
        "remediation",
        "cvss_score",
        "cve_id",
        "cwe_id",
        "owasp_category",
        "affected_control",
        "references",
        "evidence",
        "fingerprint",
    }
    assert set(d.keys()) == expected_keys


def test_finding_emit_jsonl_round_trip(tmp_path):
    from lib.finding import Finding, Severity, emit_jsonl, load_jsonl

    findings = [
        Finding(
            skill_id="t",
            title=f"finding {i}",
            severity=Severity.HIGH,
            target=f"target-{i}",
            detail="d",
            remediation="r",
        )
        for i in range(3)
    ]
    path = tmp_path / "findings.jsonl"
    count = emit_jsonl(findings, str(path))
    assert count == 3
    restored = load_jsonl(str(path))
    assert len(restored) == 3
    assert restored[0].title == "finding 0"
    assert restored[2].target == "target-2"


def test_finding_severity_enum_in_to_dict():
    """severity must serialize as its string value, not the enum repr."""
    from lib.finding import Finding, Severity

    f = Finding(
        skill_id="t",
        title="T",
        severity=Severity.CRITICAL,
        target="x",
        detail="d",
        remediation="r",
    )
    d = f.to_dict()
    assert d["severity"] == "critical"
    assert json.dumps(d)  # serializable
