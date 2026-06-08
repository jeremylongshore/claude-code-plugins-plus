#!/usr/bin/env python3
"""mapping-findings-to-owasp-top10 — enrich findings with OWASP categories.

Reads findings JSONL/JSON files, applies a deterministic rule table to assign
each finding to an OWASP Top 10 (2021) category, writes back an enriched
JSONL, and produces a per-category coverage report. Emits operational
Findings via lib/finding.py for any parse / unmapped issue.

Usage:
    python3 map_owasp.py PATH [--source FILE] [--enrich-output FILE]
                              [--coverage-output FILE] [--overrides FILE]
                              [--output FILE] [--format json|jsonl|markdown]
                              [--min-severity sev]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# --- lib/ import -------------------------------------------------------------
_LIB_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_LIB_ROOT))

from lib.finding import Finding, Severity  # noqa: E402
from lib import report  # noqa: E402

try:
    import yaml  # type: ignore[import-not-found]

    _HAS_PYYAML = True
except ImportError:
    yaml = None
    _HAS_PYYAML = False


SKILL_ID = "mapping-findings-to-owasp-top10"
CATEGORY = "owasp-mapping"

# OWASP Top 10 (2021) categories
OWASP_CATEGORIES = {
    "A01": "A01:2021 — Broken Access Control",
    "A02": "A02:2021 — Cryptographic Failures",
    "A03": "A03:2021 — Injection",
    "A04": "A04:2021 — Insecure Design",
    "A05": "A05:2021 — Security Misconfiguration",
    "A06": "A06:2021 — Vulnerable and Outdated Components",
    "A07": "A07:2021 — Identification and Authentication Failures",
    "A08": "A08:2021 — Software and Data Integrity Failures",
    "A09": "A09:2021 — Security Logging and Monitoring Failures",
    "A10": "A10:2021 — Server-Side Request Forgery",
}

# Skill-ID → OWASP category default mapping (deterministic).
# These are coarse defaults; detail-keyword rules below can override.
SKILL_TO_OWASP: dict[str, str] = {
    # Cluster 1 — Network/Transport
    "analyzing-tls-config": "A02",
    "detecting-ssl-cert-issues": "A02",
    "auditing-cors-policy": "A01",
    "checking-http-security-headers": "A05",
    "probing-dangerous-http-methods": "A05",
    # Cluster 2 — Information disclosure
    "detecting-exposed-secrets-files": "A02",
    "detecting-debug-endpoints": "A05",
    "fingerprinting-server-software": "A06",
    "detecting-directory-listing": "A05",
    # Cluster 3 — Static analysis
    "scanning-for-hardcoded-secrets": "A02",
    "detecting-sql-injection-patterns": "A03",
    "detecting-command-injection-patterns": "A03",
    "detecting-eval-exec-usage": "A03",
    "detecting-insecure-deserialization": "A08",
    "detecting-weak-cryptography": "A02",
    # Cluster 4 — Dependencies
    "auditing-npm-dependencies": "A06",
    "auditing-python-dependencies": "A06",
    "checking-license-compliance": "A06",
    "tracing-transitive-vulnerabilities": "A06",
    # Cluster 5 — Governance (not application-vulnerability findings;
    # mapped to A04 Insecure Design when classifying for coverage purposes)
    "confirming-pentest-authorization": "A04",
    "defining-pentest-scope": "A04",
    "recording-pentest-engagement": "A09",
}

# CWE → OWASP A0X mapping (subset; canonical OWASP cross-walk).
CWE_TO_OWASP = {
    "CWE-22": "A01",  # Path traversal
    "CWE-23": "A01",
    "CWE-200": "A01",
    "CWE-285": "A01",
    "CWE-639": "A01",
    "CWE-26": "A02",  # Cryptographic
    "CWE-261": "A02",
    "CWE-296": "A02",
    "CWE-310": "A02",
    "CWE-319": "A02",
    "CWE-321": "A02",
    "CWE-326": "A02",
    "CWE-327": "A02",
    "CWE-352": "A03",
    "CWE-77": "A03",  # Command injection
    "CWE-78": "A03",
    "CWE-79": "A03",  # XSS
    "CWE-89": "A03",  # SQL injection
    "CWE-94": "A03",
    "CWE-1021": "A04",
    "CWE-209": "A05",  # information leak via error msg
    "CWE-548": "A05",  # directory listing
    "CWE-1004": "A05",
    "CWE-1104": "A06",  # vulnerable third-party
    "CWE-1395": "A06",
    "CWE-287": "A07",  # auth
    "CWE-306": "A07",
    "CWE-307": "A07",
    "CWE-345": "A08",
    "CWE-502": "A08",  # insecure deserialization
    "CWE-829": "A08",
    "CWE-117": "A09",  # log injection
    "CWE-778": "A09",  # insufficient logging
    "CWE-918": "A10",  # SSRF
}

# Detail-keyword fallback rules. Tuple of (keyword, category).
DETAIL_KEYWORDS: list[tuple[str, str]] = [
    ("sql injection", "A03"),
    ("command injection", "A03"),
    ("xss", "A03"),
    ("cross-site scripting", "A03"),
    ("deserialization", "A08"),
    ("ssrf", "A10"),
    ("server-side request forgery", "A10"),
    ("tls", "A02"),
    ("ssl", "A02"),
    ("cipher", "A02"),
    ("md5", "A02"),
    ("sha1", "A02"),
    ("hardcoded secret", "A02"),
    ("hardcoded credential", "A02"),
    ("api key", "A02"),
    ("path traversal", "A01"),
    ("directory traversal", "A01"),
    ("cors", "A01"),
    ("dependency", "A06"),
    ("transitive", "A06"),
    ("cve-", "A06"),
    ("authentication", "A07"),
    ("session", "A07"),
    ("brute force", "A07"),
    ("debug", "A05"),
    ("misconfiguration", "A05"),
    ("header", "A05"),
    ("logging", "A09"),
    ("monitoring", "A09"),
    ("authorization", "A04"),
    ("scope", "A04"),
]


# --- Helpers ----------------------------------------------------------------


def _f(
    severity: Severity,
    title: str,
    target: str,
    detail: str,
    remediation: str,
    evidence: tuple[tuple[str, Any], ...] = (),
) -> Finding:
    return Finding(
        skill_id=SKILL_ID,
        title=title,
        severity=severity,
        target=target,
        detail=detail,
        remediation=remediation,
        evidence=evidence,
    )


# --- Source loading ---------------------------------------------------------


def discover_sources(root: Path, explicit: list[str]) -> list[Path]:
    if explicit:
        return [Path(p).resolve() for p in explicit]
    out: list[Path] = []
    findings_dir = root / "findings"
    if findings_dir.is_dir():
        out.extend(sorted(findings_dir.glob("**/*.json")))
        out.extend(sorted(findings_dir.glob("**/*.jsonl")))
    return [p for p in out if "all-with-owasp" not in p.name]


def load_records(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [], f"read failed: {e}"
    text = text.strip()
    if not text:
        return [], None
    out: list[dict[str, Any]] = []
    if path.suffix == ".jsonl":
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                return out, f"line parse error: {e}"
        return out, None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return [], f"parse error: {e}"
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)], None
    if isinstance(data, dict) and "findings" in data:
        return [r for r in data["findings"] if isinstance(r, dict)], None
    return [], None


# --- Overrides --------------------------------------------------------------


def load_overrides(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if _HAS_PYYAML:
        data = yaml.safe_load(text) or []
        return data if isinstance(data, list) else []
    # No YAML lib — refuse rather than misparse
    return []


def apply_override(record: dict[str, Any], override: dict[str, Any]) -> bool:
    skill = record.get("skill_id", "")
    detail = record.get("detail", "")
    if "skill_id" in override and override["skill_id"] != skill:
        return False
    if "detail_contains" in override and override["detail_contains"] not in detail:
        return False
    return True


# --- Mapping logic ----------------------------------------------------------


def classify(record: dict[str, Any], overrides: list[dict[str, Any]]) -> tuple[str | None, str]:
    """Return (owasp_code, rule_that_matched). owasp_code is None if unmapped."""
    # 1. Engagement-specific overrides
    for ov in overrides:
        if apply_override(record, ov):
            cat = ov.get("owasp_category", "")
            code = cat.split(":", 1)[0].strip() if cat else None
            if code in OWASP_CATEGORIES:
                return code, f"override: {ov.get('reason', 'no reason given')}"

    # 2. CWE-based mapping
    cwe = record.get("cwe_id")
    if cwe and cwe in CWE_TO_OWASP:
        return CWE_TO_OWASP[cwe], f"cwe-mapping: {cwe}"

    # 3. Skill-ID default
    skill = record.get("skill_id", "")
    if skill in SKILL_TO_OWASP:
        return SKILL_TO_OWASP[skill], f"skill-default: {skill}"

    # 4. Detail-keyword fallback
    detail = (record.get("detail", "") + " " + record.get("title", "")).lower()
    for kw, code in DETAIL_KEYWORDS:
        if kw in detail:
            return code, f"keyword: {kw}"

    return None, "no rule matched"


# --- Coverage report --------------------------------------------------------


def render_coverage(
    counts_by_cat: dict[str, list[dict[str, Any]]],
    engagement_id: str,
    unmapped: list[dict[str, Any]],
) -> str:
    lines = [
        f"# OWASP Top 10 (2021) Coverage — {engagement_id}",
        "",
        "| Category | Count | Critical | High | Medium | Low | Info |",
        "|---|---|---|---|---|---|---|",
    ]
    for code in sorted(OWASP_CATEGORIES.keys()):
        bucket = counts_by_cat.get(code, [])
        sev_counts = Counter(r.get("severity", "info") for r in bucket)
        lines.append(
            f"| **{OWASP_CATEGORIES[code]}** "
            f"| {len(bucket)} "
            f"| {sev_counts.get('critical', 0)} "
            f"| {sev_counts.get('high', 0)} "
            f"| {sev_counts.get('medium', 0)} "
            f"| {sev_counts.get('low', 0)} "
            f"| {sev_counts.get('info', 0)} |"
        )
    if unmapped:
        lines.append("")
        lines.append(f"## Unmapped findings ({len(unmapped)})")
        lines.append("")
        for r in unmapped[:20]:
            lines.append(f"- `{r.get('skill_id', '?')}` — {r.get('title', '')}")
        if len(unmapped) > 20:
            lines.append(f"- … and {len(unmapped) - 20} more")
    lines.append("")
    lines.append("## Per-category findings detail")
    for code in sorted(OWASP_CATEGORIES.keys()):
        bucket = counts_by_cat.get(code, [])
        if not bucket:
            continue
        lines.append("")
        lines.append(f"### {OWASP_CATEGORIES[code]} — {len(bucket)} finding(s)")
        for r in sorted(bucket, key=lambda x: x.get("title", "")):
            sev = r.get("severity", "info").upper()
            lines.append(f"- **[{sev}]** `{r.get('skill_id', '?')}` — {r.get('title', '')}")
    return "\n".join(lines)


# --- Engagement-id detection ------------------------------------------------


def detect_engagement_id(root: Path) -> str:
    roe = root / "roe.yaml"
    if not roe.exists():
        return root.name
    try:
        for line in roe.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("engagement_id:"):
                return line.split(":", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return root.name


# --- CLI ---------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("path", help="Engagement directory")
    p.add_argument("--source", action="append", default=[])
    p.add_argument("--enrich-output", default=None)
    p.add_argument("--coverage-output", default=None)
    p.add_argument("--overrides", default=None)
    p.add_argument("--output", default=None)
    p.add_argument("--format", default="markdown", choices=["json", "jsonl", "markdown"])
    p.add_argument(
        "--min-severity",
        default="info",
        choices=["info", "low", "medium", "high", "critical"],
    )
    return p


def _filter_min_severity(findings: list[Finding], min_sev: str) -> list[Finding]:
    floor = Severity(min_sev).numeric
    return [f for f in findings if f.severity.numeric >= floor]


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    root = Path(args.path).resolve()
    if not root.exists():
        f = _f(
            Severity.CRITICAL,
            f"engagement path missing: {root}",
            str(root),
            f"PATH `{root}` does not exist.",
            "Verify the engagement directory and re-run.",
        )
        report.emit([f], args.output, args.format, scan_target=str(root))
        return 1

    sources = discover_sources(root, args.source)
    if not sources:
        f = _f(
            Severity.HIGH,
            "no findings sources",
            str(root),
            f"No findings files under `{root}`.",
            "Run cluster 1-4 skills first.",
        )
        report.emit([f], args.output, args.format, scan_target=str(root))
        return 1

    overrides = load_overrides(Path(args.overrides).resolve()) if args.overrides else []

    op_findings: list[Finding] = []
    enriched: list[dict[str, Any]] = []
    by_cat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unmapped: list[dict[str, Any]] = []

    for src in sources:
        records, err = load_records(src)
        if err:
            op_findings.append(
                _f(
                    Severity.HIGH,
                    f"source unparseable: {src.name}",
                    str(src),
                    err,
                    "Fix the source or exclude.",
                )
            )
            continue
        for rec in records:
            code, rule = classify(rec, overrides)
            if code:
                category_str = OWASP_CATEGORIES[code]
                rec["owasp_category"] = category_str
                by_cat[code].append(rec)
            else:
                rec["owasp_category"] = "UNMAPPED"
                unmapped.append(rec)
                op_findings.append(
                    _f(
                        Severity.INFO,
                        f"unmapped: {rec.get('title', '')[:80]}",
                        str(src),
                        f"Skill `{rec.get('skill_id', '?')}` produced a finding the rule table couldn't classify.",
                        "Extend the rule table or accept as cross-cutting.",
                        evidence=(
                            ("skill", rec.get("skill_id", "")),
                            ("title", rec.get("title", "")),
                        ),
                    )
                )
            enriched.append(rec)

    # Write enriched output
    enrich_path = (
        Path(args.enrich_output).resolve() if args.enrich_output else root / "findings" / "all-with-owasp.jsonl"
    )
    if str(enrich_path) != "/dev/null":
        try:
            enrich_path.parent.mkdir(parents=True, exist_ok=True)
            with open(enrich_path, "w", encoding="utf-8") as fh:
                for rec in enriched:
                    fh.write(json.dumps(rec) + "\n")
        except OSError as e:
            op_findings.append(
                _f(
                    Severity.HIGH,
                    f"cannot write enriched output: {enrich_path}",
                    str(enrich_path),
                    f"OSError: {e}",
                    "Resolve permissions and re-run.",
                )
            )

    # Coverage report
    coverage_path = (
        Path(args.coverage_output).resolve() if args.coverage_output else root / "reports" / "owasp-coverage.md"
    )
    try:
        coverage_path.parent.mkdir(parents=True, exist_ok=True)
        engagement_id = detect_engagement_id(root)
        coverage_path.write_text(render_coverage(by_cat, engagement_id, unmapped), encoding="utf-8")
        # Coverage-quality assessment
        covered_codes = sum(1 for code in OWASP_CATEGORIES if by_cat.get(code))
        if covered_codes == 10:
            op_findings.append(
                _f(
                    Severity.INFO,
                    "engagement covers all 10 OWASP categories",
                    str(coverage_path),
                    "At least one finding in each of A01-A10.",
                    "Broad-coverage engagement; report includes complete OWASP narrative.",
                    evidence=(("categories_covered", covered_codes),),
                )
            )
        elif covered_codes < 5:
            op_findings.append(
                _f(
                    Severity.MEDIUM,
                    f"engagement covers only {covered_codes} of 10 OWASP categories",
                    str(coverage_path),
                    f"Findings landed in only {covered_codes} categories. Either the "
                    f"engagement scope was narrow OR the rule table didn't recognize "
                    f"findings that should map to additional categories.",
                    "If scope was narrow, document in the engagement summary. Otherwise extend the rule table.",
                    evidence=(("categories_covered", covered_codes),),
                )
            )
        else:
            op_findings.append(
                _f(
                    Severity.INFO,
                    f"OWASP coverage report written: {coverage_path.name}",
                    str(coverage_path),
                    f"Coverage: {covered_codes}/10 categories.",
                    "No action required.",
                )
            )
    except OSError as e:
        op_findings.append(
            _f(
                Severity.HIGH,
                f"cannot write coverage report: {coverage_path}",
                str(coverage_path),
                f"OSError: {e}",
                "Resolve permissions and re-run.",
            )
        )

    if not op_findings:
        op_findings = [
            _f(
                Severity.INFO,
                "OWASP mapping complete",
                str(root),
                f"{len(enriched)} findings annotated; {len(unmapped)} unmapped.",
                "No action required.",
            )
        ]

    op_findings = _filter_min_severity(op_findings, args.min_severity)
    report.emit(op_findings, args.output, args.format, scan_target=str(root))
    return report.exit_code(op_findings)


if __name__ == "__main__":
    sys.exit(main())
