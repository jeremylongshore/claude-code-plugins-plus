#!/usr/bin/env python3
"""
Crypto Tax Calculator - Main CLI

Calculate cryptocurrency tax obligations with cost basis tracking,
capital gains computation, and Form 8949 report generation.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from transaction_parser import TransactionParser
from cost_basis_engine import CostBasisEngine
from tax_engine import TaxEngine
from report_generator import ReportGenerator


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate cryptocurrency tax obligations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --transactions trades.csv --year 2025
  %(prog)s --transactions trades.csv --method hifo --output report.csv
  %(prog)s --transactions coinbase.csv binance.csv --compare-methods
  %(prog)s --transactions all.csv --income-report

DISCLAIMER: This tool provides informational calculations only, not tax advice.
Consult a qualified tax professional for your specific situation.
        """,
    )

    # Required arguments
    parser.add_argument("--transactions", "-t", nargs="+", required=True, help="Transaction CSV file(s) to process")

    # Tax year filter
    parser.add_argument("--year", "-y", type=int, help="Filter transactions by tax year (default: all years)")

    # Cost basis method
    parser.add_argument(
        "--method", "-m", choices=["fifo", "lifo", "hifo"], default="fifo", help="Cost basis method (default: fifo)"
    )

    # Compare methods
    parser.add_argument("--compare-methods", action="store_true", help="Compare results across all cost basis methods")

    # Exchange format
    parser.add_argument(
        "--exchange",
        "-e",
        choices=["coinbase", "binance", "kraken", "gemini", "generic"],
        help="Exchange format for CSV parsing (auto-detected if not specified)",
    )

    # Output options
    parser.add_argument(
        "--format", "-f", choices=["table", "csv", "json"], default="table", help="Output format (default: table)"
    )

    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    # Report types
    parser.add_argument("--income-report", action="store_true", help="Generate income report (staking, airdrops, etc.)")

    parser.add_argument("--show-lots", action="store_true", help="Show lot-level details")

    # Verbose
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    args = parser.parse_args()

    try:
        # Parse transactions
        tx_parser = TransactionParser(verbose=args.verbose)
        transactions = []

        for csv_file in args.transactions:
            if args.verbose:
                print(f"Loading transactions from {csv_file}...")

            txs = tx_parser.parse(csv_file, exchange=args.exchange)
            transactions.extend(txs)
            if args.verbose:
                print(f"  Loaded {len(txs)} transactions")

        if not transactions:
            print("Error: No transactions found in input files", file=sys.stderr)
            sys.exit(1)

        # Sort by date
        transactions.sort(key=lambda x: x["date"])

        if args.verbose:
            print(f"Total transactions: {len(transactions)}")

        # Filter by year if specified
        if args.year:
            transactions = [tx for tx in transactions if tx["date"].year == args.year]
            if args.verbose:
                print(f"Filtered to {len(transactions)} transactions for {args.year}")

        # Initialize engines
        tax_engine = TaxEngine(verbose=args.verbose)
        report_gen = ReportGenerator()

        # Compare methods or calculate with single method
        if args.compare_methods:
            results = {}
            for method in ["fifo", "lifo", "hifo"]:
                cost_engine = CostBasisEngine(method=method, verbose=args.verbose)
                result = tax_engine.calculate(transactions, cost_engine)
                results[method] = result

            output = report_gen.format_comparison(results, args.format)

        elif args.income_report:
            # Income-only report
            result = tax_engine.calculate_income(transactions)
            output = report_gen.format_income(result, args.format)

        else:
            # Standard tax calculation
            cost_engine = CostBasisEngine(method=args.method, verbose=args.verbose)
            result = tax_engine.calculate(transactions, cost_engine)

            if args.show_lots:
                result["lots"] = cost_engine.get_inventory()

            output = report_gen.format(result, format_type=args.format, year=args.year, show_lots=args.show_lots)

        # Output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Report saved to {args.output}")
        else:
            print(output)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
