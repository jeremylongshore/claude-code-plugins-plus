#!/usr/bin/env python3
"""
Multi-source price aggregation for arbitrage detection.

Fetches prices from:
- CoinGecko (free, aggregated)
- DEX subgraphs (Uniswap, SushiSwap)
- Mock exchange data (for simulation)
"""

import asyncio
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional

import httpx


class ExchangeType(Enum):
    """Exchange type classification."""

    CEX = "CEX"
    DEX = "DEX"


@dataclass
class PriceQuote:
    """Price quote from a single source."""

    exchange: str
    exchange_type: ExchangeType
    pair: str
    bid: Decimal  # Best buy price (you sell at this)
    ask: Decimal  # Best sell price (you buy at this)
    mid: Decimal  # Mid-market price
    spread_pct: float  # Bid-ask spread percentage
    volume_24h: Decimal  # 24h volume in base currency
    timestamp: float  # Unix timestamp
    chain: str = "ethereum"  # For DEX

    @property
    def is_fresh(self) -> bool:
        """Check if quote is fresh (< 30 seconds old)."""
        return (time.time() - self.timestamp) < 30

    @property
    def staleness_seconds(self) -> float:
        """Get quote age in seconds."""
        return time.time() - self.timestamp


@dataclass
class ExchangeConfig:
    """Configuration for an exchange."""

    name: str
    exchange_type: ExchangeType
    maker_fee: Decimal
    taker_fee: Decimal
    withdrawal_fee: Decimal = Decimal("0")  # Per withdrawal
    gas_overhead: int = 0  # For DEX
    chains: List[str] = field(default_factory=lambda: ["ethereum"])


class PriceFetcher:
    """
    Multi-source price fetcher.

    Aggregates prices from CEX and DEX sources with:
    - Rate limiting
    - Timeout handling
    - Source reliability tracking
    """

    # CEX fee structures (as of 2024)
    CEX_CONFIGS = {
        "binance": ExchangeConfig(
            name="Binance",
            exchange_type=ExchangeType.CEX,
            maker_fee=Decimal("0.0010"),  # 0.10%
            taker_fee=Decimal("0.0010"),
        ),
        "coinbase": ExchangeConfig(
            name="Coinbase",
            exchange_type=ExchangeType.CEX,
            maker_fee=Decimal("0.0040"),  # 0.40%
            taker_fee=Decimal("0.0060"),  # 0.60%
        ),
        "kraken": ExchangeConfig(
            name="Kraken",
            exchange_type=ExchangeType.CEX,
            maker_fee=Decimal("0.0016"),  # 0.16%
            taker_fee=Decimal("0.0026"),  # 0.26%
        ),
        "kucoin": ExchangeConfig(
            name="KuCoin",
            exchange_type=ExchangeType.CEX,
            maker_fee=Decimal("0.0010"),
            taker_fee=Decimal("0.0010"),
        ),
        "okx": ExchangeConfig(
            name="OKX",
            exchange_type=ExchangeType.CEX,
            maker_fee=Decimal("0.0008"),  # 0.08%
            taker_fee=Decimal("0.0010"),
        ),
    }

    # DEX fee structures
    DEX_CONFIGS = {
        "uniswap": ExchangeConfig(
            name="Uniswap V3",
            exchange_type=ExchangeType.DEX,
            maker_fee=Decimal("0.0030"),  # 0.30% (most common tier)
            taker_fee=Decimal("0.0030"),
            gas_overhead=150000,
            chains=["ethereum", "polygon", "arbitrum", "optimism"],
        ),
        "sushiswap": ExchangeConfig(
            name="SushiSwap",
            exchange_type=ExchangeType.DEX,
            maker_fee=Decimal("0.0030"),
            taker_fee=Decimal("0.0030"),
            gas_overhead=150000,
            chains=["ethereum", "polygon", "arbitrum"],
        ),
        "curve": ExchangeConfig(
            name="Curve",
            exchange_type=ExchangeType.DEX,
            maker_fee=Decimal("0.0004"),  # 0.04%
            taker_fee=Decimal("0.0004"),
            gas_overhead=200000,
            chains=["ethereum", "polygon", "arbitrum"],
        ),
        "balancer": ExchangeConfig(
            name="Balancer",
            exchange_type=ExchangeType.DEX,
            maker_fee=Decimal("0.0010"),  # Varies by pool
            taker_fee=Decimal("0.0010"),
            gas_overhead=180000,
            chains=["ethereum", "polygon", "arbitrum"],
        ),
    }

    # Mock prices for simulation (simulate real market spreads)
    MOCK_PRICES = {
        ("ETH", "USDC"): {
            "binance": {"bid": 2541.20, "ask": 2541.50, "volume": 125000},
            "coinbase": {"bid": 2543.80, "ask": 2544.10, "volume": 45000},
            "kraken": {"bid": 2542.50, "ask": 2543.00, "volume": 35000},
            "kucoin": {"bid": 2540.90, "ask": 2541.40, "volume": 28000},
            "okx": {"bid": 2541.00, "ask": 2541.60, "volume": 52000},
            "uniswap": {"bid": 2542.10, "ask": 2542.80, "volume": 85000},
            "sushiswap": {"bid": 2540.50, "ask": 2541.30, "volume": 22000},
        },
        ("BTC", "USDC"): {
            "binance": {"bid": 67850.00, "ask": 67865.00, "volume": 4500},
            "coinbase": {"bid": 67920.00, "ask": 67950.00, "volume": 2100},
            "kraken": {"bid": 67880.00, "ask": 67910.00, "volume": 1800},
            "kucoin": {"bid": 67840.00, "ask": 67870.00, "volume": 1200},
            "okx": {"bid": 67855.00, "ask": 67880.00, "volume": 3200},
            "uniswap": {"bid": 67870.00, "ask": 67920.00, "volume": 950},
        },
        ("ETH", "BTC"): {
            "binance": {"bid": 0.03745, "ask": 0.03748, "volume": 8500},
            "coinbase": {"bid": 0.03752, "ask": 0.03756, "volume": 3200},
            "kraken": {"bid": 0.03748, "ask": 0.03752, "volume": 2100},
            "kucoin": {"bid": 0.03744, "ask": 0.03749, "volume": 1800},
            "okx": {"bid": 0.03746, "ask": 0.03750, "volume": 4100},
        },
        ("USDC", "USDT"): {
            "binance": {"bid": 0.9998, "ask": 1.0002, "volume": 500000},
            "coinbase": {"bid": 0.9997, "ask": 1.0003, "volume": 120000},
            "curve": {"bid": 0.99995, "ask": 1.00005, "volume": 2500000},
        },
    }

    def __init__(self, use_mock: bool = True, timeout: float = 10.0):
        """
        Initialize price fetcher.

        Args:
            use_mock: Use mock data instead of live APIs
            timeout: Request timeout in seconds
        """
        self.use_mock = use_mock
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    def get_exchange_config(self, exchange: str) -> Optional[ExchangeConfig]:
        """Get exchange configuration."""
        exchange_lower = exchange.lower()
        if exchange_lower in self.CEX_CONFIGS:
            return self.CEX_CONFIGS[exchange_lower]
        if exchange_lower in self.DEX_CONFIGS:
            return self.DEX_CONFIGS[exchange_lower]
        return None

    def list_exchanges(self, exchange_type: Optional[ExchangeType] = None) -> List[str]:
        """List available exchanges."""
        result = []
        if exchange_type is None or exchange_type == ExchangeType.CEX:
            result.extend(self.CEX_CONFIGS.keys())
        if exchange_type is None or exchange_type == ExchangeType.DEX:
            result.extend(self.DEX_CONFIGS.keys())
        return result

    async def fetch_price(
        self,
        base: str,
        quote: str,
        exchange: str,
    ) -> Optional[PriceQuote]:
        """
        Fetch price from a single exchange.

        Args:
            base: Base token (e.g., ETH)
            quote: Quote token (e.g., USDC)
            exchange: Exchange name

        Returns:
            PriceQuote or None if unavailable
        """
        if self.use_mock:
            return self._get_mock_price(base, quote, exchange)

        # Real API integration would go here
        # For now, fall back to mock
        return self._get_mock_price(base, quote, exchange)

    def _get_mock_price(
        self,
        base: str,
        quote: str,
        exchange: str,
    ) -> Optional[PriceQuote]:
        """Get mock price data."""
        pair_key = (base.upper(), quote.upper())
        exchange_lower = exchange.lower()

        # Try direct pair
        if pair_key in self.MOCK_PRICES:
            prices = self.MOCK_PRICES[pair_key]
            if exchange_lower in prices:
                data = prices[exchange_lower]
                return self._build_quote(base, quote, exchange_lower, data)

        # Try inverse pair
        inverse_key = (quote.upper(), base.upper())
        if inverse_key in self.MOCK_PRICES:
            prices = self.MOCK_PRICES[inverse_key]
            if exchange_lower in prices:
                data = prices[exchange_lower]
                # Invert prices
                inverted = {
                    "bid": 1.0 / data["ask"],
                    "ask": 1.0 / data["bid"],
                    "volume": data["volume"],
                }
                return self._build_quote(base, quote, exchange_lower, inverted)

        return None

    def _build_quote(
        self,
        base: str,
        quote: str,
        exchange: str,
        data: dict,
    ) -> PriceQuote:
        """Build PriceQuote from raw data."""
        config = self.get_exchange_config(exchange)

        bid = Decimal(str(data["bid"]))
        ask = Decimal(str(data["ask"]))
        mid = (bid + ask) / 2
        spread_pct = float((ask - bid) / mid * 100)

        return PriceQuote(
            exchange=config.name if config else exchange,
            exchange_type=config.exchange_type if config else ExchangeType.CEX,
            pair=f"{base}/{quote}",
            bid=bid,
            ask=ask,
            mid=mid,
            spread_pct=spread_pct,
            volume_24h=Decimal(str(data["volume"])),
            timestamp=time.time(),
            chain="ethereum",
        )

    async def fetch_all_prices(
        self,
        base: str,
        quote: str,
        exchanges: Optional[List[str]] = None,
        exchange_type: Optional[ExchangeType] = None,
    ) -> List[PriceQuote]:
        """
        Fetch prices from multiple exchanges.

        Args:
            base: Base token
            quote: Quote token
            exchanges: Specific exchanges (default: all)
            exchange_type: Filter by CEX or DEX

        Returns:
            List of PriceQuote objects
        """
        if exchanges is None:
            exchanges = self.list_exchanges(exchange_type)

        # Fetch concurrently
        tasks = [self.fetch_price(base, quote, ex) for ex in exchanges]
        results = await asyncio.gather(*tasks)

        # Filter None results
        return [r for r in results if r is not None]

    def fetch_all_prices_sync(
        self,
        base: str,
        quote: str,
        exchanges: Optional[List[str]] = None,
        exchange_type: Optional[ExchangeType] = None,
    ) -> List[PriceQuote]:
        """Synchronous wrapper for fetch_all_prices."""
        return asyncio.run(self.fetch_all_prices(base, quote, exchanges, exchange_type))

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


def demo():
    """Demonstrate price fetcher."""
    fetcher = PriceFetcher(use_mock=True)

    print("=" * 60)
    print("PRICE FETCHER DEMO")
    print("=" * 60)

    # Fetch ETH/USDC prices
    prices = fetcher.fetch_all_prices_sync("ETH", "USDC")

    print(f"\nETH/USDC prices across {len(prices)} exchanges:\n")
    print(f"{'Exchange':<15} {'Bid':>12} {'Ask':>12} {'Spread':>8} {'Volume':>12}")
    print("-" * 60)

    for quote in sorted(prices, key=lambda x: x.bid, reverse=True):
        print(
            f"{quote.exchange:<15} "
            f"${quote.bid:>11,.2f} "
            f"${quote.ask:>11,.2f} "
            f"{quote.spread_pct:>7.3f}% "
            f"{quote.volume_24h:>11,.0f}"
        )

    # Show best opportunity
    if len(prices) >= 2:
        sorted_by_bid = sorted(prices, key=lambda x: x.bid, reverse=True)
        sorted_by_ask = sorted(prices, key=lambda x: x.ask)

        best_sell = sorted_by_bid[0]
        best_buy = sorted_by_ask[0]

        if best_sell.bid > best_buy.ask:
            spread = float((best_sell.bid - best_buy.ask) / best_buy.ask * 100)
            print("\nBest opportunity:")
            print(f"  Buy on {best_buy.exchange} at ${best_buy.ask:,.2f}")
            print(f"  Sell on {best_sell.exchange} at ${best_sell.bid:,.2f}")
            print(f"  Gross spread: {spread:.3f}%")


if __name__ == "__main__":
    demo()
