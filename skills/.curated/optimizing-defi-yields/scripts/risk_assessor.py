#!/usr/bin/env python3
"""
Risk Assessor

Assesses and scores protocol and pool risks.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class RiskAssessor:
    """Assesses risk for DeFi protocols and pools."""

    # Known audited protocols with audit information
    AUDITED_PROTOCOLS = {
        "aave-v2": {"auditors": ["OpenZeppelin", "Trail of Bits"], "year": 2020},
        "aave-v3": {"auditors": ["Certora", "SigmaPrime", "ABDK"], "year": 2022},
        "compound-v2": {"auditors": ["OpenZeppelin", "Trail of Bits"], "year": 2019},
        "compound-v3": {"auditors": ["OpenZeppelin", "ChainSecurity"], "year": 2022},
        "curve-dex": {"auditors": ["Trail of Bits", "Quantstamp"], "year": 2020},
        "convex-finance": {"auditors": ["MixBytes", "OpenZeppelin"], "year": 2021},
        "yearn-finance": {"auditors": ["Trail of Bits", "MixBytes"], "year": 2021},
        "lido": {"auditors": ["Sigma Prime", "Quantstamp"], "year": 2021},
        "rocket-pool": {"auditors": ["Sigma Prime", "Consensys"], "year": 2021},
        "balancer-v2": {"auditors": ["Trail of Bits", "OpenZeppelin"], "year": 2021},
        "uniswap-v3": {"auditors": ["ABDK", "samczsun"], "year": 2021},
        "maker": {"auditors": ["Trail of Bits", "Runtime Verification"], "year": 2019},
        "spark": {"auditors": ["ChainSecurity", "Cantina"], "year": 2023},
        "morpho": {"auditors": ["Spearbit", "Trail of Bits"], "year": 2023},
        "frax-ether": {"auditors": ["Trail of Bits"], "year": 2022},
        "beefy": {"auditors": ["Certik", "SlowMist"], "year": 2021},
        "radiant-v2": {"auditors": ["PeckShield", "Zokyo"], "year": 2023},
    }

    # Protocol launch dates (approximate)
    PROTOCOL_AGES = {
        "aave-v2": "2020-12",
        "aave-v3": "2022-03",
        "compound-v2": "2019-05",
        "compound-v3": "2022-08",
        "curve-dex": "2020-01",
        "convex-finance": "2021-05",
        "yearn-finance": "2020-07",
        "lido": "2020-12",
        "rocket-pool": "2021-11",
        "balancer-v2": "2021-05",
        "uniswap-v3": "2021-05",
        "maker": "2017-12",
        "spark": "2023-05",
        "morpho": "2022-07",
        "frax-ether": "2022-10",
        "beefy": "2020-10",
        "radiant-v2": "2023-03",
    }

    # Risk factor weights
    WEIGHTS = {
        "audit_status": 0.30,
        "tvl": 0.20,
        "protocol_age": 0.20,
        "tvl_trend": 0.15,
        "concentration": 0.15,
    }

    def __init__(self, verbose: bool = False):
        """Initialize assessor.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def assess(self, pool: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for a pool.

        Args:
            pool: Pool data dictionary

        Returns:
            Pool with risk assessment fields added
        """
        project = pool.get("project", "").lower()

        # Individual risk scores (0-10 scale)
        scores = {
            "audit_score": self._score_audit(project),
            "tvl_score": self._score_tvl(pool.get("tvlUsd", 0)),
            "age_score": self._score_age(project),
            "trend_score": self._score_trend(pool),
            "concentration_score": self._score_concentration(pool),
        }

        # Calculate weighted total
        total_score = (
            scores["audit_score"] * self.WEIGHTS["audit_status"]
            + scores["tvl_score"] * self.WEIGHTS["tvl"]
            + scores["age_score"] * self.WEIGHTS["protocol_age"]
            + scores["trend_score"] * self.WEIGHTS["tvl_trend"]
            + scores["concentration_score"] * self.WEIGHTS["concentration"]
        )

        # Store scores
        pool["risk_scores"] = scores
        pool["risk_score"] = round(total_score, 2)
        pool["risk_level"] = self._score_to_level(total_score)

        # Add audit info
        audit_info = self.AUDITED_PROTOCOLS.get(project)
        if audit_info:
            pool["audited"] = True
            pool["auditors"] = audit_info["auditors"]
            pool["audit_year"] = audit_info["year"]
        else:
            pool["audited"] = False
            pool["auditors"] = []
            pool["audit_year"] = None

        # Add risk factors (human-readable warnings)
        pool["risk_factors"] = self._identify_risk_factors(pool, scores)

        if self.verbose:
            print(f"  Risk assessed for {project}: {pool['risk_score']}/10 ({pool['risk_level']})")

        return pool

    def _score_audit(self, project: str) -> float:
        """Score based on audit status.

        Returns:
            Score 0-10
        """
        if project in self.AUDITED_PROTOCOLS:
            audit = self.AUDITED_PROTOCOLS[project]
            num_auditors = len(audit.get("auditors", []))

            if num_auditors >= 3:
                return 10.0
            elif num_auditors == 2:
                return 9.0
            else:
                return 8.0
        else:
            # Unknown audit status - assume partial
            return 4.0

    def _score_tvl(self, tvl_usd: float) -> float:
        """Score based on TVL.

        Returns:
            Score 0-10
        """
        if tvl_usd >= 1_000_000_000:  # $1B+
            return 10.0
        elif tvl_usd >= 500_000_000:  # $500M+
            return 9.0
        elif tvl_usd >= 100_000_000:  # $100M+
            return 8.0
        elif tvl_usd >= 50_000_000:  # $50M+
            return 7.0
        elif tvl_usd >= 10_000_000:  # $10M+
            return 6.0
        elif tvl_usd >= 1_000_000:  # $1M+
            return 4.0
        elif tvl_usd >= 100_000:  # $100K+
            return 2.0
        else:
            return 1.0

    def _score_age(self, project: str) -> float:
        """Score based on protocol age.

        Returns:
            Score 0-10
        """
        launch_date = self.PROTOCOL_AGES.get(project)
        if not launch_date:
            return 5.0  # Unknown - assume medium

        try:
            launch = datetime.strptime(launch_date, "%Y-%m")
            months_old = (datetime.now() - launch).days / 30

            if months_old >= 36:  # 3+ years
                return 10.0
            elif months_old >= 24:  # 2+ years
                return 9.0
            elif months_old >= 18:  # 1.5+ years
                return 8.0
            elif months_old >= 12:  # 1+ year
                return 7.0
            elif months_old >= 6:  # 6+ months
                return 5.0
            elif months_old >= 3:  # 3+ months
                return 3.0
            else:
                return 1.0
        except ValueError:
            return 5.0

    def _score_trend(self, pool: Dict[str, Any]) -> float:
        """Score based on TVL trend.

        Note: Real implementation would fetch historical data.

        Returns:
            Score 0-10
        """
        # If we have trend data from API
        tvl_change_7d = pool.get("tvlChange7d", 0)

        if tvl_change_7d > 10:
            return 10.0  # Growing rapidly
        elif tvl_change_7d > 0:
            return 8.0  # Growing
        elif tvl_change_7d > -5:
            return 7.0  # Stable
        elif tvl_change_7d > -20:
            return 5.0  # Declining
        else:
            return 3.0  # Declining rapidly

    def _score_concentration(self, pool: Dict[str, Any]) -> float:
        """Score based on token concentration.

        Note: Real implementation would analyze holder distribution.

        Returns:
            Score 0-10
        """
        # Blue-chip protocols typically have better distribution
        project = pool.get("project", "").lower()

        distributed_protocols = ["aave", "compound", "curve", "uniswap", "balancer", "maker", "lido", "rocket-pool"]

        if any(p in project for p in distributed_protocols):
            return 9.0  # Well-distributed
        else:
            return 6.0  # Unknown - assume moderate

    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to risk level.

        Args:
            score: Risk score 0-10

        Returns:
            Risk level string
        """
        if score >= 8:
            return "Low"
        elif score >= 5:
            return "Medium"
        elif score >= 3:
            return "High"
        else:
            return "Very High"

    def _identify_risk_factors(self, pool: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Identify specific risk factors for a pool.

        Returns:
            List of human-readable risk factors
        """
        factors = []

        # Audit concerns
        if scores["audit_score"] < 6:
            if not pool.get("audited"):
                factors.append("Protocol not audited or audit status unknown")
            else:
                factors.append("Limited audit coverage")

        # TVL concerns
        if scores["tvl_score"] < 5:
            tvl = pool.get("tvlUsd", 0)
            factors.append(f"Low TVL (${tvl / 1e6:.1f}M) - liquidity risk")

        # Age concerns
        if scores["age_score"] < 5:
            factors.append("Relatively new protocol - less battle-tested")

        # Trend concerns
        if scores["trend_score"] < 5:
            factors.append("Declining TVL trend - potential capital flight")

        # IL concerns
        il_risk = pool.get("il_risk", "medium")
        if il_risk == "high":
            factors.append("High impermanent loss risk (volatile pair)")

        # High APY warning
        apy = pool.get("apy", 0) or pool.get("total_apy", 0)
        if apy > 50:
            factors.append(f"Very high APY ({apy:.1f}%) - verify sustainability")
        elif apy > 20:
            factors.append(f"High APY ({apy:.1f}%) - may include volatile rewards")

        # Reward token dependency
        reward_tokens = pool.get("rewardTokens") or []
        # Filter out None values
        valid_tokens = [t for t in reward_tokens[:3] if t]
        if valid_tokens:
            factors.append(f"Yield includes reward tokens: {', '.join(valid_tokens)}")

        return factors

    def get_audit_info(self, project: str) -> Optional[Dict[str, Any]]:
        """Get detailed audit information for a protocol.

        Args:
            project: Protocol name/slug

        Returns:
            Audit info dictionary or None
        """
        return self.AUDITED_PROTOCOLS.get(project.lower())

    def filter_by_risk(self, pools: List[Dict[str, Any]], max_risk_level: str = "Medium") -> List[Dict[str, Any]]:
        """Filter pools by maximum risk level.

        Args:
            pools: List of pools with risk assessments
            max_risk_level: Maximum acceptable risk level

        Returns:
            Filtered list of pools
        """
        risk_order = ["Low", "Medium", "High", "Very High"]
        max_index = risk_order.index(max_risk_level)

        return [p for p in pools if risk_order.index(p.get("risk_level", "Very High")) <= max_index]


def main():
    """CLI entry point for testing."""
    assessor = RiskAssessor(verbose=True)

    # Test with mock pools
    pools = [
        {
            "project": "aave-v3",
            "symbol": "USDC",
            "tvlUsd": 2100000000,
            "apy": 4.2,
        },
        {
            "project": "new-protocol",
            "symbol": "ETH-SHIB",
            "tvlUsd": 500000,
            "apy": 150,
        },
    ]

    print("Risk Assessment Results:\n")
    for pool in pools:
        assessor.assess(pool)
        print(f"\n{pool['project']} - {pool['symbol']}")
        print(f"  Risk Score: {pool['risk_score']}/10 ({pool['risk_level']})")
        print(f"  Audited: {pool['audited']}")
        if pool["auditors"]:
            print(f"  Auditors: {', '.join(pool['auditors'])}")
        print("  Risk Factors:")
        for factor in pool.get("risk_factors", []):
            print(f"    • {factor}")


if __name__ == "__main__":
    main()
