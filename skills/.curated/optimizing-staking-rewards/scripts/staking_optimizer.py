#!/usr/bin/env python3
"""
Staking Rewards Optimizer - Main CLI

Compare and optimize staking rewards across validators and protocols.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from staking_fetcher import StakingFetcher
from metrics_calculator import MetricsCalculator
from risk_assessor import RiskAssessor
from formatters import StakingFormatter


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare and optimize staking rewards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --asset ETH
  %(prog)s --asset ETH --amount 10 --detailed
  %(prog)s --asset SOL --format json
  %(prog)s --compare --protocols lido,rocket-pool
  %(prog)s --optimize --positions "10 ETH @ lido 4.0%%, 100 ATOM @ native 18%%"
        """,
    )

    # Asset selection
    parser.add_argument("--asset", "-a", help="Asset to analyze (ETH, SOL, ATOM, etc.)")

    parser.add_argument("--assets", help="Multiple assets, comma-separated (ETH,SOL,ATOM)")

    # Position analysis
    parser.add_argument("--amount", type=float, help="Amount of asset for gas-adjusted analysis")

    parser.add_argument("--amount-usd", type=float, help="Position value in USD")

    # Protocol selection
    parser.add_argument("--protocol", help="Single protocol to analyze")

    parser.add_argument("--protocols", help="Protocols to compare, comma-separated")

    # Comparison mode
    parser.add_argument("--compare", action="store_true", help="Compare protocols head-to-head")

    # Optimization mode
    parser.add_argument("--optimize", action="store_true", help="Optimize existing portfolio")

    parser.add_argument("--positions", help="Current positions for optimization (e.g., '10 ETH @ lido 4.0%%')")

    # Output options
    parser.add_argument("--format", "-f", choices=["table", "json", "csv"], default="table", help="Output format")

    parser.add_argument("--output", "-o", help="Output file")

    parser.add_argument("--detailed", action="store_true", help="Show detailed analysis")

    # Other options
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--gas-price", type=float, default=30, help="Gas price in gwei (default: 30)")

    parser.add_argument("--eth-price", type=float, default=2000, help="ETH price in USD (default: 2000)")

    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    args = parser.parse_args()

    try:
        # Initialize components
        fetcher = StakingFetcher(use_cache=not args.no_cache, verbose=args.verbose)
        calculator = MetricsCalculator(
            gas_price_gwei=args.gas_price, eth_price_usd=args.eth_price, verbose=args.verbose
        )
        risk_assessor = RiskAssessor(verbose=args.verbose)
        formatter = StakingFormatter()

        # Handle optimization mode
        if args.optimize and args.positions:
            return handle_optimization(args, fetcher, calculator, risk_assessor, formatter)

        # Determine position USD value
        position_usd = args.amount_usd
        if args.amount and args.asset and not position_usd:
            # Estimate USD value (simplified)
            price_estimates = {
                "ETH": 2000,
                "SOL": 100,
                "ATOM": 10,
                "DOT": 7,
                "AVAX": 35,
                "MATIC": 1,
                "ADA": 0.5,
                "BNB": 300,
            }
            price = price_estimates.get(args.asset.upper(), 100)
            position_usd = args.amount * price

        # Fetch staking options
        if args.verbose:
            print("Fetching staking data...")

        options = []

        if args.asset:
            # Single asset analysis
            options = fetcher.fetch_pools_by_asset(args.asset)

        elif args.assets:
            # Multiple assets
            for asset in args.assets.split(","):
                asset = asset.strip().upper()
                asset_options = fetcher.fetch_pools_by_asset(asset)
                options.extend(asset_options)

        elif args.protocol:
            # Single protocol
            options = fetcher.fetch_pool_by_protocol(args.protocol)

        elif args.protocols:
            # Multiple protocols
            for protocol in args.protocols.split(","):
                protocol = protocol.strip().lower()
                proto_options = fetcher.fetch_pool_by_protocol(protocol)
                options.extend(proto_options)

        else:
            print("Please specify --asset, --protocol, or --optimize", file=sys.stderr)
            sys.exit(1)

        if not options:
            print("No staking options found.", file=sys.stderr)
            sys.exit(0)

        # Calculate metrics and risk for each option
        for opt in options:
            metrics = calculator.calculate_metrics(opt, position_usd)
            risk = risk_assessor.assess_risk(opt)

            opt["metrics"] = {
                "gross_apy": metrics.gross_apy,
                "net_apy": metrics.net_apy,
                "effective_apy": metrics.effective_apy,
                "protocol_fee_rate": metrics.protocol_fee_rate,
                "gas_cost_usd": metrics.gas_cost_usd,
                "gas_as_pct": metrics.gas_as_pct,
                "tvl_usd": metrics.tvl_usd,
                "position_usd": metrics.position_usd,
                "projected_1m": metrics.projected_1m,
                "projected_3m": metrics.projected_3m,
                "projected_6m": metrics.projected_6m,
                "projected_1y": metrics.projected_1y,
                "unbonding": metrics.unbonding,
            }

            opt["risk_assessment"] = {
                "overall_score": risk.overall_score,
                "risk_level": risk.risk_level,
                "audit_score": risk.audit_score,
                "production_score": risk.production_score,
                "tvl_score": risk.tvl_score,
                "reputation_score": risk.reputation_score,
                "validator_score": risk.validator_score,
                "factors": risk.factors,
                "warnings": risk.warnings,
                "considerations": risk.considerations,
            }

        # Sort by risk-adjusted return
        options.sort(
            key=lambda x: calculator.calculate_risk_adjusted_return(
                x["metrics"]["net_apy"], x["risk_assessment"]["overall_score"]
            ),
            reverse=True,
        )

        # Format output
        if len(options) == 1 and not args.compare:
            output = formatter.format(options[0], args.format, args.detailed)
        else:
            output = formatter.format(options, args.format, args.detailed)

        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Results saved to {args.output}")
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def handle_optimization(args, fetcher, calculator, risk_assessor, formatter):
    """Handle portfolio optimization mode.

    Args:
        args: CLI arguments
        fetcher: Data fetcher
        calculator: Metrics calculator
        risk_assessor: Risk assessor
        formatter: Output formatter

    Returns:
        Exit code
    """
    # Parse current positions
    # Format: "10 ETH @ lido 4.0%, 100 ATOM @ native 18%"
    positions = []
    total_value = 0
    total_annual = 0

    for pos_str in args.positions.split(","):
        pos_str = pos_str.strip()
        if not pos_str:
            continue

        try:
            # Parse "10 ETH @ lido 4.0%"
            parts = pos_str.split("@")
            amount_part = parts[0].strip()
            protocol_part = parts[1].strip() if len(parts) > 1 else "unknown 0%"

            # Parse amount and asset
            amount_parts = amount_part.split()
            amount = float(amount_parts[0])
            asset = amount_parts[1].upper()

            # Parse protocol and APY
            protocol_parts = protocol_part.split()
            protocol = protocol_parts[0].lower()
            apy = float(protocol_parts[1].replace("%", "")) if len(protocol_parts) > 1 else 0

            # Estimate USD value
            price_estimates = {
                "ETH": 2000,
                "SOL": 100,
                "ATOM": 10,
                "DOT": 7,
                "AVAX": 35,
                "MATIC": 1,
                "ADA": 0.5,
                "BNB": 300,
            }
            price = price_estimates.get(asset, 100)
            value_usd = amount * price
            annual_return = value_usd * (apy / 100)

            positions.append(
                {
                    "amount": amount,
                    "asset": asset,
                    "protocol": protocol,
                    "apy": apy,
                    "value_usd": value_usd,
                    "annual_return": annual_return,
                }
            )

            total_value += value_usd
            total_annual += annual_return

        except (ValueError, IndexError) as e:
            print(f"Warning: Could not parse position '{pos_str}': {e}", file=sys.stderr)
            continue

    if not positions:
        print("No valid positions found.", file=sys.stderr)
        return 1

    # Fetch alternatives for each asset
    recommendations = []
    optimized_annual = 0
    implementation_steps = []

    for pos in positions:
        asset = pos["asset"]
        current_apy = pos["apy"]
        value_usd = pos["value_usd"]

        # Get alternatives
        alternatives = fetcher.fetch_pools_by_asset(asset)

        # Calculate metrics for alternatives
        best_alternative = None
        best_net_apy = current_apy

        for alt in alternatives:
            metrics = calculator.calculate_metrics(alt, value_usd)
            if metrics.net_apy > best_net_apy:
                best_net_apy = metrics.net_apy
                best_alternative = alt

        if best_alternative and best_net_apy > current_apy + 0.1:
            # Recommend move
            new_annual = value_usd * (best_net_apy / 100)
            change = new_annual - pos["annual_return"]

            recommendations.append(
                {
                    "action": "move",
                    "asset": f"{pos['amount']} {asset}",
                    "current_protocol": pos["protocol"],
                    "target_protocol": best_alternative.get("project", "?"),
                    "current_apy": current_apy,
                    "new_apy": best_net_apy,
                    "new_annual": new_annual,
                    "change": change,
                }
            )

            optimized_annual += new_annual
            implementation_steps.append(
                f"Move {pos['amount']} {asset} from {pos['protocol']} to {best_alternative.get('project', '?')}"
            )
        else:
            # Keep current
            recommendations.append(
                {
                    "action": "keep",
                    "asset": f"{pos['amount']} {asset}",
                    "current_protocol": pos["protocol"],
                    "target_protocol": pos["protocol"],
                    "current_apy": current_apy,
                    "new_apy": current_apy,
                    "new_annual": pos["annual_return"],
                    "change": 0,
                }
            )
            optimized_annual += pos["annual_return"]

    # Summary
    improvement = optimized_annual - total_annual
    improvement_pct = (improvement / total_annual * 100) if total_annual > 0 else 0
    blended_apy = (total_annual / total_value * 100) if total_value > 0 else 0

    summary = {
        "total_value": total_value,
        "blended_apy": blended_apy,
        "total_annual": total_annual,
        "optimized_annual": optimized_annual,
        "improvement": improvement,
        "improvement_pct": improvement_pct,
        "implementation_steps": implementation_steps,
    }

    # Format output
    output = formatter.format_optimization_report(positions, recommendations, summary)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Results saved to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    main()
