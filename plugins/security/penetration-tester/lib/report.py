"""Report composition for penetration-tester v3 findings.

Emits findings as JSON, JSONL, and Markdown. Per AT-ADEC at
000-docs/001-AT-ADEC-skill-taxonomy.md, every skill emits findings through
finding.Finding and lets this module compose the output so multi-skill scan
runs produce a single deliverable.

Exit codes:
    0 — no critical or high findings
    1 — at least one critical or high finding (suitable for CI gating)
    2 — error during scan execution (authz missing, target unreachable for the
        whole scan, etc.) — distinct from "scan ran, found problems"
"""

from __future__ import annotations

import json
import sys
from typing import Iterable

from .finding import Finding, Severity


def to_json(findings: Iterable[Finding]) -> str:
    """Pretty-printed JSON array of findings, sorted by severity desc then title."""
    sorted_findings = sorted(findings, key=lambda f: (-f.severity.numeric, f.title))
    return json.dumps([f.to_dict() for f in sorted_findings], indent=2)


def to_markdown(findings: Iterable[Finding], scan_target: str) -> str:
    """Human-readable Markdown report grouped by severity.

    Output structure:
        # Penetration Test Report — <target>
        ## Summary (counts per severity)
        ## Critical findings (N)
        ## High findings (N)
        ## Medium findings (N)
        ## Low findings (N)
        ## Info findings (N)
    """
    findings_list = list(findings)
    by_severity: dict[Severity, list[Finding]] = {sev: [] for sev in Severity}
    for f in findings_list:
        by_severity[f.severity].append(f)

    lines: list[str] = []
    lines.append(f"# Penetration Test Report — {scan_target}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---|")
    for sev in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO):
        lines.append(f"| {sev.value.title()} | {len(by_severity[sev])} |")
    lines.append("")

    for sev in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO):
        items = by_severity[sev]
        if not items:
            continue
        lines.append(f"## {sev.value.title()} findings ({len(items)})")
        lines.append("")
        for f in sorted(items, key=lambda x: x.title):
            lines.append(f"### {f.title}")
            lines.append("")
            lines.append(f"- **Target:** `{f.target}`")
            if f.cvss_score is not None:
                lines.append(f"- **CVSS:** {f.cvss_score}")
            if f.cve_id:
                lines.append(f"- **CVE:** {f.cve_id}")
            if f.cwe_id:
                lines.append(f"- **CWE:** {f.cwe_id}")
            if f.owasp_category:
                lines.append(f"- **OWASP:** {f.owasp_category}")
            if f.affected_control:
                lines.append(f"- **Affected control:** {f.affected_control}")
            lines.append("")
            lines.append(f"**Detail:** {f.detail}")
            lines.append("")
            lines.append(f"**Remediation:** {f.remediation}")
            lines.append("")
            if f.references:
                lines.append("**References:**")
                for ref in f.references:
                    lines.append(f"- {ref}")
                lines.append("")
    return "\n".join(lines)


def emit(findings: list[Finding], output: str | None, fmt: str, scan_target: str) -> None:
    """Emit findings to stdout or a file in the requested format.

    Args:
        findings: list of Finding objects
        output: file path or None (stdout)
        fmt: "json" | "markdown" | "jsonl"
        scan_target: human-readable scan target for the report header
    """
    if fmt == "json":
        payload = to_json(findings)
    elif fmt == "markdown":
        payload = to_markdown(findings, scan_target)
    elif fmt == "jsonl":
        payload = "\n".join(json.dumps(f.to_dict()) for f in findings)
    else:
        raise ValueError(f"unknown format: {fmt}")

    if output is None or output == "-":
        sys.stdout.write(payload)
        if not payload.endswith("\n"):
            sys.stdout.write("\n")
    else:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(payload)
            if not payload.endswith("\n"):
                fh.write("\n")


def exit_code(findings: Iterable[Finding]) -> int:
    """Return CI-friendly exit code: 1 if any high/critical findings, else 0."""
    for f in findings:
        if f.severity in (Severity.CRITICAL, Severity.HIGH):
            return 1
    return 0
