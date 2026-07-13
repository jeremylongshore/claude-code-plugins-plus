#!/usr/bin/env python3
"""
Cache Manager - TTL-Based Caching for Price Data

Provides intelligent caching with configurable TTL for spot prices
and historical data to minimize API calls and improve response times.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import threading


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""

    data: Any
    timestamp: float
    ttl: int
    key: str

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl

    @property
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {"data": self.data, "timestamp": self.timestamp, "ttl": self.ttl, "key": self.key}

    @classmethod
    def from_dict(cls, d: dict) -> "CacheEntry":
        """Create CacheEntry from dictionary."""
        return cls(data=d["data"], timestamp=d["timestamp"], ttl=d["ttl"], key=d["key"])


class CacheManager:
    """
    TTL-based cache manager for cryptocurrency price data.

    Features:
    - Separate TTLs for spot prices (short) and historical data (long)
    - File-based persistence
    - Thread-safe operations
    - Automatic cleanup of expired entries
    - Stale data access for fallback scenarios
    """

    def __init__(self, cache_dir: Optional[Path] = None, spot_ttl: int = 30, historical_ttl: int = 3600):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory for cache files (default: ./data)
            spot_ttl: TTL for spot prices in seconds (default: 30)
            historical_ttl: TTL for historical data in seconds (default: 3600)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./data")
        self.spot_ttl = spot_ttl
        self.historical_ttl = historical_ttl

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

        # File paths
        self._spot_cache_file = self.cache_dir / "spot_cache.json"
        self._historical_cache_file = self.cache_dir / "historical_cache.json"

        # Load existing cache
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk."""
        with self._lock:
            # Load spot cache
            if self._spot_cache_file.exists():
                try:
                    with open(self._spot_cache_file, "r") as f:
                        data = json.load(f)
                        for key, entry_data in data.items():
                            entry = CacheEntry.from_dict(entry_data)
                            if not entry.is_expired:
                                self._memory_cache[key] = entry
                except (json.JSONDecodeError, KeyError):
                    pass

            # Load historical cache
            if self._historical_cache_file.exists():
                try:
                    with open(self._historical_cache_file, "r") as f:
                        data = json.load(f)
                        for key, entry_data in data.items():
                            entry = CacheEntry.from_dict(entry_data)
                            if not entry.is_expired:
                                self._memory_cache[key] = entry
                except (json.JSONDecodeError, KeyError):
                    pass

    def _save_cache(self) -> None:
        """Persist cache to disk."""
        with self._lock:
            spot_data = {}
            historical_data = {}

            for key, entry in self._memory_cache.items():
                if key.startswith("spot:"):
                    spot_data[key] = entry.to_dict()
                elif key.startswith("hist:"):
                    historical_data[key] = entry.to_dict()

            # Write spot cache
            try:
                with open(self._spot_cache_file, "w") as f:
                    json.dump(spot_data, f, indent=2)
            except IOError:
                pass

            # Write historical cache
            try:
                with open(self._historical_cache_file, "w") as f:
                    json.dump(historical_data, f, indent=2)
            except IOError:
                pass

    def _make_key(self, prefix: str, *parts: str) -> str:
        """
        Create a cache key from parts.

        Args:
            prefix: Key prefix (e.g., "spot", "hist")
            *parts: Key components

        Returns:
            Cache key string
        """
        key_str = ":".join([prefix] + [str(p).lower() for p in parts])
        return key_str

    def get_spot_price(self, symbol: str, currency: str, allow_stale: bool = False) -> Optional[dict]:
        """
        Get cached spot price.

        Args:
            symbol: Cryptocurrency symbol
            currency: Fiat currency
            allow_stale: Return stale data if no fresh data available

        Returns:
            Cached price data or None
        """
        key = self._make_key("spot", symbol, currency)

        with self._lock:
            entry = self._memory_cache.get(key)

            if entry is None:
                return None

            if entry.is_expired:
                if allow_stale:
                    # Return stale data with warning flag
                    data = entry.data.copy() if isinstance(entry.data, dict) else entry.data
                    if isinstance(data, dict):
                        data["_cache_stale"] = True
                        data["_cache_age"] = entry.age
                    return data
                return None

            data = entry.data.copy() if isinstance(entry.data, dict) else entry.data
            if isinstance(data, dict):
                data["_cached"] = True
                data["_cache_age"] = entry.age
            return data

    def set_spot_price(self, symbol: str, currency: str, data: dict) -> None:
        """
        Cache spot price data.

        Args:
            symbol: Cryptocurrency symbol
            currency: Fiat currency
            data: Price data to cache
        """
        key = self._make_key("spot", symbol, currency)

        with self._lock:
            self._memory_cache[key] = CacheEntry(data=data, timestamp=time.time(), ttl=self.spot_ttl, key=key)
            self._save_cache()

    def get_historical(self, cache_key: str, allow_stale: bool = False) -> Optional[List[dict]]:
        """
        Get cached historical data.

        Args:
            cache_key: Unique key for the historical query
            allow_stale: Return stale data if no fresh data available

        Returns:
            Cached historical data or None
        """
        key = self._make_key("hist", cache_key)

        with self._lock:
            entry = self._memory_cache.get(key)

            if entry is None:
                return None

            if entry.is_expired:
                if allow_stale:
                    return entry.data
                return None

            return entry.data

    def set_historical(self, cache_key: str, data: List[dict]) -> None:
        """
        Cache historical data.

        Args:
            cache_key: Unique key for the historical query
            data: Historical data to cache
        """
        key = self._make_key("hist", cache_key)

        with self._lock:
            self._memory_cache[key] = CacheEntry(data=data, timestamp=time.time(), ttl=self.historical_ttl, key=key)
            self._save_cache()

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Key pattern to match (None = all)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if pattern is None:
                count = len(self._memory_cache)
                self._memory_cache.clear()
            else:
                pattern_lower = pattern.lower()
                keys_to_remove = [k for k in self._memory_cache if pattern_lower in k.lower()]
                count = len(keys_to_remove)
                for key in keys_to_remove:
                    del self._memory_cache[key]

            self._save_cache()
            return count

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._memory_cache.clear()

            # Remove cache files
            if self._spot_cache_file.exists():
                self._spot_cache_file.unlink()
            if self._historical_cache_file.exists():
                self._historical_cache_file.unlink()

    def cleanup(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [k for k, v in self._memory_cache.items() if v.is_expired]
            for key in expired_keys:
                del self._memory_cache[key]

            if expired_keys:
                self._save_cache()

            return len(expired_keys)

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            spot_entries = [e for k, e in self._memory_cache.items() if k.startswith("spot:")]
            hist_entries = [e for k, e in self._memory_cache.items() if k.startswith("hist:")]

            spot_expired = sum(1 for e in spot_entries if e.is_expired)
            hist_expired = sum(1 for e in hist_entries if e.is_expired)

            return {
                "total_entries": len(self._memory_cache),
                "spot_entries": len(spot_entries),
                "spot_expired": spot_expired,
                "historical_entries": len(hist_entries),
                "historical_expired": hist_expired,
                "cache_dir": str(self.cache_dir),
                "spot_ttl": self.spot_ttl,
                "historical_ttl": self.historical_ttl,
            }

    def get_all_symbols(self) -> List[str]:
        """
        Get all symbols currently in cache.

        Returns:
            List of cached symbols
        """
        with self._lock:
            symbols = set()
            for key in self._memory_cache.keys():
                if key.startswith("spot:"):
                    parts = key.split(":")
                    if len(parts) >= 2:
                        symbols.add(parts[1].upper())
            return sorted(list(symbols))
