#!/usr/bin/env python3
"""
Feed Fetcher - Parallel RSS Feed Fetching

Fetch multiple RSS feeds in parallel with timeout handling and caching.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import sys
import hashlib
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


class FeedFetcher:
    """Fetch multiple RSS feeds in parallel with caching."""

    def __init__(
        self,
        timeout: int = 10,
        max_workers: int = 10,
        cache_ttl: int = 300,  # 5 minutes
        verbose: bool = False,
    ):
        """
        Initialize feed fetcher.

        Args:
            timeout: Request timeout in seconds
            max_workers: Max parallel requests
            cache_ttl: Cache time-to-live in seconds
            verbose: Enable verbose logging
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl
        self.verbose = verbose
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_all(self, sources: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Fetch all RSS feeds in parallel.

        Args:
            sources: List of source dictionaries with 'name' and 'url'

        Returns:
            Dictionary mapping source name to feed content
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_source = {executor.submit(self._fetch_one, source): source for source in sources}

            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    content = future.result()
                    if content:
                        results[source["name"]] = content
                except Exception as e:
                    if self.verbose:
                        print(f"Error fetching {source['name']}: {e}", file=sys.stderr)

        return results

    def _fetch_one(self, source: Dict[str, Any]) -> Optional[str]:
        """
        Fetch a single RSS feed.

        Args:
            source: Source dictionary with 'name' and 'url'

        Returns:
            Feed content string or None if failed
        """
        name = source.get("name", "unknown")
        url = source.get("url", "")

        if not url:
            return None

        # Check cache first
        cached = self._get_cached(url)
        if cached:
            if self.verbose:
                print(f"  Cache hit: {name}", file=sys.stderr)
            return cached

        # Fetch from network
        try:
            if self.verbose:
                print(f"  Fetching: {name}", file=sys.stderr)

            headers = {
                "User-Agent": "CryptoNewsAggregator/2.0 (RSS Feed Reader)",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            }

            response = requests.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()

            content = response.text

            # Cache the response
            self._set_cached(url, content)

            return content

        except requests.exceptions.Timeout:
            if self.verbose:
                print(f"  Timeout: {name}", file=sys.stderr)
            return None
        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"  Error: {name} - {e}", file=sys.stderr)
            return None

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def _get_cached(self, url: str) -> Optional[str]:
        """Get cached content if valid."""
        cache_path = self._get_cache_path(url)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                cached = json.load(f)

            # Check if expired
            cached_time = datetime.fromisoformat(cached.get("timestamp", ""))
            if datetime.utcnow() - cached_time > timedelta(seconds=self.cache_ttl):
                return None

            return cached.get("content")

        except Exception:
            return None

    def _set_cached(self, url: str, content: str) -> None:
        """Cache content for URL."""
        cache_path = self._get_cache_path(url)

        try:
            with open(cache_path, "w") as f:
                json.dump({"url": url, "timestamp": datetime.utcnow().isoformat(), "content": content}, f)
        except Exception:
            pass

    def clear_cache(self) -> int:
        """Clear all cached feeds. Returns count of files deleted."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception:
                pass
        return count
