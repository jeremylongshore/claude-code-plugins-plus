#!/usr/bin/env python3
"""
NFT Rarity Calculator

Calculate rarity scores using multiple algorithms.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import math
from dataclasses import dataclass
from typing import List, Any, Tuple
from enum import Enum


class RarityAlgorithm(Enum):
    """Available rarity scoring algorithms.

    Note: Normalization (0-100 scale) is a post-processing step applied
    via normalize_scores(), not a primary algorithm.
    """

    STATISTICAL = "statistical"  # Sum of 1/frequency (same as RARITY_SCORE)
    RARITY_SCORE = "rarity_score"  # Sum of 1/frequency for all traits
    AVERAGE = "average"  # Mean of trait rarities
    INFORMATION = "information"  # Entropy-based (-log2)


@dataclass
class TraitRarity:
    """Rarity data for a single trait."""

    trait_type: str
    value: str
    count: int
    frequency: float
    rarity: float  # 1 / frequency
    contribution: float  # Contribution to total score


@dataclass
class TokenRarity:
    """Complete rarity data for a token."""

    token_id: int
    name: str
    rarity_score: float
    rank: int
    percentile: float  # Top X%
    traits: List[TraitRarity]
    algorithm: str


class RarityCalculator:
    """Calculate NFT rarity scores."""

    def __init__(self, verbose: bool = False):
        """Initialize rarity calculator.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def calculate_trait_rarity(self, frequency: float, total_supply: int) -> float:
        """Calculate rarity for a single trait.

        Args:
            frequency: Trait frequency (0-1)
            total_supply: Total tokens in collection

        Returns:
            Rarity score (higher = rarer)
        """
        if frequency <= 0:
            return float("inf")
        return 1.0 / frequency

    def calculate_statistical_rarity(
        self,
        traits: List[Any],  # NormalizedTrait
        total_supply: int,
    ) -> Tuple[float, List[TraitRarity]]:
        """Calculate rarity using statistical method (product of rarities).

        For each trait: rarity = 1 / frequency
        Total: sum of individual rarities

        Args:
            traits: List of NormalizedTrait
            total_supply: Total tokens

        Returns:
            Tuple of (score, trait_rarities)
        """
        trait_rarities = []
        total_score = 0.0

        for trait in traits:
            frequency = trait.frequency
            if frequency <= 0:
                frequency = 1 / total_supply  # Minimum

            rarity = 1.0 / frequency
            total_score += rarity

            trait_rarities.append(
                TraitRarity(
                    trait_type=trait.trait_type,
                    value=trait.value,
                    count=trait.count,
                    frequency=frequency,
                    rarity=rarity,
                    contribution=rarity,
                )
            )

        return total_score, trait_rarities

    def calculate_rarity_score(self, traits: List[Any], total_supply: int) -> Tuple[float, List[TraitRarity]]:
        """Calculate rarity score (sum of 1/frequency).

        This is the most common rarity scoring method.

        Args:
            traits: List of NormalizedTrait
            total_supply: Total tokens

        Returns:
            Tuple of (score, trait_rarities)
        """
        return self.calculate_statistical_rarity(traits, total_supply)

    def calculate_average_rarity(self, traits: List[Any], total_supply: int) -> Tuple[float, List[TraitRarity]]:
        """Calculate average rarity across traits.

        Args:
            traits: List of NormalizedTrait
            total_supply: Total tokens

        Returns:
            Tuple of (score, trait_rarities)
        """
        if not traits:
            return 0.0, []

        total_score, trait_rarities = self.calculate_statistical_rarity(traits, total_supply)

        avg_score = total_score / len(traits)

        # Update contributions to show per-trait average impact
        for tr in trait_rarities:
            tr.contribution = tr.rarity / len(traits)

        return avg_score, trait_rarities

    def calculate_information_content(self, traits: List[Any], total_supply: int) -> Tuple[float, List[TraitRarity]]:
        """Calculate information content (entropy-based).

        Uses -log2(frequency) for each trait.
        Higher values = more information = rarer.

        Args:
            traits: List of NormalizedTrait
            total_supply: Total tokens

        Returns:
            Tuple of (score, trait_rarities)
        """
        trait_rarities = []
        total_score = 0.0

        for trait in traits:
            frequency = trait.frequency
            if frequency <= 0:
                frequency = 1 / total_supply

            # Information content in bits
            information = -math.log2(frequency) if frequency > 0 else 0
            total_score += information

            trait_rarities.append(
                TraitRarity(
                    trait_type=trait.trait_type,
                    value=trait.value,
                    count=trait.count,
                    frequency=frequency,
                    rarity=1.0 / frequency,
                    contribution=information,
                )
            )

        return total_score, trait_rarities

    def calculate_token_rarity(
        self,
        token_id: int,
        name: str,
        traits: List[Any],  # NormalizedTrait
        total_supply: int,
        algorithm: RarityAlgorithm = RarityAlgorithm.RARITY_SCORE,
    ) -> TokenRarity:
        """Calculate complete rarity for a token.

        Args:
            token_id: Token ID
            name: Token name
            traits: List of NormalizedTrait
            total_supply: Total tokens
            algorithm: Scoring algorithm to use

        Returns:
            TokenRarity with score and breakdown
        """
        if algorithm == RarityAlgorithm.STATISTICAL:
            score, trait_rarities = self.calculate_statistical_rarity(traits, total_supply)
        elif algorithm == RarityAlgorithm.AVERAGE:
            score, trait_rarities = self.calculate_average_rarity(traits, total_supply)
        elif algorithm == RarityAlgorithm.INFORMATION:
            score, trait_rarities = self.calculate_information_content(traits, total_supply)
        else:  # Default: RARITY_SCORE
            score, trait_rarities = self.calculate_rarity_score(traits, total_supply)

        # Sort traits by contribution (highest first)
        trait_rarities.sort(key=lambda x: x.contribution, reverse=True)

        return TokenRarity(
            token_id=token_id,
            name=name,
            rarity_score=score,
            rank=0,  # Set during ranking
            percentile=0.0,  # Set during ranking
            traits=trait_rarities,
            algorithm=algorithm.value,
        )

    def rank_collection(
        self,
        tokens: List[Any],  # List of TokenData
        trait_map: Any,  # TraitMap
        algorithm: RarityAlgorithm = RarityAlgorithm.RARITY_SCORE,
    ) -> List[TokenRarity]:
        """Rank all tokens in a collection by rarity.

        Args:
            tokens: List of TokenData
            trait_map: TraitMap from trait_parser
            algorithm: Scoring algorithm

        Returns:
            List of TokenRarity sorted by rank (rarest first)
        """
        total_supply = trait_map.total_supply
        rarities = []

        for token in tokens:
            token_id = token.token_id
            traits = trait_map.token_traits.get(token_id, [])

            rarity = self.calculate_token_rarity(
                token_id=token_id,
                name=token.name,
                traits=traits,
                total_supply=total_supply,
                algorithm=algorithm,
            )
            rarities.append(rarity)

        # Sort by score (descending - higher = rarer)
        rarities.sort(key=lambda x: x.rarity_score, reverse=True)

        # Assign ranks and percentiles
        for i, rarity in enumerate(rarities):
            rarity.rank = i + 1
            rarity.percentile = (i + 1) / len(rarities) * 100

        return rarities

    def get_token_by_id(self, rarities: List[TokenRarity], token_id: int) -> TokenRarity:
        """Find token rarity by ID.

        Args:
            rarities: List of TokenRarity
            token_id: Token ID to find

        Returns:
            TokenRarity or None
        """
        for rarity in rarities:
            if rarity.token_id == token_id:
                return rarity
        return None

    def normalize_scores(self, rarities: List[TokenRarity], min_score: float = 0, max_score: float = 100) -> None:
        """Normalize scores to a 0-100 scale (modifies in place).

        Args:
            rarities: List of TokenRarity to normalize
            min_score: Target minimum (default 0)
            max_score: Target maximum (default 100)
        """
        if not rarities:
            return

        scores = [r.rarity_score for r in rarities]
        old_min = min(scores)
        old_max = max(scores)
        old_range = old_max - old_min

        if old_range == 0:
            for r in rarities:
                r.rarity_score = (min_score + max_score) / 2
            return

        for r in rarities:
            normalized = (r.rarity_score - old_min) / old_range
            r.rarity_score = min_score + normalized * (max_score - min_score)


def main():
    """CLI entry point for testing."""
    from metadata_fetcher import TokenData, Trait
    from trait_parser import TraitParser

    # Create sample tokens
    sample_tokens = [
        TokenData(
            token_id=1,
            name="Rare Token",
            description="",
            image_url="",
            attributes=[
                Trait("Background", "Gold", None),  # Very rare
                Trait("Eyes", "Laser", None),
                Trait("Hat", "Crown", None),
            ],
        ),
        TokenData(
            token_id=2,
            name="Common Token",
            description="",
            image_url="",
            attributes=[
                Trait("Background", "Blue", None),
                Trait("Eyes", "Normal", None),
                Trait("Hat", "Cap", None),
            ],
        ),
        TokenData(
            token_id=3,
            name="Mid Token",
            description="",
            image_url="",
            attributes=[
                Trait("Background", "Blue", None),
                Trait("Eyes", "Normal", None),
                Trait("Hat", "Crown", None),
            ],
        ),
        TokenData(
            token_id=4,
            name="Another Common",
            description="",
            image_url="",
            attributes=[
                Trait("Background", "Blue", None),
                Trait("Eyes", "Normal", None),
                Trait("Hat", "Cap", None),
            ],
        ),
    ]

    print("=== Rarity Calculator Test ===")
    print(f"Tokens: {len(sample_tokens)}")

    # Build trait map
    parser = TraitParser()
    trait_map = parser.build_trait_map(sample_tokens)

    # Calculate rankings
    calculator = RarityCalculator(verbose=True)
    rarities = calculator.rank_collection(sample_tokens, trait_map, RarityAlgorithm.RARITY_SCORE)

    print("\n=== Rankings (Rarity Score Method) ===")
    for r in rarities:
        print(f"\n#{r.rank} - {r.name} (ID: {r.token_id})")
        print(f"   Score: {r.rarity_score:.2f} | Top {r.percentile:.1f}%")
        print("   Top traits:")
        for t in r.traits[:3]:
            print(f"     - {t.trait_type}: {t.value} ({t.frequency:.1%}) +{t.contribution:.1f}")


if __name__ == "__main__":
    main()
