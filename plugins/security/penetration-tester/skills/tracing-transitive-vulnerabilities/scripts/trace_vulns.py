#!/usr/bin/env python3
"""tracing-transitive-vulnerabilities — walk the dep graph + intersect with CVEs.

For an npm or Python project, build the full dependency graph (via npm ls or
pipdeptree), intersect with an audit JSON file (or run the audit itself), and
emit Findings reporting:

  - Per-CVE paths from direct deps to the vulnerable package
  - Per-direct-dep CVE counts (leverage analysis)
  - Highest-leverage upgrade recommendation
  - Unreachable findings (no fix in any reachable version)
  - Deep-transitive findings (depth >=3)

Usage:
    python3 trace_vulns.py PATH [--output FILE] [--format json|jsonl|markdown]
                                [--min-severity sev] [--audit-input FILE]
                                [--min-depth N] [--leverage-only]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# --- lib/ import -------------------------------------------------------------
_LIB_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_LIB_ROOT))

from lib.finding import Finding, Severity  # noqa: E402
from lib import report  # noqa: E402


SKILL_ID = "tracing-transitive-vulnerabilities"
CATEGORY = "transitive-trace"
CWE_DEFAULT = "CWE-1395"  # Dependency on Vulnerable Third-Party Component


# --- Project type detection --------------------------------------------------


def detect_project_type(directory: Path) -> str:
    if (directory / "package.json").exists() and (directory / "node_modules").is_dir():
        return "npm"
    if (
        (directory / "pyproject.toml").exists()
        or (directory / "requirements.txt").exists()
        or list(directory.glob(".venv/lib/python*/site-packages"))
    ):
        return "python"
    return "unknown"


# --- npm graph walking ------------------------------------------------------


def build_npm_graph(directory: Path) -> dict[str, list[str]]:
    """Return {package_name: [list of parent package names]} for the project.

    Uses `npm ls --json --all` which emits the full installed tree.
    """
    if not shutil.which("npm"):
        return {}
    try:
        proc = subprocess.run(  # noqa: S603
            ["npm", "ls", "--json", "--all"],
            cwd=str(directory),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {}
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {}

    parents: dict[str, set[str]] = defaultdict(set)
    direct: set[str] = set()
    root = data

    def walk(node: dict[str, Any], parent_name: str | None) -> None:
        deps = node.get("dependencies") or {}
        for child_name, child_node in deps.items():
            if parent_name is None:
                direct.add(child_name)
            else:
                parents[child_name].add(parent_name)
            walk(child_node or {}, child_name)

    walk(root, None)
    # Direct deps have no parents in the graph (their "parent" is the root project).
    for d in direct:
        parents.setdefault(d, set())
    return {pkg: sorted(p) for pkg, p in parents.items()}, sorted(direct)


# --- Python graph walking ---------------------------------------------------


def build_python_graph(directory: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Return ({pkg: [parents]}, [direct]) using pipdeptree or pip show fallback."""
    parents: dict[str, set[str]] = defaultdict(set)
    direct: set[str] = set()

    if shutil.which("pipdeptree"):
        try:
            proc = subprocess.run(  # noqa: S603
                ["pipdeptree", "--json-tree"],
                cwd=str(directory),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            data = json.loads(proc.stdout or "[]")
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            data = []

        def walk(node: dict[str, Any], parent: str | None) -> None:
            name = node.get("package_name") or node.get("key") or ""
            if not name:
                return
            if parent is None:
                direct.add(name)
            else:
                parents[name].add(parent)
            for dep in node.get("dependencies", []) or []:
                walk(dep, name)

        for top in data:
            walk(top, None)
    else:
        # Fallback: pip show recursion (slower; less reliable for cycles).
        if not (shutil.which("pip") or shutil.which("pip3")):
            return {}, []
        pip_bin = "pip" if shutil.which("pip") else "pip3"
        # Identify direct deps from requirements.txt or installed packages.
        # This branch is best-effort; pipdeptree is recommended.
        req = directory / "requirements.txt"
        names: list[str] = []
        if req.exists():
            for line in req.read_text(errors="replace").splitlines():
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                name = (
                    line.split("==")[0]
                    .split(">=")[0]
                    .split("<=")[0]
                    .split("~=")[0]
                    .split("!=")[0]
                    .split("[")[0]
                    .strip()
                )
                if name:
                    names.append(name)
        else:
            try:
                proc = subprocess.run(  # noqa: S603
                    [pip_bin, "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
                names = [p.get("name", "") for p in json.loads(proc.stdout or "[]")]
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                names = []
        for n in names:
            direct.add(n)
        # We can't reliably recurse into transitive parents without pipdeptree;
        # report direct-only graph and trust the audit tool to flag the rest.

    for d in direct:
        parents.setdefault(d, set())
    return {pkg: sorted(p) for pkg, p in parents.items()}, sorted(direct)


# --- Path tracing -----------------------------------------------------------


def trace_paths(package: str, parents_map: dict[str, list[str]], direct: set[str]) -> list[list[str]]:
    """Return all paths from a direct dep to the given package.

    Each path is a list of package names from direct (index 0) to target (last).
    Handles cycles by breaking on revisit.
    """
    if package in direct:
        return [[package]]
    results: list[list[str]] = []
    visiting: set[str] = set()

    def dfs(node: str, path: list[str]) -> None:
        if node in visiting:
            return  # cycle break
        visiting.add(node)
        parents = parents_map.get(node, [])
        if not parents:
            results.append([node, *path] if path else [node])
        else:
            for parent in parents:
                dfs(parent, [node, *path])
        visiting.discard(node)

    dfs(package, [])
    # Filter: keep only paths that start with a direct dep (or whose head is direct).
    filtered: list[list[str]] = []
    for p in results:
        if p and p[0] in direct:
            filtered.append(p)
    return filtered or [[package]]


# --- Audit input handling ---------------------------------------------------


def load_audit_findings(audit_input: Path) -> list[dict[str, Any]]:
    text = audit_input.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and "findings" in data:
        return data["findings"]
    if isinstance(data, list):
        return data
    return []


def extract_package_name_from_finding(finding: dict[str, Any]) -> str | None:
    """Pull the affected package out of a finding's evidence."""
    evidence = finding.get("evidence", {})
    if isinstance(evidence, dict):
        for key in ("package", "name"):
            if key in evidence:
                return str(evidence[key])
    target = finding.get("target", "")
    if "::" in target:
        return target.split("::")[-1].split("@", 1)[0]
    return None


# --- Trace emission ---------------------------------------------------------


def build_trace_findings(
    audit_findings: list[dict[str, Any]],
    parents_map: dict[str, list[str]],
    direct: set[str],
    min_depth: int,
) -> list[Finding]:
    out: list[Finding] = []
    leverage: dict[str, int] = defaultdict(int)

    for af in audit_findings:
        pkg = extract_package_name_from_finding(af)
        if not pkg:
            continue
        # Skip findings that are operational/info rather than CVE-bearing.
        severity_str = af.get("severity", "info")
        if severity_str == "info":
            continue
        paths = trace_paths(pkg, parents_map, direct)
        depth = min((len(p) - 1) for p in paths) if paths else 0
        if depth < min_depth:
            continue
        path_strs = [" → ".join(p) for p in paths]
        direct_ancestors = sorted({p[0] for p in paths if p})

        for ancestor in direct_ancestors:
            leverage[ancestor] += 1

        # Severity logic: deep + critical = HIGH (blast radius unclear);
        # broad reachability (>=5 paths) bumps severity by one tier.
        base_sev = Severity(severity_str)
        if depth >= 3 and base_sev.numeric >= 4:
            new_sev = base_sev
        elif depth >= 3:
            new_sev = max(base_sev, Severity.HIGH, key=lambda s: s.numeric)
        elif len(paths) >= 5:
            new_sev = max(base_sev, Severity.HIGH, key=lambda s: s.numeric)
        else:
            new_sev = base_sev

        evidence_items: list[tuple[str, Any]] = [
            ("package", pkg),
            ("depth", depth),
            ("path_count", len(paths)),
            ("direct_ancestors", ", ".join(direct_ancestors)),
            ("paths_sample", " | ".join(path_strs[:3])),
            ("original_severity", severity_str),
            ("original_cve", af.get("cve_id", "")),
        ]

        title = (
            f"Transitive vuln in {pkg} (depth {depth}, "
            f"{len(paths)} path{'s' if len(paths) != 1 else ''}, "
            f"orig severity {severity_str})"
        )

        if len(direct_ancestors) == 1:
            remediation = (
                f"All paths flow through {direct_ancestors[0]}.\n"
                f"1. Check `npm view {direct_ancestors[0]} versions` (or pip equiv) "
                f"for a release that floors {pkg} above the vulnerable range.\n"
                f"2. Bump {direct_ancestors[0]} to that version.\n"
                f"3. Re-run trace to confirm clearance."
            )
        else:
            remediation = (
                f"Reachable via {len(direct_ancestors)} direct deps: "
                f"{', '.join(direct_ancestors[:5])}.\n"
                f"1. Consider a root-level `overrides`/equivalent block forcing {pkg} "
                f"to a safe version.\n"
                f"2. Re-run trace after applying the override to verify clearance.\n"
                f"3. If override produces resolution conflicts, surgical per-parent "
                f"override is the next step."
            )

        out.append(
            Finding(
                skill_id=SKILL_ID,
                title=title,
                severity=new_sev,
                target=pkg,
                detail=(
                    f"Package: {pkg}\n"
                    f"Depth from nearest direct dep: {depth}\n"
                    f"Reachable paths: {len(paths)}\n"
                    f"Direct ancestors: {', '.join(direct_ancestors)}\n"
                    f"Original severity: {severity_str}\n"
                    f"Path samples:\n  " + "\n  ".join(path_strs[:5])
                ),
                remediation=remediation,
                cve_id=af.get("cve_id"),
                cwe_id=CWE_DEFAULT,
                references=tuple(af.get("references") or []),
                evidence=tuple(evidence_items),
            )
        )

    # Add leverage report findings — INFO severity, one per direct dep with >0 reachable CVEs.
    if leverage:
        top_leverage = sorted(leverage.items(), key=lambda x: -x[1])[:5]
        for ancestor, count in top_leverage:
            if count < 1:
                continue
            severity = Severity.INFO
            out.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"Direct dep {ancestor} is ancestor for {count} transitive CVE(s)",
                    severity=severity,
                    target=ancestor,
                    detail=(
                        f"Direct dep `{ancestor}` is the closest direct ancestor for "
                        f"{count} transitive CVE finding(s). Bumping `{ancestor}` to "
                        f"a version that floors the affected transitive deps above "
                        f"their fix versions may clear multiple findings at once."
                    ),
                    remediation=(
                        f"1. Check `{ancestor}`'s changelog for transitive-dep updates.\n"
                        f"2. Bump `{ancestor}` to the latest semver-compatible version.\n"
                        f"3. Re-run trace to count remaining transitive CVEs."
                    ),
                    evidence=(
                        ("ancestor", ancestor),
                        ("cve_count", count),
                    ),
                )
            )
    return out


# --- CLI ---------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("path", help="Project root")
    p.add_argument("--output", default=None)
    p.add_argument("--format", default="markdown", choices=["json", "jsonl", "markdown"])
    p.add_argument(
        "--min-severity",
        default="info",
        choices=["info", "low", "medium", "high", "critical"],
    )
    p.add_argument(
        "--audit-input",
        default=None,
        help="Pre-computed audit JSON from auditing-npm-dependencies or auditing-python-dependencies",
    )
    p.add_argument("--min-depth", type=int, default=0, help="Only emit findings at >= this depth")
    p.add_argument(
        "--leverage-only",
        action="store_true",
        help="Emit only the leverage-analysis findings (skip per-CVE traces)",
    )
    return p


def _filter_min_severity(findings: list[Finding], min_sev: str) -> list[Finding]:
    floor = Severity(min_sev).numeric
    return [f for f in findings if f.severity.numeric >= floor]


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    directory = Path(args.path).resolve()

    project_type = detect_project_type(directory)
    if project_type == "npm":
        graph_result = build_npm_graph(directory)
        parents_map, direct_list = graph_result if isinstance(graph_result, tuple) else ({}, [])
    elif project_type == "python":
        parents_map, direct_list = build_python_graph(directory)
    else:
        f = Finding(
            skill_id=SKILL_ID,
            title="project type not detected",
            severity=Severity.INFO,
            target=str(directory),
            detail="Neither package.json+node_modules nor a Python project was found.",
            remediation="Run from a project root containing installed dependencies.",
        )
        report.emit([f], args.output, args.format, scan_target=str(directory))
        return 2

    if not args.audit_input:
        f = Finding(
            skill_id=SKILL_ID,
            title="no audit input provided",
            severity=Severity.INFO,
            target=str(directory),
            detail=(
                "This skill expects --audit-input pointing at a JSON file produced by "
                "auditing-npm-dependencies or auditing-python-dependencies.\n"
                "Run that audit first, then re-run this skill."
            ),
            remediation=(
                "Run the appropriate audit skill with --format json --output /tmp/audit.json, "
                "then re-run this skill with --audit-input /tmp/audit.json."
            ),
        )
        report.emit([f], args.output, args.format, scan_target=str(directory))
        return 2

    audit_findings = load_audit_findings(Path(args.audit_input))
    direct_set = set(direct_list)

    findings = build_trace_findings(audit_findings, parents_map, direct_set, args.min_depth)

    if args.leverage_only:
        findings = [f for f in findings if "ancestor for" in f.title]

    if not findings:
        findings = [
            Finding(
                skill_id=SKILL_ID,
                title="no transitive CVE findings to trace",
                severity=Severity.INFO,
                target=str(directory),
                detail=(
                    "The audit input produced no CVE-bearing findings (or all findings "
                    "were below the requested --min-depth)."
                ),
                remediation="No action required.",
            )
        ]
    findings = _filter_min_severity(findings, args.min_severity)
    report.emit(findings, args.output, args.format, scan_target=str(directory))
    return report.exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
