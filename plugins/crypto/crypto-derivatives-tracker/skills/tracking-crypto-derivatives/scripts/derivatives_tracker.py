#!/usr/bin/env python3
"""
Crypto Derivatives Tracker - Main CLI.

Comprehensive derivatives market analysis:
- Funding rate tracking
- Open interest analysis
- Liquidation monitoring
- Options flow analysis
- Basis/spread calculations
- Multi-asset dashboard

Usage:
    python derivatives_tracker.py funding BTC
    python derivatives_tracker.py oi BTC --format json
    python derivatives_tracker.py liquidations BTC
    python derivatives_tracker.py options BTC
    python derivatives_tracker.py basis BTC
    python derivatives_tracker.py dashboard BTC ETH
"""

import argparse
import sys
from decimal import Decimal

from funding_tracker import FundingTracker
from oi_analyzer import OIAnalyzer
from liquidation_monitor import LiquidationMonitor
from options_analyzer import OptionsAnalyzer
from basis_calculator import BasisCalculator
from formatters import ConsoleFormatter, JSONFormatter, ReportGenerator


def cmd_funding(args):
    """Handle funding subcommand."""
    tracker = FundingTracker()
    console = ConsoleFormatter()
    json_fmt = JSONFormatter()

    print(console.header(f"{args.symbol} FUNDING RATE ANALYSIS"))

    analysis = tracker.analyze(args.symbol)

    if args.format == "json":
        print(
            json_fmt.funding_report(
                args.symbol,
                {
                    "weighted_avg": analysis.weighted_avg,
                    "annualized_avg": analysis.annualized_avg,
                    "spread": analysis.spread,
                    "sentiment": analysis.sentiment,
                    "sentiment_strength": analysis.sentiment_strength,
                    "arbitrage_opportunity": analysis.arbitrage_opportunity,
                    "rates": [
                        {
                            "exchange": r.exchange,
                            "rate": float(r.rate),
                            "annualized": r.annualized,
                            "next_payment": r.time_to_payment_str,
                        }
                        for r in analysis.rates
                    ],
                },
            )
        )
        return

    # Console format
    print(f"\n{'Exchange':<12} {'Current':>10} {'Annualized':>12} {'Next Payment':>14}")
    print("-" * 50)

    for rate in sorted(analysis.rates, key=lambda r: r.rate, reverse=True):
        print(
            f"{rate.exchange:<12} {float(rate.rate):>+9.4%} {rate.annualized:>+11.2f}% {rate.time_to_payment_str:>14}"
        )

    print("-" * 50)
    print(f"\nWeighted Average: {analysis.weighted_avg:+.4%}")
    print(f"Annualized: {analysis.annualized_avg:+.2f}%")
    print(f"Spread (max-min): {analysis.spread:.4%}")
    print(
        f"\nSentiment: {console.sentiment_icon(analysis.sentiment)} "
        f"{analysis.sentiment_strength.title()} {analysis.sentiment.title()}"
    )

    if analysis.is_extreme:
        print("\n⚠️  EXTREME FUNDING - Contrarian opportunity")

    if analysis.arbitrage_opportunity:
        print("\n💰 ARBITRAGE OPPORTUNITY")
        print(f"   Long on {analysis.min_rate.exchange} ({float(analysis.min_rate.rate):+.4%})")
        print(f"   Short on {analysis.max_rate.exchange} ({float(analysis.max_rate.rate):+.4%})")
        print(f"   Profit: {analysis.arbitrage_spread:.4%} per 8h")


def cmd_oi(args):
    """Handle open interest subcommand."""
    analyzer = OIAnalyzer()
    console = ConsoleFormatter()
    json_fmt = JSONFormatter()

    print(console.header(f"{args.symbol} OPEN INTEREST ANALYSIS"))

    analysis = analyzer.analyze(args.symbol)

    if args.format == "json":
        print(
            json_fmt.oi_report(
                args.symbol,
                {
                    "total_oi_usd": float(analysis.total_oi_usd),
                    "total_oi_contracts": float(analysis.total_oi_contracts),
                    "avg_change_24h": analysis.avg_change_24h,
                    "avg_change_7d": analysis.avg_change_7d,
                    "weighted_long_ratio": analysis.weighted_long_ratio,
                    "long_percentage": analysis.long_percentage,
                    "dominant_exchange": analysis.dominant_exchange,
                    "dominant_share": analysis.dominant_share,
                    "trend": analysis.trend,
                    "trend_strength": analysis.trend_strength,
                    "exchanges": [
                        {
                            "exchange": oi.exchange,
                            "oi_usd": float(oi.oi_usd),
                            "change_24h": oi.change_24h_pct,
                            "change_7d": oi.change_7d_pct,
                            "long_ratio": oi.long_ratio,
                        }
                        for oi in analysis.exchanges
                    ],
                },
            )
        )
        return

    # Console format
    print(f"\n{'Exchange':<12} {'OI (USD)':>14} {'24h Chg':>10} {'7d Chg':>10} {'Share':>8}")
    print("-" * 60)

    for oi in sorted(analysis.exchanges, key=lambda x: x.oi_usd, reverse=True):
        share = float(oi.oi_usd) / float(analysis.total_oi_usd) * 100
        print(
            f"{oi.exchange:<12} "
            f"${float(oi.oi_usd) / 1e9:>12.2f}B "
            f"{oi.change_24h_pct:>+9.1f}% "
            f"{oi.change_7d_pct:>+9.1f}% "
            f"{share:>7.1f}%"
        )

    print("-" * 60)
    print(f"\nTotal OI: ${float(analysis.total_oi_usd) / 1e9:.2f}B")
    print(f"24h Change: {analysis.avg_change_24h:+.1f}%")
    print(f"7d Change: {analysis.avg_change_7d:+.1f}%")
    print(f"\nLong/Short Ratio: {analysis.weighted_long_ratio:.2f} ({analysis.long_percentage:.1f}% long)")
    print(f"Trend: {analysis.trend_strength.title()} {analysis.trend.title()}")
    print(f"Dominant Exchange: {analysis.dominant_exchange} ({analysis.dominant_share:.1f}%)")

    # Check for divergence
    if args.price_change:
        print(console.section("DIVERGENCE ANALYSIS"))
        divergence = analyzer.detect_divergence(args.symbol, args.price_change)
        if divergence:
            print("\n🔍 Divergence Detected!")
            print(f"   OI:    {divergence.oi_direction} ({divergence.oi_change_pct:+.1f}%)")
            print(f"   Price: {divergence.price_direction} ({divergence.price_change_pct:+.1f}%)")
            print(f"   Signal: {divergence.signal.upper()}")
            print(f"   {divergence.description}")
            print(f"   Confidence: {divergence.confidence}")
        else:
            print("\nNo significant divergence detected")


def cmd_liquidations(args):
    """Handle liquidations subcommand."""
    monitor = LiquidationMonitor()
    console = ConsoleFormatter()
    json_fmt = JSONFormatter()

    price = Decimal(str(args.price)) if args.price else None
    summary = monitor.get_summary(args.symbol, price)

    print(console.header(f"{args.symbol} LIQUIDATION MONITOR"))

    if args.format == "json":
        print(
            json_fmt.format(
                {
                    "symbol": summary.symbol,
                    "current_price": float(summary.current_price),
                    "total_24h_usd": float(summary.total_24h_usd),
                    "long_liquidations_usd": float(summary.long_liquidations_usd),
                    "short_liquidations_usd": float(summary.short_liquidations_usd),
                    "cascade_risk": summary.cascade_risk,
                    "long_levels": [
                        {
                            "price": float(l.price),
                            "total_value_usd": float(l.total_value_usd),
                            "density": l.density,
                        }
                        for l in summary.long_levels
                    ],
                    "short_levels": [
                        {
                            "price": float(l.price),
                            "total_value_usd": float(l.total_value_usd),
                            "density": l.density,
                        }
                        for l in summary.short_levels
                    ],
                }
            )
        )
        return

    print(f"\n   Current Price: ${summary.current_price:,}")
    print("-" * 60)

    # 24h totals
    print("\n24h Liquidations:")
    print(f"   Total:  ${float(summary.total_24h_usd) / 1e6:,.1f}M")
    print(f"   Longs:  ${float(summary.long_liquidations_usd) / 1e6:,.1f}M")
    print(f"   Shorts: ${float(summary.short_liquidations_usd) / 1e6:,.1f}M")

    # Cascade risk
    print(f"\nCascade Risk: {console.risk_icon(summary.cascade_risk)} {summary.cascade_risk.upper()}")

    # Heatmap
    print(console.section("LIQUIDATION HEATMAP"))

    print(f"\nLONG LIQUIDATIONS (below ${summary.current_price:,}):")
    for level in summary.long_levels[:4]:
        bar_len = min(int(float(level.total_value_usd) / 10_000_000), 20)
        bar = "█" * bar_len
        density_mark = "⚠️ " if level.density in ["high", "critical"] else ""
        print(
            f"  ${float(level.price):>10,.0f} {bar} "
            f"${float(level.total_value_usd) / 1e6:.0f}M "
            f"{density_mark}{level.density.upper()}"
        )

    print(f"\nSHORT LIQUIDATIONS (above ${summary.current_price:,}):")
    for level in summary.short_levels[:4]:
        bar_len = min(int(float(level.total_value_usd) / 10_000_000), 20)
        bar = "█" * bar_len
        density_mark = "⚠️ " if level.density in ["high", "critical"] else ""
        print(
            f"  ${float(level.price):>10,.0f} {bar} "
            f"${float(level.total_value_usd) / 1e6:.0f}M "
            f"{density_mark}{level.density.upper()}"
        )

    # Large liquidations
    if args.large:
        print(console.section("RECENT LARGE LIQUIDATIONS"))
        large = monitor.get_recent_large_liquidations(args.symbol, min_value_usd=1_000_000, limit=5)
        if large:
            print(f"\n{'Exchange':<10} {'Side':<6} {'Price':>12} {'Value':>12} {'When':>10}")
            print("-" * 60)
            for l in large:
                print(
                    f"{l['exchange']:<10} "
                    f"{l['side']:<6} "
                    f"${l['price']:>10,.0f} "
                    f"${l['value_usd'] / 1e6:>10.1f}M "
                    f"{l['time_ago']:>10}"
                )


def cmd_options(args):
    """Handle options subcommand."""
    analyzer = OptionsAnalyzer()
    console = ConsoleFormatter()
    json_fmt = JSONFormatter()

    price = Decimal(str(args.price)) if args.price else None
    analysis = analyzer.analyze(args.symbol, current_price=price)

    print(console.header(f"{args.symbol} OPTIONS ANALYSIS"))

    if args.format == "json":
        print(
            json_fmt.format(
                {
                    "symbol": analysis.symbol,
                    "expiry": analysis.snapshot.expiry,
                    "atm_iv": analysis.snapshot.atm_iv,
                    "iv_interpretation": analysis.iv_interpretation,
                    "iv_percentile": analysis.iv_percentile,
                    "put_call_ratio_volume": analysis.snapshot.put_call_ratio_volume,
                    "put_call_ratio_oi": analysis.snapshot.put_call_ratio_oi,
                    "sentiment_from_pcr": analysis.sentiment_from_pcr,
                    "sentiment_from_skew": analysis.sentiment_from_skew,
                    "overall_sentiment": analysis.overall_sentiment,
                    "max_pain": float(analysis.snapshot.max_pain),
                    "max_pain_distance_pct": analysis.max_pain_distance_pct,
                    "expiry_pressure": analysis.expiry_pressure,
                    "total_call_oi": float(analysis.snapshot.total_call_oi),
                    "total_put_oi": float(analysis.snapshot.total_put_oi),
                }
            )
        )
        return

    snap = analysis.snapshot
    print(f"\nExpiry: {snap.expiry}")
    print(f"Exchange: {snap.exchange}")

    print("\nImplied Volatility:")
    print(f"   ATM IV: {snap.atm_iv:.1f}%")
    print(f"   Interpretation: {analysis.iv_interpretation.upper()}")
    print(f"   IV Rank: {analysis.iv_percentile:.0f}th percentile")

    print("\nPut/Call Analysis:")
    print(f"   PCR (Volume): {snap.put_call_ratio_volume:.2f}")
    print(f"   PCR (OI): {snap.put_call_ratio_oi:.2f}")
    print(f"   Sentiment: {console.sentiment_icon(analysis.sentiment_from_pcr)} {analysis.sentiment_from_pcr.upper()}")

    print("\nMax Pain:")
    print(f"   Price: ${snap.max_pain:,.0f}")
    print(f"   Distance: {analysis.max_pain_distance_pct:+.1f}% from current")

    print("\nOpen Interest:")
    print(f"   Calls: ${float(snap.total_call_oi) / 1e9:.2f}B")
    print(f"   Puts:  ${float(snap.total_put_oi) / 1e9:.2f}B")

    print(
        f"\nOverall Sentiment: {console.sentiment_icon(analysis.overall_sentiment)} "
        f"{analysis.overall_sentiment.upper()}"
    )
    print(f"Expiry Pressure: {analysis.expiry_pressure.upper()}")

    # Max pain levels
    if args.max_pain:
        print(console.section("MAX PAIN BY EXPIRY"))
        levels = analyzer.get_max_pain_levels(args.symbol)
        print(f"\n{'Expiry':<12} {'Max Pain':>12} {'Call OI':>12} {'Put OI':>12} {'PCR':>6}")
        print("-" * 50)
        for lvl in levels:
            print(
                f"{lvl['expiry']:<12} "
                f"${lvl['max_pain']:>10,.0f} "
                f"${lvl['call_oi'] / 1e9:>10.1f}B "
                f"${lvl['put_oi'] / 1e9:>10.1f}B "
                f"{lvl['pcr_oi']:>5.2f}"
            )

    # Options flow
    if args.flow:
        print(console.section("OPTIONS FLOW (Simulated)"))
        flows = analyzer.generate_mock_flow(args.symbol, count=5)
        print(f"\n{'Type':<6} {'Strike':>10} {'Size':>8} {'Premium':>12} {'Interpretation':<25}")
        print("-" * 70)
        for flow in flows:
            print(
                f"{flow.option_type.upper():<6} "
                f"${float(flow.strike):>8,.0f} "
                f"{flow.size_contracts:>8} "
                f"${float(flow.premium_usd):>10,.0f} "
                f"{flow.interpretation:<25}"
            )


def cmd_basis(args):
    """Handle basis subcommand."""
    calc = BasisCalculator()
    console = ConsoleFormatter()
    json_fmt = JSONFormatter()

    price = Decimal(str(args.price)) if args.price else None
    analysis = calc.analyze(args.symbol, price)

    print(console.header(f"{args.symbol} BASIS ANALYSIS"))

    if args.format == "json":
        print(
            json_fmt.format(
                {
                    "symbol": analysis.symbol,
                    "spot_price": float(analysis.spot_price),
                    "avg_basis_pct": analysis.avg_basis_pct,
                    "avg_annualized": analysis.avg_annualized,
                    "market_structure": analysis.market_structure,
                    "structure_strength": analysis.structure_strength,
                    "best_carry_expiry": analysis.best_carry_expiry,
                    "best_carry_yield": analysis.best_carry_yield,
                    "basis_data": [
                        {
                            "expiry": b.expiry,
                            "futures_price": float(b.futures_price),
                            "basis_pct": b.basis_pct,
                            "annualized_pct": b.annualized_pct,
                            "days_to_expiry": b.days_to_expiry,
                        }
                        for b in analysis.basis_data
                    ],
                }
            )
        )
        return

    print(f"\n   Spot Price: ${analysis.spot_price:,}")
    print("-" * 60)

    print(f"\n{'Expiry':<12} {'Futures':>12} {'Basis':>10} {'Annual':>10} {'Days':>6}")
    print("-" * 60)

    for basis in sorted(analysis.basis_data, key=lambda b: b.days_to_expiry):
        print(
            f"{basis.expiry:<12} "
            f"${float(basis.futures_price):>10,.0f} "
            f"{basis.basis_pct:>+9.2f}% "
            f"{basis.annualized_pct:>+9.1f}% "
            f"{basis.days_to_expiry:>6}"
        )

    print("-" * 60)
    print(f"\nMarket Structure: {analysis.structure_strength.title()} {analysis.market_structure.title()}")
    print(f"Average Basis: {analysis.avg_basis_pct:+.2f}%")
    print(f"Average Annualized: {analysis.avg_annualized:+.1f}%")
    print(f"Best Carry: {analysis.best_carry_expiry} ({analysis.best_carry_yield:+.1f}% annualized)")

    # Term structure
    print(console.section("TERM STRUCTURE"))
    structure = calc.get_term_structure(args.symbol, analysis.spot_price)
    for point in structure:
        bar = "+" * min(int(abs(point["annualized_pct"]) / 2), 20)
        direction = "▲" if point["annualized_pct"] > 0 else "▼"
        print(f"{point['expiry']:<12} {direction} {bar} {point['annualized_pct']:+.1f}%")

    # Carry scanner
    if args.carry:
        print(console.section("CARRY TRADE SCANNER"))
        opportunities = calc.find_carry_opportunities([args.symbol], min_yield=5.0)
        if opportunities:
            print(f"\n{'Expiry':<12} {'Basis':>8} {'Annual':>10} {'Direction':<12}")
            print("-" * 50)
            for opp in opportunities[:5]:
                print(f"{opp.expiry:<12} {opp.basis_pct:>+7.2f}% {opp.annualized_yield:>+9.1f}% {opp.direction:<12}")

            print("\nTop Opportunity:")
            top = opportunities[0]
            print(f"   Strategy: {top.strategy}")
            print(f"   Risk: {top.risk_notes}")
        else:
            print("\nNo carry opportunities found above threshold")


def cmd_dashboard(args):
    """Handle dashboard subcommand."""
    console = ConsoleFormatter()
    ReportGenerator()

    funding_tracker = FundingTracker()
    oi_analyzer = OIAnalyzer()
    liq_monitor = LiquidationMonitor()

    print(console.header("CRYPTO DERIVATIVES DASHBOARD"))

    for symbol in args.symbols:
        print(f"\n{'=' * 70}")
        print(f" {symbol} ".center(70, "="))
        print("=" * 70)

        try:
            # Funding
            funding = funding_tracker.analyze(symbol)
            print("\n📊 FUNDING")
            print(f"   Rate: {funding.weighted_avg:+.4%} ({funding.annualized_avg:+.1f}% annual)")
            print(f"   Sentiment: {console.sentiment_icon(funding.sentiment)} {funding.sentiment.title()}")

            # OI
            oi = oi_analyzer.analyze(symbol)
            print("\n📈 OPEN INTEREST")
            print(f"   Total: ${float(oi.total_oi_usd) / 1e9:.1f}B ({oi.avg_change_24h:+.1f}% 24h)")
            print(f"   Long/Short: {oi.weighted_long_ratio:.2f} ({oi.long_percentage:.0f}% long)")
            print(f"   Trend: {oi.trend_strength.title()} {oi.trend.title()}")

            # Liquidations
            liq = liq_monitor.get_summary(symbol)
            print("\n💥 LIQUIDATIONS (24h)")
            print(f"   Total: ${float(liq.total_24h_usd) / 1e6:.1f}M")
            print(
                f"   Longs: ${float(liq.long_liquidations_usd) / 1e6:.1f}M | "
                f"Shorts: ${float(liq.short_liquidations_usd) / 1e6:.1f}M"
            )
            print(f"   Cascade Risk: {console.risk_icon(liq.cascade_risk)} {liq.cascade_risk.upper()}")

        except Exception as e:
            print(f"\n⚠️  Error fetching data for {symbol}: {e}")

    print(f"\n{'=' * 70}")
    print(f"Dashboard generated at: {console.H_LINE * 50}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Crypto Derivatives Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s funding BTC
    %(prog)s oi BTC --price-change 3.5
    %(prog)s liquidations BTC --large
    %(prog)s options BTC --flow --max-pain
    %(prog)s basis BTC --carry
    %(prog)s dashboard BTC ETH SOL
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Funding subcommand
    funding_parser = subparsers.add_parser("funding", help="Analyze funding rates")
    funding_parser.add_argument("symbol", help="Trading symbol (e.g., BTC)")
    funding_parser.add_argument("--format", choices=["console", "json"], default="console", help="Output format")

    # OI subcommand
    oi_parser = subparsers.add_parser("oi", help="Analyze open interest")
    oi_parser.add_argument("symbol", help="Trading symbol")
    oi_parser.add_argument(
        "--price-change", type=float, dest="price_change", help="24h price change %% for divergence analysis"
    )
    oi_parser.add_argument("--format", choices=["console", "json"], default="console", help="Output format")

    # Liquidations subcommand
    liq_parser = subparsers.add_parser("liquidations", help="Monitor liquidations")
    liq_parser.add_argument("symbol", help="Trading symbol")
    liq_parser.add_argument("--price", type=float, help="Current price override")
    liq_parser.add_argument("--large", action="store_true", help="Show recent large liquidations")
    liq_parser.add_argument("--format", choices=["console", "json"], default="console", help="Output format")

    # Options subcommand
    opt_parser = subparsers.add_parser("options", help="Analyze options market")
    opt_parser.add_argument("symbol", help="Trading symbol")
    opt_parser.add_argument("--price", type=float, help="Current price override")
    opt_parser.add_argument("--max-pain", action="store_true", dest="max_pain", help="Show max pain by expiry")
    opt_parser.add_argument("--flow", action="store_true", help="Show options flow")
    opt_parser.add_argument("--format", choices=["console", "json"], default="console", help="Output format")

    # Basis subcommand
    basis_parser = subparsers.add_parser("basis", help="Calculate futures basis")
    basis_parser.add_argument("symbol", help="Trading symbol")
    basis_parser.add_argument("--price", type=float, help="Spot price override")
    basis_parser.add_argument("--carry", action="store_true", help="Show carry opportunities")
    basis_parser.add_argument("--format", choices=["console", "json"], default="console", help="Output format")

    # Dashboard subcommand
    dash_parser = subparsers.add_parser("dashboard", help="Multi-asset dashboard")
    dash_parser.add_argument("symbols", nargs="+", help="Trading symbols")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handler
    commands = {
        "funding": cmd_funding,
        "oi": cmd_oi,
        "liquidations": cmd_liquidations,
        "options": cmd_options,
        "basis": cmd_basis,
        "dashboard": cmd_dashboard,
    }

    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
