#!/usr/bin/env python3
"""Unified dependency vulnerability scanner.

Scans project dependencies across multiple ecosystems (npm, pip) and produces
a consolidated vulnerability report. Wraps native audit tools (npm audit,
pip-audit, pip check) and normalizes their output into a unified finding
format suitable for CI pipelines and human review.

Usage:
    python3 dependency_auditor.py /path/to/project [options]

Options:
    --scanners npm,pip     Comma-separated list of scanners to run
    --min-severity low     Minimum severity to report (low|moderate|high|critical)
    --output findings.json Write JSON report to file
    --verbose              Enable verbose progress output

Exit codes:
    0  No critical or high severity findings
    1  Critical or high severity findings detected, or fatal error

Copyright 2026 Claude Code Plugins contributors. Licensed under MIT.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

# Severity ranking for sorting and filtering. Lower number means more severe.
SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "moderate": 2,
    "low": 3,
    "info": 4,
}

SUPPORTED_SCANNERS: set[str] = {"npm", "pip"}
FUTURE_SCANNERS: dict[str, str] = {
    "cargo": "Cargo.toml",
    "go": "go.mod",
    "bundler": "Gemfile",
}

SUBPROCESS_TIMEOUT: int = 60


def log(message: str, verbose: bool = True) -> None:
    """Print a progress message to stderr."""
    if verbose:
        print(f"[*] {message}", file=sys.stderr)


def log_warn(message: str) -> None:
    """Print a warning message to stderr (always shown)."""
    print(f"[!] {message}", file=sys.stderr)


def log_error(message: str) -> None:
    """Print an error message to stderr (always shown)."""
    print(f"[-] {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Project detection
# ---------------------------------------------------------------------------

def detect_project_type(directory: Path) -> list[str]:
    """Auto-detect project ecosystems by scanning for manifest files.

    Checks for well-known dependency manifest files and returns a list of
    ecosystem identifiers. Supported ecosystems produce actionable scans;
    future-support ecosystems print an informational message.

    Args:
        directory: Root directory of the project to scan.

    Returns:
        List of detected ecosystem strings (e.g. ["npm", "pip"]).
    """
    detected: list[str] = []

    # npm / Node.js
    npm_markers = ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]
    if any((directory / marker).exists() for marker in npm_markers):
        detected.append("npm")

    # pip / Python
    pip_markers = ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "setup.cfg"]
    if any((directory / marker).exists() for marker in pip_markers):
        detected.append("pip")

    # Future-support ecosystems
    for ecosystem, manifest in FUTURE_SCANNERS.items():
        if (directory / manifest).exists():
            log_warn(
                f"Detected {ecosystem} project ({manifest}), but {ecosystem} "
                f"scanning is not yet implemented. Skipping."
            )

    return detected


# ---------------------------------------------------------------------------
# npm audit
# ---------------------------------------------------------------------------

def run_npm_audit(directory: Path) -> list[dict[str, Any]]:
    """Run npm audit and parse vulnerability findings.

    Executes ``npm audit --json`` in the target directory and parses the
    structured output. Handles missing npm installations and projects that
    lack a node_modules directory.

    Args:
        directory: Project root containing package.json.

    Returns:
        List of finding dicts with keys matching the unified schema.
    """
    findings: list[dict[str, Any]] = []

    # Check npm is available
    npm_check = subprocess.run(
        ["npm", "--version"],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    if npm_check.returncode != 0:
        log_warn("npm is not installed or not in PATH. Skipping npm audit.")
        return findings

    # Check for package.json
    if not (directory / "package.json").exists():
        log_warn(f"No package.json found in {directory}. Skipping npm audit.")
        return findings

    # Warn if node_modules is missing
    if not (directory / "node_modules").is_dir():
        log_warn(
            f"No node_modules directory in {directory}. "
            f"Run 'npm install' first for accurate audit results."
        )

    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            capture_output=True, text=True,
            cwd=str(directory),
            timeout=SUBPROCESS_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        log_error("npm audit timed out after {SUBPROCESS_TIMEOUT}s.")
        return findings
    except FileNotFoundError:
        log_warn("npm executable not found. Skipping npm audit.")
        return findings

    # npm audit returns non-zero when vulnerabilities exist, so we parse
    # the output regardless of the return code.
    if not result.stdout.strip():
        log_warn("npm audit produced no output.")
        return findings

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        log_error(f"Failed to parse npm audit JSON output: {exc}")
        return findings

    findings.extend(_parse_npm_audit_v2(data))
    if not findings:
        findings.extend(_parse_npm_audit_v1(data))

    return findings


def _parse_npm_audit_v2(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse npm audit JSON output in the v2 format (npm 7+).

    The v2 format uses a top-level ``vulnerabilities`` object keyed by
    package name.
    """
    findings: list[dict[str, Any]] = []
    vulnerabilities = data.get("vulnerabilities", {})

    for pkg_name, vuln_info in vulnerabilities.items():
        severity = vuln_info.get("severity", "moderate")
        fix_available = vuln_info.get("fixAvailable")
        fixed_version: Optional[str] = None
        if isinstance(fix_available, dict):
            fixed_version = fix_available.get("version")

        # Each vulnerability entry may reference multiple advisories via "via"
        via_entries = vuln_info.get("via", [])
        if not via_entries:
            findings.append({
                "scanner": "npm",
                "package": pkg_name,
                "severity": _normalize_severity(severity),
                "title": f"Vulnerability in {pkg_name}",
                "detail": f"Severity: {severity}. Check npm audit for details.",
                "cve": None,
                "installed_version": vuln_info.get("range"),
                "fixed_version": fixed_version,
            })
            continue

        for via in via_entries:
            if isinstance(via, str):
                # Indirect vulnerability reference (transitive dependency name)
                findings.append({
                    "scanner": "npm",
                    "package": pkg_name,
                    "severity": _normalize_severity(severity),
                    "title": f"Depends on vulnerable {via}",
                    "detail": f"{pkg_name} is affected through dependency on {via}.",
                    "cve": None,
                    "installed_version": vuln_info.get("range"),
                    "fixed_version": fixed_version,
                })
            elif isinstance(via, dict):
                cve = _extract_cve(via.get("url", ""))
                findings.append({
                    "scanner": "npm",
                    "package": pkg_name,
                    "severity": _normalize_severity(via.get("severity", severity)),
                    "title": via.get("title", f"Vulnerability in {pkg_name}"),
                    "detail": via.get("title", "No description available."),
                    "cve": cve,
                    "installed_version": via.get("range") or vuln_info.get("range"),
                    "fixed_version": fixed_version,
                })

    return findings


def _parse_npm_audit_v1(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse npm audit JSON output in the v1 format (npm 6).

    The v1 format uses a top-level ``advisories`` object keyed by advisory ID.
    """
    findings: list[dict[str, Any]] = []
    advisories = data.get("advisories", {})

    for _adv_id, advisory in advisories.items():
        cve_list = advisory.get("cves", [])
        cve = cve_list[0] if cve_list else None
        findings.append({
            "scanner": "npm",
            "package": advisory.get("module_name", "unknown"),
            "severity": _normalize_severity(advisory.get("severity", "moderate")),
            "title": advisory.get("title", "Unknown vulnerability"),
            "detail": advisory.get("overview", "No description available."),
            "cve": cve,
            "installed_version": advisory.get("findings", [{}])[0].get("version"),
            "fixed_version": advisory.get("patched_versions"),
        })

    return findings


# ---------------------------------------------------------------------------
# pip-audit
# ---------------------------------------------------------------------------

def run_pip_audit(directory: Path) -> list[dict[str, Any]]:
    """Run pip-audit and parse vulnerability findings.

    Attempts to use pip-audit first. If not installed, tries to install it
    via pip. If that also fails, falls back to ``pip list --outdated`` with
    a warning that the results are not a true vulnerability scan.

    Args:
        directory: Project root containing Python dependency manifests.

    Returns:
        List of finding dicts with keys matching the unified schema.
    """
    findings: list[dict[str, Any]] = []

    # Determine requirement file arguments
    req_args = _pip_audit_requirement_args(directory)

    # Try running pip-audit
    pip_audit_cmd = ["pip-audit", "--format=json"] + req_args
    try:
        result = subprocess.run(
            pip_audit_cmd,
            capture_output=True, text=True,
            cwd=str(directory),
            timeout=SUBPROCESS_TIMEOUT,
        )
        return _parse_pip_audit_output(result.stdout)
    except FileNotFoundError:
        log_warn("pip-audit is not installed. Attempting to install it...")
    except subprocess.TimeoutExpired:
        log_error(f"pip-audit timed out after {SUBPROCESS_TIMEOUT}s.")
        return findings

    # Try installing pip-audit
    install_result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "pip-audit", "--quiet"],
        capture_output=True, text=True,
        timeout=SUBPROCESS_TIMEOUT,
    )
    if install_result.returncode == 0:
        try:
            result = subprocess.run(
                pip_audit_cmd,
                capture_output=True, text=True,
                cwd=str(directory),
                timeout=SUBPROCESS_TIMEOUT,
            )
            return _parse_pip_audit_output(result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Fallback: pip list --outdated (not a real vulnerability scan)
    log_warn(
        "pip-audit unavailable. Falling back to 'pip list --outdated'. "
        "NOTE: Outdated packages are not necessarily vulnerable."
    )
    return _run_pip_outdated_fallback()


def _pip_audit_requirement_args(directory: Path) -> list[str]:
    """Build pip-audit CLI args pointing to requirement files if present."""
    args: list[str] = []
    req_file = directory / "requirements.txt"
    if req_file.exists():
        args.extend(["--requirement", str(req_file)])
    return args


def _parse_pip_audit_output(raw_output: str) -> list[dict[str, Any]]:
    """Parse JSON output from pip-audit into unified findings."""
    findings: list[dict[str, Any]] = []
    if not raw_output.strip():
        return findings

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        log_error(f"Failed to parse pip-audit JSON output: {exc}")
        return findings

    # pip-audit can return either a top-level list or a dict with
    # "dependencies" key depending on version.
    vulns: list[dict[str, Any]] = []
    if isinstance(data, list):
        vulns = data
    elif isinstance(data, dict):
        vulns = data.get("dependencies", data.get("vulnerabilities", []))

    for entry in vulns:
        pkg_name = entry.get("name", "unknown")
        installed = entry.get("version", entry.get("installed_version"))
        vuln_list = entry.get("vulns", [entry] if "id" in entry else [])

        for vuln in vuln_list:
            vuln_id = vuln.get("id", "")
            cve = vuln_id if vuln_id.startswith("CVE-") else _extract_cve(vuln_id)
            description = vuln.get("description", vuln.get("detail", ""))
            fix = vuln.get("fix_versions", vuln.get("fixed_version"))
            if isinstance(fix, list):
                fix = fix[0] if fix else None

            findings.append({
                "scanner": "pip-audit",
                "package": pkg_name,
                "severity": _severity_from_vuln_id(vuln_id),
                "title": f"{vuln_id}: {pkg_name}" if vuln_id else f"Vulnerability in {pkg_name}",
                "detail": description or "No description provided by pip-audit.",
                "cve": cve,
                "installed_version": installed,
                "fixed_version": fix,
            })

    return findings


def _run_pip_outdated_fallback() -> list[dict[str, Any]]:
    """Fallback: list outdated pip packages as low-severity informational."""
    findings: list[dict[str, Any]] = []
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True, text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        log_error("pip list --outdated failed or timed out.")
        return findings

    if not result.stdout.strip():
        return findings

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return findings

    for entry in data:
        findings.append({
            "scanner": "pip-audit",
            "package": entry.get("name", "unknown"),
            "severity": "info",
            "title": f"Outdated package: {entry.get('name', 'unknown')}",
            "detail": (
                f"Installed {entry.get('version', '?')}, "
                f"latest {entry.get('latest_version', '?')}. "
                f"Outdated packages may contain known vulnerabilities."
            ),
            "cve": None,
            "installed_version": entry.get("version"),
            "fixed_version": entry.get("latest_version"),
        })

    return findings


# ---------------------------------------------------------------------------
# pip check
# ---------------------------------------------------------------------------

def run_pip_check(directory: Path) -> list[dict[str, Any]]:
    """Run pip check to detect broken dependencies and version conflicts.

    Parses the text output of ``pip check`` into structured findings. Broken
    dependencies are reported as moderate severity because they may indicate
    supply-chain manipulation or installation tampering.

    Args:
        directory: Project root (used as working directory).

    Returns:
        List of finding dicts with keys matching the unified schema.
    """
    findings: list[dict[str, Any]] = []

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True, text=True,
            cwd=str(directory),
            timeout=SUBPROCESS_TIMEOUT,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        log_error(f"pip check failed: {exc}")
        return findings

    if result.returncode == 0 and not result.stdout.strip():
        return findings

    # pip check output lines look like:
    #   packageA 1.0 requires packageB, which is not installed.
    #   packageA 1.0 has requirement packageB>=2.0, but you have packageB 1.5.
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # Extract package name (first token)
        parts = line.split()
        pkg_name = parts[0] if parts else "unknown"
        installed_version = parts[1] if len(parts) > 1 else None

        findings.append({
            "scanner": "pip-check",
            "package": pkg_name,
            "severity": "moderate",
            "title": f"Dependency conflict: {pkg_name}",
            "detail": line,
            "cve": None,
            "installed_version": installed_version,
            "fixed_version": None,
        })

    return findings


# ---------------------------------------------------------------------------
# Unification and deduplication
# ---------------------------------------------------------------------------

def unify_results(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize, deduplicate, and sort findings by severity.

    Deduplication key is (package, cve) for findings with a CVE, or
    (package, scanner, title) for findings without one. Results are sorted
    with critical findings first.

    Args:
        findings: Raw list of finding dicts from all scanners.

    Returns:
        Deduplicated and sorted list of unified finding dicts.
    """
    seen: set[tuple[str, ...]] = set()
    unified: list[dict[str, Any]] = []

    for f in findings:
        # Normalize severity
        f["severity"] = _normalize_severity(f.get("severity", "moderate"))

        # Build dedup key
        if f.get("cve"):
            key = (f["package"], f["cve"])
        else:
            key = (f["package"], f["scanner"], f["title"])

        if key in seen:
            continue
        seen.add(key)
        unified.append(f)

    # Sort by severity rank, then package name
    unified.sort(key=lambda f: (SEVERITY_RANK.get(f["severity"], 99), f["package"]))
    return unified


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def generate_report(
    directory: Path,
    findings: list[dict[str, Any]],
    output_path: Optional[Path],
) -> None:
    """Generate a markdown report to stdout and optionally write JSON to file.

    The report includes a summary table of findings by severity and detailed
    listings grouped by severity level.

    Args:
        directory: Scanned project directory (shown in report header).
        findings: Unified and sorted list of finding dicts.
        output_path: Optional path for JSON file output.
    """
    # Summary counts
    counts: dict[str, int] = {"critical": 0, "high": 0, "moderate": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "moderate")
        counts[sev] = counts.get(sev, 0) + 1

    total = len(findings)

    print()
    print("=" * 60)
    print("  Dependency Vulnerability Audit Report")
    print("=" * 60)
    print(f"  Project: {directory}")
    print(f"  Total findings: {total}")
    print()

    if total == 0:
        print("  No vulnerabilities found.")
        print()
        print("=" * 60)
    else:
        # Summary table
        print("  Severity Breakdown:")
        print("  -------------------")
        for sev in ("critical", "high", "moderate", "low", "info"):
            count = counts.get(sev, 0)
            if count > 0:
                label = sev.upper().ljust(10)
                print(f"    {label} {count}")
        print()

        # Detailed findings grouped by severity
        for sev in ("critical", "high", "moderate", "low", "info"):
            sev_findings = [f for f in findings if f["severity"] == sev]
            if not sev_findings:
                continue

            print(f"  [{sev.upper()}]")
            print(f"  {'-' * 40}")
            for f in sev_findings:
                print(f"    Package:   {f['package']}")
                print(f"    Scanner:   {f['scanner']}")
                print(f"    Title:     {f['title']}")
                if f.get("cve"):
                    print(f"    CVE:       {f['cve']}")
                if f.get("installed_version"):
                    print(f"    Installed: {f['installed_version']}")
                if f.get("fixed_version"):
                    print(f"    Fix:       {f['fixed_version']}")
                if f.get("detail") and f["detail"] != f["title"]:
                    detail_lines = f["detail"].splitlines()
                    print(f"    Detail:    {detail_lines[0]}")
                    for dl in detail_lines[1:]:
                        print(f"               {dl}")
                print()

        print("=" * 60)

    # JSON output
    if output_path is not None:
        report_data = {
            "project": str(directory),
            "total": total,
            "counts": counts,
            "findings": findings,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        log(f"JSON report written to {output_path}", verbose=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_severity(severity: str) -> str:
    """Normalize a severity string to one of the canonical levels."""
    s = severity.strip().lower()
    mapping: dict[str, str] = {
        "critical": "critical",
        "high": "high",
        "moderate": "moderate",
        "medium": "moderate",
        "low": "low",
        "info": "info",
        "informational": "info",
        "none": "info",
    }
    return mapping.get(s, "moderate")


def _extract_cve(text: str) -> Optional[str]:
    """Extract a CVE identifier from a string, if present."""
    import re
    match = re.search(r"CVE-\d{4}-\d{4,}", text)
    return match.group(0) if match else None


def _severity_from_vuln_id(vuln_id: str) -> str:
    """Estimate severity from a vulnerability ID prefix.

    pip-audit does not always include severity, so we assign a default of
    moderate. GHSA and PYSEC entries are treated as moderate unless the
    caller overrides later.
    """
    if not vuln_id:
        return "moderate"
    # CVEs and GHSAs do not encode severity in the ID. Default to moderate
    # and let the user investigate specific IDs.
    return "moderate"


def _filter_by_severity(
    findings: list[dict[str, Any]],
    min_severity: str,
) -> list[dict[str, Any]]:
    """Filter findings to only include those at or above the minimum severity."""
    threshold = SEVERITY_RANK.get(min_severity, 3)
    return [f for f in findings if SEVERITY_RANK.get(f["severity"], 99) <= threshold]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the dependency auditor CLI."""
    parser = argparse.ArgumentParser(
        description="Unified dependency vulnerability scanner.",
        epilog="Example: python3 dependency_auditor.py ./my-project --min-severity moderate",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Path to the project directory to scan.",
    )
    parser.add_argument(
        "--scanners",
        type=str,
        default=None,
        help="Comma-separated list of scanners to run (e.g. npm,pip). Default: auto-detect.",
    )
    parser.add_argument(
        "--min-severity",
        type=str,
        default="low",
        choices=["critical", "high", "moderate", "low", "info"],
        help="Minimum severity to include in the report (default: low).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write JSON report file.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose progress output on stderr.",
    )

    args = parser.parse_args()
    directory: Path = args.directory.resolve()
    verbose: bool = args.verbose

    if not directory.is_dir():
        log_error(f"Directory does not exist: {directory}")
        sys.exit(1)

    # Determine which scanners to run
    if args.scanners:
        requested = [s.strip().lower() for s in args.scanners.split(",")]
        unknown = [s for s in requested if s not in SUPPORTED_SCANNERS]
        if unknown:
            log_warn(f"Unknown scanners ignored: {', '.join(unknown)}")
        ecosystems = [s for s in requested if s in SUPPORTED_SCANNERS]
    else:
        log(f"Auto-detecting project types in {directory}...", verbose)
        ecosystems = detect_project_type(directory)

    if not ecosystems:
        log_warn(
            f"No supported project types detected in {directory}. "
            f"Supported: {', '.join(sorted(SUPPORTED_SCANNERS))}"
        )
        sys.exit(0)

    log(f"Scanners to run: {', '.join(ecosystems)}", verbose)

    # Collect findings from all scanners
    all_findings: list[dict[str, Any]] = []

    if "npm" in ecosystems:
        log("Running npm audit...", verbose)
        all_findings.extend(run_npm_audit(directory))
        log(f"npm audit: {len(all_findings)} raw findings so far.", verbose)

    if "pip" in ecosystems:
        pip_start = len(all_findings)

        log("Running pip-audit...", verbose)
        all_findings.extend(run_pip_audit(directory))

        log("Running pip check...", verbose)
        all_findings.extend(run_pip_check(directory))

        pip_count = len(all_findings) - pip_start
        log(f"pip scanners: {pip_count} raw findings.", verbose)

    # Unify and filter
    unified = unify_results(all_findings)
    filtered = _filter_by_severity(unified, args.min_severity)

    log(
        f"Unified: {len(unified)} total, {len(filtered)} at or above "
        f"{args.min_severity} severity.",
        verbose,
    )

    # Report
    generate_report(directory, filtered, args.output)

    # Exit code: 1 if any critical or high findings remain after filtering
    has_critical_or_high = any(
        f["severity"] in ("critical", "high") for f in filtered
    )
    sys.exit(1 if has_critical_or_high else 0)


if __name__ == "__main__":
    main()
