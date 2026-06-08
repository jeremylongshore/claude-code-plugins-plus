#!/usr/bin/env python3
"""auditing-python-dependencies — wrap `pip-audit` into canonical Findings.

Auto-detects the project's requirement source (poetry.lock, Pipfile.lock,
requirements.txt, pyproject.toml, or installed environment), runs pip-audit,
parses the JSON output, and emits Findings via lib/finding.py. When pip-audit
is not installed, falls back to `pip list --outdated` and emits INFO findings
explaining the degraded scan.

Output formats and exit-code semantics are shared with the rest of the
penetration-tester v3 pack via lib/report.py.

Usage:
    python3 audit_python.py PATH [--output FILE] [--format json|jsonl|markdown]
                                 [--min-severity sev] [--requirement FILE]
                                 [--include-dev] [--strict]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# --- Make lib/ importable regardless of CWD ----------------------------------
_LIB_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_LIB_ROOT))

from lib.finding import Finding, Severity  # noqa: E402
from lib import report  # noqa: E402


SKILL_ID = "auditing-python-dependencies"
CATEGORY = "dependency-vulnerability"
CWE_DEFAULT = "CWE-1104"


# --- Tool detection ----------------------------------------------------------


def _pip_audit_present() -> bool:
    return shutil.which("pip-audit") is not None


def _pip_present() -> bool:
    return shutil.which("pip") is not None or shutil.which("pip3") is not None


def _pip_binary() -> str:
    return "pip" if shutil.which("pip") is not None else "pip3"


# --- Requirement-file detection ---------------------------------------------


def detect_requirement_sources(directory: Path) -> list[Path]:
    """Return ordered list of plausible requirement sources for the project."""
    candidates: list[Path] = []
    for name in ("poetry.lock", "Pipfile.lock"):
        p = directory / name
        if p.exists():
            candidates.append(p)
    # requirements*.txt (top-level)
    for p in sorted(directory.glob("requirements*.txt")):
        candidates.append(p)
    # pyproject.toml — only useful when poetry.lock isn't present and the
    # project actually pins deps in pyproject (PEP 621 or poetry-without-lock).
    pyproject = directory / "pyproject.toml"
    if pyproject.exists() and not (directory / "poetry.lock").exists():
        candidates.append(pyproject)
    return candidates


# --- pip-audit invocation ----------------------------------------------------


def _run_pip_audit(requirement_path: Path | None, strict: bool) -> tuple[list[dict[str, Any]] | None, str]:
    """Run pip-audit on the given requirement file (or installed env if None).

    Returns (records, raw_stdout) or (None, raw_stdout) on parse failure.
    """
    cmd: list[str] = ["pip-audit", "--format", "json", "--progress-spinner", "off"]
    if strict:
        cmd.append("--strict")
    if requirement_path is not None:
        requirement_path.suffix.lower()
        # pip-audit's --requirement flag accepts requirements.txt; for
        # poetry.lock / Pipfile.lock / pyproject.toml, pip-audit reads them
        # via --requirement too as of v2.7+.
        cmd.extend(["--requirement", str(requirement_path)])

    try:
        proc = subprocess.run(  # noqa: S603 — pip-audit is the audit tool
            cmd,
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "pip-audit timed out after 240s"
    except FileNotFoundError:
        return None, "pip-audit binary not found"

    stdout = proc.stdout or ""
    try:
        records = json.loads(stdout)
    except json.JSONDecodeError:
        return None, stdout

    # pip-audit returns a list of {name, version, vulns} per package
    # (v2.x format); older versions returned a dependency-keyed dict.
    if isinstance(records, list):
        return records, stdout
    if isinstance(records, dict) and "dependencies" in records:
        return records.get("dependencies", []), stdout
    return [], stdout


# --- pip-audit output parsing ------------------------------------------------


def _osv_severity_to_enum(severity_str: str) -> Severity:
    """OSV emits severity strings or CVSS strings; map to Severity."""
    s = (severity_str or "").strip().lower()
    if s.startswith("crit"):
        return Severity.CRITICAL
    if s.startswith("high"):
        return Severity.HIGH
    if s.startswith("med") or s.startswith("moderate"):
        return Severity.MEDIUM
    if s.startswith("low"):
        return Severity.LOW
    return Severity.INFO


def _extract_cvss(vuln: dict[str, Any]) -> float | None:
    """Best-effort CVSS score extraction from a pip-audit vuln record."""
    severities = vuln.get("severity") or []
    for entry in severities:
        if not isinstance(entry, dict):
            continue
            # OSV severity may be {"type": "CVSS_V3", "score": "9.8/CVSS..."}
        score_str = str(entry.get("score", ""))
        # CVSS string looks like "9.8/CVSS:3.1/AV:N..." — pull the leading number.
        head = score_str.split("/", 1)[0].strip()
        try:
            return float(head)
        except ValueError:
            continue
    return None


def _parse_pip_audit_records(records: list[dict[str, Any]], target_label: str) -> list[Finding]:
    findings: list[Finding] = []
    for record in records:
        pkg_name = record.get("name") or record.get("package") or "<unknown>"
        installed_version = record.get("version") or "<unknown>"
        vulns = record.get("vulns") or record.get("vulnerabilities") or []
        for vuln in vulns:
            adv_id = vuln.get("id") or vuln.get("ghsa") or vuln.get("pypa_id") or "ADVISORY"
            aliases = vuln.get("aliases") or []
            cve_id = next(
                (a for a in aliases if isinstance(a, str) and a.upper().startswith("CVE-")),
                None,
            )
            fix_versions = vuln.get("fix_versions") or []
            description = vuln.get("description") or ""

            cvss_score = _extract_cvss(vuln)
            if cvss_score is not None:
                severity = Severity.from_cvss(cvss_score)
            else:
                severity = _osv_severity_to_enum(str(vuln.get("severity_label", "")))

            title = (
                f"{adv_id} in {pkg_name}=={installed_version}"
                if description == ""
                else f"{adv_id}: {description.splitlines()[0][:100]}"
            )

            detail_lines = [
                f"Affected package: {pkg_name}",
                f"Installed version: {installed_version}",
                f"Advisory: {adv_id}",
            ]
            if cve_id:
                detail_lines.append(f"CVE: {cve_id}")
            if cvss_score is not None:
                detail_lines.append(f"CVSS v3.1: {cvss_score}")
            if description:
                detail_lines.append(f"Summary: {description[:300]}")

            if fix_versions:
                remediation = (
                    f"1. Bump {pkg_name} to one of: "
                    f"{', '.join(fix_versions)}.\n"
                    f"2. Update the requirement file pin and run "
                    f"`pip install -U {pkg_name}` (or `poetry update {pkg_name}`).\n"
                    f"3. Run the test suite; CVE fixes sometimes include "
                    f"behavioral changes.\n"
                    f"4. Commit the lock-file diff."
                )
            else:
                remediation = (
                    "NO FIX AVAILABLE.\n"
                    "1. Subscribe to PyPA / GHSA notifications for this advisory.\n"
                    "2. If exploitable in your usage, replace the package or vendor + patch.\n"
                    "3. Document the exception with a re-evaluation date."
                )
                # Bump severity to HIGH if moderate or higher when no fix.
                if severity.numeric >= 3:
                    severity = max(severity, Severity.HIGH, key=lambda s: s.numeric)

            evidence_items: list[tuple[str, Any]] = [
                ("package", pkg_name),
                ("installed", installed_version),
                ("advisory", adv_id),
            ]
            if fix_versions:
                evidence_items.append(("fix_versions", ", ".join(fix_versions)))
            if cve_id:
                evidence_items.append(("cve", cve_id))
            if cvss_score is not None:
                evidence_items.append(("cvss", cvss_score))

            references_list: list[str] = []
            for r in vuln.get("references") or []:
                if isinstance(r, dict) and r.get("url"):
                    references_list.append(r["url"])
                elif isinstance(r, str):
                    references_list.append(r)
            # Add OSV deeplink if it looks like an OSV/GHSA-style ID.
            if adv_id.startswith("GHSA-"):
                references_list.append(f"https://osv.dev/vulnerability/{adv_id}")
            if cve_id:
                references_list.append(f"https://nvd.nist.gov/vuln/detail/{cve_id}")

            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=title,
                    severity=severity,
                    target=f"{target_label}::{pkg_name}",
                    detail="\n".join(detail_lines),
                    remediation=remediation,
                    cvss_score=cvss_score,
                    cve_id=cve_id,
                    cwe_id=CWE_DEFAULT,
                    references=tuple(references_list),
                    evidence=tuple(evidence_items),
                )
            )
    return findings


# --- Fallback: pip list --outdated -------------------------------------------


def _run_pip_outdated() -> list[dict[str, Any]]:
    """Run `pip list --outdated --format=json` as a degraded fallback."""
    if not _pip_present():
        return []
    try:
        proc = subprocess.run(  # noqa: S603
            [_pip_binary(), "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    try:
        return json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []


def _outdated_to_findings(records: list[dict[str, Any]], target_label: str) -> list[Finding]:
    findings: list[Finding] = []
    for r in records:
        name = r.get("name", "<unknown>")
        installed = r.get("version", "?")
        latest = r.get("latest_version", "?")
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=f"{name} is outdated (no CVE data; pip-audit not installed)",
                severity=Severity.INFO,
                target=f"{target_label}::{name}",
                detail=(
                    f"pip-audit was not found on PATH; falling back to pip list --outdated.\n"
                    f"Package {name} is at {installed}; latest is {latest}.\n"
                    f"Install pip-audit (`pip install pip-audit`) and re-run for accurate CVE detection."
                ),
                remediation=(
                    "Install pip-audit and re-run this skill for vulnerability data.\n`pip install pip-audit`"
                ),
                cwe_id=CWE_DEFAULT,
                references=(
                    "https://pypi.org/project/pip-audit/",
                    "https://github.com/pypa/pip-audit",
                ),
                evidence=(
                    ("package", name),
                    ("installed", installed),
                    ("latest", latest),
                ),
            )
        )
    return findings


# --- Operational helpers -----------------------------------------------------


def _info_finding(title: str, detail: str, target: str) -> Finding:
    return Finding(
        skill_id=SKILL_ID,
        title=title,
        severity=Severity.INFO,
        target=target,
        detail=detail,
        remediation="Operational issue; no security action required.",
        references=(),
        evidence=(),
    )


def audit_directory(
    directory: Path,
    requirement_paths: list[Path] | None,
    strict: bool,
) -> list[Finding]:
    if not _pip_audit_present():
        outdated = _run_pip_outdated()
        if outdated:
            findings = _outdated_to_findings(outdated, directory.name)
            findings.insert(
                0,
                _info_finding(
                    "pip-audit not installed — degraded scan",
                    "Falling back to pip list --outdated. Install pip-audit for true vulnerability detection.",
                    str(directory),
                ),
            )
            return findings
        return [
            _info_finding(
                "pip-audit not installed and no fallback data available",
                "Install pip-audit (`pip install pip-audit`) and re-run.",
                str(directory),
            )
        ]

    sources = requirement_paths or detect_requirement_sources(directory)
    if not sources:
        # No requirement file found; pip-audit can audit the installed env.
        records, raw = _run_pip_audit(None, strict)
        if records is None:
            return [
                _info_finding(
                    "pip-audit returned non-JSON output",
                    f"Raw stdout (first 500 chars): {raw[:500]}",
                    str(directory),
                )
            ]
        if not records:
            return [
                _info_finding(
                    "no Python vulnerabilities found (installed-env scan)",
                    "pip-audit found no advisories against the currently installed packages.",
                    str(directory),
                )
            ]
        return _parse_pip_audit_records(records, directory.name)

    # Iterate over detected sources, accumulate findings.
    all_findings: list[Finding] = []
    seen_fingerprints: set[str] = set()
    for src in sources:
        records, raw = _run_pip_audit(src, strict)
        if records is None:
            all_findings.append(
                _info_finding(
                    f"pip-audit non-JSON output for {src.name}",
                    f"Raw stdout (first 500 chars): {raw[:500]}",
                    str(src),
                )
            )
            continue
        for f in _parse_pip_audit_records(records, f"{directory.name}/{src.name}"):
            fp = f.fingerprint()
            if fp in seen_fingerprints:
                continue
            seen_fingerprints.add(fp)
            all_findings.append(f)

    if not all_findings:
        all_findings = [
            _info_finding(
                "no Python vulnerabilities found",
                "pip-audit found no advisories across the detected requirement sources.",
                str(directory),
            )
        ]
    return all_findings


# --- CLI ---------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("path", help="Path to Python project root")
    p.add_argument("--output", default=None)
    p.add_argument(
        "--format",
        default="markdown",
        choices=["json", "jsonl", "markdown"],
    )
    p.add_argument(
        "--min-severity",
        default="info",
        choices=["info", "low", "medium", "high", "critical"],
    )
    p.add_argument(
        "--requirement",
        action="append",
        help="Override auto-detected requirements (repeatable)",
    )
    p.add_argument("--include-dev", action="store_true")
    p.add_argument("--strict", action="store_true")
    return p


def _filter_min_severity(findings: list[Finding], min_sev: str) -> list[Finding]:
    floor = Severity(min_sev).numeric
    return [f for f in findings if f.severity.numeric >= floor]


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    directory = Path(args.path).resolve()
    req_paths = [Path(p).resolve() for p in (args.requirement or [])] or None

    findings = audit_directory(directory, req_paths, args.strict)
    findings = _filter_min_severity(findings, args.min_severity)
    report.emit(findings, args.output, args.format, scan_target=str(directory))
    return report.exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
