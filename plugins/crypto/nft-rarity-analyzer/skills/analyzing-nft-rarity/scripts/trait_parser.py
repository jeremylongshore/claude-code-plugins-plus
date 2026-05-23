#!/usr/bin/env python3
"""
NFT Trait Parser

Parse and normalize NFT traits for rarity analysis.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Any
from collections import defaultdict


@dataclass
class NormalizedTrait:
    """Normalized trait with frequency data."""

    trait_type: str
    value: str
    count: int
    frequency: float  # 0-1
    is_none: bool  # True if this represents missing trait


@dataclass
class TraitType:
    """Trait type with all possible values."""

    name: str
    values: Dict[str, int]  # value -> count
    total_with_trait: int
    total_without: int


@dataclass
class TraitMap:
    """Complete trait frequency map for a collection."""

    trait_types: Dict[str, TraitType]
    total_supply: int
    token_traits: Dict[int, List[NormalizedTrait]]  # token_id -> traits


class TraitParser:
    """Parse and normalize NFT traits."""

    def __init__(self, verbose: bool = False):
        """Initialize trait parser.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def normalize_value(self, value: Any) -> str:
        """Normalize trait value to string.

        Args:
            value: Raw trait value

        Returns:
            Normalized string value
        """
        if value is None:
            return "None"

        # Handle numeric values
        if isinstance(value, (int, float)):
            # Remove trailing zeros for cleaner display
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)

        # Handle boolean
        if isinstance(value, bool):
            return "Yes" if value else "No"

        # Handle string
        value_str = str(value).strip()

        # Normalize common variations
        value_lower = value_str.lower()
        if value_lower in ("none", "null", "n/a", ""):
            return "None"

        return value_str

    def normalize_trait_type(self, trait_type: str) -> str:
        """Normalize trait type name.

        Args:
            trait_type: Raw trait type

        Returns:
            Normalized trait type
        """
        if not trait_type:
            return "Unknown"

        return trait_type.strip().title()

    def parse_token_attributes(self, attributes: List[Dict[str, Any]]) -> List[NormalizedTrait]:
        """Parse token attributes into normalized traits.

        Args:
            attributes: Raw attribute list from metadata

        Returns:
            List of NormalizedTrait (without frequency - set later)
        """
        traits = []

        for attr in attributes:
            trait_type = self.normalize_trait_type(attr.get("trait_type", "Unknown"))
            value = self.normalize_value(attr.get("value"))

            # Skip display_type traits like "number" or "boost_percentage"
            display_type = attr.get("display_type")
            if display_type in ("number", "boost_number", "boost_percentage"):
                continue

            traits.append(
                NormalizedTrait(
                    trait_type=trait_type,
                    value=value,
                    count=0,
                    frequency=0.0,
                    is_none=value == "None",
                )
            )

        return traits

    def build_trait_map(
        self,
        tokens: List[Any],  # List of TokenData
    ) -> TraitMap:
        """Build complete trait frequency map from token list.

        Args:
            tokens: List of TokenData objects

        Returns:
            TraitMap with all frequency data
        """
        total_supply = len(tokens)
        trait_types: Dict[str, TraitType] = {}
        token_traits: Dict[int, List[NormalizedTrait]] = {}

        # First pass: count all trait occurrences
        trait_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        trait_presence: Dict[str, Set[int]] = defaultdict(set)  # trait_type -> token_ids

        for token in tokens:
            token_id = token.token_id
            parsed_traits = []

            # Iterate directly over Trait objects (no conversion needed)
            for attr in token.attributes:
                trait_type = self.normalize_trait_type(attr.trait_type)
                value = self.normalize_value(attr.value)

                # Skip display_type traits like "number" or "boost_percentage"
                if attr.display_type in ("number", "boost_number", "boost_percentage"):
                    continue

                trait_counts[trait_type][value] += 1
                trait_presence[trait_type].add(token_id)

                parsed_traits.append(
                    NormalizedTrait(
                        trait_type=trait_type,
                        value=value,
                        count=0,
                        frequency=0.0,
                        is_none=value == "None",
                    )
                )

            token_traits[token_id] = parsed_traits

        # Build TraitType objects with None counts
        for trait_type, values in trait_counts.items():
            total_with = len(trait_presence[trait_type])
            total_without = total_supply - total_with

            trait_types[trait_type] = TraitType(
                name=trait_type,
                values=dict(values),
                total_with_trait=total_with,
                total_without=total_without,
            )

            # Add implicit "None" for tokens missing this trait
            if total_without > 0:
                trait_types[trait_type].values["None"] = total_without

        # Second pass: update traits with frequency data
        for token_id, traits in token_traits.items():
            # Track which trait types this token has
            present_types = {t.trait_type for t in traits}

            # Add explicit "None" traits for missing trait types
            for trait_type, tt in trait_types.items():
                if trait_type not in present_types:
                    traits.append(
                        NormalizedTrait(
                            trait_type=trait_type,
                            value="None",
                            count=tt.total_without,
                            frequency=tt.total_without / total_supply,
                            is_none=True,
                        )
                    )

            # Update counts and frequencies
            for trait in traits:
                tt = trait_types.get(trait.trait_type)
                if tt:
                    trait.count = tt.values.get(trait.value, 0)
                    trait.frequency = trait.count / total_supply if total_supply > 0 else 0

        return TraitMap(
            trait_types=trait_types,
            total_supply=total_supply,
            token_traits=token_traits,
        )

    def get_trait_summary(self, trait_map: TraitMap) -> List[Dict[str, Any]]:
        """Get summary of trait types and their value distributions.

        Args:
            trait_map: TraitMap from build_trait_map

        Returns:
            List of trait type summaries
        """
        summaries = []

        for name, tt in sorted(trait_map.trait_types.items()):
            values_sorted = sorted(tt.values.items(), key=lambda x: x[1], reverse=True)

            summaries.append(
                {
                    "trait_type": name,
                    "unique_values": len(tt.values),
                    "total_with": tt.total_with_trait,
                    "total_without": tt.total_without,
                    "top_values": [
                        {"value": v, "count": c, "percentage": c / trait_map.total_supply * 100}
                        for v, c in values_sorted[:5]
                    ],
                    "rarest_values": [
                        {"value": v, "count": c, "percentage": c / trait_map.total_supply * 100}
                        for v, c in values_sorted[-3:]
                        if c > 0
                    ],
                }
            )

        return summaries


def main():
    """CLI entry point for testing."""
    from metadata_fetcher import TokenData, Trait

    parser = TraitParser(verbose=True)

    # Create sample tokens
    sample_tokens = [
        TokenData(
            token_id=1,
            name="Token #1",
            description="",
            image_url="",
            attributes=[
                Trait("Background", "Blue", None),
                Trait("Eyes", "Laser", None),
                Trait("Hat", "Crown", None),
            ],
        ),
        TokenData(
            token_id=2,
            name="Token #2",
            description="",
            image_url="",
            attributes=[
                Trait("Background", "Red", None),
                Trait("Eyes", "Normal", None),
                Trait("Hat", "Cap", None),
            ],
        ),
        TokenData(
            token_id=3,
            name="Token #3",
            description="",
            image_url="",
            attributes=[
                Trait("Background", "Blue", None),
                Trait("Eyes", "Normal", None),
                # No Hat trait
            ],
        ),
    ]

    print("=== Trait Parser Test ===")
    print(f"Tokens: {len(sample_tokens)}")

    trait_map = parser.build_trait_map(sample_tokens)

    print(f"\nTrait Types: {len(trait_map.trait_types)}")
    for name, tt in trait_map.trait_types.items():
        print(f"\n  {name}:")
        for value, count in sorted(tt.values.items(), key=lambda x: -x[1]):
            pct = count / trait_map.total_supply * 100
            print(f"    - {value}: {count} ({pct:.1f}%)")

    print("\n=== Token Traits ===")
    for token_id, traits in trait_map.token_traits.items():
        print(f"\nToken #{token_id}:")
        for t in traits:
            marker = " (NONE)" if t.is_none else ""
            print(f"  {t.trait_type}: {t.value} ({t.frequency:.1%}){marker}")


if __name__ == "__main__":
    main()
