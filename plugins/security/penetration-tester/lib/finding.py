"""Finding schema shared across every penetration-tester v3 skill.

Per AT-ADEC at 000-docs/001-AT-ADEC-skill-taxonomy.md, every skill emits findings
through this schema so report.py can compose multi-skill scans into a single
deliverable without each skill reinventing the structure.

Severity normalization:
    CRITICAL — known exploitation in the wild (CISA KEV) OR CVSS ≥ 9.0
    HIGH     — CVSS 7.0–8.9 OR confirmed remote code execution capability
    MEDIUM   — CVSS 4.0–6.9 OR auth bypass requiring chained conditions
    LOW      — CVSS 0.1–3.9 OR information disclosure without immediate impact
    INFO     — defense-in-depth observation; no exploitable condition

CVSS source: NVD calculator v3.1. EPSS / KEV enrichment via MCP cve_lookup
(per AT-ADEC 687) when wired; falls back to local CVSS-only scoring otherwise.
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
from typing import Any


class Severity(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @classmethod
    def from_cvss(cls, score: float) -> "Severity":
        """NVD CVSS v3.1 severity bands."""
        if score >= 9.0:
            return cls.CRITICAL
        if score >= 7.0:
            return cls.HIGH
        if score >= 4.0:
            return cls.MEDIUM
        if score > 0.0:
            return cls.LOW
        return cls.INFO

    @classmethod
    def from_npm_audit(cls, npm_level: str) -> "Severity":
        """npm audit emits {critical, high, moderate, low, info}."""
        mapping = {
            "critical": cls.CRITICAL,
            "high": cls.HIGH,
            "moderate": cls.MEDIUM,
            "low": cls.LOW,
            "info": cls.INFO,
        }
        return mapping.get(npm_level.lower(), cls.INFO)

    @classmethod
    def from_bandit(cls, bandit_level: str) -> "Severity":
        """bandit emits {HIGH, MEDIUM, LOW}; confidence is a second axis we ignore here."""
        mapping = {
            "HIGH": cls.HIGH,
            "MEDIUM": cls.MEDIUM,
            "LOW": cls.LOW,
        }
        return mapping.get(bandit_level.upper(), cls.INFO)

    @property
    def numeric(self) -> int:
        """Ordering for sort / threshold-floor checks. Higher = more severe."""
        return {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}[self.value]


@dataclasses.dataclass(frozen=True)
class Finding:
    """A single security finding.

    Required fields:
        skill_id     — the v3 skill that produced this finding (e.g. "analyzing-tls-config")
        title        — one-line description in imperative voice
        severity     — Severity enum
        target       — what was scanned (URL, file path, package name)
        detail       — technical explanation of WHY this is a finding
        remediation  — specific steps to fix; copy-paste-ready where possible

    Optional enrichment:
        cvss_score        — 0.0–10.0 if applicable
        cve_id            — "CVE-YYYY-NNNNN" if matched
        cwe_id            — "CWE-XX" if matched
        owasp_category    — "A0X:YYYY" OWASP Top 10 mapping
        affected_control  — e.g. "NIST 800-53 AC-2", "PCI DSS Req 8.3.6"
        references        — list of source URLs
        evidence          — opaque dict captured at scan time (response body, regex match, etc.)
    """

    skill_id: str
    title: str
    severity: Severity
    target: str
    detail: str
    remediation: str

    cvss_score: float | None = None
    cve_id: str | None = None
    cwe_id: str | None = None
    owasp_category: str | None = None
    affected_control: str | None = None
    references: tuple[str, ...] = ()
    evidence: tuple[tuple[str, Any], ...] = ()  # tuple-of-tuples so the dataclass stays hashable

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable representation."""
        return {
            "skill_id": self.skill_id,
            "title": self.title,
            "severity": self.severity.value,
            "target": self.target,
            "detail": self.detail,
            "remediation": self.remediation,
            "cvss_score": self.cvss_score,
            "cve_id": self.cve_id,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "affected_control": self.affected_control,
            "references": list(self.references),
            "evidence": dict(self.evidence),
            "fingerprint": self.fingerprint(),
        }

    def fingerprint(self) -> str:
        """Stable hash of (skill_id, title, target) — for dedup across multi-scan runs.

        Excludes severity / remediation / evidence so a finding that re-scans
        the same condition has the same fingerprint even if our scoring or
        suggested fix changed between releases.
        """
        h = hashlib.sha256()
        h.update(self.skill_id.encode())
        h.update(b"\x00")
        h.update(self.title.encode())
        h.update(b"\x00")
        h.update(self.target.encode())
        return h.hexdigest()[:16]


def from_json(data: dict[str, Any]) -> Finding:
    """Construct a Finding from its dict representation (round-trips with to_dict)."""
    return Finding(
        skill_id=data["skill_id"],
        title=data["title"],
        severity=Severity(data["severity"]),
        target=data["target"],
        detail=data["detail"],
        remediation=data["remediation"],
        cvss_score=data.get("cvss_score"),
        cve_id=data.get("cve_id"),
        cwe_id=data.get("cwe_id"),
        owasp_category=data.get("owasp_category"),
        affected_control=data.get("affected_control"),
        references=tuple(data.get("references", ())),
        evidence=tuple((k, v) for k, v in data.get("evidence", {}).items()),
    )


def emit_jsonl(findings: list[Finding], path: str) -> int:
    """Write findings as JSONL (one object per line). Returns count written."""
    with open(path, "w", encoding="utf-8") as fh:
        for f in findings:
            fh.write(json.dumps(f.to_dict()) + "\n")
    return len(findings)


def load_jsonl(path: str) -> list[Finding]:
    """Read findings from JSONL (inverse of emit_jsonl)."""
    out: list[Finding] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(from_json(json.loads(line)))
    return out
