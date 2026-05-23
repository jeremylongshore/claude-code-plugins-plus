#!/usr/bin/env python3
"""
Crypto API Client - Multi-Source Price Data Fetcher

Provides unified interface to CoinGecko (primary) and yfinance (fallback)
for cryptocurrency price data retrieval.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import os
import time
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

try:
    import requests
except ImportError:
    raise ImportError("Required: pip install requests")


class APIError(Exception):
    """Base exception for API errors."""

    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""

    pass


class NetworkError(APIError):
    """Network connectivity error."""

    pass


class SymbolNotFoundError(APIError):
    """Cryptocurrency symbol not found."""

    pass


class DataSource(Enum):
    """Available data sources."""

    COINGECKO = "coingecko"
    YFINANCE = "yfinance"


@dataclass
class PriceData:
    """Standardized price data structure."""

    symbol: str
    name: str
    price: float
    currency: str
    change_24h: Optional[float] = None
    change_7d: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: Optional[str] = None
    source: str = "coingecko"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "change_24h": self.change_24h,
            "change_7d": self.change_7d,
            "volume_24h": self.volume_24h,
            "market_cap": self.market_cap,
            "timestamp": self.timestamp or datetime.utcnow().isoformat(),
            "source": self.source,
        }


class CryptoAPIClient:
    """
    Unified cryptocurrency API client with multi-source support.

    Primary: CoinGecko API (free tier or Pro)
    Fallback: yfinance (Yahoo Finance)
    """

    COINGECKO_BASE = "https://api.coingecko.com/api/v3"
    COINGECKO_PRO_BASE = "https://pro-api.coingecko.com/api/v3"

    # Common symbol to CoinGecko ID mapping
    SYMBOL_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "AVAX": "avalanche-2",
        "MATIC": "matic-network",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "AAVE": "aave",
        "MKR": "maker",
        "COMP": "compound-governance-token",
        "CRV": "curve-dao-token",
        "SUSHI": "sushi",
        "ARB": "arbitrum",
        "OP": "optimism",
        "IMX": "immutable-x",
        "USDT": "tether",
        "USDC": "usd-coin",
        "DAI": "dai",
        "BNB": "binancecoin",
        "SHIB": "shiba-inu",
        "PEPE": "pepe",
        "BONK": "bonk",
    }

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the API client.

        Args:
            config: Optional configuration dictionary with API keys
        """
        self.config = config or {}

        # CoinGecko API setup
        self.api_key = os.environ.get("COINGECKO_API_KEY") or self.config.get("api", {}).get("coingecko", {}).get(
            "api_key"
        )
        self.use_pro = self.api_key and self.config.get("api", {}).get("coingecko", {}).get("use_pro", False)

        self.base_url = self.COINGECKO_PRO_BASE if self.use_pro else self.COINGECKO_BASE

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.5  # seconds (CoinGecko free tier)
        self._retry_count = 0
        self._max_retries = 3

        # yfinance availability
        self._yfinance_available = None

        # Coin list cache
        self._coin_list_cache = None
        self._coin_list_timestamp = None

    def _check_yfinance(self) -> bool:
        """Check if yfinance is available."""
        if self._yfinance_available is None:
            try:
                import yfinance  # noqa: F401 — capability probe

                self._yfinance_available = True
            except ImportError:
                self._yfinance_available = False
        return self._yfinance_available

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Make HTTP request to CoinGecko API with error handling.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            RateLimitError: Rate limit exceeded
            NetworkError: Connection failed
            APIError: Other API errors
        """
        self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        headers = {}

        if self.api_key:
            if self.use_pro:
                headers["x-cg-pro-api-key"] = self.api_key
            else:
                headers["x-cg-demo-api-key"] = self.api_key

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after}s")

            if response.status_code == 404:
                raise SymbolNotFoundError("Resource not found")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection failed: {e}")
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")

    def _symbol_to_id(self, symbol: str) -> str:
        """
        Convert ticker symbol to CoinGecko ID.

        Args:
            symbol: Cryptocurrency ticker (e.g., "BTC")

        Returns:
            CoinGecko ID (e.g., "bitcoin")
        """
        symbol_upper = symbol.upper()

        # Check direct mapping
        if symbol_upper in self.SYMBOL_MAP:
            return self.SYMBOL_MAP[symbol_upper]

        # Assume lowercase symbol is the ID
        return symbol.lower()

    def list_coins(self, query: Optional[str] = None, limit: int = 100) -> List[dict]:
        """
        List available cryptocurrencies.

        Args:
            query: Optional search query
            limit: Maximum results to return

        Returns:
            List of coin info dictionaries
        """
        # Refresh coin list if stale (older than 1 hour)
        now = time.time()
        if self._coin_list_cache is None or self._coin_list_timestamp is None or now - self._coin_list_timestamp > 3600:
            try:
                self._coin_list_cache = self._make_request("/coins/list")
                self._coin_list_timestamp = now
            except APIError:
                # Return empty if we can't fetch
                return []

        coins = self._coin_list_cache

        # Filter by query
        if query:
            query_lower = query.lower()
            coins = [
                c
                for c in coins
                if (
                    query_lower in c.get("id", "").lower()
                    or query_lower in c.get("name", "").lower()
                    or query_lower in c.get("symbol", "").lower()
                )
            ]

        # Limit results
        return coins[:limit]

    def get_current_price(self, symbol: str, currency: str = "usd") -> dict:
        """
        Get current price for a cryptocurrency.

        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC") or CoinGecko ID
            currency: Fiat currency code (e.g., "usd")

        Returns:
            Price data dictionary
        """
        coin_id = self._symbol_to_id(symbol)

        try:
            data = self._make_request(
                f"/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "community_data": "false",
                    "developer_data": "false",
                    "sparkline": "false",
                },
            )

            market_data = data.get("market_data", {})
            current_price = market_data.get("current_price", {})
            price = current_price.get(currency.lower())

            if price is None:
                raise APIError(f"Price not available in {currency}")

            return PriceData(
                symbol=data.get("symbol", symbol).upper(),
                name=data.get("name", symbol),
                price=price,
                currency=currency.upper(),
                change_24h=market_data.get("price_change_percentage_24h"),
                change_7d=market_data.get("price_change_percentage_7d"),
                volume_24h=market_data.get("total_volume", {}).get(currency.lower()),
                market_cap=market_data.get("market_cap", {}).get(currency.lower()),
                source="coingecko",
            ).to_dict()

        except SymbolNotFoundError:
            # Try yfinance fallback
            if self._check_yfinance():
                return self._get_price_yfinance(symbol, currency)
            raise SymbolNotFoundError(f"Unknown symbol: {symbol}")

        except RateLimitError:
            # Try yfinance fallback
            if self._check_yfinance():
                return self._get_price_yfinance(symbol, currency)
            raise

    def _get_price_yfinance(self, symbol: str, currency: str = "usd") -> dict:
        """
        Get price using yfinance as fallback.

        Args:
            symbol: Cryptocurrency symbol
            currency: Fiat currency

        Returns:
            Price data dictionary
        """
        try:
            import yfinance as yf
        except ImportError:
            raise APIError("yfinance not installed")

        # yfinance uses format like "BTC-USD"
        ticker_symbol = f"{symbol.upper()}-{currency.upper()}"

        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            if not info or "regularMarketPrice" not in info:
                raise SymbolNotFoundError(f"Unknown symbol: {symbol}")

            return PriceData(
                symbol=symbol.upper(),
                name=info.get("shortName", symbol),
                price=info.get("regularMarketPrice", 0),
                currency=currency.upper(),
                change_24h=info.get("regularMarketChangePercent"),
                volume_24h=info.get("regularMarketVolume"),
                market_cap=info.get("marketCap"),
                source="yfinance",
            ).to_dict()

        except Exception as e:
            raise APIError(f"yfinance error: {e}")

    def get_historical_prices(
        self,
        symbol: str,
        currency: str = "usd",
        period: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[dict]:
        """
        Get historical OHLCV data.

        Args:
            symbol: Cryptocurrency symbol
            currency: Fiat currency
            period: Period string (e.g., "7d", "30d", "90d", "1y", "max")
            start_date: Custom start date
            end_date: Custom end date

        Returns:
            List of OHLCV data points
        """
        coin_id = self._symbol_to_id(symbol)

        # Convert period to days
        if period:
            period_map = {
                "1d": 1,
                "7d": 7,
                "14d": 14,
                "30d": 30,
                "60d": 60,
                "90d": 90,
                "180d": 180,
                "1y": 365,
                "2y": 730,
                "max": "max",
            }
            days = period_map.get(period.lower(), 30)
        elif start_date and end_date:
            days = (end_date - start_date).days
        else:
            days = 30

        try:
            # Use market_chart for period-based queries
            if isinstance(days, int):
                data = self._make_request(
                    f"/coins/{coin_id}/market_chart",
                    params={
                        "vs_currency": currency.lower(),
                        "days": days,
                        "interval": "daily" if days > 1 else "hourly",
                    },
                )

                prices = data.get("prices", [])
                volumes = data.get("total_volumes", [])

                results = []
                for i, (timestamp, price) in enumerate(prices):
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    vol = volumes[i][1] if i < len(volumes) else None

                    results.append(
                        {"date": dt.strftime("%Y-%m-%d"), "timestamp": timestamp, "price": price, "volume": vol}
                    )

                return results

            else:  # "max" period
                data = self._make_request(
                    f"/coins/{coin_id}/market_chart", params={"vs_currency": currency.lower(), "days": "max"}
                )

                prices = data.get("prices", [])
                results = []

                for timestamp, price in prices:
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    results.append({"date": dt.strftime("%Y-%m-%d"), "timestamp": timestamp, "price": price})

                return results

        except (RateLimitError, SymbolNotFoundError):
            # Try yfinance fallback
            if self._check_yfinance():
                return self._get_historical_yfinance(symbol, currency, period, start_date, end_date)
            raise

    def _get_historical_yfinance(
        self,
        symbol: str,
        currency: str = "usd",
        period: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[dict]:
        """
        Get historical data using yfinance.

        Args:
            symbol: Cryptocurrency symbol
            currency: Fiat currency
            period: Period string
            start_date: Start date
            end_date: End date

        Returns:
            List of OHLCV data points
        """
        try:
            import yfinance as yf
        except ImportError:
            raise APIError("yfinance not installed")

        ticker_symbol = f"{symbol.upper()}-{currency.upper()}"
        ticker = yf.Ticker(ticker_symbol)

        # Map period to yfinance format
        if period:
            yf_period_map = {
                "1d": "1d",
                "7d": "7d",
                "14d": "14d",
                "30d": "1mo",
                "60d": "2mo",
                "90d": "3mo",
                "180d": "6mo",
                "1y": "1y",
                "2y": "2y",
                "max": "max",
            }
            yf_period = yf_period_map.get(period.lower(), "1mo")
            df = ticker.history(period=yf_period)
        elif start_date and end_date:
            df = ticker.history(start=start_date, end=end_date)
        else:
            df = ticker.history(period="1mo")

        results = []
        for date, row in df.iterrows():
            results.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "open": row.get("Open"),
                    "high": row.get("High"),
                    "low": row.get("Low"),
                    "close": row.get("Close"),
                    "volume": row.get("Volume"),
                }
            )

        return results
