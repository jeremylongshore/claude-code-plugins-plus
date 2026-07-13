#!/usr/bin/env python3
"""
Token Resolver

Resolve token metadata, prices, and formatting.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    import requests
except ImportError:
    requests = None


@dataclass
class TokenInfo:
    """Token metadata and pricing."""

    address: str
    symbol: str
    name: str
    decimals: int
    price_usd: Optional[float]
    chain: str
    logo_url: Optional[str] = None


# Well-known tokens by chain (address -> info)
KNOWN_TOKENS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "ethereum": {
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {"symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
        "0xdac17f958d2ee523a2206206994597c13d831ec7": {"symbol": "USDT", "name": "Tether USD", "decimals": 6},
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
        "0x6b175474e89094c44da98b954eedeac495271d0f": {"symbol": "DAI", "name": "Dai Stablecoin", "decimals": 18},
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {"symbol": "WBTC", "name": "Wrapped BTC", "decimals": 8},
        "0x514910771af9ca656af840dff83e8264ecf986ca": {"symbol": "LINK", "name": "Chainlink", "decimals": 18},
        "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": {"symbol": "UNI", "name": "Uniswap", "decimals": 18},
        "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": {"symbol": "AAVE", "name": "Aave", "decimals": 18},
        "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce": {"symbol": "SHIB", "name": "Shiba Inu", "decimals": 18},
        "0x4d224452801aced8b2f0aebe155379bb5d594381": {"symbol": "APE", "name": "ApeCoin", "decimals": 18},
    },
    "polygon": {
        "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270": {"symbol": "WMATIC", "name": "Wrapped Matic", "decimals": 18},
        "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": {"symbol": "USDC", "name": "USD Coin (PoS)", "decimals": 6},
        "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": {"symbol": "USDT", "name": "Tether USD (PoS)", "decimals": 6},
        "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619": {"symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
    },
    "bsc": {
        "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": {"symbol": "WBNB", "name": "Wrapped BNB", "decimals": 18},
        "0x55d398326f99059ff775485246999027b3197955": {"symbol": "USDT", "name": "Tether USD", "decimals": 18},
        "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d": {"symbol": "USDC", "name": "USD Coin", "decimals": 18},
        "0x2170ed0880ac9a755fd29b2688956bd959f933f8": {"symbol": "ETH", "name": "Ethereum Token", "decimals": 18},
    },
    "arbitrum": {
        "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": {"symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
        "0xaf88d065e77c8cc2239327c5edb3a432268e5831": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
        "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": {"symbol": "USDT", "name": "Tether USD", "decimals": 6},
        "0x912ce59144191c1204e64559fe8253a0e49e6548": {"symbol": "ARB", "name": "Arbitrum", "decimals": 18},
    },
}


class TokenResolver:
    """Resolve token metadata and prices."""

    def __init__(self, chain: str = "ethereum", verbose: bool = False):
        """Initialize resolver.

        Args:
            chain: Default chain
            verbose: Enable verbose output
        """
        self.chain = chain
        self.verbose = verbose
        self._cache: Dict[str, TokenInfo] = {}
        self._price_cache: Dict[str, tuple] = {}  # (price, timestamp)
        self._price_ttl = 60  # seconds

    def resolve(self, address: str, chain: Optional[str] = None) -> TokenInfo:
        """Resolve token info by address.

        Args:
            address: Token contract address
            chain: Chain name (uses default if not specified)

        Returns:
            TokenInfo with metadata and price
        """
        chain = chain or self.chain
        cache_key = f"{chain}:{address.lower()}"

        # Check cache
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Refresh price if stale
            cached.price_usd = self._get_price(address, chain)
            return cached

        # Check known tokens
        address_lower = address.lower()
        chain_tokens = KNOWN_TOKENS.get(chain, {})

        if address_lower in chain_tokens:
            token_data = chain_tokens[address_lower]
            info = TokenInfo(
                address=address,
                symbol=token_data["symbol"],
                name=token_data["name"],
                decimals=token_data["decimals"],
                price_usd=self._get_price(address, chain),
                chain=chain,
            )
            self._cache[cache_key] = info
            return info

        # Try to fetch from API
        info = self._fetch_token_info(address, chain)
        if info:
            self._cache[cache_key] = info
            return info

        # Return unknown token
        return TokenInfo(address=address, symbol="???", name="Unknown Token", decimals=18, price_usd=None, chain=chain)

    def _get_price(self, address: str, chain: str) -> Optional[float]:
        """Get token price with caching.

        Args:
            address: Token address
            chain: Chain name

        Returns:
            Price in USD or None
        """
        cache_key = f"{chain}:{address.lower()}"

        # Check price cache
        if cache_key in self._price_cache:
            price, timestamp = self._price_cache[cache_key]
            if time.time() - timestamp < self._price_ttl:
                return price

        # Fetch fresh price
        price = self._fetch_price(address, chain)
        self._price_cache[cache_key] = (price, time.time())
        return price

    def _fetch_price(self, address: str, chain: str) -> Optional[float]:
        """Fetch token price from CoinGecko.

        Args:
            address: Token address
            chain: Chain name

        Returns:
            Price in USD or None
        """
        if not requests:
            return None

        # Map chain to CoinGecko platform ID
        platform_map = {
            "ethereum": "ethereum",
            "polygon": "polygon-pos",
            "bsc": "binance-smart-chain",
            "arbitrum": "arbitrum-one",
            "optimism": "optimistic-ethereum",
            "avalanche": "avalanche",
            "base": "base",
        }

        platform = platform_map.get(chain)
        if not platform:
            return None

        try:
            if self.verbose:
                print(f"Fetching price for {address} on {chain}")

            response = requests.get(
                f"https://api.coingecko.com/api/v3/simple/token_price/{platform}",
                params={"contract_addresses": address, "vs_currencies": "usd"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get(address.lower(), {}).get("usd")

        except Exception as e:
            if self.verbose:
                print(f"Price fetch error: {e}")

        return None

    def _fetch_token_info(self, address: str, chain: str) -> Optional[TokenInfo]:
        """Fetch token info from CoinGecko.

        Args:
            address: Token address
            chain: Chain name

        Returns:
            TokenInfo or None
        """
        if not requests:
            return None

        platform_map = {
            "ethereum": "ethereum",
            "polygon": "polygon-pos",
            "bsc": "binance-smart-chain",
            "arbitrum": "arbitrum-one",
            "optimism": "optimistic-ethereum",
            "avalanche": "avalanche",
            "base": "base",
        }

        platform = platform_map.get(chain)
        if not platform:
            return None

        try:
            response = requests.get(f"https://api.coingecko.com/api/v3/coins/{platform}/contract/{address}", timeout=10)

            if response.status_code == 200:
                data = response.json()
                return TokenInfo(
                    address=address,
                    symbol=data.get("symbol", "???").upper(),
                    name=data.get("name", "Unknown"),
                    decimals=data.get("detail_platforms", {}).get(platform, {}).get("decimal_place", 18),
                    price_usd=data.get("market_data", {}).get("current_price", {}).get("usd"),
                    chain=chain,
                    logo_url=data.get("image", {}).get("small"),
                )

        except Exception as e:
            if self.verbose:
                print(f"Token info fetch error: {e}")

        return None

    def format_amount(self, amount_raw: int, token: TokenInfo, include_usd: bool = True) -> str:
        """Format token amount for display.

        Args:
            amount_raw: Raw token amount (in smallest unit)
            token: Token info
            include_usd: Include USD value

        Returns:
            Formatted string
        """
        amount = amount_raw / (10**token.decimals)

        if amount >= 1_000_000:
            formatted = f"{amount / 1_000_000:.2f}M"
        elif amount >= 1_000:
            formatted = f"{amount / 1_000:.2f}K"
        elif amount >= 1:
            formatted = f"{amount:.4f}"
        else:
            formatted = f"{amount:.8f}"

        result = f"{formatted} {token.symbol}"

        if include_usd and token.price_usd:
            usd_value = amount * token.price_usd
            if usd_value >= 1_000_000:
                result += f" (${usd_value / 1_000_000:.2f}M)"
            elif usd_value >= 1_000:
                result += f" (${usd_value / 1_000:.2f}K)"
            else:
                result += f" (${usd_value:.2f})"

        return result

    def get_native_token(self, chain: str) -> TokenInfo:
        """Get native token info for chain.

        Args:
            chain: Chain name

        Returns:
            Native token info
        """
        native_tokens = {
            "ethereum": TokenInfo("native", "ETH", "Ether", 18, None, "ethereum"),
            "polygon": TokenInfo("native", "MATIC", "Polygon", 18, None, "polygon"),
            "bsc": TokenInfo("native", "BNB", "BNB", 18, None, "bsc"),
            "arbitrum": TokenInfo("native", "ETH", "Ether", 18, None, "arbitrum"),
            "optimism": TokenInfo("native", "ETH", "Ether", 18, None, "optimism"),
            "avalanche": TokenInfo("native", "AVAX", "Avalanche", 18, None, "avalanche"),
            "base": TokenInfo("native", "ETH", "Ether", 18, None, "base"),
        }

        token = native_tokens.get(chain, TokenInfo("native", "???", "Unknown", 18, None, chain))

        # Get price
        price = self._get_native_price(chain)
        token.price_usd = price

        return token

    def _get_native_price(self, chain: str) -> Optional[float]:
        """Get native token price.

        Args:
            chain: Chain name

        Returns:
            Price in USD or None
        """
        if not requests:
            return None

        coin_ids = {
            "ethereum": "ethereum",
            "polygon": "matic-network",
            "bsc": "binancecoin",
            "arbitrum": "ethereum",
            "optimism": "ethereum",
            "avalanche": "avalanche-2",
            "base": "ethereum",
        }

        coin_id = coin_ids.get(chain)
        if not coin_id:
            return None

        cache_key = f"native:{coin_id}"
        if cache_key in self._price_cache:
            price, timestamp = self._price_cache[cache_key]
            if time.time() - timestamp < self._price_ttl:
                return price

        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                price = data.get(coin_id, {}).get("usd")
                self._price_cache[cache_key] = (price, time.time())
                return price

        except Exception:
            pass

        return None


def main():
    """CLI entry point for testing."""
    resolver = TokenResolver(chain="ethereum", verbose=True)

    # Test USDC
    usdc = resolver.resolve("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
    print(f"Token: {usdc.name} ({usdc.symbol})")
    print(f"Decimals: {usdc.decimals}")
    print(f"Price: ${usdc.price_usd:.4f}" if usdc.price_usd else "Price: N/A")

    # Test formatting
    amount_raw = 1_000_000_000  # 1000 USDC (6 decimals)
    print(f"Amount: {resolver.format_amount(amount_raw, usdc)}")


if __name__ == "__main__":
    main()
