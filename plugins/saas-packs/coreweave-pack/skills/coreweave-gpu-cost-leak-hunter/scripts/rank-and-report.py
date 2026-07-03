#!/usr/bin/env python3
"""Deterministic ranker + CFO-report renderer for coreweave-gpu-cost-leak-hunter.

The LLM does NOT do the dollar arithmetic. CoreWeave exposes no dollars metric — spend
is reconstructed by multiplying PromQL usage counts by a rate card — so this script
ingests the per-category detection results (JSON, one object per leak) and does every
multiplication, sum, and ranking itself, then renders the CFO-grokkable report verbatim
per references/cfo-output-format.md.

CRITICAL invariant (per references/cfo-output-format.md): NEVER sum confirmed and
unconfirmed (estimated/at-risk) dollars under one verb. The headline is split into a
confirmed half ("is burning ~$X/month") and a pending half ("plus up to ~$Y/month
pending review"), and the ranked table carries a load-bearing Confidence column.

Input (stdin or --in): a JSON array of leak objects, each:
    {
      "category": "...",       # short leak name
      "root_cause": "...",     # FinOps-language cause
      "fix": "...",            # the one change
      "kind": "confirmed" | "estimated" | "at-risk",
      # the 30-day dollar figure, supplied one of two ways:
      "waste_30d_usd": <float>            # pre-computed dollars, OR
      "usage_gpu_hours": <float>,         # PromQL usage ...
      "rate_usd_per_gpu_hour": <float>,   # ... times the rate card =>
      # optional modifiers (mutually exclusive):
      "reprice_rate_usd_per_gpu_hour": <float>,  # savings = hours*(rate-reprice)
      "discount_frac": <float>                    # savings = hours*rate*discount
    }

Because there is no billing API, `waste_30d_usd = usage_gpu_hours * rate` (or the
re-price / discount variant) is computed HERE, deterministically — never by the agent.

Usage:
    jq -s '.' "$OUT"/leak-*.json | python3 rank-and-report.py \
        --out "$OUT/cost-leak-report.md" [--monthly-spend 180000] [--window-end 2026-06-22]
    python3 rank-and-report.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys

UNCONFIRMED = ("estimated", "at-risk")


def norm_kind(val: object) -> str:
    """Lowercase + strip a confidence tier so case/whitespace never silently drops a
    row from a sum (e.g. "Confirmed" / " AT-RISK " -> "confirmed"/"at-risk")."""
    return str(val or "").strip().lower()


def parse_usd(val: object) -> float:
    """Coerce a dollar/usage figure to float, tolerating LLM-formatted currency
    like "$1,200.50" or "1,200"; fall back to 0.0 on anything still non-numeric."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = str(val).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def waste_30d(leak: dict) -> float:
    """The 30-day dollar figure for a leak.

    CoreWeave has no dollars metric, so unless a pre-computed `waste_30d_usd` is
    supplied, this multiplies PromQL `usage_gpu_hours` by the rate-card
    `rate_usd_per_gpu_hour`, then applies the leak-specific modifier:
      - reprice_rate_usd_per_gpu_hour -> savings = hours * (rate - reprice)  [right-size]
      - discount_frac                 -> savings = hours * rate * discount   [commitment]
      - neither                        -> waste  = hours * rate              [idle]
    """
    if leak.get("waste_30d_usd") is not None:
        return parse_usd(leak.get("waste_30d_usd"))
    hours = parse_usd(leak.get("usage_gpu_hours"))
    rate = parse_usd(leak.get("rate_usd_per_gpu_hour"))
    base = hours * rate
    if leak.get("reprice_rate_usd_per_gpu_hour") is not None:
        reprice = parse_usd(leak.get("reprice_rate_usd_per_gpu_hour"))
        return max(0.0, hours * (rate - reprice))
    if leak.get("discount_frac") is not None:
        return max(0.0, base * parse_usd(leak.get("discount_frac")))
    return base


def to_monthly(w30: float) -> float:
    """30-day window -> calendar-month figure (365/12 days per month)."""
    return w30 * (365.0 / 12.0) / 30.0


def fmt_money_full(n: float) -> str:
    """Full-digit dollars, no decimals: 12000 -> $12,000."""
    return f"${round(n):,}"


def fmt_money_k(n: float) -> str:
    """K-abbreviated annualized dollars: 264000 -> $264K."""
    return f"${round(n / 1000):,}K"


def build_report(leaks: list[dict], monthly_spend: float | None, window_end: str | None) -> str:
    ranked = sorted(
        ({**c, "monthly": to_monthly(waste_30d(c))} for c in leaks),
        key=lambda c: c["monthly"],
        reverse=True,
    )
    # Split sum — confirmed and unconfirmed dollars are NEVER added under one verb.
    # Normalize the kind so a capitalized "Confirmed"/"At-risk" is not silently
    # dropped from its sum (which would understate the headline as ~$0/month).
    confirmed = sum(c["monthly"] for c in ranked if (norm_kind(c.get("kind")) or "confirmed") == "confirmed")
    pending = sum(c["monthly"] for c in ranked if (norm_kind(c.get("kind")) or "confirmed") in UNCONFIRMED)

    lines: list[str] = []
    spend_label = fmt_money_k(monthly_spend) if monthly_spend else "$<SPEND>"

    # A — split headline (confirmed leads; pending hedged).
    lines.append(
        f"### A {spend_label}/month CoreWeave GPU cluster is burning "
        f"**~{fmt_money_full(confirmed)}/month** (confirmed), plus up to "
        f"**~{fmt_money_full(pending)}/month** pending review"
    )
    lines.append("")
    window = f"Trailing 30 days ending {window_end}" if window_end else "Trailing 30 days"
    lines.append(
        f"{window}. Confirmed **~{fmt_money_k(confirmed * 12.0)}/year**; up to "
        f"**~{fmt_money_k(pending * 12.0)}/year** more pending review. Spend is "
        f"reconstructed from PromQL against CoreWeave's managed Grafana (no billing "
        f"API). Every line below is one change."
    )
    lines.append("")

    # B — ranked table with the load-bearing Confidence column.
    lines.append("| # | Where it's leaking | $/month | Confidence | The fix |")
    lines.append("|---|---|--:|---|---|")
    for i, c in enumerate(ranked, start=1):
        confidence = (norm_kind(c.get("kind")) or "confirmed").capitalize()
        lines.append(
            f"| {i} | **{c.get('category', '?')}** — {c.get('root_cause', '')} "
            f"| **{fmt_money_full(c['monthly'])}** | {confidence} | {c.get('fix', '')} |"
        )
    lines.append("")

    # C — the #1-line callout.
    if ranked:
        top = ranked[0]
        top_kind = norm_kind(top.get("kind")) or "confirmed"
        lines.append(
            f"**The #1 line alone — {(top.get('category') or '?').lower()} "
            f"({top_kind}) — is ~{fmt_money_k(top['monthly'] * 12.0)}/year, fixed in one setting.**"
        )
        lines.append("")

    # D — assumed-vs-measured disclosure.
    lines.append(
        "> **What's assumed vs. what's measured.** The monthly GPU spend is the only "
        "assumed input. Every per-row dollar figure is computed by multiplying PromQL "
        "usage (from CoreWeave's managed Grafana) by the rate card — CoreWeave exposes "
        "no dollars metric, so there is no single billed number to read. The "
        "`Confidence` column marks billed idle waste (Confirmed) vs. a right-sizing "
        "model (Estimated) vs. a commitment decision (At-risk)."
    )
    lines.append("")
    return "\n".join(lines)


def _load(raw: str) -> list[dict]:
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("leaks", data.get("categories", []))
    raise ValueError("input must be a JSON array of leak objects (or an object with a 'leaks' array)")


def self_test() -> int:
    """Tiny self-test: proves usage x rate math and the never-sum split invariant."""
    sample = [
        # Confirmed idle reserved: 8000 GPU-hrs * $2.25/hr = $18,000/30d.
        {
            "category": "Idle reserved GPUs",
            "root_cause": "reserved below floor",
            "fix": "release",
            "kind": "confirmed",
            "usage_gpu_hours": 8000,
            "rate_usd_per_gpu_hour": 2.25,
        },
        # Estimated right-size: 4000 hrs * ($6.155 - $2.25) = $15,620/30d.
        {
            "category": "H100 on small inference",
            "root_cause": "wrong GPU",
            "fix": "move to L40S",
            "kind": "Estimated",  # mis-cased on purpose
            "usage_gpu_hours": 4000,
            "rate_usd_per_gpu_hour": 6.155,
            "reprice_rate_usd_per_gpu_hour": 2.25,
        },
        # At-risk commitment: 6000 hrs * $6.155 * 0.4 = $14,772/30d.
        {
            "category": "Steady on-demand",
            "root_cause": "should commit",
            "fix": "reserve floor",
            "kind": "at-risk",
            "usage_gpu_hours": 6000,
            "rate_usd_per_gpu_hour": 6.155,
            "discount_frac": 0.4,
        },
    ]
    assert abs(waste_30d(sample[0]) - 18000.0) < 1e-6, "idle usage*rate"
    assert abs(waste_30d(sample[1]) - 15620.0) < 1e-6, "reprice delta"
    assert abs(waste_30d(sample[2]) - 14772.0) < 1e-6, "discount"
    report = build_report(sample, monthly_spend=180000, window_end="2026-06-22")
    # Never-sum invariant: the confirmed headline number must equal ONLY the confirmed
    # row (mis-cased "Estimated" must land in pending, not confirmed).
    conf_monthly = to_monthly(18000.0)
    assert f"~{fmt_money_full(conf_monthly)}/month** (confirmed)" in report, "confirmed split"
    assert "pending review" in report, "pending half present"
    assert "Estimated" in report and "At-risk" in report, "confidence tags rendered"
    total = to_monthly(18000.0 + 15620.0 + 14772.0)
    assert fmt_money_full(total) not in report.split("pending review")[0], "no all-in sum in headline"
    print("SELF-TEST PASSED: usage*rate math + confirmed/pending split invariant hold.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="-")
    ap.add_argument("--out", dest="outfile")
    ap.add_argument("--monthly-spend", type=float, default=None)
    ap.add_argument("--window-end", dest="window_end", default=None)
    ap.add_argument("--self-test", action="store_true", help="run the built-in self-test and exit")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.outfile:
        print("error: --out is required (or pass --self-test)", file=sys.stderr)
        return 1

    if args.infile == "-":
        if sys.stdin.isatty():
            print("error: no input on stdin (pipe JSON in, or pass --in <file>)", file=sys.stderr)
            ap.print_help(sys.stderr)
            return 1
        raw = sys.stdin.read()
    else:
        with open(args.infile, encoding="utf-8") as fh:
            raw = fh.read()

    try:
        leaks = _load(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        detail = "empty input" if not raw.strip() else str(exc)
        print(f"error: could not parse input ({detail})", file=sys.stderr)
        return 1

    report = build_report(leaks, args.monthly_spend, args.window_end)
    with open(args.outfile, "w", encoding="utf-8") as fh:
        fh.write(report)
    print(f"wrote {args.outfile} ({len(leaks)} leaks ranked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
