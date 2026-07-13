#!/usr/bin/env python3
"""checking-license-compliance — audit dep licenses against a policy.

Walks an npm or Python project, extracts the license from each installed
package's metadata, classifies by SPDX family, and emits Findings via
lib/finding.py for any deny-listed, review-required, or unknown-license
package. Detects copyleft contamination of permissive-licensed projects
and SPDX-incompatible license combinations.

Policy is a JSON file at ./.license-policy.json (auto-detected) or passed
via --policy. Default policy flags GPL/AGPL family in projects declaring
MIT/Apache-2.0/BSD.

Usage:
    python3 check_licenses.py PATH [--output FILE] [--format json|jsonl|markdown]
                                   [--min-severity sev] [--policy FILE]
                                   [--emit-attribution]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# --- lib/ import -------------------------------------------------------------
_LIB_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_LIB_ROOT))

from lib.finding import Finding, Severity  # noqa: E402
from lib import report  # noqa: E402


SKILL_ID = "checking-license-compliance"
CATEGORY = "license-compliance"

# SPDX family classification — broad, not legal advice.
STRONG_COPYLEFT = {
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
}
WEAK_COPYLEFT = {
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
    "MPL-1.1",
    "MPL-2.0",
    "EPL-1.0",
    "EPL-2.0",
    "CDDL-1.0",
    "CDDL-1.1",
}
PERMISSIVE = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "0BSD",
    "Unlicense",
    "CC0-1.0",
    "Zlib",
    "Python-2.0",
}

DEFAULT_POLICY: dict[str, Any] = {
    "allow": list(PERMISSIVE),
    "deny": list(STRONG_COPYLEFT),
    "review": ["MPL-2.0", "EPL-2.0", "CDDL-1.0"] + list(WEAK_COPYLEFT - {"MPL-2.0", "EPL-2.0", "CDDL-1.0"}),
    "project_license": None,  # auto-detected from project metadata
}

# Known-incompatible pairs (illustrative subset — not exhaustive legal advice).
INCOMPATIBLE_PAIRS: list[tuple[str, str]] = [
    ("GPL-2.0-only", "Apache-2.0"),  # no patent grant in GPLv2
    ("GPL-2.0-only", "CDDL-1.0"),
    ("MPL-1.1", "GPL-2.0-only"),
]


# --- Policy loading ----------------------------------------------------------


def load_policy(directory: Path, override_path: Path | None) -> dict[str, Any]:
    if override_path:
        with open(override_path, encoding="utf-8") as fh:
            return json.load(fh)
    auto = directory / ".license-policy.json"
    if auto.exists():
        with open(auto, encoding="utf-8") as fh:
            return json.load(fh)
    return dict(DEFAULT_POLICY)


# --- Project license detection ----------------------------------------------


def detect_project_license(directory: Path) -> str | None:
    pkg = directory / "package.json"
    if pkg.exists():
        try:
            with open(pkg, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None
        lic = data.get("license")
        if isinstance(lic, str):
            return lic
        if isinstance(lic, dict):
            return lic.get("type")

    pyproj = directory / "pyproject.toml"
    if pyproj.exists():
        text = pyproj.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^\s*license\s*=\s*[\'"]([^\'"]+)[\'"]', text, flags=re.M)
        if m:
            return m.group(1)
        m = re.search(r'license\s*=\s*{\s*text\s*=\s*[\'"]([^\'"]+)[\'"]', text)
        if m:
            return m.group(1)
    return None


# --- npm dep enumeration ----------------------------------------------------


def enumerate_npm_packages(directory: Path) -> list[dict[str, Any]]:
    """Walk node_modules/<pkg>/package.json and extract license info."""
    out: list[dict[str, Any]] = []
    nm = directory / "node_modules"
    if not nm.is_dir():
        return out
    for pkg_json in nm.glob("**/package.json"):
        # Skip nested node_modules within packages — those are already
        # captured under their own top-level walk if hoisted, and
        # represent installed copies that don't add new license info.
        rel = pkg_json.relative_to(nm)
        if any(part == "node_modules" for part in rel.parts[:-1]):
            continue
        try:
            with open(pkg_json, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        name = data.get("name") or str(rel.parent)
        version = data.get("version") or "?"
        lic = data.get("license")
        license_str: str
        if isinstance(lic, str):
            license_str = lic
        elif isinstance(lic, dict):
            license_str = lic.get("type") or "UNKNOWN"
        elif isinstance(lic, list):
            license_str = " OR ".join(str(l.get("type") if isinstance(l, dict) else l) for l in lic)
        else:
            license_str = "UNKNOWN"
        out.append(
            {
                "ecosystem": "npm",
                "name": name,
                "version": version,
                "license": license_str.strip(),
                "path": str(pkg_json),
                "homepage": data.get("homepage", ""),
            }
        )
    return out


# --- Python dep enumeration -------------------------------------------------


def enumerate_python_packages(directory: Path) -> list[dict[str, Any]]:
    """Walk site-packages METADATA files for installed Python packages.

    Searches a few likely locations: a `.venv/lib/pythonX.Y/site-packages`
    inside the project, then the active interpreter's site-packages.
    """
    out: list[dict[str, Any]] = []
    candidates: list[Path] = []
    # Project-local venv
    for venv in directory.glob(".venv/lib/python*/site-packages"):
        candidates.append(venv)
    for venv in directory.glob("venv/lib/python*/site-packages"):
        candidates.append(venv)
    # Fall back to the running interpreter's site-packages
    if not candidates:
        import sysconfig

        purelib = sysconfig.get_paths().get("purelib")
        if purelib:
            candidates.append(Path(purelib))

    seen: set[tuple[str, str]] = set()
    for site_pkgs in candidates:
        if not site_pkgs.is_dir():
            continue
        for metadata_file in list(site_pkgs.glob("*.dist-info/METADATA")) + list(site_pkgs.glob("*.egg-info/PKG-INFO")):
            try:
                text = metadata_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            name_m = re.search(r"^Name:\s*(.+)$", text, flags=re.M)
            ver_m = re.search(r"^Version:\s*(.+)$", text, flags=re.M)
            lic_m = re.search(r"^License:\s*(.+)$", text, flags=re.M)
            classifier_lics = re.findall(
                r"^Classifier:\s*License\s*::\s*(?:OSI Approved\s*::\s*)?(.+)$",
                text,
                flags=re.M,
            )
            name = name_m.group(1).strip() if name_m else metadata_file.parent.name
            version = ver_m.group(1).strip() if ver_m else "?"
            license_str = (lic_m.group(1).strip() if lic_m else "") or (
                ", ".join(c.strip() for c in classifier_lics) if classifier_lics else "UNKNOWN"
            )
            key = (name, version)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "ecosystem": "pypi",
                    "name": name,
                    "version": version,
                    "license": license_str,
                    "path": str(metadata_file),
                    "homepage": "",
                }
            )
    return out


# --- Classification + finding emission --------------------------------------


def classify_license(license_str: str) -> str:
    """Return a family label for a license string."""
    s = (license_str or "").strip()
    if not s or s.upper() in {"UNKNOWN", "UNLICENSED", "NONE"}:
        return "unknown"
    # Try matching SPDX-ish parts (e.g. "MIT OR Apache-2.0" — take the first).
    parts = re.split(r"\s+(?:OR|AND|WITH)\s+", s)
    head = parts[0].strip().strip("()")
    if head in STRONG_COPYLEFT:
        return "strong_copyleft"
    if head in WEAK_COPYLEFT:
        return "weak_copyleft"
    if head in PERMISSIVE:
        return "permissive"
    # Loose heuristics for non-SPDX strings
    if re.search(r"\b(AGPL|GPL)\b", s, flags=re.I):
        return "strong_copyleft"
    if re.search(r"\b(LGPL|MPL|EPL|CDDL)\b", s, flags=re.I):
        return "weak_copyleft"
    if re.search(r"\b(MIT|Apache|BSD|ISC|Unlicense|CC0)\b", s, flags=re.I):
        return "permissive"
    return "custom"


def assess_package(pkg: dict[str, Any], policy: dict[str, Any], project_license: str | None) -> Finding | None:
    license_str = pkg["license"]
    family = classify_license(license_str)

    head = re.split(r"\s+(?:OR|AND|WITH)\s+", license_str)[0].strip().strip("()")

    deny = set(policy.get("deny", []))
    review = set(policy.get("review", []))
    allow = set(policy.get("allow", []))

    if head in deny or family == "strong_copyleft":
        if project_license in PERMISSIVE or (policy.get("project_license") in PERMISSIVE):
            severity = Severity.CRITICAL
            title = (
                f"Strong-copyleft license ({license_str}) in a {project_license or 'permissive'} project: {pkg['name']}"
            )
        else:
            severity = Severity.HIGH
            title = f"Deny-listed license ({license_str}) on {pkg['name']}"
        remediation = (
            f"1. Remove {pkg['name']} from the dependency tree, OR\n"
            "2. Replace with a permissively-licensed equivalent, OR\n"
            "3. Re-license the project to a compatible license (legal review required), OR\n"
            "4. Document an explicit exception with legal sign-off."
        )
    elif head in review or family == "weak_copyleft":
        severity = Severity.MEDIUM
        title = f"Review-required license ({license_str}) on {pkg['name']}"
        remediation = (
            f"Send {pkg['name']} ({license_str}) to legal for review.\n"
            "Weak-copyleft licenses typically require source disclosure on modified\n"
            "versions; obligations vary. Document the legal position."
        )
    elif family == "unknown":
        severity = Severity.MEDIUM
        title = f"Unknown license on {pkg['name']}"
        remediation = (
            f"Inspect {pkg['path']} for a LICENSE file or check the package home page.\n"
            "If no license is granted, default copyright applies — you may have NO rights\n"
            "to redistribute. Either remove the package or obtain explicit permission."
        )
    elif family == "custom":
        severity = Severity.HIGH
        title = f"Custom / non-SPDX license on {pkg['name']}"
        remediation = (
            f"License declared as `{license_str}` — not a standard SPDX identifier.\n"
            "Custom licenses require manual legal review. Either ensure the license\n"
            "text is reviewed or replace with a package whose license is SPDX-standard."
        )
    elif head in allow or family == "permissive":
        # Permissive — emit INFO reminding to attribute.
        severity = Severity.INFO
        title = f"Permissive license ({license_str}) on {pkg['name']} — attribution recommended"
        remediation = (
            f"Add {pkg['name']} ({license_str}) to your project's NOTICE / attribution file.\n"
            "Use --emit-attribution to auto-generate NOTICE.md."
        )
    else:
        return None

    evidence: tuple[tuple[str, Any], ...] = (
        ("ecosystem", pkg["ecosystem"]),
        ("name", pkg["name"]),
        ("version", pkg["version"]),
        ("declared_license", license_str),
        ("family", family),
        ("project_license", project_license or "<unknown>"),
    )
    references_list: list[str] = []
    if head in (PERMISSIVE | STRONG_COPYLEFT | WEAK_COPYLEFT):
        references_list.append(f"https://spdx.org/licenses/{head}.html")
    if pkg.get("homepage"):
        references_list.append(pkg["homepage"])

    return Finding(
        skill_id=SKILL_ID,
        title=title,
        severity=severity,
        target=f"{pkg['ecosystem']}::{pkg['name']}@{pkg['version']}",
        detail=(
            f"Declared license: {license_str}\n"
            f"Classified family: {family}\n"
            f"Project license: {project_license or '<unknown>'}\n"
            f"Policy match: {('deny' if head in deny else 'review' if head in review else 'allow' if head in allow else 'default')}"
        ),
        remediation=remediation,
        references=tuple(references_list),
        evidence=evidence,
    )


def emit_attribution(packages: list[dict[str, Any]], output_path: Path) -> None:
    lines = [
        "# NOTICE",
        "",
        "This product includes the following third-party packages and their",
        "respective licenses. The full text of each license is available at the",
        "SPDX URL or the package home page.",
        "",
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for pkg in packages:
        family = classify_license(pkg["license"])
        if family != "permissive":
            continue
        grouped.setdefault(pkg["license"], []).append(pkg)
    for license_str, pkgs in sorted(grouped.items()):
        lines.append(f"## {license_str}")
        lines.append("")
        for pkg in sorted(pkgs, key=lambda p: p["name"]):
            lines.append(f"- **{pkg['name']}** @ {pkg['version']}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


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
    p.add_argument("--policy", default=None)
    p.add_argument(
        "--emit-attribution",
        action="store_true",
        help="Also emit NOTICE.md listing permissively-licensed deps for attribution.",
    )
    return p


def _filter_min_severity(findings: list[Finding], min_sev: str) -> list[Finding]:
    floor = Severity(min_sev).numeric
    return [f for f in findings if f.severity.numeric >= floor]


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    directory = Path(args.path).resolve()

    policy = load_policy(directory, Path(args.policy).resolve() if args.policy else None)
    project_license = policy.get("project_license") or detect_project_license(directory)

    packages = enumerate_npm_packages(directory) + enumerate_python_packages(directory)

    if not packages:
        findings = [
            Finding(
                skill_id=SKILL_ID,
                title="no packages found to audit",
                severity=Severity.INFO,
                target=str(directory),
                detail=(
                    "Neither node_modules/ nor a Python venv site-packages was found.\n"
                    "Install deps first (`npm install` / `pip install -r requirements.txt`) "
                    "and re-run."
                ),
                remediation="Install dependencies, then re-run.",
            )
        ]
    else:
        findings = []
        for pkg in packages:
            f = assess_package(pkg, policy, project_license)
            if f is not None:
                findings.append(f)
        if not findings:
            findings = [
                Finding(
                    skill_id=SKILL_ID,
                    title="all dependency licenses pass policy",
                    severity=Severity.INFO,
                    target=str(directory),
                    detail=f"Audited {len(packages)} packages; none triggered findings.",
                    remediation="No action required.",
                )
            ]

    if args.emit_attribution:
        emit_attribution(packages, directory / "NOTICE.md")

    findings = _filter_min_severity(findings, args.min_severity)
    report.emit(findings, args.output, args.format, scan_target=str(directory))
    return report.exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
