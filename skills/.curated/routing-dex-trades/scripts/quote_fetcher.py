#!/usr/bin/env python3
"""
Multi-source quote aggregation for DEX trades.

Fetches quotes from multiple aggregator APIs (1inch, Paraswap, 0x)
in parallel and normalizes them to a standard format.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

# Token address mappings for major chains
TOKEN_ADDRESSES = {
    "ethereum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EescdDEAC495271",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    },
    "arbitrum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    },
    "polygon": {
        "MATIC": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    },
}

CHAIN_IDS = {
    "ethereum": 1,
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10,
}


@dataclass
class NormalizedQuote:
    """Standardized quote format across all aggregator sources."""

    source: str
    input_token: str
    output_token: str
    input_amount: Decimal
    output_amount: Decimal
    price: Decimal
    price_impact: float
    gas_estimate: int
    gas_price_gwei: float
    gas_cost_usd: float
    effective_rate: Decimal
    route: List[str]
    route_readable: List[str]
    protocols: List[str]
    timestamp: datetime
    valid_for_seconds: int = 30
    raw_response: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if quote has expired."""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.valid_for_seconds


@dataclass
class SwapParams:
    """Parameters for a swap quote request."""

    from_token: str
    to_token: str
    amount: Decimal
    chain: str = "ethereum"
    slippage: float = 0.5  # percentage


class QuoteFetcher:
    """
    Aggregates quotes from multiple DEX aggregator APIs.

    Supports:
    - 1inch API
    - Paraswap API
    - 0x API

    All requests are made in parallel with timeout handling.
    """

    AGGREGATORS = {
        "1inch": {
            "base_url": "https://api.1inch.dev/swap/v6.0",
            "chains": {1: 1, 137: 137, 42161: 42161, 10: 10},
            "rate_limit": 1.0,
            "auth_type": "bearer",
        },
        "paraswap": {
            "base_url": "https://apiv5.paraswap.io",
            "chains": {1: 1, 137: 137, 42161: 42161, 10: 10},
            "rate_limit": 10.0,
            "auth_type": None,
        },
        "0x": {
            "base_url": "https://api.0x.org/swap/v1",
            "chains": {1: "ethereum", 137: "polygon", 42161: "arbitrum"},
            "rate_limit": 3.0,
            "auth_type": "header",
        },
    }

    def __init__(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        eth_price_usd: float = 2500.0,
        gas_price_gwei: float = 30.0,
    ):
        """
        Initialize the quote fetcher.

        Args:
            api_keys: Optional API keys for rate limit increases
            eth_price_usd: Current ETH price for gas calculations
            gas_price_gwei: Current gas price
        """
        self.api_keys = api_keys or {}
        self.eth_price_usd = eth_price_usd
        self.gas_price_gwei = gas_price_gwei
        self._last_request_time: Dict[str, float] = {}

    def resolve_token_address(self, symbol: str, chain: str) -> str:
        """Resolve token symbol to address."""
        symbol_upper = symbol.upper()
        chain_tokens = TOKEN_ADDRESSES.get(chain, {})

        if symbol_upper in chain_tokens:
            return chain_tokens[symbol_upper]

        # If already an address, return as-is
        if symbol.startswith("0x") and len(symbol) == 42:
            return symbol

        raise ValueError(f"Unknown token: {symbol} on {chain}")

    async def fetch_all_quotes(self, params: SwapParams) -> List[NormalizedQuote]:
        """
        Fetch quotes from all aggregators in parallel.

        Args:
            params: Swap parameters

        Returns:
            List of normalized quotes from all sources
        """
        chain_id = CHAIN_IDS.get(params.chain, 1)

        tasks = []
        for agg_name in self.AGGREGATORS:
            if chain_id in self.AGGREGATORS[agg_name]["chains"]:
                tasks.append(self._fetch_with_timeout(agg_name, params))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        quotes = []
        for result in results:
            if isinstance(result, NormalizedQuote):
                quotes.append(result)
            elif isinstance(result, Exception):
                # Log but don't fail on individual aggregator errors
                pass

        return quotes

    async def _fetch_with_timeout(
        self, aggregator: str, params: SwapParams, timeout: float = 10.0
    ) -> Optional[NormalizedQuote]:
        """Fetch quote with timeout and rate limiting."""
        # Rate limiting
        await self._wait_for_rate_limit(aggregator)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if aggregator == "1inch":
                    return await self._fetch_1inch(client, params)
                elif aggregator == "paraswap":
                    return await self._fetch_paraswap(client, params)
                elif aggregator == "0x":
                    return await self._fetch_0x(client, params)
        except Exception:
            return None

    async def _wait_for_rate_limit(self, aggregator: str):
        """Enforce rate limiting per aggregator."""
        rate_limit = self.AGGREGATORS[aggregator]["rate_limit"]
        min_interval = 1.0 / rate_limit

        last_time = self._last_request_time.get(aggregator, 0)
        elapsed = time.time() - last_time

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self._last_request_time[aggregator] = time.time()

    async def _fetch_1inch(self, client: httpx.AsyncClient, params: SwapParams) -> Optional[NormalizedQuote]:
        """Fetch quote from 1inch API."""
        chain_id = CHAIN_IDS.get(params.chain, 1)
        from_token = self.resolve_token_address(params.from_token, params.chain)
        to_token = self.resolve_token_address(params.to_token, params.chain)

        # Convert amount to wei (assuming 18 decimals for ETH)
        amount_wei = int(params.amount * Decimal(10**18))

        url = f"{self.AGGREGATORS['1inch']['base_url']}/{chain_id}/quote"
        query_params = {
            "src": from_token,
            "dst": to_token,
            "amount": str(amount_wei),
        }

        headers = {}
        if "oneinch" in self.api_keys:
            headers["Authorization"] = f"Bearer {self.api_keys['oneinch']}"

        try:
            response = await client.get(url, params=query_params, headers=headers)
            if response.status_code != 200:
                return None

            data = response.json()
            return self._normalize_1inch_quote(data, params)
        except Exception:
            return None

    async def _fetch_paraswap(self, client: httpx.AsyncClient, params: SwapParams) -> Optional[NormalizedQuote]:
        """Fetch quote from Paraswap API."""
        chain_id = CHAIN_IDS.get(params.chain, 1)
        from_token = self.resolve_token_address(params.from_token, params.chain)
        to_token = self.resolve_token_address(params.to_token, params.chain)

        amount_wei = int(params.amount * Decimal(10**18))

        url = f"{self.AGGREGATORS['paraswap']['base_url']}/prices"
        query_params = {
            "srcToken": from_token,
            "destToken": to_token,
            "amount": str(amount_wei),
            "srcDecimals": 18,
            "destDecimals": 6 if "USD" in params.to_token.upper() else 18,
            "network": chain_id,
        }

        try:
            response = await client.get(url, params=query_params)
            if response.status_code != 200:
                return None

            data = response.json()
            return self._normalize_paraswap_quote(data, params)
        except Exception:
            return None

    async def _fetch_0x(self, client: httpx.AsyncClient, params: SwapParams) -> Optional[NormalizedQuote]:
        """Fetch quote from 0x API."""
        from_token = self.resolve_token_address(params.from_token, params.chain)
        to_token = self.resolve_token_address(params.to_token, params.chain)

        amount_wei = int(params.amount * Decimal(10**18))

        url = f"{self.AGGREGATORS['0x']['base_url']}/quote"
        query_params = {
            "sellToken": from_token,
            "buyToken": to_token,
            "sellAmount": str(amount_wei),
        }

        headers = {}
        if "zerox" in self.api_keys:
            headers["0x-api-key"] = self.api_keys["zerox"]

        try:
            response = await client.get(url, params=query_params, headers=headers)
            if response.status_code != 200:
                return None

            data = response.json()
            return self._normalize_0x_quote(data, params)
        except Exception:
            return None

    def _normalize_1inch_quote(self, data: Dict, params: SwapParams) -> NormalizedQuote:
        """Normalize 1inch quote to standard format."""
        # Determine output decimals (6 for stablecoins, 18 for others)
        out_decimals = 6 if "USD" in params.to_token.upper() else 18

        output_amount = Decimal(data.get("dstAmount", 0)) / Decimal(10**out_decimals)
        input_amount = params.amount

        price = output_amount / input_amount if input_amount > 0 else Decimal(0)

        gas_estimate = int(data.get("estimatedGas", 150000))
        gas_cost_eth = (gas_estimate * self.gas_price_gwei) / 1e9
        gas_cost_usd = gas_cost_eth * self.eth_price_usd

        # Effective rate accounts for gas
        gas_cost_in_output = Decimal(gas_cost_usd)
        effective_output = output_amount - gas_cost_in_output
        effective_rate = effective_output / input_amount if input_amount > 0 else Decimal(0)

        protocols = []
        if "protocols" in data:
            for route in data["protocols"]:
                for hop in route:
                    for pool in hop:
                        if "name" in pool:
                            protocols.append(pool["name"])

        return NormalizedQuote(
            source="1inch",
            input_token=params.from_token,
            output_token=params.to_token,
            input_amount=input_amount,
            output_amount=output_amount,
            price=price,
            price_impact=0.0,  # 1inch doesn't always provide this
            gas_estimate=gas_estimate,
            gas_price_gwei=self.gas_price_gwei,
            gas_cost_usd=gas_cost_usd,
            effective_rate=effective_rate,
            route=[params.from_token, params.to_token],
            route_readable=[params.from_token, params.to_token],
            protocols=list(set(protocols)) if protocols else ["Various"],
            timestamp=datetime.now(),
            raw_response=data,
        )

    def _normalize_paraswap_quote(self, data: Dict, params: SwapParams) -> NormalizedQuote:
        """Normalize Paraswap quote to standard format."""
        price_route = data.get("priceRoute", {})
        out_decimals = 6 if "USD" in params.to_token.upper() else 18

        output_amount = Decimal(price_route.get("destAmount", 0)) / Decimal(10**out_decimals)
        input_amount = params.amount

        price = output_amount / input_amount if input_amount > 0 else Decimal(0)

        gas_estimate = int(price_route.get("gasCost", 150000))
        gas_cost_eth = (gas_estimate * self.gas_price_gwei) / 1e9
        gas_cost_usd = gas_cost_eth * self.eth_price_usd

        gas_cost_in_output = Decimal(gas_cost_usd)
        effective_output = output_amount - gas_cost_in_output
        effective_rate = effective_output / input_amount if input_amount > 0 else Decimal(0)

        # Extract protocols from best route
        protocols = []
        best_route = price_route.get("bestRoute", [])
        for swap in best_route:
            for exchange in swap.get("swaps", []):
                for swap_exchange in exchange.get("swapExchanges", []):
                    if "exchange" in swap_exchange:
                        protocols.append(swap_exchange["exchange"])

        return NormalizedQuote(
            source="Paraswap",
            input_token=params.from_token,
            output_token=params.to_token,
            input_amount=input_amount,
            output_amount=output_amount,
            price=price,
            price_impact=float(price_route.get("priceImpact", 0)) / 100,
            gas_estimate=gas_estimate,
            gas_price_gwei=self.gas_price_gwei,
            gas_cost_usd=gas_cost_usd,
            effective_rate=effective_rate,
            route=[params.from_token, params.to_token],
            route_readable=[params.from_token, params.to_token],
            protocols=list(set(protocols)) if protocols else ["Various"],
            timestamp=datetime.now(),
            raw_response=data,
        )

    def _normalize_0x_quote(self, data: Dict, params: SwapParams) -> NormalizedQuote:
        """Normalize 0x quote to standard format."""
        out_decimals = 6 if "USD" in params.to_token.upper() else 18

        output_amount = Decimal(data.get("buyAmount", 0)) / Decimal(10**out_decimals)
        input_amount = params.amount

        price = output_amount / input_amount if input_amount > 0 else Decimal(0)

        gas_estimate = int(data.get("estimatedGas", 150000))
        gas_price_wei = int(data.get("gasPrice", self.gas_price_gwei * 1e9))
        gas_price_gwei = gas_price_wei / 1e9

        gas_cost_eth = (gas_estimate * gas_price_gwei) / 1e9
        gas_cost_usd = gas_cost_eth * self.eth_price_usd

        gas_cost_in_output = Decimal(gas_cost_usd)
        effective_output = output_amount - gas_cost_in_output
        effective_rate = effective_output / input_amount if input_amount > 0 else Decimal(0)

        # Extract sources from 0x response
        protocols = []
        for source in data.get("sources", []):
            if float(source.get("proportion", 0)) > 0:
                protocols.append(source.get("name", "Unknown"))

        return NormalizedQuote(
            source="0x",
            input_token=params.from_token,
            output_token=params.to_token,
            input_amount=input_amount,
            output_amount=output_amount,
            price=price,
            price_impact=float(data.get("estimatedPriceImpact", 0)),
            gas_estimate=gas_estimate,
            gas_price_gwei=gas_price_gwei,
            gas_cost_usd=gas_cost_usd,
            effective_rate=effective_rate,
            route=[params.from_token, params.to_token],
            route_readable=[params.from_token, params.to_token],
            protocols=protocols if protocols else ["Various"],
            timestamp=datetime.now(),
            raw_response=data,
        )


async def main():
    """Test the quote fetcher."""
    fetcher = QuoteFetcher(eth_price_usd=2500.0, gas_price_gwei=30.0)

    params = SwapParams(
        from_token="ETH",
        to_token="USDC",
        amount=Decimal("1.0"),
        chain="ethereum",
    )

    print(f"Fetching quotes for {params.amount} {params.from_token} → {params.to_token}")
    print("-" * 60)

    quotes = await fetcher.fetch_all_quotes(params)

    for quote in quotes:
        print(f"\n{quote.source}:")
        print(f"  Output: {quote.output_amount:.2f} {quote.output_token}")
        print(f"  Rate: {quote.price:.2f} {quote.output_token}/{quote.input_token}")
        print(f"  Gas: ${quote.gas_cost_usd:.2f}")
        print(f"  Effective: {quote.effective_rate:.2f}")
        print(f"  Protocols: {', '.join(quote.protocols)}")

    if not quotes:
        print("No quotes received (API keys may be required)")


if __name__ == "__main__":
    asyncio.run(main())
