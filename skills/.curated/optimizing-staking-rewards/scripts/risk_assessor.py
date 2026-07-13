#!/usr/bin/env python3
"""
Risk Assessor

Assesses risk for staking protocols and validators.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class RiskAssessment:
    """Risk assessment for a staking option."""

    overall_score: int  # 1-10 (10 = safest)
    risk_level: str  # low, medium, high, very_high

    # Score breakdown
    audit_score: float
    production_score: float
    tvl_score: float
    reputation_score: float
    validator_score: float

    # Risk factors
    factors: List[str]
    warnings: List[str]
    considerations: List[str]


# Protocol risk database
PROTOCOL_RISK_DATA = {
    "lido": {
        "audited": True,
        "audit_age_months": 6,
        "production_months": 40,
        "validator_count": 30,
        "has_insurance": True,
        "reputation": "excellent",
        "slashing_incidents": 0,
        "considerations": [
            "Largest LSD by market share - potential centralization concerns",
            "stETH occasionally trades at slight discount to ETH",
            "10% fee on staking rewards",
        ],
    },
    "rocket-pool": {
        "audited": True,
        "audit_age_months": 8,
        "production_months": 36,
        "validator_count": 2000,  # Decentralized node operators
        "has_insurance": True,
        "reputation": "excellent",
        "slashing_incidents": 1,  # Minor
        "considerations": [
            "More decentralized than Lido (permissionless node operators)",
            "14% fee split between protocol and node operators",
            "rETH has lower liquidity than stETH",
        ],
    },
    "frax-ether": {
        "audited": True,
        "audit_age_months": 10,
        "production_months": 18,
        "validator_count": 10,
        "has_insurance": False,
        "reputation": "good",
        "slashing_incidents": 0,
        "considerations": [
            "Higher APY through validator MEV optimization",
            "Newer protocol with less track record",
            "Part of larger Frax ecosystem",
        ],
    },
    "coinbase-wrapped-staked-eth": {
        "audited": True,
        "audit_age_months": 4,
        "production_months": 24,
        "validator_count": 100,  # Coinbase managed
        "has_insurance": True,  # Coinbase backing
        "reputation": "excellent",
        "slashing_incidents": 0,
        "considerations": [
            "Centralized custodian (Coinbase)",
            "25% fee on rewards - highest in category",
            "Strong regulatory compliance",
        ],
    },
    "marinade-finance": {
        "audited": True,
        "audit_age_months": 6,
        "production_months": 30,
        "validator_count": 450,
        "has_insurance": False,
        "reputation": "good",
        "slashing_incidents": 0,
        "considerations": [
            "Native liquid staking for Solana",
            "Diversified across many validators",
            "MNDE governance token adds complexity",
        ],
    },
    "benqi-staked-avax": {
        "audited": True,
        "audit_age_months": 8,
        "production_months": 24,
        "validator_count": 25,
        "has_insurance": False,
        "reputation": "good",
        "slashing_incidents": 0,
        "considerations": [
            "Native liquid staking for Avalanche",
            "Part of Benqi lending ecosystem",
            "Lower TVL than ETH alternatives",
        ],
    },
}

# Default data for unknown protocols
DEFAULT_PROTOCOL_DATA = {
    "audited": False,
    "audit_age_months": 999,
    "production_months": 0,
    "validator_count": 0,
    "has_insurance": False,
    "reputation": "unknown",
    "slashing_incidents": 0,
    "considerations": ["Unknown protocol - exercise extreme caution"],
}


class RiskAssessor:
    """Assesses risk for staking protocols."""

    # Weights for each risk factor
    WEIGHTS = {
        "audit": 0.30,  # 30%
        "production": 0.25,  # 25%
        "tvl": 0.20,  # 20%
        "reputation": 0.15,  # 15%
        "validator": 0.10,  # 10%
    }

    def __init__(self, verbose: bool = False):
        """Initialize assessor.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def assess_risk(self, pool: Dict[str, Any]) -> RiskAssessment:
        """Assess risk for a staking option.

        Args:
            pool: Pool data from fetcher

        Returns:
            RiskAssessment with scores and factors
        """
        project = pool.get("project", "").lower()
        tvl = pool.get("tvlUsd", 0) or 0
        staking_type = pool.get("staking_type", "liquid")

        # Get protocol data
        protocol_data = PROTOCOL_RISK_DATA.get(project, DEFAULT_PROTOCOL_DATA)

        # Calculate individual scores (0-10)
        audit_score = self._score_audit(protocol_data)
        production_score = self._score_production(protocol_data)
        tvl_score = self._score_tvl(tvl)
        reputation_score = self._score_reputation(protocol_data)
        validator_score = self._score_validators(protocol_data)

        # Native staking gets bonus points
        if staking_type == "native":
            audit_score = min(10, audit_score + 1)
            reputation_score = min(10, reputation_score + 1)

        # Calculate weighted overall score
        overall = (
            audit_score * self.WEIGHTS["audit"]
            + production_score * self.WEIGHTS["production"]
            + tvl_score * self.WEIGHTS["tvl"]
            + reputation_score * self.WEIGHTS["reputation"]
            + validator_score * self.WEIGHTS["validator"]
        )

        overall_score = max(1, min(10, round(overall)))

        # Determine risk level
        if overall_score >= 8:
            risk_level = "low"
        elif overall_score >= 6:
            risk_level = "medium"
        elif overall_score >= 4:
            risk_level = "high"
        else:
            risk_level = "very_high"

        # Compile factors and warnings
        factors = self._get_factors(protocol_data, staking_type)
        warnings = self._get_warnings(protocol_data, tvl)
        considerations = protocol_data.get("considerations", [])

        return RiskAssessment(
            overall_score=overall_score,
            risk_level=risk_level,
            audit_score=round(audit_score, 1),
            production_score=round(production_score, 1),
            tvl_score=round(tvl_score, 1),
            reputation_score=round(reputation_score, 1),
            validator_score=round(validator_score, 1),
            factors=factors,
            warnings=warnings,
            considerations=considerations,
        )

    def _score_audit(self, data: Dict) -> float:
        """Score based on audit status."""
        if not data.get("audited"):
            return 3.0

        age = data.get("audit_age_months", 999)
        if age <= 6:
            return 10.0
        elif age <= 12:
            return 8.0
        elif age <= 24:
            return 6.0
        else:
            return 4.0

    def _score_production(self, data: Dict) -> float:
        """Score based on time in production."""
        months = data.get("production_months", 0)

        if months >= 36:
            return 10.0
        elif months >= 24:
            return 8.0
        elif months >= 12:
            return 6.0
        elif months >= 6:
            return 4.0
        else:
            return 2.0

    def _score_tvl(self, tvl: float) -> float:
        """Score based on TVL size."""
        if tvl >= 10_000_000_000:  # $10B+
            return 10.0
        elif tvl >= 1_000_000_000:  # $1B+
            return 9.0
        elif tvl >= 100_000_000:  # $100M+
            return 7.0
        elif tvl >= 10_000_000:  # $10M+
            return 5.0
        elif tvl >= 1_000_000:  # $1M+
            return 3.0
        else:
            return 1.0

    def _score_reputation(self, data: Dict) -> float:
        """Score based on protocol reputation."""
        reputation = data.get("reputation", "unknown")

        scores = {
            "excellent": 10.0,
            "good": 7.5,
            "moderate": 5.0,
            "questionable": 3.0,
            "unknown": 2.0,
        }

        base = scores.get(reputation, 2.0)

        # Adjust for slashing incidents
        incidents = data.get("slashing_incidents", 0)
        if incidents > 0:
            base -= min(incidents * 1.0, 3.0)

        # Bonus for insurance
        if data.get("has_insurance"):
            base += 0.5

        return max(1, min(10, base))

    def _score_validators(self, data: Dict) -> float:
        """Score based on validator diversity."""
        count = data.get("validator_count", 0)

        if count >= 100:
            return 10.0
        elif count >= 30:
            return 8.0
        elif count >= 10:
            return 6.0
        elif count >= 5:
            return 4.0
        else:
            return 2.0

    def _get_factors(self, data: Dict, staking_type: str) -> List[str]:
        """Get positive risk factors."""
        factors = []

        if data.get("audited"):
            age = data.get("audit_age_months", 999)
            if age <= 12:
                factors.append(f"Multiple audits, latest {age} months ago")
            else:
                factors.append("Audited (audit may be outdated)")

        months = data.get("production_months", 0)
        if months >= 24:
            factors.append(f"{months // 12}+ years in production")
        elif months >= 6:
            factors.append(f"{months} months in production")

        if data.get("has_insurance"):
            factors.append("Has slashing insurance or protocol backing")

        if data.get("validator_count", 0) >= 30:
            factors.append(f"Diversified across {data['validator_count']}+ validators")

        if staking_type == "native":
            factors.append("Native staking (no smart contract risk)")

        if data.get("reputation") == "excellent":
            factors.append("Industry-standard protocol with strong governance")

        return factors

    def _get_warnings(self, data: Dict, tvl: float) -> List[str]:
        """Get risk warnings."""
        warnings = []

        if not data.get("audited"):
            warnings.append("No audit found - smart contract risk")

        months = data.get("production_months", 0)
        if months < 6:
            warnings.append("New protocol - limited track record")

        if tvl < 10_000_000:
            warnings.append("Low TVL - potential liquidity issues")

        if data.get("slashing_incidents", 0) > 0:
            warnings.append(f"{data['slashing_incidents']} slashing incident(s) on record")

        if data.get("validator_count", 0) < 10:
            warnings.append("Low validator diversity - concentration risk")

        if data.get("reputation") in ["questionable", "unknown"]:
            warnings.append("Reputation unknown or questionable")

        return warnings

    def compare_risks(self, assessments: List[RiskAssessment]) -> Dict[str, Any]:
        """Compare risk across multiple assessments.

        Args:
            assessments: List of risk assessments

        Returns:
            Comparison summary
        """
        if not assessments:
            return {}

        scores = [a.overall_score for a in assessments]

        return {
            "safest_score": max(scores),
            "riskiest_score": min(scores),
            "average_score": round(sum(scores) / len(scores), 1),
            "low_risk_count": sum(1 for a in assessments if a.risk_level == "low"),
            "high_risk_count": sum(1 for a in assessments if a.risk_level in ["high", "very_high"]),
        }


def main():
    """CLI entry point for testing."""
    assessor = RiskAssessor(verbose=True)

    print("\n" + "=" * 60)
    print("Testing Risk Assessor")
    print("=" * 60)

    # Test protocols
    test_pools = [
        {"project": "lido", "tvlUsd": 15_000_000_000, "staking_type": "liquid"},
        {"project": "rocket-pool", "tvlUsd": 3_000_000_000, "staking_type": "liquid"},
        {"project": "frax-ether", "tvlUsd": 450_000_000, "staking_type": "liquid"},
        {"project": "unknown-protocol", "tvlUsd": 5_000_000, "staking_type": "liquid"},
    ]

    for pool in test_pools:
        assessment = assessor.assess_risk(pool)
        print(f"\n{pool['project'].title()}")
        print(f"  Overall Score: {assessment.overall_score}/10 ({assessment.risk_level.replace('_', ' ').title()})")
        print("  Breakdown:")
        print(f"    Audit: {assessment.audit_score}")
        print(f"    Production: {assessment.production_score}")
        print(f"    TVL: {assessment.tvl_score}")
        print(f"    Reputation: {assessment.reputation_score}")
        print(f"    Validators: {assessment.validator_score}")

        if assessment.warnings:
            print("  Warnings:")
            for w in assessment.warnings[:3]:
                print(f"    - {w}")


if __name__ == "__main__":
    main()
