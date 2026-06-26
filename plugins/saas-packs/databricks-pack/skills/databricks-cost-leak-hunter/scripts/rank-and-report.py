#!/usr/bin/env python3
"""Deterministic ranker + CFO-report renderer for databricks-cost-leak-hunter.

The LLM does NOT do the dollar arithmetic. This script ingests the per-category
detection results (JSON, one object per leak category with a 30-day savings/waste
figure and a confidence tier), converts to monthly, ranks descending by monthly
dollar impact, and renders the CFO-grokkable report verbatim per
references/cfo-output-format.md.

CRITICAL invariant (per references/cfo-output-format.md): NEVER sum confirmed and
unconfirmed (estimated/at-risk) dollars under one verb. The headline is split into
a confirmed half ("is burning ~$X/month") and a pending half ("plus up to
~$Y/month pending review"), and the ranked table carries a load-bearing
Confidence column.

Input (stdin or --in): a JSON array of category objects, each:
    {
      "category": "...",            # short leak name
      "root_cause": "...",          # FinOps-language cause
      "fix": "...",                 # the one config change
      "waste_30d_usd": <float>,     # 30-day dollar figure (from system.billing.usage)
      "kind": "confirmed" | "estimated" | "at-risk"
    }

Usage:
    jq -s '.' scripts/out/leak-*.json | python3 scripts/rank-and-report.py \
        --out scripts/out/cost-leak-report.md [--monthly-spend 100000] [--window-end 2026-06-22]
"""

from __future__ import annotations

import argparse
import json
import sys

UNCONFIRMED = ("estimated", "at-risk")


def to_monthly(waste_30d: float) -> float:
    """30-day window -> calendar-month figure (365/12 days per month)."""
    return waste_30d * (365.0 / 12.0) / 30.0


def fmt_money_full(n: float) -> str:
    """Full-digit dollars, no decimals: 12000 -> $12,000."""
    return f"${round(n):,}"


def fmt_money_k(n: float) -> str:
    """K-abbreviated annualized dollars: 144000 -> $144K."""
    return f"${round(n / 1000):,}K"


def build_report(categories: list[dict], monthly_spend: float | None, window_end: str | None) -> str:
    ranked = sorted(
        ({**c, "monthly": to_monthly(float(c.get("waste_30d_usd") or 0))} for c in categories),
        key=lambda c: c["monthly"],
        reverse=True,
    )
    # Split sum — confirmed and unconfirmed dollars are NEVER added under one verb.
    confirmed_monthly = sum(c["monthly"] for c in ranked if c.get("kind") == "confirmed")
    unconfirmed_monthly = sum(c["monthly"] for c in ranked if c.get("kind") in UNCONFIRMED)
    confirmed_annual = confirmed_monthly * 12.0
    unconfirmed_annual = unconfirmed_monthly * 12.0

    lines: list[str] = []
    spend_label = fmt_money_full(monthly_spend) if monthly_spend else "$<spend>"

    # A — split headline (confirmed leads; pending hedged).
    lines.append(
        f"### A {spend_label}/month Databricks workspace is burning "
        f"**~{fmt_money_full(confirmed_monthly)}/month** (confirmed), plus up to "
        f"**~{fmt_money_full(unconfirmed_monthly)}/month** pending review"
    )
    lines.append("")
    window = f"Trailing 30 days ending {window_end}" if window_end else "Trailing 30 days"
    lines.append(
        f"{window}. Confirmed **~{fmt_money_k(confirmed_annual)}/year**; up to "
        f"**~{fmt_money_k(unconfirmed_annual)}/year** more pending review. Every dollar "
        f"is computed from the workspace's own `system.billing.usage` table. Every line "
        f"below is one config change."
    )
    lines.append("")

    # B — ranked table with the load-bearing Confidence column.
    lines.append("| # | Where it's leaking | $/month | Confidence | The fix |")
    lines.append("|---|---|--:|---|---|")
    for i, c in enumerate(ranked, start=1):
        confidence = str(c.get("kind", "confirmed")).capitalize()
        lines.append(
            f"| {i} | **{c.get('category', '?')}** — {c.get('root_cause', '')} "
            f"| **{fmt_money_full(c['monthly'])}** | {confidence} | {c.get('fix', '')} |"
        )
    lines.append("")

    if ranked:
        top = ranked[0]
        top_kind = str(top.get("kind", "confirmed"))
        top_annual = top["monthly"] * 12.0
        lines.append(
            f"**The #1 line alone — {(top.get('category') or '?').lower()} "
            f"({top_kind}) — is ~{fmt_money_k(top_annual)}/year, fixed in one setting.**"
        )
        lines.append("")

    lines.append(
        "> **What's assumed vs. what's cited.** Only the workspace-spend input is "
        "assumed. Every per-row dollar figure is computed from the customer's own "
        "`system.billing.usage` table — never estimated. The `Confidence` column marks "
        "which leaks are measured billed spend (Confirmed) vs. modeled savings "
        "(Estimated / At-risk)."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="-")
    ap.add_argument("--out", dest="outfile", required=True)
    ap.add_argument("--monthly-spend", type=float, default=None)
    ap.add_argument("--window-end", dest="window_end", default=None)
    args = ap.parse_args()

    if args.infile == "-":
        raw = sys.stdin.read()
    else:
        with open(args.infile) as fh:
            raw = fh.read()

    data = json.loads(raw)
    if isinstance(data, list):
        categories = data
    elif isinstance(data, dict):
        categories = data.get("categories", [])
    else:
        print(
            "error: input must be a JSON array of category objects (or an object with a 'categories' array)",
            file=sys.stderr,
        )
        return 1

    report = build_report(categories, args.monthly_spend, args.window_end)
    with open(args.outfile, "w") as fh:
        fh.write(report)
    print(f"wrote {args.outfile} ({len(categories)} categories ranked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
