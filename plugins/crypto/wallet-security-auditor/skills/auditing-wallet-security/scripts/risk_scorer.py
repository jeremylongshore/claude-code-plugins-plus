#!/usr/bin/env python3
"""
Wallet Risk Scorer

Calculate security risk score for wallets.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

from dataclasses import dataclass, field
from typing import List

from approval_scanner import ApprovalSummary


@dataclass
class RiskFactor:
    """Individual risk factor."""

    category: str
    severity: str  # critical, high, medium, low, info
    description: str
    affected_items: List[str] = field(default_factory=list)
    mitigation: str = ""
    score_impact: int = 0


@dataclass
class Recommendation:
    """Security recommendation."""

    priority: int  # 1 = highest
    action: str
    reason: str
    items: List[str] = field(default_factory=list)


@dataclass
class SecurityScore:
    """Overall security score."""

    total_score: int  # 0-100 (higher = safer)
    approval_score: int
    interaction_score: int
    pattern_score: int
    risk_level: str  # critical, high, medium, low, safe
    risk_factors: List[RiskFactor] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)


class RiskScorer:
    """Calculate wallet security risk score."""

    # Score weights by category
    WEIGHTS = {
        "approvals": 0.40,
        "interactions": 0.30,
        "patterns": 0.20,
        "age": 0.10,
    }

    # Risk factor impacts
    RISK_IMPACTS = {
        "unlimited_unknown": -30,  # Unlimited approval to unknown contract
        "approval_flagged": -25,  # Approval to flagged/scam contract
        "interaction_scam": -20,  # Interaction with known scam
        "many_unlimited": -15,  # >5 unlimited approvals
        "unlimited_known": -5,  # Unlimited approval to known contract (lower risk)
        "unknown_contract": -5,  # Interaction with unverified contract
        "high_value_approval": -10,  # Approval for high-value token
    }

    def __init__(self):
        """Initialize risk scorer."""
        pass

    def calculate_approval_risk(self, summary: ApprovalSummary) -> tuple[int, List[RiskFactor]]:
        """Calculate risk score based on approvals.

        Args:
            summary: ApprovalSummary from scanner

        Returns:
            Tuple of (score 0-100, list of risk factors)
        """
        score = 100  # Start with perfect score
        factors = []

        # Check unlimited approvals
        unlimited = [a for a in summary.approvals if a.is_unlimited]
        if len(unlimited) > 0:
            # Deduct for each unlimited approval
            for approval in unlimited:
                if not approval.spender_name:
                    # Unknown spender - critical risk
                    score += self.RISK_IMPACTS["unlimited_unknown"]
                    factors.append(
                        RiskFactor(
                            category="approvals",
                            severity="critical",
                            description="Unlimited approval to unknown contract",
                            affected_items=[f"{approval.token_symbol} → {approval.spender[:20]}..."],
                            mitigation="Revoke this approval if you don't recognize the spender",
                            score_impact=self.RISK_IMPACTS["unlimited_unknown"],
                        )
                    )
                else:
                    # Known spender - lower risk but unlimited approvals are still a concern
                    score += self.RISK_IMPACTS["unlimited_known"]

        # Check for many unlimited approvals
        if len(unlimited) > 5:
            score += self.RISK_IMPACTS["many_unlimited"]
            factors.append(
                RiskFactor(
                    category="approvals",
                    severity="medium",
                    description=f"Many unlimited approvals ({len(unlimited)})",
                    affected_items=[f"{a.token_symbol} → {a.spender_name or a.spender[:15]}..." for a in unlimited[:5]],
                    mitigation="Review and revoke unnecessary approvals",
                    score_impact=self.RISK_IMPACTS["many_unlimited"],
                )
            )

        # Check risky approvals
        risky = [a for a in summary.approvals if a.is_risky]
        for approval in risky:
            score += self.RISK_IMPACTS["approval_flagged"]
            factors.append(
                RiskFactor(
                    category="approvals",
                    severity="critical",
                    description=f"Approval to flagged contract: {approval.risk_reason or 'Unknown risk'}",
                    affected_items=[f"{approval.token_symbol} → {approval.spender[:20]}..."],
                    mitigation="IMMEDIATELY revoke this approval",
                    score_impact=self.RISK_IMPACTS["approval_flagged"],
                )
            )

        # Ensure score stays in bounds
        score = max(0, min(100, score))

        return score, factors

    def calculate_interaction_risk(self, interactions: List[dict] = None) -> tuple[int, List[RiskFactor]]:
        """Calculate risk based on contract interactions.

        Args:
            interactions: List of contract interactions

        Returns:
            Tuple of (score 0-100, list of risk factors)
        """
        score = 100
        factors = []

        # Placeholder - would analyze actual interactions
        # For now, return neutral score

        return score, factors

    def calculate_pattern_risk(self, patterns: dict = None) -> tuple[int, List[RiskFactor]]:
        """Calculate risk based on transaction patterns.

        Args:
            patterns: Pattern analysis data

        Returns:
            Tuple of (score 0-100, list of risk factors)
        """
        score = 100
        factors = []

        # Placeholder - would analyze actual patterns
        # For now, return neutral score

        return score, factors

    def get_total_score(
        self, approval_summary: ApprovalSummary, interactions: List[dict] = None, patterns: dict = None
    ) -> SecurityScore:
        """Calculate total security score.

        Args:
            approval_summary: Approval scan results
            interactions: Contract interaction data
            patterns: Transaction pattern data

        Returns:
            SecurityScore with all details
        """
        # Calculate component scores
        approval_score, approval_factors = self.calculate_approval_risk(approval_summary)
        interaction_score, interaction_factors = self.calculate_interaction_risk(interactions)
        pattern_score, pattern_factors = self.calculate_pattern_risk(patterns)

        # Weighted total
        total_score = int(
            approval_score * self.WEIGHTS["approvals"]
            + interaction_score * self.WEIGHTS["interactions"]
            + pattern_score * self.WEIGHTS["patterns"]
            + 100 * self.WEIGHTS["age"]  # Age score placeholder
        )

        # Combine factors
        all_factors = approval_factors + interaction_factors + pattern_factors

        # Determine risk level
        if total_score >= 90:
            risk_level = "safe"
        elif total_score >= 70:
            risk_level = "low"
        elif total_score >= 50:
            risk_level = "medium"
        elif total_score >= 30:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Generate recommendations
        recommendations = self._generate_recommendations(all_factors, approval_summary)

        return SecurityScore(
            total_score=total_score,
            approval_score=approval_score,
            interaction_score=interaction_score,
            pattern_score=pattern_score,
            risk_level=risk_level,
            risk_factors=sorted(
                all_factors,
                key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(x.severity, 5),
            ),
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, factors: List[RiskFactor], approval_summary: ApprovalSummary
    ) -> List[Recommendation]:
        """Generate actionable recommendations.

        Args:
            factors: List of risk factors
            approval_summary: Approval scan results

        Returns:
            List of recommendations sorted by priority
        """
        recommendations = []

        # Check for critical/high severity factors
        critical_factors = [f for f in factors if f.severity in ["critical", "high"]]
        if critical_factors:
            recommendations.append(
                Recommendation(
                    priority=1,
                    action="Revoke risky approvals immediately",
                    reason="Critical security risks detected in token approvals",
                    items=[f.affected_items[0] if f.affected_items else f.description for f in critical_factors[:3]],
                )
            )

        # Check for many unlimited approvals
        unlimited = [a for a in approval_summary.approvals if a.is_unlimited]
        if len(unlimited) > 3:
            recommendations.append(
                Recommendation(
                    priority=2,
                    action="Review and revoke unnecessary unlimited approvals",
                    reason=f"You have {len(unlimited)} unlimited approvals which increase your risk",
                    items=[f"{a.token_symbol} → {a.spender_name or a.spender[:15]}..." for a in unlimited[:5]],
                )
            )

        # Check for old approvals (would need block timestamp data)
        if approval_summary.total_approvals > 10:
            recommendations.append(
                Recommendation(
                    priority=3,
                    action="Audit all approvals periodically",
                    reason=f"You have {approval_summary.total_approvals} active approvals",
                    items=["Use revoke.cash or similar tool to review"],
                )
            )

        # General best practices
        if not recommendations:
            recommendations.append(
                Recommendation(
                    priority=4,
                    action="Continue good security practices",
                    reason="No critical issues found, but stay vigilant",
                    items=[
                        "Regularly review approvals",
                        "Use hardware wallet for high-value assets",
                        "Be cautious with new dApps",
                    ],
                )
            )

        return sorted(recommendations, key=lambda x: x.priority)

    def get_risk_level_description(self, level: str) -> str:
        """Get human-readable risk level description."""
        descriptions = {
            "critical": "CRITICAL - Immediate action required",
            "high": "HIGH - Significant risks detected",
            "medium": "MEDIUM - Some concerns to address",
            "low": "LOW - Minor improvements possible",
            "safe": "SAFE - Good security posture",
        }
        return descriptions.get(level, "UNKNOWN")


def main():
    """CLI entry point for testing."""
    from approval_scanner import ApprovalScanner

    print("=== Risk Scorer Test ===")

    # Create mock data
    scanner = ApprovalScanner(chain="ethereum", verbose=True)
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    print(f"Scanning {test_address[:20]}...")
    summary = scanner.get_all_approvals(test_address)

    scorer = RiskScorer()
    score = scorer.get_total_score(summary)

    print(f"\nSecurity Score: {score.total_score}/100")
    print(f"Risk Level: {scorer.get_risk_level_description(score.risk_level)}")
    print("\nComponent Scores:")
    print(f"  Approvals: {score.approval_score}/100")
    print(f"  Interactions: {score.interaction_score}/100")
    print(f"  Patterns: {score.pattern_score}/100")

    if score.risk_factors:
        print("\nRisk Factors:")
        for factor in score.risk_factors[:5]:
            print(f"  [{factor.severity.upper()}] {factor.description}")

    if score.recommendations:
        print("\nRecommendations:")
        for rec in score.recommendations[:3]:
            print(f"  {rec.priority}. {rec.action}")


if __name__ == "__main__":
    main()
