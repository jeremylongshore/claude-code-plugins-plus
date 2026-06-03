"""Tests for the shared lib/report.py output / exit-code module."""

from __future__ import annotations

import json

import pytest


def _make_finding(severity_str: str = "high"):
    from lib.finding import Finding, Severity

    return Finding(
        skill_id="test-skill",
        title=f"Test {severity_str}",
        severity=Severity(severity_str),
        target="example.com",
        detail="Detail",
        remediation="Fix it",
    )


def test_emit_json_format(tmp_path):
    from lib import report

    findings = [_make_finding("high"), _make_finding("medium")]
    out = tmp_path / "out.json"
    report.emit(findings, str(out), "json", scan_target="example.com")
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["severity"] in ("high", "medium")


def test_emit_jsonl_format(tmp_path):
    from lib import report

    findings = [_make_finding("high"), _make_finding("low")]
    out = tmp_path / "out.jsonl"
    report.emit(findings, str(out), "jsonl", scan_target="example.com")
    lines = [l for l in out.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    for line in lines:
        record = json.loads(line)
        assert "severity" in record


def test_emit_markdown_format(tmp_path):
    from lib import report

    findings = [_make_finding("critical")]
    out = tmp_path / "out.md"
    report.emit(findings, str(out), "markdown", scan_target="example.com")
    text = out.read_text()
    # Markdown output should mention severity and the scan target somewhere
    assert "critical" in text.lower() or "CRITICAL" in text
    assert "example.com" in text


def test_emit_to_stdout(capsys):
    """When output is None, emit writes to stdout."""
    from lib import report

    findings = [_make_finding("high")]
    report.emit(findings, None, "json", scan_target="example.com")
    captured = capsys.readouterr()
    assert captured.out  # something was written
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 1


@pytest.mark.parametrize(
    "max_severity, expected_code",
    [
        ("critical", 1),
        ("high", 1),
        ("medium", 0),
        ("low", 0),
        ("info", 0),
    ],
)
def test_exit_code_thresholds(max_severity, expected_code):
    from lib import report

    findings = [_make_finding(max_severity)]
    assert report.exit_code(findings) == expected_code


def test_exit_code_picks_highest():
    from lib import report

    findings = [
        _make_finding("low"),
        _make_finding("critical"),
        _make_finding("medium"),
    ]
    assert report.exit_code(findings) == 1


def test_exit_code_empty_findings():
    from lib import report

    assert report.exit_code([]) == 0
