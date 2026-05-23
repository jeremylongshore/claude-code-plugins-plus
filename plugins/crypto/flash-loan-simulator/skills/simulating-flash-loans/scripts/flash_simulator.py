#!/usr/bin/env python3
"""
Flash Loan Simulator - Main CLI Entry Point.

Simulates flash loan strategies across DeFi protocols with:
- Profitability analysis
- Gas cost estimation
- Risk assessment
- Provider comparison

Usage:
    python flash_simulator.py arbitrage ETH USDC 100 --dex-buy sushiswap --dex-sell uniswap
    python flash_simulator.py liquidation --protocol aave --health-factor 0.95
    python flash_simulator.py triangular ETH USDC WBTC ETH --amount 50
    python flash_simulator.py compare ETH 100
"""

import argparse
import sys
from decimal import Decimal, InvalidOperation

from strategy_engine import (
    StrategyFactory,
    StrategyType,
    ArbitrageParams,
    TriangularArbitrageParams,
    LiquidationParams,
)
from profit_calculator import ProfitCalculator
from risk_assessor import RiskAssessor
from protocol_adapters import ProviderManager
from formatters import ConsoleFormatter, JSONFormatter, MarkdownFormatter


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Flash Loan Strategy Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple arbitrage simulation
  %(prog)s arbitrage ETH USDC 100 --dex-buy sushiswap --dex-sell uniswap

  # Triangular arbitrage
  %(prog)s triangular ETH USDC WBTC ETH --amount 50

  # Liquidation profitability
  %(prog)s liquidation --protocol aave --health-factor 0.95

  # Compare providers
  %(prog)s compare ETH 100

  # Full analysis with risk assessment
  %(prog)s arbitrage ETH USDC 100 --full --risk-analysis

  # JSON output for integration
  %(prog)s arbitrage ETH USDC 100 --output json > result.json

Providers:
  aave      - Aave V3 (0.09% fee, multi-chain)
  dydx      - dYdX (0% fee, Ethereum only)
  balancer  - Balancer (0.01% fee, multi-chain)
  uniswap   - Uniswap V3 (~0.3% implicit, flash swap)

DEXes:
  uniswap, sushiswap, curve, balancer, 1inch

EDUCATIONAL DISCLAIMER:
  This tool is for simulation and learning only.
  Flash loans carry significant risks. Never deploy
  untested code. Start with testnets.
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Simulation type")

    # Arbitrage subcommand
    arb_parser = subparsers.add_parser("arbitrage", help="Simple two-DEX arbitrage simulation")
    arb_parser.add_argument("input_token", help="Input token (e.g., ETH)")
    arb_parser.add_argument("output_token", help="Output token (e.g., USDC)")
    arb_parser.add_argument("amount", type=str, help="Loan amount")
    arb_parser.add_argument("--dex-buy", default="sushiswap", help="DEX to buy on (default: sushiswap)")
    arb_parser.add_argument("--dex-sell", default="uniswap", help="DEX to sell on (default: uniswap)")
    arb_parser.add_argument("--provider", default="aave", help="Flash loan provider (default: aave)")

    # Triangular arbitrage subcommand
    tri_parser = subparsers.add_parser("triangular", help="Multi-hop circular arbitrage simulation")
    tri_parser.add_argument("tokens", nargs="+", help="Token path (e.g., ETH USDC WBTC ETH)")
    tri_parser.add_argument("--amount", type=str, required=True, help="Loan amount")
    tri_parser.add_argument("--provider", default="aave", help="Flash loan provider (default: aave)")

    # Liquidation subcommand
    liq_parser = subparsers.add_parser("liquidation", help="Liquidation opportunity analysis")
    liq_parser.add_argument("--protocol", default="aave", help="Lending protocol (default: aave)")
    liq_parser.add_argument(
        "--health-factor",
        type=float,
        default=0.95,
        help="Health factor threshold (default: 0.95)",
    )
    liq_parser.add_argument("--collateral", default="ETH", help="Collateral asset (default: ETH)")
    liq_parser.add_argument("--debt", default="USDC", help="Debt asset (default: USDC)")
    liq_parser.add_argument("--amount", type=str, default="10", help="Debt amount to liquidate")
    liq_parser.add_argument("--provider", default="aave", help="Flash loan provider (default: aave)")

    # Compare providers subcommand
    cmp_parser = subparsers.add_parser("compare", help="Compare flash loan providers")
    cmp_parser.add_argument("asset", help="Asset to borrow (e.g., ETH)")
    cmp_parser.add_argument("amount", type=str, help="Amount to borrow")
    cmp_parser.add_argument("--chain", default="ethereum", help="Chain (default: ethereum)")

    # Global options
    for sub in [arb_parser, tri_parser, liq_parser]:
        sub.add_argument(
            "--compare-providers",
            action="store_true",
            help="Compare all providers for this strategy",
        )
        sub.add_argument(
            "--risk-analysis",
            action="store_true",
            help="Include risk assessment",
        )
        sub.add_argument(
            "--full",
            action="store_true",
            help="Full analysis (breakdown + risk + providers)",
        )

    # Output options for all subcommands
    for sub in [arb_parser, tri_parser, liq_parser, cmp_parser]:
        sub.add_argument(
            "--output",
            choices=["console", "json", "markdown"],
            default="console",
            help="Output format (default: console)",
        )
        sub.add_argument(
            "--eth-price",
            type=float,
            default=2500.0,
            help="ETH price in USD (default: 2500)",
        )
        sub.add_argument(
            "--gas-price",
            type=float,
            default=30.0,
            help="Gas price in gwei (default: 30)",
        )

    return parser.parse_args()


def run_arbitrage(args: argparse.Namespace) -> int:
    """Run simple arbitrage simulation."""
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print(f"Error: Invalid amount '{args.amount}'", file=sys.stderr)
        return 1

    # Create strategy
    factory = StrategyFactory()
    strategy = factory.create(StrategyType.SIMPLE_ARBITRAGE)

    params = ArbitrageParams(
        input_token=args.input_token.upper(),
        output_token=args.output_token.upper(),
        amount=amount,
        dex_buy=args.dex_buy.lower(),
        dex_sell=args.dex_sell.lower(),
        provider=args.provider.lower(),
    )

    # Run simulation
    result = strategy.simulate(params)

    # Calculate extras if needed
    calculator = None
    breakdown = None
    assessor = None
    assessment = None
    providers = None

    if args.full or hasattr(args, "compare_providers") and args.compare_providers:
        calculator = ProfitCalculator(eth_price_usd=args.eth_price, gas_price_gwei=args.gas_price)
        breakdown = calculator.calculate_breakdown(result)

    if args.full or (hasattr(args, "risk_analysis") and args.risk_analysis):
        assessor = RiskAssessor(eth_price_usd=args.eth_price)
        assessment = assessor.assess(result)

    if args.full or (hasattr(args, "compare_providers") and args.compare_providers):
        manager = ProviderManager()
        providers = manager.compare_providers(args.input_token.upper(), amount, "ethereum")

    # Format output
    output_result(args, result, breakdown, assessment, providers)

    return 0 if result.is_profitable else 1


def run_triangular(args: argparse.Namespace) -> int:
    """Run triangular arbitrage simulation."""
    if len(args.tokens) < 3:
        print("Error: Triangular arbitrage requires at least 3 tokens", file=sys.stderr)
        return 1

    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print(f"Error: Invalid amount '{args.amount}'", file=sys.stderr)
        return 1

    # Create strategy
    factory = StrategyFactory()
    strategy = factory.create(StrategyType.TRIANGULAR_ARBITRAGE)

    params = TriangularArbitrageParams(
        tokens=[t.upper() for t in args.tokens],
        amount=amount,
        provider=args.provider.lower(),
    )

    # Run simulation
    result = strategy.simulate(params)

    # Calculate extras
    calculator = None
    breakdown = None
    assessment = None
    providers = None

    if args.full:
        calculator = ProfitCalculator(eth_price_usd=args.eth_price, gas_price_gwei=args.gas_price)
        breakdown = calculator.calculate_breakdown(result)

        assessor = RiskAssessor(eth_price_usd=args.eth_price)
        assessment = assessor.assess(result)

        manager = ProviderManager()
        providers = manager.compare_providers(args.tokens[0].upper(), amount, "ethereum")

    if hasattr(args, "risk_analysis") and args.risk_analysis:
        assessor = RiskAssessor(eth_price_usd=args.eth_price)
        assessment = assessor.assess(result)

    # Format output
    output_result(args, result, breakdown, assessment, providers)

    return 0 if result.is_profitable else 1


def run_liquidation(args: argparse.Namespace) -> int:
    """Run liquidation simulation."""
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print(f"Error: Invalid amount '{args.amount}'", file=sys.stderr)
        return 1

    # Create strategy
    factory = StrategyFactory()
    strategy = factory.create(StrategyType.LIQUIDATION)

    params = LiquidationParams(
        collateral_asset=args.collateral.upper(),
        debt_asset=args.debt.upper(),
        debt_amount=amount,
        health_factor=args.health_factor,
        lending_protocol=args.protocol.lower(),
        provider=args.provider.lower(),
    )

    # Run simulation
    result = strategy.simulate(params)

    # Calculate extras
    calculator = None
    breakdown = None
    assessment = None
    providers = None

    if args.full:
        calculator = ProfitCalculator(eth_price_usd=args.eth_price, gas_price_gwei=args.gas_price)
        breakdown = calculator.calculate_breakdown(result)

        assessor = RiskAssessor(eth_price_usd=args.eth_price)
        assessment = assessor.assess(result)

        manager = ProviderManager()
        providers = manager.compare_providers(args.debt.upper(), amount, "ethereum")

    if hasattr(args, "risk_analysis") and args.risk_analysis:
        assessor = RiskAssessor(eth_price_usd=args.eth_price)
        assessment = assessor.assess(result)

    # Format output
    output_result(args, result, breakdown, assessment, providers)

    return 0 if result.is_profitable else 1


def run_compare(args: argparse.Namespace) -> int:
    """Run provider comparison."""
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print(f"Error: Invalid amount '{args.amount}'", file=sys.stderr)
        return 1

    manager = ProviderManager()
    providers = manager.compare_providers(args.asset.upper(), amount, args.chain.lower())

    if not providers:
        print(
            f"No providers support {amount} {args.asset} on {args.chain}",
            file=sys.stderr,
        )
        return 1

    # Format output
    if args.output == "json":
        JSONFormatter()
        # Create a minimal result for JSON output
        output = {
            "comparison": {
                "asset": args.asset.upper(),
                "amount": float(amount),
                "chain": args.chain,
            },
            "providers": [
                {
                    "name": p.name,
                    "fee_rate": float(p.fee_rate),
                    "fee_amount": float(p.fee_amount),
                    "max_available": float(p.max_available),
                    "gas_overhead": p.gas_overhead,
                    "supported_chains": p.supported_chains,
                }
                for p in providers
            ],
        }
        import json

        print(json.dumps(output, indent=2))
    else:
        console = ConsoleFormatter()
        print(console.format_provider_comparison(providers, args.asset.upper(), amount))

    return 0


def output_result(
    args: argparse.Namespace,
    result,
    breakdown=None,
    assessment=None,
    providers=None,
) -> None:
    """Output simulation result in requested format."""
    if args.output == "json":
        json_fmt = JSONFormatter()
        print(json_fmt.format_full_report(result, breakdown, assessment, providers))

    elif args.output == "markdown":
        md_fmt = MarkdownFormatter()
        print(md_fmt.format_simulation_report(result, breakdown, assessment))

    else:  # console (default)
        console = ConsoleFormatter()

        # Always show strategy result
        print(console.format_strategy_result(result))

        # Show breakdown if calculated
        if breakdown:
            print(console.format_profit_breakdown(breakdown))

        # Show risk assessment if calculated
        if assessment:
            print(console.format_risk_assessment(assessment))

        # Show provider comparison if calculated
        if providers:
            print(console.format_provider_comparison(providers, result.loan_asset, result.loan_amount))

        # Always show quick summary at end
        print(console.format_quick_summary(result, assessment))


def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║              FLASH LOAN SIMULATOR v1.0.0                        ║
║                                                                  ║
║  Simulate flash loan strategies across DeFi protocols          ║
║  Providers: Aave V3 | dYdX | Balancer | Uniswap V3            ║
║                                                                  ║
║  ⚠️  EDUCATIONAL PURPOSES ONLY - Not financial advice          ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner, file=sys.stderr)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if not args.command:
        print_banner()
        print("Use --help for usage information", file=sys.stderr)
        print("\nQuick start:")
        print("  flash_simulator.py arbitrage ETH USDC 100")
        print("  flash_simulator.py compare ETH 100")
        print("  flash_simulator.py liquidation --protocol aave")
        return 1

    # Run appropriate command
    if args.command == "arbitrage":
        return run_arbitrage(args)
    elif args.command == "triangular":
        return run_triangular(args)
    elif args.command == "liquidation":
        return run_liquidation(args)
    elif args.command == "compare":
        return run_compare(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
