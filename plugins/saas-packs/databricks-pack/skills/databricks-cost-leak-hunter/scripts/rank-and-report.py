#!/usr/bin/env python3
"""Deterministic ranker + CFO-report renderer for databricks-cost-leak-hunter.

The LLM does NOT do the dollar arithmetic. This script ingests the per-category
detection results (JSON, one object per leak category with a 30-day savings/waste
figure), converts to monthly, ranks descending by monthly dollar impact, annualizes
the headline and the #1 line, and renders the CFO-grokkable report verbatim per
references/cfo-output-format.md.

Input (stdin or --in): a JSON array of category objects, each:
    {"category": "...", "fix": "...", "root_cause": "...", "waste_30d_usd": <float>}

Usage:
    jq -s '.' scripts/out/leak-*.json | python3 scripts/rank-and-report.py \
        --out scripts/out/cost-leak-report.md [--monthly-spend 100000]
"""

from __future__ import annotations

import argparse
import json
import sys


def to_monthly(waste_30d: float) -> float:
    """30-day window -> calendar-month figure (365/12 days per month)."""
    return waste_30d * (365.0 / 12.0) / 30.0


def fmt_money_full(n: float) -> str:
    """Full-digit dollars, no decimals: 12000 -> $12,000."""
    return f"${round(n):,}"


def fmt_money_k(n: float) -> str:
    """K-abbreviated annualized dollars: 144000 -> $144K."""
    return f"${round(n / 1000):,}K"


def build_report(categories: list[dict], monthly_spend: float | None) -> str:
    ranked = sorted(
        ({**c, "monthly": to_monthly(float(c.get("waste_30d_usd", 0)))} for c in categories),
        key=lambda c: c["monthly"],
        reverse=True,
    )
    total_monthly = sum(c["monthly"] for c in ranked)
    total_annual = total_monthly * 12.0

    lines: list[str] = []
    spend_label = fmt_money_full(monthly_spend) if monthly_spend else "$<spend>"
    lines.append(
        f"### A {spend_label}/month Databricks workspace is likely burning **~{fmt_money_full(total_monthly)}/month**"
    )
    lines.append("")
    lines.append(
        f"That's **~{fmt_money_k(total_annual)}/year**. Every dollar below is computed "
        f"from the workspace's own `system.billing.usage` table. Every line is one "
        f"config change."
    )
    lines.append("")
    lines.append("| # | Where it's leaking | $/month | The fix |")
    lines.append("|---|---|--:|---|")
    for i, c in enumerate(ranked, start=1):
        lines.append(
            f"| {i} | **{c.get('category', '?')}** — {c.get('root_cause', '')} "
            f"| **{fmt_money_full(c['monthly'])}** | {c.get('fix', '')} |"
        )
    lines.append("")
    if ranked:
        top = ranked[0]
        lines.append(
            f"**The #1 line alone — {top.get('category', '?').lower()} — is "
            f"~{fmt_money_k(top['monthly'] * 12.0)}/year, fixed in one setting.**"
        )
        lines.append("")
    lines.append(
        "> **What's assumed vs. what's cited.** Only the workspace-spend input is "
        "assumed. Every per-row dollar figure is computed from the customer's own "
        "`system.billing.usage` table — never estimated."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="-")
    ap.add_argument("--out", dest="outfile", required=True)
    ap.add_argument("--monthly-spend", type=float, default=None)
    args = ap.parse_args()

    raw = sys.stdin.read() if args.infile == "-" else open(args.infile).read()
    data = json.loads(raw)
    categories = data if isinstance(data, list) else data.get("categories", [])

    report = build_report(categories, args.monthly_spend)
    with open(args.outfile, "w") as fh:
        fh.write(report)
    print(f"wrote {args.outfile} ({len(categories)} categories ranked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
