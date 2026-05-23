#!/usr/bin/env python3
"""
Flash loan strategy simulation engine.

Implements various flash loan strategies:
- Simple arbitrage (2 DEX)
- Triangular arbitrage (3+ DEX)
- Liquidation
- Collateral swap
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any

from protocol_adapters import ProviderManager, FlashLoanProvider


class StrategyType(Enum):
    """Types of flash loan strategies."""

    SIMPLE_ARBITRAGE = "arbitrage"
    TRIANGULAR_ARBITRAGE = "triangular"
    LIQUIDATION = "liquidation"
    COLLATERAL_SWAP = "collateral_swap"
    SELF_LIQUIDATION = "self_liquidation"
    DEBT_REFINANCING = "refinancing"


@dataclass
class DEXPrice:
    """Price quote from a DEX."""

    dex_name: str
    input_token: str
    output_token: str
    input_amount: Decimal
    output_amount: Decimal
    price: Decimal  # output per input
    price_impact: float  # percentage
    liquidity: Decimal  # available liquidity


@dataclass
class TransactionStep:
    """Single step in a flash loan transaction."""

    step_number: int
    action: str  # "borrow", "swap", "repay", etc.
    protocol: str
    input_token: str
    input_amount: Decimal
    output_token: str
    output_amount: Decimal
    fee: Decimal
    gas_estimate: int
    description: str


@dataclass
class StrategyResult:
    """Result of a strategy simulation."""

    strategy_type: StrategyType
    success: bool
    steps: List[TransactionStep]
    loan_amount: Decimal
    loan_asset: str
    loan_provider: str
    loan_fee: Decimal
    gross_profit: Decimal
    total_fees: Decimal
    gas_cost_eth: Decimal
    gas_cost_usd: Decimal
    net_profit: Decimal
    net_profit_usd: Decimal
    roi_percent: float
    execution_path: str
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArbitrageParams:
    """Parameters for arbitrage simulation."""

    input_token: str
    output_token: str
    amount: Decimal
    dex_buy: str  # DEX with lower price (buy here)
    dex_sell: str  # DEX with higher price (sell here)
    provider: str = "aave"
    chain: str = "ethereum"
    slippage: float = 0.5  # percentage


@dataclass
class LiquidationParams:
    """Parameters for liquidation simulation."""

    protocol: str  # "aave", "compound"
    borrower: Optional[str] = None
    health_factor_threshold: float = 1.0
    debt_asset: str = "USDC"
    collateral_asset: str = "ETH"
    provider: str = "aave"
    chain: str = "ethereum"


class FlashLoanStrategy(ABC):
    """Abstract base class for flash loan strategies."""

    def __init__(self, provider_manager: ProviderManager):
        """Initialize with provider manager."""
        self.provider_manager = provider_manager

    @property
    @abstractmethod
    def strategy_type(self) -> StrategyType:
        """Get strategy type."""
        pass

    @abstractmethod
    def simulate(self, params: Any) -> StrategyResult:
        """Run strategy simulation."""
        pass

    def get_provider(self, name: str) -> Optional[FlashLoanProvider]:
        """Get flash loan provider by name."""
        return self.provider_manager.get_provider(name)


class SimpleArbitrageStrategy(FlashLoanStrategy):
    """
    Simple two-DEX arbitrage strategy.

    1. Flash borrow asset A
    2. Sell A for B on DEX with high A price
    3. Buy A with B on DEX with low A price
    4. Repay flash loan + fee
    5. Keep profit
    """

    # Mock DEX prices for simulation
    # In production, these would be fetched from actual DEXs
    MOCK_PRICES = {
        "uniswap": {
            ("ETH", "USDC"): Decimal("2543.22"),
            ("USDC", "ETH"): Decimal("1") / Decimal("2543.22"),
            ("WBTC", "ETH"): Decimal("15.5"),
            ("ETH", "WBTC"): Decimal("1") / Decimal("15.5"),
        },
        "sushiswap": {
            ("ETH", "USDC"): Decimal("2538.50"),
            ("USDC", "ETH"): Decimal("1") / Decimal("2538.50"),
            ("WBTC", "ETH"): Decimal("15.48"),
            ("ETH", "WBTC"): Decimal("1") / Decimal("15.48"),
        },
        "curve": {
            ("ETH", "USDC"): Decimal("2540.00"),
            ("USDC", "ETH"): Decimal("1") / Decimal("2540.00"),
        },
    }

    # Gas costs per DEX
    DEX_GAS = {
        "uniswap": 150000,
        "sushiswap": 140000,
        "curve": 200000,
        "balancer": 180000,
    }

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.SIMPLE_ARBITRAGE

    def get_dex_price(self, dex: str, from_token: str, to_token: str) -> Optional[Decimal]:
        """Get price from DEX (mock data)."""
        dex_prices = self.MOCK_PRICES.get(dex.lower(), {})
        return dex_prices.get((from_token.upper(), to_token.upper()))

    def simulate(self, params: ArbitrageParams) -> StrategyResult:
        """
        Simulate simple arbitrage.

        Flow:
        1. Borrow {amount} {input_token} from flash loan
        2. Sell on {dex_sell} → get {output_token}
        3. Buy on {dex_buy} → get back {input_token}
        4. Repay loan + fee
        """
        steps = []
        warnings = []

        # Get provider
        provider = self.get_provider(params.provider)
        if not provider:
            return self._error_result(f"Unknown provider: {params.provider}")

        # Step 1: Flash borrow
        loan_fee = provider.get_fee(params.input_token, params.amount)
        steps.append(
            TransactionStep(
                step_number=1,
                action="flash_borrow",
                protocol=provider.name,
                input_token=params.input_token,
                input_amount=Decimal("0"),
                output_token=params.input_token,
                output_amount=params.amount,
                fee=loan_fee,
                gas_estimate=provider.get_gas_overhead(),
                description=f"Flash borrow {params.amount} {params.input_token} from {provider.name}",
            )
        )

        # Step 2: Sell on high-price DEX
        sell_price = self.get_dex_price(params.dex_sell, params.input_token, params.output_token)
        if not sell_price:
            warnings.append(f"No price data for {params.dex_sell}")
            sell_price = Decimal("2540")  # Fallback

        sell_output = params.amount * sell_price
        sell_gas = self.DEX_GAS.get(params.dex_sell.lower(), 150000)

        steps.append(
            TransactionStep(
                step_number=2,
                action="swap",
                protocol=params.dex_sell,
                input_token=params.input_token,
                input_amount=params.amount,
                output_token=params.output_token,
                output_amount=sell_output,
                fee=Decimal("0"),  # DEX fee included in price
                gas_estimate=sell_gas,
                description=f"Sell {params.amount} {params.input_token} on {params.dex_sell}",
            )
        )

        # Step 3: Buy on low-price DEX
        buy_price = self.get_dex_price(params.dex_buy, params.output_token, params.input_token)
        if not buy_price:
            warnings.append(f"No price data for {params.dex_buy}")
            buy_price = Decimal("1") / Decimal("2538")  # Fallback

        buy_output = sell_output * buy_price
        buy_gas = self.DEX_GAS.get(params.dex_buy.lower(), 150000)

        steps.append(
            TransactionStep(
                step_number=3,
                action="swap",
                protocol=params.dex_buy,
                input_token=params.output_token,
                input_amount=sell_output,
                output_token=params.input_token,
                output_amount=buy_output,
                fee=Decimal("0"),
                gas_estimate=buy_gas,
                description=f"Buy {params.input_token} on {params.dex_buy}",
            )
        )

        # Step 4: Repay flash loan
        repay_amount = params.amount + loan_fee
        steps.append(
            TransactionStep(
                step_number=4,
                action="flash_repay",
                protocol=provider.name,
                input_token=params.input_token,
                input_amount=repay_amount,
                output_token=params.input_token,
                output_amount=Decimal("0"),
                fee=Decimal("0"),
                gas_estimate=50000,
                description=f"Repay {repay_amount} {params.input_token} to {provider.name}",
            )
        )

        # Calculate profit
        gross_profit = buy_output - params.amount
        total_gas = sum(s.gas_estimate for s in steps)

        # Assume 30 gwei gas price and $2500 ETH
        gas_price_gwei = 30
        eth_price = Decimal("2500")
        gas_cost_eth = Decimal(total_gas * gas_price_gwei) / Decimal("1e9")
        gas_cost_usd = gas_cost_eth * eth_price

        net_profit = gross_profit - loan_fee - gas_cost_eth
        net_profit_usd = net_profit * eth_price

        # Check profitability
        if net_profit < 0:
            warnings.append("Strategy is NOT profitable after costs")

        roi = float(net_profit / params.amount * 100) if params.amount > 0 else 0

        return StrategyResult(
            strategy_type=self.strategy_type,
            success=net_profit > 0,
            steps=steps,
            loan_amount=params.amount,
            loan_asset=params.input_token,
            loan_provider=provider.name,
            loan_fee=loan_fee,
            gross_profit=gross_profit,
            total_fees=loan_fee,
            gas_cost_eth=gas_cost_eth,
            gas_cost_usd=gas_cost_usd,
            net_profit=net_profit,
            net_profit_usd=net_profit_usd,
            roi_percent=roi,
            execution_path=f"{params.dex_sell} → {params.dex_buy}",
            warnings=warnings,
            metadata={
                "sell_price": float(sell_price),
                "buy_price": float(buy_price),
                "price_spread": float((sell_price - Decimal("1") / buy_price) / sell_price * 100),
            },
        )

    def _error_result(self, message: str) -> StrategyResult:
        """Create error result."""
        return StrategyResult(
            strategy_type=self.strategy_type,
            success=False,
            steps=[],
            loan_amount=Decimal("0"),
            loan_asset="",
            loan_provider="",
            loan_fee=Decimal("0"),
            gross_profit=Decimal("0"),
            total_fees=Decimal("0"),
            gas_cost_eth=Decimal("0"),
            gas_cost_usd=Decimal("0"),
            net_profit=Decimal("0"),
            net_profit_usd=Decimal("0"),
            roi_percent=0,
            execution_path="",
            warnings=[message],
        )


class LiquidationStrategy(FlashLoanStrategy):
    """
    Liquidation strategy using flash loans.

    1. Flash borrow debt asset
    2. Repay borrower's debt on lending protocol
    3. Receive collateral + liquidation bonus
    4. Swap collateral back to debt asset
    5. Repay flash loan
    6. Keep liquidation bonus
    """

    # Liquidation bonuses by protocol
    LIQUIDATION_BONUSES = {
        "aave": Decimal("0.05"),  # 5% bonus
        "compound": Decimal("0.08"),  # 8% bonus
    }

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.LIQUIDATION

    def simulate(self, params: LiquidationParams) -> StrategyResult:
        """Simulate liquidation strategy."""
        steps = []
        warnings = []

        # Get provider
        provider = self.get_provider(params.provider)
        if not provider:
            return self._error_result(f"Unknown provider: {params.provider}")

        # Mock position data
        # In production, this would be fetched from the lending protocol
        debt_amount = Decimal("10000")  # 10K USDC debt
        collateral_amount = Decimal("5")  # 5 ETH collateral
        collateral_price = Decimal("2500")  # $2500/ETH
        collateral_amount * collateral_price  # $12,500

        liquidation_bonus = self.LIQUIDATION_BONUSES.get(params.protocol.lower(), Decimal("0.05"))

        # Step 1: Flash borrow debt asset
        loan_fee = provider.get_fee(params.debt_asset, debt_amount)
        steps.append(
            TransactionStep(
                step_number=1,
                action="flash_borrow",
                protocol=provider.name,
                input_token=params.debt_asset,
                input_amount=Decimal("0"),
                output_token=params.debt_asset,
                output_amount=debt_amount,
                fee=loan_fee,
                gas_estimate=provider.get_gas_overhead(),
                description=f"Flash borrow {debt_amount} {params.debt_asset}",
            )
        )

        # Step 2: Liquidate position
        collateral_received = collateral_amount * (1 + liquidation_bonus)
        steps.append(
            TransactionStep(
                step_number=2,
                action="liquidate",
                protocol=params.protocol,
                input_token=params.debt_asset,
                input_amount=debt_amount,
                output_token=params.collateral_asset,
                output_amount=collateral_received,
                fee=Decimal("0"),
                gas_estimate=300000,
                description=f"Liquidate position, receive {collateral_received} {params.collateral_asset}",
            )
        )

        # Step 3: Swap collateral to debt asset
        swap_output = collateral_received * collateral_price
        steps.append(
            TransactionStep(
                step_number=3,
                action="swap",
                protocol="Uniswap",
                input_token=params.collateral_asset,
                input_amount=collateral_received,
                output_token=params.debt_asset,
                output_amount=swap_output,
                fee=Decimal("0"),
                gas_estimate=150000,
                description=f"Swap {params.collateral_asset} to {params.debt_asset}",
            )
        )

        # Step 4: Repay flash loan
        repay_amount = debt_amount + loan_fee
        steps.append(
            TransactionStep(
                step_number=4,
                action="flash_repay",
                protocol=provider.name,
                input_token=params.debt_asset,
                input_amount=repay_amount,
                output_token=params.debt_asset,
                output_amount=Decimal("0"),
                fee=Decimal("0"),
                gas_estimate=50000,
                description="Repay flash loan",
            )
        )

        # Calculate profit
        gross_profit = swap_output - debt_amount
        total_gas = sum(s.gas_estimate for s in steps)

        gas_price_gwei = 30
        eth_price = Decimal("2500")
        gas_cost_eth = Decimal(total_gas * gas_price_gwei) / Decimal("1e9")
        gas_cost_usd = gas_cost_eth * eth_price

        # For USDC-denominated profit
        gas_cost_in_debt = gas_cost_usd
        net_profit = gross_profit - loan_fee - gas_cost_in_debt
        net_profit_usd = net_profit  # Already in USD

        roi = float(net_profit / debt_amount * 100) if debt_amount > 0 else 0

        if net_profit < 0:
            warnings.append("Liquidation not profitable after costs")

        return StrategyResult(
            strategy_type=self.strategy_type,
            success=net_profit > 0,
            steps=steps,
            loan_amount=debt_amount,
            loan_asset=params.debt_asset,
            loan_provider=provider.name,
            loan_fee=loan_fee,
            gross_profit=gross_profit,
            total_fees=loan_fee,
            gas_cost_eth=gas_cost_eth,
            gas_cost_usd=gas_cost_usd,
            net_profit=net_profit,
            net_profit_usd=net_profit_usd,
            roi_percent=roi,
            execution_path=f"{params.protocol} liquidation",
            warnings=warnings,
            metadata={
                "debt_amount": float(debt_amount),
                "collateral_received": float(collateral_received),
                "liquidation_bonus": float(liquidation_bonus * 100),
            },
        )

    def _error_result(self, message: str) -> StrategyResult:
        """Create error result."""
        return StrategyResult(
            strategy_type=self.strategy_type,
            success=False,
            steps=[],
            loan_amount=Decimal("0"),
            loan_asset="",
            loan_provider="",
            loan_fee=Decimal("0"),
            gross_profit=Decimal("0"),
            total_fees=Decimal("0"),
            gas_cost_eth=Decimal("0"),
            gas_cost_usd=Decimal("0"),
            net_profit=Decimal("0"),
            net_profit_usd=Decimal("0"),
            roi_percent=0,
            execution_path="",
            warnings=[message],
        )


class StrategyFactory:
    """Factory for creating strategy instances."""

    def __init__(self):
        """Initialize with provider manager."""
        self.provider_manager = ProviderManager()
        self._strategies = {
            StrategyType.SIMPLE_ARBITRAGE: SimpleArbitrageStrategy,
            StrategyType.LIQUIDATION: LiquidationStrategy,
        }

    def create(self, strategy_type: StrategyType) -> Optional[FlashLoanStrategy]:
        """Create strategy instance."""
        strategy_class = self._strategies.get(strategy_type)
        if strategy_class:
            return strategy_class(self.provider_manager)
        return None

    def list_strategies(self) -> List[StrategyType]:
        """List available strategies."""
        return list(self._strategies.keys())


def demo():
    """Demonstrate strategy simulation."""
    factory = StrategyFactory()

    print("=" * 60)
    print("FLASH LOAN STRATEGY SIMULATION")
    print("=" * 60)

    # Simulate simple arbitrage
    arbitrage = factory.create(StrategyType.SIMPLE_ARBITRAGE)
    if arbitrage:
        params = ArbitrageParams(
            input_token="ETH",
            output_token="USDC",
            amount=Decimal("100"),
            dex_buy="sushiswap",
            dex_sell="uniswap",
            provider="aave",
        )

        result = arbitrage.simulate(params)

        print(f"\nStrategy: {result.strategy_type.value}")
        print(f"Loan: {result.loan_amount} {result.loan_asset} from {result.loan_provider}")
        print(f"Path: {result.execution_path}")
        print("-" * 40)
        print(f"Gross Profit: {result.gross_profit:.6f} {result.loan_asset}")
        print(f"Loan Fee: -{result.loan_fee:.6f} {result.loan_asset}")
        print(f"Gas Cost: -{result.gas_cost_eth:.6f} ETH (${result.gas_cost_usd:.2f})")
        print("-" * 40)
        print(f"Net Profit: {result.net_profit:.6f} {result.loan_asset}")
        print(f"           (${result.net_profit_usd:.2f})")
        print(f"ROI: {result.roi_percent:.4f}%")
        print(f"Profitable: {'YES' if result.success else 'NO'}")

        if result.warnings:
            print("\nWarnings:")
            for w in result.warnings:
                print(f"  ⚠️  {w}")


if __name__ == "__main__":
    demo()
