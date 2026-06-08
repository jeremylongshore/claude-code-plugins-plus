"""Shared pytest fixtures for the penetration-tester pack test suite.

All cluster 4/5/6 test modules consume these fixtures. Adding new
fixtures here keeps cross-cluster test code DRY.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# --- Module path injection --------------------------------------------------
# Make lib/ importable in tests without each module repeating the dance.
_PACK_ROOT = Path(__file__).resolve().parents[1]
if str(_PACK_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACK_ROOT))


# --- Sample ROE fixture -----------------------------------------------------


@pytest.fixture
def sample_roe_dict() -> dict[str, Any]:
    """A complete, valid ROE represented as a Python dict."""
    return {
        "engagement_id": "TEST-ENG-001",
        "authorizer": {
            "name": "Jane Doe",
            "email": "jane.doe@example.test",
            "role": "CISO",
            "organization": "Example Corp",
        },
        "in_scope_targets": [
            {"host": "app.example.test"},
            {"cidr": "203.0.113.0/24"},
        ],
        "out_of_scope_targets": [
            {"host": "payments.example.test", "reason": "PCI scope"},
        ],
        "time_window": {
            "start": "2026-01-01T00:00:00Z",
            "end": "2099-12-31T23:59:59Z",  # far future to keep test stable
        },
        "emergency_contact": {
            "name": "SOC On-Call",
            "phone": "+1-555-555-5555",
            "email": "soc@example.test",
        },
        "rules": [
            "No exploitation of confirmed findings without written approval.",
        ],
        "signature_block": {
            "signer": "jane.doe@example.test",
            "signed_at": "2026-01-01T00:00:00Z",
            "signature": "(test-fixture signature placeholder)",
        },
    }


@pytest.fixture
def sample_roe_path(tmp_path: Path, sample_roe_dict: dict[str, Any]) -> Path:
    """Write the sample ROE to a temp YAML-shaped file."""
    roe_path = tmp_path / "roe.yaml"
    # Render as minimal YAML the in-tree parser can read.
    lines: list[str] = []
    for key, value in sample_roe_dict.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    keys = list(item.keys())
                    if keys:
                        first = keys[0]
                        lines.append(f"  - {first}: {item[first]}")
                        for k in keys[1:]:
                            lines.append(f"    {k}: {item[k]}")
                else:
                    lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    roe_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return roe_path


# --- Sample findings fixture ------------------------------------------------


@pytest.fixture
def sample_findings() -> list[dict[str, Any]]:
    """Three representative findings spanning multiple severities + skills."""
    return [
        {
            "skill_id": "auditing-npm-dependencies",
            "title": "Critical CVE in lodash",
            "severity": "critical",
            "target": "test-project::lodash",
            "detail": "lodash<4.17.21 has a prototype pollution CVE",
            "remediation": "Bump lodash to >=4.17.21",
            "cve_id": "CVE-2019-10744",
            "cwe_id": "CWE-1104",
            "references": ["https://nvd.nist.gov/vuln/detail/CVE-2019-10744"],
            "evidence": {"package": "lodash", "range": "<4.17.21"},
        },
        {
            "skill_id": "scanning-for-hardcoded-secrets",
            "title": "AWS access key in source",
            "severity": "high",
            "target": "test-project::src/config.py",
            "detail": "AWS access key matched in config.py line 14",
            "remediation": "Rotate the key + move to environment variable",
            "cwe_id": "CWE-798",
            "references": [],
            "evidence": {"file": "src/config.py", "line": 14},
        },
        {
            "skill_id": "checking-http-security-headers",
            "title": "Missing X-Frame-Options",
            "severity": "medium",
            "target": "https://app.example.test",
            "detail": "Response did not include X-Frame-Options header",
            "remediation": "Set X-Frame-Options: DENY on the response",
            "cwe_id": "CWE-1021",
            "references": [],
            "evidence": {"url": "https://app.example.test"},
        },
    ]


@pytest.fixture
def sample_findings_jsonl(tmp_path: Path, sample_findings: list[dict[str, Any]]) -> Path:
    """Write the sample findings to a JSONL file."""
    p = tmp_path / "findings.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        for record in sample_findings:
            fh.write(json.dumps(record) + "\n")
    return p


# --- Engagement directory fixture ------------------------------------------


@pytest.fixture
def engagement_dir(
    tmp_path: Path,
    sample_roe_path: Path,
    sample_findings_jsonl: Path,
) -> Path:
    """A complete fake engagement directory with ROE + findings."""
    eng = tmp_path / "test-engagement"
    eng.mkdir()
    (eng / "findings").mkdir()
    (eng / "reports").mkdir()

    # Move ROE into the engagement dir
    target_roe = eng / "roe.yaml"
    target_roe.write_text(sample_roe_path.read_text(), encoding="utf-8")
    # Move findings into the engagement dir
    target_findings = eng / "findings" / "test-findings.jsonl"
    target_findings.write_text(sample_findings_jsonl.read_text(), encoding="utf-8")
    return eng


# --- npm-audit JSON fixtures ------------------------------------------------


@pytest.fixture
def npm_audit_v2_output() -> dict[str, Any]:
    """A realistic-shaped npm audit (v2) JSON output."""
    return {
        "auditReportVersion": 2,
        "vulnerabilities": {
            "lodash": {
                "name": "lodash",
                "severity": "critical",
                "isDirect": True,
                "via": [
                    {
                        "source": 1234567,
                        "name": "lodash",
                        "dependency": "lodash",
                        "title": "Prototype Pollution in lodash",
                        "url": "https://github.com/advisories/GHSA-test",
                        "severity": "critical",
                        "cwe": ["CWE-1321"],
                        "cvss": {"score": 9.1, "vectorString": "CVSS:3.1/..."},
                        "range": "<4.17.21",
                    }
                ],
                "effects": [],
                "range": "<4.17.21",
                "nodes": ["node_modules/lodash"],
                "fixAvailable": {
                    "name": "lodash",
                    "version": "4.17.21",
                    "isSemVerMajor": False,
                },
            }
        },
        "metadata": {"vulnerabilities": {"critical": 1}},
    }


@pytest.fixture
def npm_audit_v1_output() -> dict[str, Any]:
    """A realistic-shaped npm audit (v1, npm 6) JSON output."""
    return {
        "advisories": {
            "1234567": {
                "id": 1234567,
                "module_name": "lodash",
                "title": "Prototype Pollution in lodash",
                "url": "https://npmjs.com/advisories/1234567",
                "severity": "critical",
                "vulnerable_versions": "<4.17.21",
                "patched_versions": ">=4.17.21",
                "cves": ["CVE-2019-10744"],
            }
        }
    }
