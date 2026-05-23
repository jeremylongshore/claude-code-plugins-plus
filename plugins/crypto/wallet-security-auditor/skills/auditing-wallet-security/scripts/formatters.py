#!/usr/bin/env python3
"""
Output Formatters for Wallet Security Auditor

Format security audit results for display.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from dataclasses import asdict
from typing import List, Any
from decimal import Decimal

from approval_scanner import TokenApproval, ApprovalSummary
from risk_scorer import SecurityScore, RiskFactor, Recommendation


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def format_address(address: str, length: int = 10) -> str:
    """Format address for display."""
    if len(address) <= length * 2 + 2:
        return address
    return f"{address[:length]}...{address[-8:]}"


def format_allowance(allowance: Decimal, is_unlimited: bool) -> str:
    """Format allowance for display."""
    if is_unlimited:
        return "UNLIMITED"
    if allowance >= 1_000_000_000:
        return f"{allowance / 1_000_000_000:.2f}B"
    if allowance >= 1_000_000:
        return f"{allowance / 1_000_000:.2f}M"
    if allowance >= 1_000:
        return f"{allowance / 1_000:.2f}K"
    return f"{allowance:.4f}"


def format_risk_badge(severity: str) -> str:
    """Format risk severity badge."""
    badges = {
        "critical": "[CRITICAL]",
        "high": "[HIGH]",
        "medium": "[MEDIUM]",
        "low": "[LOW]",
        "info": "[INFO]",
    }
    return badges.get(severity.lower(), "[UNKNOWN]")


def format_score_bar(score: int, width: int = 20) -> str:
    """Format score as visual bar."""
    filled = int((score / 100) * width)
    empty = width - filled

    if score >= 80:
        char = "█"
    elif score >= 50:
        char = "▓"
    elif score >= 30:
        char = "▒"
    else:
        char = "░"

    return f"[{char * filled}{'·' * empty}] {score}/100"


def format_approvals_table(approvals: List[TokenApproval], show_all: bool = False, max_rows: int = 20) -> str:
    """Format approvals as ASCII table.

    Args:
        approvals: List of token approvals
        show_all: Show all approvals (ignore max_rows)
        max_rows: Maximum rows to display

    Returns:
        Formatted table string
    """
    if not approvals:
        return "No active approvals found."

    display_approvals = approvals if show_all else approvals[:max_rows]

    # Header
    lines = [
        "",
        "┌" + "─" * 12 + "┬" + "─" * 25 + "┬" + "─" * 18 + "┬" + "─" * 10 + "┐",
        "│ {:^10} │ {:^23} │ {:^16} │ {:^8} │".format("Token", "Spender", "Allowance", "Risk"),
        "├" + "─" * 12 + "┼" + "─" * 25 + "┼" + "─" * 18 + "┼" + "─" * 10 + "┤",
    ]

    for approval in display_approvals:
        spender_display = approval.spender_name or format_address(approval.spender, 8)
        allowance_display = format_allowance(approval.allowance, approval.is_unlimited)

        risk_display = ""
        if approval.is_risky:
            risk_display = "RISKY"
        elif approval.is_unlimited:
            risk_display = "UNLIM"
        else:
            risk_display = "OK"

        lines.append(
            "│ {:>10} │ {:>23} │ {:>16} │ {:^8} │".format(
                approval.token_symbol[:10],
                spender_display[:23],
                allowance_display[:16],
                risk_display,
            )
        )

    lines.append("└" + "─" * 12 + "┴" + "─" * 25 + "┴" + "─" * 18 + "┴" + "─" * 10 + "┘")

    if not show_all and len(approvals) > max_rows:
        lines.append(f"\n... and {len(approvals) - max_rows} more approvals")

    return "\n".join(lines)


def format_approval_summary(summary: ApprovalSummary) -> str:
    """Format approval summary statistics.

    Args:
        summary: ApprovalSummary data

    Returns:
        Formatted summary string
    """
    lines = [
        "",
        "═══════════════════════════════════════════════════════════════════",
        "                      APPROVAL SUMMARY                              ",
        "═══════════════════════════════════════════════════════════════════",
        "",
        f"  Total Active Approvals:   {summary.total_approvals}",
        f"  Unlimited Approvals:      {summary.unlimited_approvals}",
        f"  Risky Approvals:          {summary.risky_approvals}",
        f"  Unique Spenders:          {summary.unique_spenders}",
        f"  Unique Tokens:            {summary.unique_tokens}",
        "",
    ]

    if summary.unlimited_approvals > 0:
        lines.append(f"  ⚠️  {summary.unlimited_approvals} unlimited approval(s) detected")

    if summary.risky_approvals > 0:
        lines.append(f"  🚨 {summary.risky_approvals} risky approval(s) detected")

    lines.append("═══════════════════════════════════════════════════════════════════")

    return "\n".join(lines)


def format_security_score(score: SecurityScore) -> str:
    """Format security score report.

    Args:
        score: SecurityScore data

    Returns:
        Formatted report string
    """
    # Risk level colors/indicators
    level_indicators = {
        "critical": "🔴 CRITICAL",
        "high": "🟠 HIGH",
        "medium": "🟡 MEDIUM",
        "low": "🟢 LOW",
        "safe": "✅ SAFE",
    }

    level_display = level_indicators.get(score.risk_level, score.risk_level.upper())

    lines = [
        "",
        "╔═══════════════════════════════════════════════════════════════════╗",
        "║                    WALLET SECURITY SCORE                          ║",
        "╠═══════════════════════════════════════════════════════════════════╣",
        "║                                                                   ║",
        f"║  Overall Score:  {format_score_bar(score.total_score):<40}       ║",
        f"║  Risk Level:     {level_display:<40}       ║",
        "║                                                                   ║",
        "╠═══════════════════════════════════════════════════════════════════╣",
        "║  Component Scores:                                                ║",
        f"║    Approvals:     {format_score_bar(score.approval_score):<40}  ║",
        f"║    Interactions:  {format_score_bar(score.interaction_score):<40}  ║",
        f"║    Patterns:      {format_score_bar(score.pattern_score):<40}  ║",
        "║                                                                   ║",
        "╚═══════════════════════════════════════════════════════════════════╝",
    ]

    return "\n".join(lines)


def format_risk_factors(factors: List[RiskFactor], max_display: int = 10) -> str:
    """Format risk factors list.

    Args:
        factors: List of risk factors
        max_display: Maximum factors to show

    Returns:
        Formatted factors string
    """
    if not factors:
        return "\nNo risk factors identified."

    lines = [
        "",
        "═══════════════════════════════════════════════════════════════════",
        "                       RISK FACTORS                                 ",
        "═══════════════════════════════════════════════════════════════════",
    ]

    for i, factor in enumerate(factors[:max_display], 1):
        badge = format_risk_badge(factor.severity)
        lines.extend(
            [
                "",
                f"  {i}. {badge} {factor.description}",
                f"     Category: {factor.category}",
            ]
        )

        if factor.affected_items:
            lines.append(f"     Affected: {', '.join(factor.affected_items[:3])}")

        if factor.mitigation:
            lines.append(f"     Action: {factor.mitigation}")

        lines.append(f"     Impact: {factor.score_impact:+d} points")

    if len(factors) > max_display:
        lines.append(f"\n  ... and {len(factors) - max_display} more factors")

    lines.append("\n═══════════════════════════════════════════════════════════════════")

    return "\n".join(lines)


def format_recommendations(recommendations: List[Recommendation]) -> str:
    """Format recommendations list.

    Args:
        recommendations: List of recommendations

    Returns:
        Formatted recommendations string
    """
    if not recommendations:
        return "\nNo recommendations at this time."

    priority_icons = {
        1: "🚨",
        2: "⚠️",
        3: "💡",
        4: "ℹ️",
    }

    lines = [
        "",
        "═══════════════════════════════════════════════════════════════════",
        "                     RECOMMENDATIONS                                ",
        "═══════════════════════════════════════════════════════════════════",
    ]

    for rec in recommendations:
        icon = priority_icons.get(rec.priority, "•")
        lines.extend(
            [
                "",
                f"  {icon} Priority {rec.priority}: {rec.action}",
                f"     Reason: {rec.reason}",
            ]
        )

        if rec.items:
            lines.append("     Items:")
            for item in rec.items[:5]:
                lines.append(f"       - {item}")

    lines.append("\n═══════════════════════════════════════════════════════════════════")

    return "\n".join(lines)


def format_full_report(
    address: str, chain: str, summary: ApprovalSummary, score: SecurityScore, explorer_url: str = ""
) -> str:
    """Format complete security audit report.

    Args:
        address: Wallet address
        chain: Chain name
        summary: Approval summary
        score: Security score
        explorer_url: Block explorer URL

    Returns:
        Full formatted report
    """
    lines = [
        "",
        "╔═══════════════════════════════════════════════════════════════════╗",
        "║              WALLET SECURITY AUDIT REPORT                         ║",
        "╚═══════════════════════════════════════════════════════════════════╝",
        "",
        f"  Address: {address}",
        f"  Chain:   {chain.capitalize()}",
    ]

    if explorer_url:
        lines.append(f"  Explorer: {explorer_url}/address/{address}")

    lines.append("")

    # Add security score
    lines.append(format_security_score(score))

    # Add approval summary
    lines.append(format_approval_summary(summary))

    # Add approvals table
    lines.append("\n--- Active Approvals ---")
    lines.append(format_approvals_table(summary.approvals))

    # Add risk factors
    if score.risk_factors:
        lines.append(format_risk_factors(score.risk_factors))

    # Add recommendations
    if score.recommendations:
        lines.append(format_recommendations(score.recommendations))

    # Footer
    lines.extend(
        [
            "",
            "═══════════════════════════════════════════════════════════════════",
            "  Report generated by Wallet Security Auditor",
            "  For detailed analysis, use: wallet_auditor.py scan --verbose",
            "═══════════════════════════════════════════════════════════════════",
        ]
    )

    return "\n".join(lines)


def format_revoke_list(approvals: List[TokenApproval]) -> str:
    """Format list of approvals to revoke.

    Args:
        approvals: List of approvals to revoke

    Returns:
        Formatted revoke list
    """
    if not approvals:
        return "No approvals recommended for revocation."

    lines = [
        "",
        "═══════════════════════════════════════════════════════════════════",
        "                   REVOKE RECOMMENDATIONS                           ",
        "═══════════════════════════════════════════════════════════════════",
        "",
        "  The following approvals should be reviewed and potentially revoked:",
        "",
    ]

    for i, approval in enumerate(approvals, 1):
        spender_display = approval.spender_name or format_address(approval.spender)
        risk_indicator = " 🚨 RISKY" if approval.is_risky else ""

        lines.extend(
            [
                f"  {i}. {approval.token_symbol} → {spender_display}{risk_indicator}",
                f"     Token:   {approval.token_address}",
                f"     Spender: {approval.spender}",
            ]
        )

        if approval.is_unlimited:
            lines.append("     Amount:  UNLIMITED (max uint256)")
        else:
            lines.append(f"     Amount:  {format_allowance(approval.allowance, False)}")

        if approval.risk_reason:
            lines.append(f"     Risk:    {approval.risk_reason}")

        lines.append("")

    lines.extend(
        [
            "  To revoke, use:",
            "    - revoke.cash",
            "    - Etherscan Token Approval Checker",
            "    - Your wallet's built-in approval manager",
            "",
            "═══════════════════════════════════════════════════════════════════",
        ]
    )

    return "\n".join(lines)


def to_json(data: Any, indent: int = 2) -> str:
    """Convert data to JSON string.

    Args:
        data: Data to convert (dataclass or dict)
        indent: JSON indentation

    Returns:
        JSON string
    """
    if hasattr(data, "__dataclass_fields__"):
        data = asdict(data)
    return json.dumps(data, indent=indent, cls=DecimalEncoder)


def main():
    """Test formatters."""
    from approval_scanner import ApprovalScanner
    from risk_scorer import RiskScorer

    print("=== Formatter Test ===")

    # Create mock data
    scanner = ApprovalScanner(chain="ethereum", verbose=True)
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    print(f"Scanning {test_address[:20]}...")
    summary = scanner.get_all_approvals(test_address)

    print(format_approval_summary(summary))
    print(format_approvals_table(summary.approvals))

    # Calculate score
    scorer = RiskScorer()
    score = scorer.get_total_score(summary)

    print(format_security_score(score))
    print(format_risk_factors(score.risk_factors))
    print(format_recommendations(score.recommendations))


if __name__ == "__main__":
    main()
