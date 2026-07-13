#!/usr/bin/env python3
"""
NFT Rarity Analyzer CLI

Analyze NFT collections to calculate trait rarity and rank tokens.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import argparse
import sys

from metadata_fetcher import MetadataFetcher
from trait_parser import TraitParser
from rarity_calculator import RarityCalculator, RarityAlgorithm
from formatters import (
    format_collection_summary,
    format_trait_distribution,
    format_rankings,
    format_token_detail,
    format_rarest_traits,
    format_comparison,
    format_json,
    format_csv_rankings,
)


def cmd_collection(args):
    """Analyze a collection."""
    fetcher = MetadataFetcher(verbose=args.verbose)
    parser = TraitParser(verbose=args.verbose)
    calculator = RarityCalculator(verbose=args.verbose)

    # Fetch collection
    print(f"Fetching collection: {args.slug}...")
    collection = fetcher.fetch_collection_opensea(args.slug, limit=args.limit)

    if not collection:
        print("Error: Failed to fetch collection. Check slug or API key.")
        sys.exit(1)

    if not collection.tokens:
        print("Error: No tokens found in collection.")
        sys.exit(1)

    # Build trait map
    print("Analyzing traits...")
    trait_map = parser.build_trait_map(collection.tokens)
    trait_summary = parser.get_trait_summary(trait_map)

    # Calculate rankings
    algorithm = RarityAlgorithm(args.algorithm)
    print(f"Calculating rarity ({algorithm.value})...")
    rarities = calculator.rank_collection(collection.tokens, trait_map, algorithm)

    # Normalize if requested
    if args.normalize:
        calculator.normalize_scores(rarities)

    # Output
    if args.json:
        print(
            format_json(
                {
                    "collection": {
                        "name": collection.name,
                        "slug": collection.slug,
                        "contract": collection.contract_address,
                        "total_supply": collection.total_supply,
                        "fetched": len(collection.tokens),
                    },
                    "traits": trait_summary,
                    "rankings": rarities[: args.top],
                }
            )
        )
    else:
        print(format_collection_summary(collection, len(trait_map.trait_types)))

        if args.traits:
            print(format_trait_distribution(trait_summary))

        print(format_rankings(rarities, limit=args.top))

        if args.rarest:
            print(format_rarest_traits(rarities, top_n=10))


def cmd_token(args):
    """Analyze a specific token."""
    fetcher = MetadataFetcher(verbose=args.verbose)
    parser = TraitParser(verbose=args.verbose)
    calculator = RarityCalculator(verbose=args.verbose)

    # Fetch collection
    print(f"Fetching collection: {args.slug}...")
    collection = fetcher.fetch_collection_opensea(args.slug, limit=args.limit)

    if not collection or not collection.tokens:
        print("Error: Failed to fetch collection.")
        sys.exit(1)

    # Build trait map and rankings
    trait_map = parser.build_trait_map(collection.tokens)
    algorithm = RarityAlgorithm(args.algorithm)
    rarities = calculator.rank_collection(collection.tokens, trait_map, algorithm)

    if args.normalize:
        calculator.normalize_scores(rarities)

    # Find token
    token_rarity = calculator.get_token_by_id(rarities, args.token_id)

    if not token_rarity:
        print(f"Error: Token #{args.token_id} not found in fetched data.")
        if collection.tokens:
            print(
                f"Fetched tokens: {min(t.token_id for t in collection.tokens)} - {max(t.token_id for t in collection.tokens)}"
            )
        sys.exit(1)

    # Output
    if args.json:
        print(format_json(token_rarity))
    else:
        print(format_token_detail(token_rarity))


def cmd_compare(args):
    """Compare multiple tokens."""
    fetcher = MetadataFetcher(verbose=args.verbose)
    parser = TraitParser(verbose=args.verbose)
    calculator = RarityCalculator(verbose=args.verbose)

    # Fetch collection
    print(f"Fetching collection: {args.slug}...")
    collection = fetcher.fetch_collection_opensea(args.slug, limit=args.limit)

    if not collection or not collection.tokens:
        print("Error: Failed to fetch collection.")
        sys.exit(1)

    # Build trait map and rankings
    trait_map = parser.build_trait_map(collection.tokens)
    algorithm = RarityAlgorithm(args.algorithm)
    rarities = calculator.rank_collection(collection.tokens, trait_map, algorithm)

    if args.normalize:
        calculator.normalize_scores(rarities)

    # Find tokens
    token_ids = [int(x) for x in args.tokens.split(",")]
    tokens_to_compare = []

    for tid in token_ids:
        token = calculator.get_token_by_id(rarities, tid)
        if token:
            tokens_to_compare.append(token)
        else:
            print(f"Warning: Token #{tid} not found")

    if not tokens_to_compare:
        print("Error: No valid tokens found.")
        sys.exit(1)

    # Output
    if args.json:
        print(format_json(tokens_to_compare))
    else:
        print(format_comparison(tokens_to_compare))


def cmd_traits(args):
    """Show trait distribution."""
    fetcher = MetadataFetcher(verbose=args.verbose)
    parser = TraitParser(verbose=args.verbose)

    # Fetch collection
    print(f"Fetching collection: {args.slug}...")
    collection = fetcher.fetch_collection_opensea(args.slug, limit=args.limit)

    if not collection or not collection.tokens:
        print("Error: Failed to fetch collection.")
        sys.exit(1)

    # Build trait map
    trait_map = parser.build_trait_map(collection.tokens)
    trait_summary = parser.get_trait_summary(trait_map)

    # Output
    if args.json:
        print(format_json(trait_summary))
    else:
        print(format_collection_summary(collection, len(trait_map.trait_types)))
        print(format_trait_distribution(trait_summary))


def cmd_export(args):
    """Export rarity data."""
    fetcher = MetadataFetcher(verbose=args.verbose)
    parser = TraitParser(verbose=args.verbose)
    calculator = RarityCalculator(verbose=args.verbose)

    # Fetch collection
    print(f"Fetching collection: {args.slug}...", file=sys.stderr)
    collection = fetcher.fetch_collection_opensea(args.slug, limit=args.limit)

    if not collection or not collection.tokens:
        print("Error: Failed to fetch collection.", file=sys.stderr)
        sys.exit(1)

    # Calculate
    trait_map = parser.build_trait_map(collection.tokens)
    algorithm = RarityAlgorithm(args.algorithm)
    rarities = calculator.rank_collection(collection.tokens, trait_map, algorithm)

    if args.normalize:
        calculator.normalize_scores(rarities)

    # Export
    if args.format == "csv":
        print(format_csv_rankings(rarities))
    else:
        print(format_json(rarities))


def cmd_cache(args):
    """Manage cache."""
    fetcher = MetadataFetcher(verbose=args.verbose)

    if args.clear:
        count = fetcher.clear_cache(args.pattern)
        print(f"Cleared {count} cache files")
    else:
        cache_files = list(fetcher.cache_dir.glob("*.json"))
        print(f"Cache directory: {fetcher.cache_dir}")
        print(f"Cached items: {len(cache_files)}")
        if args.list:
            for f in sorted(cache_files)[:20]:
                print(f"  - {f.name}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NFT Rarity Analyzer - Calculate and rank NFT rarity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rarity_analyzer.py collection boredapeyachtclub
  rarity_analyzer.py collection pudgypenguins --top 50
  rarity_analyzer.py token boredapeyachtclub 1234
  rarity_analyzer.py compare boredapeyachtclub 1234,5678,9012
  rarity_analyzer.py traits boredapeyachtclub
  rarity_analyzer.py export boredapeyachtclub --format csv > rankings.csv
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # collection command
    p_col = subparsers.add_parser("collection", help="Analyze a collection")
    p_col.add_argument("slug", help="Collection slug (e.g., 'boredapeyachtclub')")
    p_col.add_argument("--limit", "-l", type=int, default=200, help="Max tokens to fetch (default: 200)")
    p_col.add_argument("--top", "-t", type=int, default=20, help="Show top N tokens (default: 20)")
    p_col.add_argument(
        "--algorithm",
        "-a",
        default="rarity_score",
        choices=["statistical", "rarity_score", "average", "information"],
        help="Rarity algorithm (default: rarity_score)",
    )
    p_col.add_argument("--normalize", "-n", action="store_true", help="Normalize scores to 0-100")
    p_col.add_argument("--traits", action="store_true", help="Show trait distribution")
    p_col.add_argument("--rarest", action="store_true", help="Show rarest traits")
    p_col.set_defaults(func=cmd_collection)

    # token command
    p_token = subparsers.add_parser("token", help="Analyze a specific token")
    p_token.add_argument("slug", help="Collection slug")
    p_token.add_argument("token_id", type=int, help="Token ID")
    p_token.add_argument("--limit", "-l", type=int, default=200, help="Max tokens to fetch for context")
    p_token.add_argument(
        "--algorithm", "-a", default="rarity_score", choices=["statistical", "rarity_score", "average", "information"]
    )
    p_token.add_argument("--normalize", "-n", action="store_true")
    p_token.set_defaults(func=cmd_token)

    # compare command
    p_compare = subparsers.add_parser("compare", help="Compare multiple tokens")
    p_compare.add_argument("slug", help="Collection slug")
    p_compare.add_argument("tokens", help="Comma-separated token IDs")
    p_compare.add_argument("--limit", "-l", type=int, default=200)
    p_compare.add_argument(
        "--algorithm", "-a", default="rarity_score", choices=["statistical", "rarity_score", "average", "information"]
    )
    p_compare.add_argument("--normalize", "-n", action="store_true")
    p_compare.set_defaults(func=cmd_compare)

    # traits command
    p_traits = subparsers.add_parser("traits", help="Show trait distribution")
    p_traits.add_argument("slug", help="Collection slug")
    p_traits.add_argument("--limit", "-l", type=int, default=200)
    p_traits.set_defaults(func=cmd_traits)

    # export command
    p_export = subparsers.add_parser("export", help="Export rarity data")
    p_export.add_argument("slug", help="Collection slug")
    p_export.add_argument(
        "--format", "-f", default="json", choices=["json", "csv"], help="Export format (default: json)"
    )
    p_export.add_argument("--limit", "-l", type=int, default=500)
    p_export.add_argument(
        "--algorithm", "-a", default="rarity_score", choices=["statistical", "rarity_score", "average", "information"]
    )
    p_export.add_argument("--normalize", "-n", action="store_true")
    p_export.set_defaults(func=cmd_export)

    # cache command
    p_cache = subparsers.add_parser("cache", help="Manage cache")
    p_cache.add_argument("--clear", "-c", action="store_true", help="Clear cache")
    p_cache.add_argument("--list", action="store_true", help="List cached items")
    p_cache.add_argument("--pattern", "-p", help="Pattern to match when clearing")
    p_cache.set_defaults(func=cmd_cache)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if hasattr(args, "func"):
        args.func(args)


if __name__ == "__main__":
    main()
