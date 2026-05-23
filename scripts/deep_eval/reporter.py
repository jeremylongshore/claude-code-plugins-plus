"""
Multi-format reporter for deep evaluation results.

Outputs:
- Terminal (colorized summary)
- JSON (machine-readable, full detail)
- Markdown (human-readable report)
- HTML (visual report with badges)

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .badges import BADGE_META


def format_terminal(
    results: List[Dict[str, Any]],
    summary: Dict[str, Any],
    rankings: Optional[Dict] = None,
    verbose: bool = False,
) -> str:
    """Format results for terminal output."""
    lines = []
    lines.append("=" * 70)
    lines.append("INTENT SOLUTIONS DEEP EVALUATION ENGINE v1.0")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    lines.append(f"Skills evaluated: {summary['count']}")
    lines.append(f"Mean composite:   {summary['mean_composite']}/100")
    ci = summary.get("ci_95", (0, 0))
    lines.append(f"95% CI:           [{ci[0]}, {ci[1]}]")
    lines.append(f"LLM layer:        {'Active' if summary.get('llm_available') else 'Inactive (static only)'}")
    lines.append("")

    # Badge distribution
    lines.append("Badge Distribution:")
    badge_order = ["flagship", "established", "emerging", "early", "none"]
    badge_emoji = {
        "flagship": "\u2b50",
        "established": "\u2705",
        "emerging": "\U0001f331",
        "early": "\U0001f527",
        "none": " ",
    }
    for badge in badge_order:
        count = summary.get("badge_distribution", {}).get(badge, 0)
        pct = (count / summary["count"] * 100) if summary["count"] else 0
        bar = "\u2588" * int(pct / 2)
        label = badge.capitalize() if badge != "none" else "Unrated"
        emoji = badge_emoji.get(badge, "")
        lines.append(f"  {emoji} {label:10s}: {count:4d} ({pct:5.1f}%) {bar}")
    lines.append("")

    # Grade alignment
    alignment = summary.get("grade_alignment", {})
    if alignment.get("aligned", 0) + alignment.get("divergent", 0) > 0:
        total_compared = alignment["aligned"] + alignment["divergent"]
        align_pct = alignment["aligned"] / total_compared * 100
        lines.append(f"Grade/Badge alignment: {alignment['aligned']}/{total_compared} ({align_pct:.0f}%)")
        lines.append("")

    # Per-skill details (verbose mode)
    if verbose:
        lines.append("-" * 70)
        lines.append("Per-Skill Results:")
        lines.append("-" * 70)

        # Sort by composite score descending
        sorted_results = sorted(results, key=lambda r: r["composite_score"], reverse=True)
        for r in sorted_results:
            badge = r.get("badge") or "none"
            emoji = badge_emoji.get(badge, "")
            name = r.get("skill_name", "?")
            score = r["composite_score"]
            det_score = r.get("deterministic_score", "?")
            elapsed = r.get("elapsed_seconds", 0)

            lines.append(f"  {emoji} {name:40s}  deep={score:5.1f}  det={det_score}  ({elapsed:.1f}s)")

            # Show dimension breakdown
            static_dims = r.get("layers", {}).get("static", {}).get("dimensions", {})
            if static_dims and verbose:
                dim_strs = []
                for dim, data in sorted(static_dims.items(), key=lambda x: x[1].get("weight", 0), reverse=True):
                    dim_strs.append(f"{dim[:12]}={data['score']}")
                lines.append(f"      dims: {', '.join(dim_strs[:5])}")

            # Anti-patterns
            anti = r.get("layers", {}).get("static", {}).get("anti_patterns", {})
            if anti and anti.get("count", 0) > 0:
                lines.append(f"      anti-patterns: {anti['count']} ({', '.join(h['name'] for h in anti['hits'][:3])})")
        lines.append("")

    # Rankings (if available)
    if rankings and rankings.get("category_rankings"):
        lines.append("-" * 70)
        lines.append("Category Rankings (Elo):")
        lines.append("-" * 70)
        for cat, ranked in sorted(rankings["category_rankings"].items()):
            stats = rankings.get("statistics", {}).get(cat, {})
            mean = stats.get("mean", 0)
            count = stats.get("count", 0)
            lines.append(f"\n  {cat} ({count} skills, mean={mean}):")
            for i, (skill_id, data) in enumerate(ranked[:10]):
                name = Path(skill_id).parent.name if "/" in skill_id else skill_id
                lines.append(
                    f"    #{i + 1:2d}  Elo={data['rating']:6.1f}  "
                    f"W={data['wins']} L={data['losses']} D={data['draws']}  "
                    f"{name}"
                )
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def format_json(
    results: List[Dict[str, Any]],
    summary: Dict[str, Any],
    rankings: Optional[Dict] = None,
) -> str:
    """Format results as JSON."""
    output = {
        "version": "1.0.0",
        "engine": "Intent Solutions Deep Evaluation Engine",
        "summary": summary,
        "results": results,
    }
    if rankings:
        # Convert ranking tuples to serializable format
        serializable_rankings = {}
        if "global_ranking" in rankings:
            serializable_rankings["global_ranking"] = [{"skill_path": k, **v} for k, v in rankings["global_ranking"]]
        if "category_rankings" in rankings:
            serializable_rankings["category_rankings"] = {
                cat: [{"skill_path": k, **v} for k, v in ranked]
                for cat, ranked in rankings["category_rankings"].items()
            }
        if "statistics" in rankings:
            serializable_rankings["statistics"] = rankings["statistics"]
        output["rankings"] = serializable_rankings

    return json.dumps(output, indent=2, default=str)


def format_markdown(
    results: List[Dict[str, Any]],
    summary: Dict[str, Any],
    rankings: Optional[Dict] = None,
) -> str:
    """Format results as a Markdown report."""
    lines = []
    lines.append("# Intent Solutions Deep Evaluation Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Skills evaluated | {summary['count']} |")
    lines.append(f"| Mean composite | {summary['mean_composite']}/100 |")
    ci = summary.get("ci_95", (0, 0))
    lines.append(f"| 95% CI | [{ci[0]}, {ci[1]}] |")
    lines.append(f"| Min | {summary.get('min_composite', 0)} |")
    lines.append(f"| Max | {summary.get('max_composite', 0)} |")
    lines.append(f"| LLM layer | {'Active' if summary.get('llm_available') else 'Static only'} |")
    lines.append("")

    # Badge distribution
    lines.append("## Badge Distribution")
    lines.append("")
    lines.append("| Badge | Count | % |")
    lines.append("|-------|-------|---|")
    for badge in ["flagship", "established", "emerging", "early", "none"]:
        count = summary.get("badge_distribution", {}).get(badge, 0)
        pct = (count / summary["count"] * 100) if summary["count"] else 0
        label = badge.capitalize() if badge != "none" else "Unrated"
        meta = BADGE_META.get(badge, {})
        emoji = meta.get("emoji", "")
        lines.append(f"| {emoji} {label} | {count} | {pct:.1f}% |")
    lines.append("")

    # Top and bottom skills
    sorted_results = sorted(results, key=lambda r: r["composite_score"], reverse=True)
    if len(sorted_results) > 5:
        lines.append("## Top 10 Skills")
        lines.append("")
        lines.append("| Rank | Skill | Composite | Badge |")
        lines.append("|------|-------|-----------|-------|")
        for i, r in enumerate(sorted_results[:10]):
            badge = r.get("badge") or "none"
            meta = BADGE_META.get(badge, {})
            emoji = meta.get("emoji", "")
            lines.append(
                f"| {i + 1} | {r['skill_name']} | {r['composite_score']} | {emoji} {badge.capitalize() if badge != 'none' else 'Unrated'} |"
            )
        lines.append("")

        lines.append("## Bottom 10 Skills")
        lines.append("")
        lines.append("| Rank | Skill | Composite | Badge |")
        lines.append("|------|-------|-----------|-------|")
        for i, r in enumerate(sorted_results[-10:]):
            badge = r.get("badge") or "none"
            lines.append(
                f"| {len(sorted_results) - 9 + i} | {r['skill_name']} | {r['composite_score']} | {badge or 'none'} |"
            )
        lines.append("")

    return "\n".join(lines)


def format_html(
    results: List[Dict[str, Any]],
    summary: Dict[str, Any],
    rankings: Optional[Dict] = None,
) -> str:
    """Format results as a self-contained HTML report."""
    sorted_results = sorted(results, key=lambda r: r["composite_score"], reverse=True)

    badge_colors = {
        "flagship": "#DA70D6",
        "established": "#4CAF50",
        "emerging": "#FF9800",
        "early": "#9E9E9E",
        None: "#666",
    }

    rows = []
    for i, r in enumerate(sorted_results):
        badge = r.get("badge")
        color = badge_colors.get(badge, "#666")
        label = badge.capitalize() if badge else "Unrated"
        rows.append(f"""
        <tr>
            <td>{i + 1}</td>
            <td>{r["skill_name"]}</td>
            <td>{r["composite_score"]}</td>
            <td><span style="background:{color};padding:2px 8px;border-radius:4px;
                font-weight:bold;color:#111">{label}</span></td>
            <td>{r.get("deterministic_score", "-")}</td>
        </tr>""")

    ci = summary.get("ci_95", (0, 0))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Deep Evaluation Report — Intent Solutions</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto;
         padding: 20px; background: #0a0a0a; color: #e0e0e0; }}
  h1 {{ color: #f0f0f0; border-bottom: 2px solid #333; padding-bottom: 10px; }}
  h2 {{ color: #ccc; margin-top: 30px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #222; }}
  th {{ background: #1a1a1a; color: #aaa; font-weight: 600; }}
  tr:hover {{ background: #111; }}
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
              gap: 15px; margin: 20px 0; }}
  .stat {{ background: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #222; }}
  .stat-value {{ font-size: 24px; font-weight: bold; color: #f0f0f0; }}
  .stat-label {{ font-size: 12px; color: #888; text-transform: uppercase; }}
</style>
</head>
<body>
<h1>Intent Solutions Deep Evaluation Report</h1>

<div class="summary">
  <div class="stat">
    <div class="stat-value">{summary["count"]}</div>
    <div class="stat-label">Skills Evaluated</div>
  </div>
  <div class="stat">
    <div class="stat-value">{summary["mean_composite"]}</div>
    <div class="stat-label">Mean Composite Score</div>
  </div>
  <div class="stat">
    <div class="stat-value">[{ci[0]}, {ci[1]}]</div>
    <div class="stat-label">95% Confidence Interval</div>
  </div>
  <div class="stat">
    <div class="stat-value">{"Active" if summary.get("llm_available") else "Static"}</div>
    <div class="stat-label">LLM Layer</div>
  </div>
</div>

<h2>All Skills</h2>
<table>
<thead>
  <tr><th>#</th><th>Skill</th><th>Deep Score</th><th>Badge</th><th>Det. Score</th></tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>

<footer style="margin-top:40px;padding-top:20px;border-top:1px solid #222;color:#555;font-size:12px">
  Generated by Intent Solutions Deep Evaluation Engine v1.0 |
  Tons of Skills by Intent Solutions
</footer>
</body>
</html>"""
