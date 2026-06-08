#!/usr/bin/env python3
"""generating-executive-summary — render exec-readable engagement summary.

Reads the unified findings JSONL (post OWASP enrichment), the OWASP coverage
report, and the ROE; computes a single risk score; selects top-3 remediation
priorities deterministically; and writes a markdown executive summary intended
for a C-level / board audience.

Usage:
    python3 exec_summary.py PATH [--source FILE] [--coverage FILE] [--roe FILE]
                                  [--summary-output FILE]
                                  [--priority-overrides FILE]
                                  [--output FILE] [--format json|jsonl|markdown]
                                  [--min-severity sev]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
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


SKILL_ID = "generating-executive-summary"
CATEGORY = "executive-summary"


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


def load_findings(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    if not path.exists():
        return [], f"file missing: {path}"
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError as e:
        return [], f"read error: {e}"
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
                return out, f"jsonl line parse error: {e}"
        return out, None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return [], f"json parse error: {e}"
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)], None
    if isinstance(data, dict) and "findings" in data:
        return [r for r in data["findings"] if isinstance(r, dict)], None
    return [], None


def load_roe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if _HAS_PYYAML:
        return yaml.safe_load(text) or {}
    # Minimal extract of key fields without full YAML parse
    out: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("engagement_id:"):
            out["engagement_id"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("  name:") and "authorizer" not in out:
            out.setdefault("authorizer", {})["name"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("authorizer:"):
            out["_in_authorizer"] = True
    return out


# --- Risk score -------------------------------------------------------------


def severity_counts(findings: list[dict[str, Any]]) -> Counter:
    return Counter(r.get("severity", "info") for r in findings)


def compute_risk_score(findings: list[dict[str, Any]], roe_clean: bool) -> int:
    counts = severity_counts(findings)
    score = (
        20 * counts.get("critical", 0)
        + 10 * counts.get("high", 0)
        + 3 * counts.get("medium", 0)
        + 1 * counts.get("low", 0)
    )
    # OWASP-coverage breadth term
    categories = {r.get("owasp_category", "UNMAPPED") for r in findings}
    if "UNMAPPED" in categories:
        categories.discard("UNMAPPED")
    breadth = len(categories)
    if breadth > 5:
        score += 5 * (breadth - 5)
    # Governance bonus
    if roe_clean:
        score -= 10
    return max(0, min(100, score))


def interpret_risk(score: int) -> str:
    if score <= 25:
        return "Low"
    if score <= 50:
        return "Moderate"
    if score <= 75:
        return "Elevated"
    if score <= 90:
        return "High"
    return "Critical"


# --- Top-3 priorities -------------------------------------------------------


def pick_top_priorities(findings: list[dict[str, Any]], overrides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if overrides:
        return overrides[:3]

    # Aggregate by title to detect reachability (same finding affecting many targets)
    by_title: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in findings:
        if r.get("severity", "info") in ("critical", "high"):
            by_title[r.get("title", "<no title>")].append(r)

    if not by_title:
        # No critical/high; fall back to medium
        for r in findings:
            if r.get("severity") == "medium":
                by_title[r.get("title", "<no title>")].append(r)

    # Score: severity-weight * reachability_factor
    severity_weight = {"critical": 100, "high": 50, "medium": 20, "low": 5}

    def title_score(title: str) -> int:
        records = by_title[title]
        max_sev = max(records, key=lambda x: severity_weight.get(x.get("severity", "info"), 0))
        base = severity_weight.get(max_sev.get("severity", "info"), 0)
        reach = len({r.get("target", "") for r in records})
        return base + (reach * 5)

    sorted_titles = sorted(by_title.keys(), key=lambda t: (-title_score(t), t))
    out: list[dict[str, Any]] = []
    for title in sorted_titles[:3]:
        records = by_title[title]
        sample = records[0]
        out.append(
            {
                "title": title,
                "severity": sample.get("severity", "info"),
                "skill_id": sample.get("skill_id", "?"),
                "reach": len({r.get("target", "") for r in records}),
                "effort": estimate_effort(sample),
                "impact": estimate_impact(sample, records),
                "owasp": sample.get("owasp_category", "UNMAPPED"),
                "fingerprint": sample.get("fingerprint", ""),
            }
        )
    return out


def estimate_effort(record: dict[str, Any]) -> str:
    skill = record.get("skill_id", "")
    severity = record.get("severity", "info")
    if "dependencies" in skill or "transitive" in skill:
        return "Hours" if severity in ("critical", "high") else "Days"
    if "secret" in skill or "credential" in skill:
        return "Hours"
    if "config" in skill or "header" in skill or "cors" in skill or "tls" in skill:
        return "Days"
    if "injection" in skill or "deserialization" in skill or "license" in skill:
        return "Weeks"
    return "Days"


def estimate_impact(record: dict[str, Any], all_records: list[dict[str, Any]]) -> str:
    severity = record.get("severity", "info")
    reach = len({r.get("target", "") for r in all_records})
    if severity == "critical":
        return "Material"
    if severity == "high" and reach >= 3:
        return "Material"
    if severity == "high":
        return "Significant"
    if severity == "medium" and reach >= 5:
        return "Significant"
    return "Limited"


def load_priority_overrides(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not _HAS_PYYAML:
        return []
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or []
    return data if isinstance(data, list) else []


# --- ROE summary extraction -------------------------------------------------


def summarize_roe(roe: dict[str, Any]) -> str:
    if not roe:
        return "_ROE not available._"
    eng_id = roe.get("engagement_id", "<unknown>")
    auth = roe.get("authorizer") or {}
    auth_name = auth.get("name", "<unknown>")
    auth_role = auth.get("role", "<role>")
    time = roe.get("time_window") or {}
    start = time.get("start", "<start>")
    end = time.get("end", "<end>")
    in_scope = roe.get("in_scope_targets") or []
    return (
        f"Engagement `{eng_id}` was authorized by {auth_name} ({auth_role}) for the time window "
        f"{start} through {end}. Scope: {len(in_scope)} in-scope target(s)."
    )


# --- Coverage report excerpt ------------------------------------------------


def summarize_coverage(coverage_path: Path) -> str:
    if not coverage_path.exists():
        return "_OWASP coverage report not available._"
    try:
        text = coverage_path.read_text(encoding="utf-8")
    except OSError:
        return "_OWASP coverage report not readable._"
    # Pull the summary table
    lines = text.splitlines()
    out: list[str] = []
    in_table = False
    table_count = 0
    for line in lines:
        if line.startswith("| Category"):
            in_table = True
        if in_table:
            out.append(line)
            if line.startswith("|"):
                table_count += 1
            if table_count > 11:  # header + 10 categories
                break
    return "\n".join(out) if out else "_Coverage table not located._"


# --- Render -----------------------------------------------------------------


def render_summary(
    findings: list[dict[str, Any]],
    risk_score: int,
    risk_band: str,
    counts: Counter,
    priorities: list[dict[str, Any]],
    roe_summary: str,
    coverage_excerpt: str,
    engagement_id: str,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    crit = counts.get("critical", 0)
    high = counts.get("high", 0)
    med = counts.get("medium", 0)
    low = counts.get("low", 0)

    priorities_md = ""
    for i, p in enumerate(priorities, start=1):
        priorities_md += (
            f"### {i}. {p['title']}\n\n"
            f"- **Severity:** {p['severity'].upper()}\n"
            f"- **Reach:** {p['reach']} affected target(s)\n"
            f"- **Estimated effort to remediate:** {p['effort']}\n"
            f"- **Estimated impact if exploited:** {p['impact']}\n"
            f"- **OWASP:** {p['owasp']}\n"
            f"- **Source skill:** `{p['skill_id']}`\n"
            f"- **Cross-reference:** vulnerability-report.md#finding-{p['fingerprint']}\n\n"
        )
    if not priorities_md:
        priorities_md = "_No HIGH or CRITICAL findings identified._\n"

    return f"""# Executive Summary — {engagement_id}

**Generated:** {now}

## Risk score: {risk_score} / 100 ({risk_band})

| Severity | Count |
|---|---|
| CRITICAL | {crit} |
| HIGH | {high} |
| MEDIUM | {med} |
| LOW | {low} |

Risk-score composition: severity-weighted finding counts adjusted for
OWASP-category breadth and engagement governance posture. See the
vulnerability report for full per-finding detail.

## Engagement scope and authorization

{roe_summary}

## Top remediation priorities

{priorities_md}

## OWASP Top 10 (2021) coverage

{coverage_excerpt}

## Suggested next steps

1. Address the top remediation priorities above in the order listed.
   Effort estimates are heuristic; refine after a brief planning
   discussion with the responsible engineering team.
2. File a security-register entry for any MEDIUM-severity finding
   that will not be remediated within the next quarter.
3. Schedule a re-test for the high-priority items once remediation is
   complete to confirm the fixes hold.
4. Treat this summary plus the full vulnerability report as the
   engagement's authoritative deliverables for compliance evidence,
   board reporting, and insurance documentation.

## Reference artifacts

- Full vulnerability report: `reports/vulnerability-report.md`
- OWASP coverage detail: `reports/owasp-coverage.md`
- Engagement archive: `manifest.sha256` + manifest signature
- Rules of Engagement: `roe.yaml`

---
_Generated by `{SKILL_ID}`. The risk-score composition formula and
priority-selection logic are deterministic and documented in the
skill's THEORY reference. Re-running with the same source findings
produces a byte-identical document except for the generation date._
"""


# --- CLI ---------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("path", help="Engagement directory")
    p.add_argument("--source", default=None)
    p.add_argument("--coverage", default=None)
    p.add_argument("--roe", default=None)
    p.add_argument("--summary-output", default=None)
    p.add_argument("--priority-overrides", default=None)
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

    source_path = Path(args.source).resolve() if args.source else root / "findings" / "all-with-owasp.jsonl"
    coverage_path = Path(args.coverage).resolve() if args.coverage else root / "reports" / "owasp-coverage.md"
    roe_path = Path(args.roe).resolve() if args.roe else root / "roe.yaml"

    op_findings: list[Finding] = []

    findings, err = load_findings(source_path)
    if err:
        op_findings.append(
            _f(
                Severity.CRITICAL,
                f"cannot load findings: {source_path.name}",
                str(source_path),
                err,
                "Resolve the source and re-run.",
            )
        )
        report.emit(op_findings, args.output, args.format, scan_target=str(root))
        return 1

    roe = load_roe(roe_path)
    if not roe:
        op_findings.append(
            _f(
                Severity.MEDIUM,
                "ROE not loaded",
                str(roe_path),
                f"No ROE at {roe_path}; scope/authorization section will be a placeholder.",
                "Provide --roe FILE or place the ROE at the expected path.",
            )
        )

    roe_clean = bool(roe.get("authorizer") and roe.get("time_window") and roe.get("signature_block"))

    counts = severity_counts(findings)
    risk = compute_risk_score(findings, roe_clean)
    band = interpret_risk(risk)
    if risk > 90:
        op_findings.append(
            _f(
                Severity.CRITICAL,
                f"risk score {risk} (Critical)",
                str(root),
                "Computed engagement risk is in the Critical band. Findings warrant "
                "executive attention and urgent remediation planning.",
                "Review the top remediation priorities and start remediation today.",
            )
        )
    elif risk > 75:
        op_findings.append(
            _f(
                Severity.HIGH,
                f"risk score {risk} (High)",
                str(root),
                "Computed engagement risk is in the High band.",
                "Schedule executive review and a remediation plan within the next week.",
            )
        )

    overrides = load_priority_overrides(Path(args.priority_overrides).resolve()) if args.priority_overrides else []
    priorities = pick_top_priorities(findings, overrides)

    coverage_excerpt = summarize_coverage(coverage_path)
    if not coverage_path.exists():
        op_findings.append(
            _f(
                Severity.MEDIUM,
                "OWASP coverage report missing",
                str(coverage_path),
                "Coverage section will be a placeholder.",
                "Run mapping-findings-to-owasp-top10 first.",
            )
        )

    engagement_id = roe.get("engagement_id") or root.name
    summary_md = render_summary(
        findings,
        risk,
        band,
        counts,
        priorities,
        summarize_roe(roe),
        coverage_excerpt,
        engagement_id,
    )

    out_path = Path(args.summary_output).resolve() if args.summary_output else root / "reports" / "executive-summary.md"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(summary_md, encoding="utf-8")
        op_findings.append(
            _f(
                Severity.INFO,
                f"executive summary written: {out_path.name}",
                str(out_path),
                f"Risk: {risk}/100 ({band}); priorities: {len(priorities)}; findings: {len(findings)}.",
                "Hand off to customer for the exec-readout meeting.",
                evidence=(
                    ("risk_score", risk),
                    ("band", band),
                    ("finding_count", len(findings)),
                    ("priority_count", len(priorities)),
                    ("output", str(out_path)),
                ),
            )
        )
    except OSError as e:
        op_findings.append(
            _f(
                Severity.HIGH,
                f"cannot write summary: {out_path}",
                str(out_path),
                f"OSError: {e}",
                "Resolve permissions and re-run.",
            )
        )

    op_findings = _filter_min_severity(op_findings, args.min_severity)
    report.emit(op_findings, args.output, args.format, scan_target=str(root))
    return report.exit_code(op_findings)


if __name__ == "__main__":
    sys.exit(main())
