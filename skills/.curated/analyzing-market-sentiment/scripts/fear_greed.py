#!/usr/bin/env python3
"""
Fear & Greed Index Fetcher

Fetches the Crypto Fear & Greed Index from Alternative.me API.
Provides historical data and classification.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


class FearGreedFetcher:
    """Fetches Fear & Greed Index from Alternative.me API."""

    API_URL = "https://api.alternative.me/fng/"
    CACHE_FILE = Path(__file__).parent / ".fng_cache.json"
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, verbose: bool = False):
        """Initialize fetcher.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0

    def fetch(self, limit: int = 1) -> Optional[Dict[str, Any]]:
        """Fetch Fear & Greed Index data.

        Args:
            limit: Number of historical values to fetch (default: 1 for current)

        Returns:
            Dict with value, classification, timestamp, or None on error
        """
        # Check memory cache first
        if self._is_cache_valid():
            if self.verbose:
                print("Using memory cache for Fear & Greed Index", file=sys.stderr)
            return self._cache

        # Check file cache
        cached = self._load_file_cache()
        if cached:
            if self.verbose:
                print("Using file cache for Fear & Greed Index", file=sys.stderr)
            self._cache = cached
            self._cache_time = time.time()
            return cached

        # Fetch from API
        try:
            if self.verbose:
                print(f"Fetching Fear & Greed Index from {self.API_URL}", file=sys.stderr)

            response = requests.get(self.API_URL, params={"limit": limit}, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("metadata", {}).get("error"):
                if self.verbose:
                    print(f"API error: {data['metadata']['error']}", file=sys.stderr)
                return self._get_fallback()

            if not data.get("data"):
                if self.verbose:
                    print("No data in API response", file=sys.stderr)
                return self._get_fallback()

            # Parse current value
            current = data["data"][0]
            result = {
                "value": int(current.get("value", 50)),
                "classification": current.get("value_classification", "Neutral"),
                "timestamp": self._parse_timestamp(current.get("timestamp")),
                "time_until_update": current.get("time_until_update"),
                "source": "alternative.me",
            }

            # Add historical data if requested
            if limit > 1 and len(data["data"]) > 1:
                result["history"] = [
                    {
                        "value": int(item.get("value", 50)),
                        "classification": item.get("value_classification", "Neutral"),
                        "timestamp": self._parse_timestamp(item.get("timestamp")),
                    }
                    for item in data["data"][1:]
                ]

            # Update caches
            self._cache = result
            self._cache_time = time.time()
            self._save_file_cache(result)

            return result

        except requests.exceptions.Timeout:
            if self.verbose:
                print("API request timed out", file=sys.stderr)
            return self._get_fallback()
        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"API request failed: {e}", file=sys.stderr)
            return self._get_fallback()
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if self.verbose:
                print(f"Failed to parse API response: {e}", file=sys.stderr)
            return self._get_fallback()

    def fetch_historical(self, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch historical Fear & Greed data.

        Args:
            days: Number of days of history

        Returns:
            List of historical data points
        """
        result = self.fetch(limit=days)
        if not result:
            return []

        history = [
            {"value": result["value"], "classification": result["classification"], "timestamp": result["timestamp"]}
        ]

        if "history" in result:
            history.extend(result["history"])

        return history

    def get_average(self, days: int = 7) -> float:
        """Get average Fear & Greed value over specified days.

        Args:
            days: Number of days to average

        Returns:
            Average value (0-100)
        """
        history = self.fetch_historical(days)
        if not history:
            return 50.0

        values = [item["value"] for item in history]
        return sum(values) / len(values)

    def _is_cache_valid(self) -> bool:
        """Check if memory cache is still valid."""
        if self._cache is None:
            return False
        return (time.time() - self._cache_time) < self.CACHE_TTL

    def _load_file_cache(self) -> Optional[Dict[str, Any]]:
        """Load cached data from file."""
        try:
            if not self.CACHE_FILE.exists():
                return None

            with open(self.CACHE_FILE, "r") as f:
                data = json.load(f)

            # Check cache freshness
            cache_time = data.get("_cache_time", 0)
            if (time.time() - cache_time) > self.CACHE_TTL:
                return None

            return data.get("data")
        except Exception:
            return None

    def _save_file_cache(self, data: Dict[str, Any]) -> None:
        """Save data to file cache."""
        try:
            cache_data = {"_cache_time": time.time(), "data": data}
            with open(self.CACHE_FILE, "w") as f:
                json.dump(cache_data, f)
        except Exception:
            pass  # Cache write failure is non-fatal

    def _parse_timestamp(self, ts: Optional[str]) -> str:
        """Parse Unix timestamp to ISO format."""
        if not ts:
            return datetime.utcnow().isoformat() + "Z"
        try:
            dt = datetime.utcfromtimestamp(int(ts))
            return dt.isoformat() + "Z"
        except (ValueError, TypeError):
            return datetime.utcnow().isoformat() + "Z"

    def _get_fallback(self) -> Optional[Dict[str, Any]]:
        """Get fallback data when API is unavailable."""
        # Try file cache even if stale
        try:
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, "r") as f:
                    data = json.load(f)
                result = data.get("data", {})
                result["stale"] = True
                result["stale_reason"] = "API unavailable, using cached data"
                if self.verbose:
                    print("Using stale cache as fallback", file=sys.stderr)
                return result
        except Exception:
            pass

        # Return neutral fallback
        if self.verbose:
            print("Returning neutral fallback value", file=sys.stderr)
        return {
            "value": 50,
            "classification": "Neutral",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "fallback",
            "stale": True,
            "stale_reason": "API unavailable, no cache available",
        }


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Fear & Greed Index")
    parser.add_argument("--history", type=int, default=1, help="Days of history")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    fetcher = FearGreedFetcher(verbose=args.verbose)

    if args.history > 1:
        data = fetcher.fetch_historical(args.history)
        print(json.dumps(data, indent=2))
    else:
        data = fetcher.fetch()
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
