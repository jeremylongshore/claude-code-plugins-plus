#!/usr/bin/env python3
"""
Wallet Security Auditor

Audit wallet security by analyzing approvals, permissions, and transaction patterns.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT

Usage:
    wallet_auditor.py approvals <address> [--chain CHAIN] [--unlimited]
    wallet_auditor.py scan <address> [--chain CHAIN] [--verbose]
    wallet_auditor.py score <address> [--chain CHAIN]
    wallet_auditor.py history <address> [--chain CHAIN] [--days DAYS]
    wallet_auditor.py revoke-list <address> [--chain CHAIN]
    wallet_auditor.py report <address> [--chain CHAIN] [--output FILE] [--json]
    wallet_auditor.py chains
"""

import argparse
import sys
import os
import json

# Add script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from approval_scanner import ApprovalScanner, CHAIN_CONFIGS
from risk_scorer import RiskScorer
from tx_analyzer import TxAnalyzer
from formatters import (
    format_approvals_table,
    format_approval_summary,
    format_security_score,
    format_risk_factors,
    format_recommendations,
    format_full_report,
    format_revoke_list,
    to_json,
)


def validate_address(address: str) -> str:
    """Validate Ethereum address format."""
    if not address:
        raise argparse.ArgumentTypeError("Address is required")

    address = address.strip()

    # Handle ENS names (would need resolution in production)
    if address.endswith(".eth"):
        raise argparse.ArgumentTypeError("ENS resolution not yet supported. Please use hex address.")

    # Basic validation
    if not address.startswith("0x"):
        raise argparse.ArgumentTypeError("Address must start with 0x")

    if len(address) != 42:
        raise argparse.ArgumentTypeError("Address must be 42 characters (0x + 40 hex chars)")

    try:
        int(address, 16)
    except ValueError:
        raise argparse.ArgumentTypeError("Address contains invalid hex characters")

    return address.lower()


def cmd_approvals(args):
    """List all token approvals for a wallet."""
    try:
        scanner = ApprovalScanner(
            chain=args.chain,
            verbose=args.verbose,
        )

        print(f"Scanning approvals for {args.address[:20]}... on {args.chain}")
        summary = scanner.get_all_approvals(args.address)

        if args.unlimited:
            # Filter to unlimited only
            unlimited = [a for a in summary.approvals if a.is_unlimited]
            if not unlimited:
                print("\nNo unlimited approvals found.")
                return 0
            print(f"\nFound {len(unlimited)} unlimited approval(s):")
            print(format_approvals_table(unlimited, show_all=True))
        else:
            print(format_approval_summary(summary))
            print(format_approvals_table(summary.approvals))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_scan(args):
    """Full security scan of wallet."""
    try:
        print("=== Full Security Scan ===")
        print(f"Address: {args.address}")
        print(f"Chain:   {args.chain}")
        print()

        # 1. Scan approvals
        if args.verbose:
            print("Step 1/3: Scanning token approvals...")
        scanner = ApprovalScanner(chain=args.chain, verbose=args.verbose)
        approval_summary = scanner.get_all_approvals(args.address)
        print(f"✓ Found {approval_summary.total_approvals} active approvals")

        # 2. Analyze transactions
        if args.verbose:
            print("Step 2/3: Analyzing transaction history...")
        tx_analyzer = TxAnalyzer(chain=args.chain, verbose=args.verbose)
        interaction_report = tx_analyzer.analyze_interaction_patterns(args.address)
        print(f"✓ Analyzed {interaction_report.total_transactions} transactions")

        # 3. Calculate risk score
        if args.verbose:
            print("Step 3/3: Calculating security score...")
        scorer = RiskScorer()
        security_score = scorer.get_total_score(
            approval_summary,
            interactions=interaction_report.interactions,
        )
        print("✓ Security score calculated")

        # Display results
        print(format_security_score(security_score))
        print(format_approval_summary(approval_summary))

        if security_score.risk_factors:
            print(format_risk_factors(security_score.risk_factors))

        if security_score.recommendations:
            print(format_recommendations(security_score.recommendations))

        # Show suspicious activities
        if interaction_report.suspicious_activities:
            print("\n⚠️  Suspicious Activities Detected:")
            for activity in interaction_report.suspicious_activities:
                print(f"  [{activity.severity.upper()}] {activity.description}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_score(args):
    """Calculate security risk score."""
    try:
        scanner = ApprovalScanner(chain=args.chain, verbose=args.verbose)
        print(f"Calculating score for {args.address[:20]}... on {args.chain}")

        summary = scanner.get_all_approvals(args.address)

        scorer = RiskScorer()
        score = scorer.get_total_score(summary)

        if args.json:
            print(to_json(score))
        else:
            print(format_security_score(score))

            # Quick summary
            print("\nQuick Summary:")
            print(f"  Score: {score.total_score}/100 ({score.risk_level.upper()})")
            print(f"  Risk Factors: {len(score.risk_factors)}")
            print(f"  Recommendations: {len(score.recommendations)}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_history(args):
    """Analyze transaction history."""
    try:
        analyzer = TxAnalyzer(chain=args.chain, verbose=args.verbose)
        print(f"Analyzing {args.days}-day history for {args.address[:20]}... on {args.chain}")

        # Get transactions
        transactions = analyzer.get_recent_transactions(args.address, days=args.days)
        print(f"\nFound {len(transactions)} transactions in the last {args.days} days")

        if not transactions:
            print("No transactions found.")
            return 0

        # Analyze patterns
        report = analyzer.analyze_interaction_patterns(args.address, transactions)

        print("\n=== Transaction History Analysis ===")
        print(f"  Total Transactions: {report.total_transactions}")
        print(f"  Unique Contracts:   {report.unique_contracts}")
        print(f"    Verified:         {report.verified_contracts}")
        print(f"    Unverified:       {report.unverified_contracts}")
        print(f"    Flagged:          {report.flagged_contracts}")
        print(f"  Total Value Sent:   {report.total_value_sent:.4f} ETH")
        print(f"  Total Gas Spent:    {report.total_gas_spent:.4f} Gwei")

        # Top interactions
        if report.interactions:
            print("\n=== Top Contract Interactions ===")
            for i, interaction in enumerate(report.interactions[:10], 1):
                name = interaction.contract_name or interaction.contract_address[:20] + "..."
                verified = "✓" if interaction.is_verified else "✗"
                flagged = " 🚨" if interaction.is_flagged else ""
                print(f"  {i:2}. {name} ({interaction.interaction_count} txs) [{verified}]{flagged}")

        # Suspicious activities
        if report.suspicious_activities:
            print("\n=== Suspicious Activities ===")
            for activity in report.suspicious_activities:
                print(f"  [{activity.severity.upper()}] {activity.description}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_revoke_list(args):
    """Generate list of approvals to revoke."""
    try:
        scanner = ApprovalScanner(chain=args.chain, verbose=args.verbose)
        print(f"Generating revoke list for {args.address[:20]}... on {args.chain}")

        summary = scanner.get_all_approvals(args.address)

        # Filter approvals that should be revoked
        revoke_candidates = []

        for approval in summary.approvals:
            should_revoke = False
            reason = []

            # Risky approvals
            if approval.is_risky:
                should_revoke = True
                reason.append("flagged as risky")

            # Unlimited to unknown spender
            if approval.is_unlimited and not approval.spender_name:
                should_revoke = True
                reason.append("unlimited to unknown contract")

            if should_revoke:
                revoke_candidates.append(approval)

        if not revoke_candidates:
            print("\nNo high-risk approvals found that require immediate revocation.")
            print("Review unlimited approvals periodically with: wallet_auditor.py approvals --unlimited")
            return 0

        print(format_revoke_list(revoke_candidates))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_report(args):
    """Generate full security audit report."""
    try:
        # Collect all data
        scanner = ApprovalScanner(chain=args.chain, verbose=args.verbose)
        tx_analyzer = TxAnalyzer(chain=args.chain, verbose=args.verbose)
        scorer = RiskScorer()

        if not args.json:
            print(f"Generating security report for {args.address[:20]}...")
            print("This may take a moment...")

        # Get data
        approval_summary = scanner.get_all_approvals(args.address)
        interaction_report = tx_analyzer.analyze_interaction_patterns(args.address)
        security_score = scorer.get_total_score(
            approval_summary,
            interactions=interaction_report.interactions,
        )

        if args.json:
            # JSON output
            report_data = {
                "address": args.address,
                "chain": args.chain,
                "security_score": {
                    "total": security_score.total_score,
                    "approval_score": security_score.approval_score,
                    "interaction_score": security_score.interaction_score,
                    "pattern_score": security_score.pattern_score,
                    "risk_level": security_score.risk_level,
                },
                "approval_summary": {
                    "total": approval_summary.total_approvals,
                    "unlimited": approval_summary.unlimited_approvals,
                    "risky": approval_summary.risky_approvals,
                    "unique_spenders": approval_summary.unique_spenders,
                    "unique_tokens": approval_summary.unique_tokens,
                },
                "transaction_summary": {
                    "total_transactions": interaction_report.total_transactions,
                    "unique_contracts": interaction_report.unique_contracts,
                    "verified_contracts": interaction_report.verified_contracts,
                    "flagged_contracts": interaction_report.flagged_contracts,
                },
                "risk_factors": [
                    {
                        "category": f.category,
                        "severity": f.severity,
                        "description": f.description,
                        "impact": f.score_impact,
                    }
                    for f in security_score.risk_factors
                ],
                "recommendations": [
                    {
                        "priority": r.priority,
                        "action": r.action,
                        "reason": r.reason,
                    }
                    for r in security_score.recommendations
                ],
            }
            output = json.dumps(report_data, indent=2)
        else:
            # Formatted report
            explorer_url = CHAIN_CONFIGS.get(args.chain, {}).get("explorer_url", "")
            output = format_full_report(
                address=args.address,
                chain=args.chain,
                summary=approval_summary,
                score=security_score,
                explorer_url=explorer_url,
            )

        # Output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Report saved to: {args.output}")
        else:
            print(output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_chains(args):
    """List supported chains."""
    print("\n=== Supported Chains ===\n")
    print(f"{'Chain':<12} {'Chain ID':<10} {'Explorer':<30}")
    print("-" * 55)

    for chain, config in CHAIN_CONFIGS.items():
        explorer = config.get("explorer_url", "N/A")
        print(f"{chain:<12} {config['chain_id']:<10} {explorer:<30}")

    print("\nUse --chain <name> to specify a chain (default: ethereum)")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Wallet Security Auditor - Analyze wallet security and token approvals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s approvals 0x1234...abcd                    # List all approvals
  %(prog)s approvals 0x1234...abcd --unlimited        # Show only unlimited
  %(prog)s scan 0x1234...abcd --verbose               # Full security scan
  %(prog)s score 0x1234...abcd                        # Get security score
  %(prog)s history 0x1234...abcd --days 90            # 90-day tx history
  %(prog)s revoke-list 0x1234...abcd                  # Get revoke recommendations
  %(prog)s report 0x1234...abcd --output report.txt   # Save full report
  %(prog)s report 0x1234...abcd --json                # JSON output
  %(prog)s chains                                     # List supported chains

Supported chains: ethereum, bsc, polygon, arbitrum, optimism, base
        """,
    )

    parser.add_argument("--version", "-v", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # approvals command
    approvals_parser = subparsers.add_parser("approvals", help="List token approvals for a wallet")
    approvals_parser.add_argument("address", type=validate_address, help="Wallet address")
    approvals_parser.add_argument("--chain", "-c", default="ethereum", help="Chain (default: ethereum)")
    approvals_parser.add_argument("--unlimited", "-u", action="store_true", help="Show only unlimited approvals")
    approvals_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Full security scan of wallet")
    scan_parser.add_argument("address", type=validate_address, help="Wallet address")
    scan_parser.add_argument("--chain", "-c", default="ethereum", help="Chain (default: ethereum)")
    scan_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # score command
    score_parser = subparsers.add_parser("score", help="Calculate security risk score")
    score_parser.add_argument("address", type=validate_address, help="Wallet address")
    score_parser.add_argument("--chain", "-c", default="ethereum", help="Chain (default: ethereum)")
    score_parser.add_argument("--json", action="store_true", help="JSON output")
    score_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # history command
    history_parser = subparsers.add_parser("history", help="Analyze transaction history")
    history_parser.add_argument("address", type=validate_address, help="Wallet address")
    history_parser.add_argument("--chain", "-c", default="ethereum", help="Chain (default: ethereum)")
    history_parser.add_argument("--days", "-d", type=int, default=30, help="Days to analyze (default: 30)")
    history_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # revoke-list command
    revoke_parser = subparsers.add_parser("revoke-list", help="Generate list of approvals to revoke")
    revoke_parser.add_argument("address", type=validate_address, help="Wallet address")
    revoke_parser.add_argument("--chain", "-c", default="ethereum", help="Chain (default: ethereum)")
    revoke_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # report command
    report_parser = subparsers.add_parser("report", help="Generate full security audit report")
    report_parser.add_argument("address", type=validate_address, help="Wallet address")
    report_parser.add_argument("--chain", "-c", default="ethereum", help="Chain (default: ethereum)")
    report_parser.add_argument("--output", "-o", help="Output file path")
    report_parser.add_argument("--json", action="store_true", help="JSON output")
    report_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # chains command
    subparsers.add_parser("chains", help="List supported chains")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handler
    commands = {
        "approvals": cmd_approvals,
        "scan": cmd_scan,
        "score": cmd_score,
        "history": cmd_history,
        "revoke-list": cmd_revoke_list,
        "report": cmd_report,
        "chains": cmd_chains,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
