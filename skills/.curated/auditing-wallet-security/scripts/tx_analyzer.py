#!/usr/bin/env python3
"""
Transaction Analyzer

Analyze wallet transaction patterns for security assessment.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

try:
    import requests
except ImportError:
    requests = None


# Chain configurations
CHAIN_CONFIGS = {
    "ethereum": {
        "chain_id": 1,
        "rpc_url": "https://eth.llamarpc.com",
        "explorer_api": "https://api.etherscan.io/api",
    },
    "bsc": {
        "chain_id": 56,
        "rpc_url": "https://bsc-dataseed1.binance.org",
        "explorer_api": "https://api.bscscan.com/api",
    },
    "polygon": {
        "chain_id": 137,
        "rpc_url": "https://polygon-rpc.com",
        "explorer_api": "https://api.polygonscan.com/api",
    },
    "arbitrum": {
        "chain_id": 42161,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "explorer_api": "https://api.arbiscan.io/api",
    },
    "optimism": {
        "chain_id": 10,
        "rpc_url": "https://mainnet.optimism.io",
        "explorer_api": "https://api-optimistic.etherscan.io/api",
    },
    "base": {
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "explorer_api": "https://api.basescan.org/api",
    },
}


@dataclass
class Transaction:
    """Transaction data."""

    tx_hash: str
    block_number: int
    timestamp: int
    from_address: str
    to_address: str
    value: Decimal
    gas_used: int
    gas_price: Decimal
    is_error: bool
    method_id: str
    method_name: Optional[str] = None


@dataclass
class ContractInteraction:
    """Contract interaction data."""

    contract_address: str
    contract_name: Optional[str]
    interaction_count: int
    first_interaction: int  # timestamp
    last_interaction: int  # timestamp
    total_value: Decimal
    is_verified: bool
    is_flagged: bool = False
    flag_reason: Optional[str] = None


@dataclass
class SuspiciousActivity:
    """Suspicious activity detection."""

    activity_type: str
    severity: str  # critical, high, medium, low
    description: str
    related_tx: List[str] = field(default_factory=list)
    timestamp: int = 0


@dataclass
class InteractionReport:
    """Contract interaction analysis report."""

    total_transactions: int
    unique_contracts: int
    verified_contracts: int
    unverified_contracts: int
    flagged_contracts: int
    total_value_sent: Decimal
    total_gas_spent: Decimal
    interactions: List[ContractInteraction] = field(default_factory=list)
    suspicious_activities: List[SuspiciousActivity] = field(default_factory=list)


class TxAnalyzer:
    """Analyze wallet transaction patterns."""

    # Known suspicious patterns
    SUSPICIOUS_PATTERNS = {
        "rapid_approvals": {
            "threshold": 5,  # More than 5 approvals in 1 hour
            "window_seconds": 3600,
            "severity": "high",
        },
        "drain_pattern": {
            "threshold": 0.9,  # >90% of balance moved
            "severity": "critical",
        },
        "dust_attack": {
            "threshold": 0.001,  # Very small incoming value
            "severity": "low",
        },
        "interaction_burst": {
            "threshold": 20,  # >20 unique contracts in 24h
            "window_seconds": 86400,
            "severity": "medium",
        },
    }

    def __init__(self, chain: str = "ethereum", explorer_api_key: str = None, verbose: bool = False):
        """Initialize transaction analyzer.

        Args:
            chain: Chain to analyze
            explorer_api_key: Block explorer API key
            verbose: Enable verbose output
        """
        if not requests:
            raise ImportError("requests library required: pip install requests")

        self.chain = chain.lower()
        if self.chain not in CHAIN_CONFIGS:
            raise ValueError(f"Unsupported chain: {chain}")

        self.config = CHAIN_CONFIGS[self.chain]
        self.explorer_api_key = explorer_api_key or os.environ.get("ETHERSCAN_API_KEY", "")
        self.verbose = verbose
        self._contract_cache: Dict[str, Dict] = {}

    def _api_call(self, params: Dict) -> Optional[Dict]:
        """Make explorer API call."""
        if self.explorer_api_key:
            params["apikey"] = self.explorer_api_key

        try:
            response = requests.get(
                self.config["explorer_api"],
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "1":
                return data.get("result")
            return None

        except Exception as e:
            if self.verbose:
                print(f"API error: {e}")
            return None

    def get_recent_transactions(self, address: str, days: int = 30, limit: int = 1000) -> List[Transaction]:
        """Get recent transactions for an address.

        Args:
            address: Wallet address
            days: Number of days to look back
            limit: Maximum transactions to fetch

        Returns:
            List of Transaction objects
        """
        address = address.lower()

        # Fetch normal transactions
        result = self._api_call(
            {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": limit,
                "sort": "desc",
            }
        )

        if not result:
            return []

        transactions = []
        cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp())

        for tx in result:
            try:
                timestamp = int(tx.get("timeStamp", 0))

                # Filter by date
                if timestamp < cutoff_time:
                    continue

                transactions.append(
                    Transaction(
                        tx_hash=tx.get("hash", ""),
                        block_number=int(tx.get("blockNumber", 0)),
                        timestamp=timestamp,
                        from_address=tx.get("from", "").lower(),
                        to_address=tx.get("to", "").lower(),
                        value=Decimal(tx.get("value", 0)) / Decimal(10**18),
                        gas_used=int(tx.get("gasUsed", 0)),
                        gas_price=Decimal(tx.get("gasPrice", 0)) / Decimal(10**9),
                        is_error=tx.get("isError", "0") == "1",
                        method_id=tx.get("methodId", ""),
                        method_name=tx.get("functionName", "").split("(")[0] if tx.get("functionName") else None,
                    )
                )

            except Exception as e:
                if self.verbose:
                    print(f"Error parsing tx: {e}")

        return transactions

    def _get_contract_info(self, address: str) -> Dict:
        """Get contract information."""
        if address in self._contract_cache:
            return self._contract_cache[address]

        info = {
            "name": None,
            "is_verified": False,
            "is_contract": False,
        }

        # Check if it's a contract
        result = self._api_call(
            {
                "module": "contract",
                "action": "getabi",
                "address": address,
            }
        )

        if result and result != "Contract source code not verified":
            info["is_contract"] = True
            info["is_verified"] = True

            # Try to get contract name
            source_result = self._api_call(
                {
                    "module": "contract",
                    "action": "getsourcecode",
                    "address": address,
                }
            )

            if source_result and isinstance(source_result, list) and len(source_result) > 0:
                info["name"] = source_result[0].get("ContractName", "")

        self._contract_cache[address] = info
        return info

    def analyze_interaction_patterns(self, address: str, transactions: List[Transaction] = None) -> InteractionReport:
        """Analyze contract interaction patterns.

        Args:
            address: Wallet address
            transactions: Pre-fetched transactions (optional)

        Returns:
            InteractionReport with analysis
        """
        address = address.lower()

        if transactions is None:
            transactions = self.get_recent_transactions(address)

        if not transactions:
            return InteractionReport(
                total_transactions=0,
                unique_contracts=0,
                verified_contracts=0,
                unverified_contracts=0,
                flagged_contracts=0,
                total_value_sent=Decimal(0),
                total_gas_spent=Decimal(0),
            )

        # Analyze interactions by contract
        contract_stats: Dict[str, Dict] = {}
        total_value_sent = Decimal(0)
        total_gas_spent = Decimal(0)

        for tx in transactions:
            # Track outgoing value
            if tx.from_address == address:
                total_value_sent += tx.value
                total_gas_spent += tx.gas_price * tx.gas_used / Decimal(10**9)

                # Track contract interaction
                if tx.to_address and tx.to_address != address:
                    if tx.to_address not in contract_stats:
                        contract_stats[tx.to_address] = {
                            "count": 0,
                            "first": tx.timestamp,
                            "last": tx.timestamp,
                            "value": Decimal(0),
                        }

                    stats = contract_stats[tx.to_address]
                    stats["count"] += 1
                    stats["first"] = min(stats["first"], tx.timestamp)
                    stats["last"] = max(stats["last"], tx.timestamp)
                    stats["value"] += tx.value

        # Build interaction list
        interactions = []
        verified_count = 0
        unverified_count = 0
        flagged_count = 0

        for contract_addr, stats in contract_stats.items():
            contract_info = self._get_contract_info(contract_addr)

            is_flagged = False
            flag_reason = None

            # Flag unverified contracts with high interaction
            if not contract_info["is_verified"] and stats["count"] > 5:
                is_flagged = True
                flag_reason = "Frequent interaction with unverified contract"
                flagged_count += 1

            interaction = ContractInteraction(
                contract_address=contract_addr,
                contract_name=contract_info.get("name"),
                interaction_count=stats["count"],
                first_interaction=stats["first"],
                last_interaction=stats["last"],
                total_value=stats["value"],
                is_verified=contract_info["is_verified"],
                is_flagged=is_flagged,
                flag_reason=flag_reason,
            )
            interactions.append(interaction)

            if contract_info["is_verified"]:
                verified_count += 1
            else:
                unverified_count += 1

        # Sort by interaction count
        interactions.sort(key=lambda x: x.interaction_count, reverse=True)

        # Detect suspicious activities
        suspicious = self._detect_suspicious_activities(address, transactions)

        return InteractionReport(
            total_transactions=len(transactions),
            unique_contracts=len(contract_stats),
            verified_contracts=verified_count,
            unverified_contracts=unverified_count,
            flagged_contracts=flagged_count,
            total_value_sent=total_value_sent,
            total_gas_spent=total_gas_spent,
            interactions=interactions,
            suspicious_activities=suspicious,
        )

    def _detect_suspicious_activities(self, address: str, transactions: List[Transaction]) -> List[SuspiciousActivity]:
        """Detect suspicious transaction patterns.

        Args:
            address: Wallet address
            transactions: List of transactions

        Returns:
            List of suspicious activities
        """
        suspicious = []
        address = address.lower()

        # Check for rapid approvals (approve method = 0x095ea7b3)
        approval_txs = [tx for tx in transactions if tx.method_id == "0x095ea7b3" and tx.from_address == address]

        if approval_txs:
            # Group by hour
            approval_times = [tx.timestamp for tx in approval_txs]
            approval_times.sort()

            # Use configured threshold (default 5)
            threshold = self.SUSPICIOUS_PATTERNS["rapid_approvals"]["threshold"]
            window_seconds = self.SUSPICIOUS_PATTERNS["rapid_approvals"]["window_seconds"]

            for i in range(len(approval_times) - (threshold - 1)):
                window = approval_times[i + threshold - 1] - approval_times[i]
                if window <= window_seconds:  # threshold+ approvals in window
                    suspicious.append(
                        SuspiciousActivity(
                            activity_type="rapid_approvals",
                            severity="high",
                            description=f"Multiple approvals ({len(approval_txs)}) in short time window",
                            related_tx=[tx.tx_hash for tx in approval_txs[:5]],
                            timestamp=approval_times[i],
                        )
                    )
                    break

        # Check for interaction burst
        unique_contracts_24h = set()
        recent_time = int(datetime.now().timestamp()) - 86400

        for tx in transactions:
            if tx.timestamp >= recent_time and tx.from_address == address:
                if tx.to_address:
                    unique_contracts_24h.add(tx.to_address)

        if len(unique_contracts_24h) > 20:
            suspicious.append(
                SuspiciousActivity(
                    activity_type="interaction_burst",
                    severity="medium",
                    description=f"High number of unique contracts ({len(unique_contracts_24h)}) in 24h",
                    timestamp=recent_time,
                )
            )

        # Check for failed transactions
        failed_txs = [tx for tx in transactions if tx.is_error and tx.from_address == address]
        if len(failed_txs) > 10:
            suspicious.append(
                SuspiciousActivity(
                    activity_type="high_failure_rate",
                    severity="low",
                    description=f"Many failed transactions ({len(failed_txs)})",
                    related_tx=[tx.tx_hash for tx in failed_txs[:5]],
                )
            )

        # Check for dust attacks (many tiny incoming values)
        dust_txs = [tx for tx in transactions if tx.to_address == address and Decimal(0) < tx.value < Decimal("0.001")]

        if len(dust_txs) > 5:
            suspicious.append(
                SuspiciousActivity(
                    activity_type="dust_attack",
                    severity="low",
                    description=f"Multiple tiny incoming transactions ({len(dust_txs)}) - possible dust attack",
                    related_tx=[tx.tx_hash for tx in dust_txs[:5]],
                )
            )

        return sorted(suspicious, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.severity, 4))

    def get_contract_interactions(
        self, address: str, transactions: List[Transaction] = None
    ) -> List[ContractInteraction]:
        """Get list of contract interactions.

        Args:
            address: Wallet address
            transactions: Pre-fetched transactions (optional)

        Returns:
            List of ContractInteraction objects
        """
        report = self.analyze_interaction_patterns(address, transactions)
        return report.interactions

    def detect_suspicious_activity(
        self, address: str, transactions: List[Transaction] = None
    ) -> List[SuspiciousActivity]:
        """Detect suspicious transaction patterns.

        Args:
            address: Wallet address
            transactions: Pre-fetched transactions (optional)

        Returns:
            List of SuspiciousActivity objects
        """
        if transactions is None:
            transactions = self.get_recent_transactions(address)

        return self._detect_suspicious_activities(address, transactions)


def main():
    """CLI entry point for testing."""
    analyzer = TxAnalyzer(chain="ethereum", verbose=True)

    # Test with a sample address
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    print("=== Transaction Analyzer Test ===")
    print(f"Analyzing: {test_address[:20]}...")

    # Get recent transactions
    print("\nFetching transactions...")
    txs = analyzer.get_recent_transactions(test_address, days=30)
    print(f"Found {len(txs)} transactions")

    # Analyze patterns
    print("\nAnalyzing interaction patterns...")
    report = analyzer.analyze_interaction_patterns(test_address, txs)

    print("\nResults:")
    print(f"  Total transactions: {report.total_transactions}")
    print(f"  Unique contracts: {report.unique_contracts}")
    print(f"  Verified: {report.verified_contracts}")
    print(f"  Unverified: {report.unverified_contracts}")
    print(f"  Flagged: {report.flagged_contracts}")
    print(f"  Total value sent: {report.total_value_sent:.4f} ETH")
    print(f"  Total gas spent: {report.total_gas_spent:.4f} Gwei")

    if report.suspicious_activities:
        print("\nSuspicious Activities:")
        for activity in report.suspicious_activities:
            print(f"  [{activity.severity.upper()}] {activity.description}")


if __name__ == "__main__":
    main()
