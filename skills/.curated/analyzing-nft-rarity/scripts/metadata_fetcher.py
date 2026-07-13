#!/usr/bin/env python3
"""
NFT Metadata Fetcher

Fetch NFT collection metadata from OpenSea, Alchemy, or direct contract.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import requests
except ImportError:
    requests = None


@dataclass
class Trait:
    """Single trait attribute."""

    trait_type: str
    value: str
    display_type: Optional[str] = None


@dataclass
class TokenData:
    """NFT token metadata."""

    token_id: int
    name: str
    description: str
    image_url: str
    attributes: List[Trait]
    external_url: Optional[str] = None


@dataclass
class CollectionData:
    """Collection metadata."""

    name: str
    slug: str
    contract_address: str
    total_supply: int
    description: str
    image_url: str
    tokens: List[TokenData]


# IPFS gateway fallbacks
IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs/",
    "https://gateway.pinata.cloud/ipfs/",
    "https://cloudflare-ipfs.com/ipfs/",
    "https://dweb.link/ipfs/",
]


class MetadataFetcher:
    """Fetch NFT metadata from multiple sources."""

    def __init__(self, opensea_api_key: str = None, alchemy_api_key: str = None, verbose: bool = False):
        """Initialize metadata fetcher.

        Args:
            opensea_api_key: OpenSea API key
            alchemy_api_key: Alchemy API key
            verbose: Enable verbose output
        """
        self.opensea_key = opensea_api_key or os.environ.get("OPENSEA_API_KEY", "")
        self.alchemy_key = alchemy_api_key or os.environ.get("ALCHEMY_API_KEY", "")
        self.verbose = verbose
        self.cache_dir = Path.home() / ".nft_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path."""
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def _load_cache(self, key: str, max_age: int = 3600) -> Optional[Dict]:
        """Load data from cache if fresh enough."""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text())
                if time.time() - data.get("timestamp", 0) < max_age:
                    return data.get("data")
            except (json.JSONDecodeError, IOError):
                pass  # Cache file corrupted or missing - fetch fresh data
        return None

    def _save_cache(self, key: str, data: Any) -> None:
        """Save data to cache."""
        cache_path = self._get_cache_path(key)
        try:
            cache_path.write_text(json.dumps({"timestamp": time.time(), "data": data}, indent=2))
        except IOError:
            pass  # Non-critical - cache save failed, will refetch next time

    def _resolve_ipfs(self, url: str) -> str:
        """Convert IPFS URL to HTTP gateway URL."""
        if not url:
            return url

        if url.startswith("ipfs://"):
            ipfs_hash = url[7:]
            return IPFS_GATEWAYS[0] + ipfs_hash

        if url.startswith("Qm") or url.startswith("baf"):
            return IPFS_GATEWAYS[0] + url

        return url

    def _fetch_with_ipfs_fallback(self, url: str) -> Optional[Dict]:
        """Fetch URL with IPFS gateway fallback."""
        if not requests:
            return None

        url = self._resolve_ipfs(url)

        # If it's an IPFS URL, try multiple gateways
        is_ipfs = any(gw in url for gw in IPFS_GATEWAYS)

        if is_ipfs:
            # Extract hash
            for gw in IPFS_GATEWAYS:
                if gw in url:
                    ipfs_hash = url.replace(gw, "")
                    break
            else:
                ipfs_hash = url

            for gateway in IPFS_GATEWAYS:
                try:
                    full_url = gateway + ipfs_hash
                    response = requests.get(full_url, timeout=10)
                    if response.status_code == 200:
                        return response.json()
                except Exception:
                    continue
            return None
        else:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception:
                return None

    def fetch_collection_opensea(self, slug: str, limit: int = 200) -> Optional[CollectionData]:
        """Fetch collection from OpenSea API.

        Args:
            slug: Collection slug (e.g., 'boredapeyachtclub')
            limit: Max tokens to fetch

        Returns:
            CollectionData or None
        """
        if not requests:
            raise ImportError("requests library required")

        cache_key = f"opensea_{slug}"
        cached = self._load_cache(cache_key, max_age=3600)
        if cached:
            return self._parse_collection_data(cached)

        headers = {}
        if self.opensea_key:
            headers["X-API-KEY"] = self.opensea_key

        try:
            # Fetch collection info
            col_url = f"https://api.opensea.io/api/v2/collections/{slug}"
            col_response = requests.get(col_url, headers=headers, timeout=30)
            col_response.raise_for_status()
            col_data = col_response.json()

            # Fetch NFTs
            nfts_url = f"https://api.opensea.io/api/v2/collection/{slug}/nfts"
            all_nfts = []
            next_cursor = None

            while len(all_nfts) < limit:
                params = {"limit": min(50, limit - len(all_nfts))}
                if next_cursor:
                    params["next"] = next_cursor

                nfts_response = requests.get(nfts_url, headers=headers, params=params, timeout=30)
                nfts_response.raise_for_status()
                nfts_data = nfts_response.json()

                all_nfts.extend(nfts_data.get("nfts", []))
                next_cursor = nfts_data.get("next")

                if not next_cursor:
                    break

                time.sleep(0.5)  # Rate limiting

            result = {"collection": col_data, "nfts": all_nfts}

            self._save_cache(cache_key, result)
            return self._parse_collection_data(result)

        except Exception as e:
            if self.verbose:
                print(f"OpenSea fetch error: {e}")
            return None

    def _parse_collection_data(self, data: Dict) -> CollectionData:
        """Parse API response into CollectionData."""
        col = data.get("collection", {})
        nfts = data.get("nfts", [])

        tokens = []
        for nft in nfts:
            try:
                token_id = int(nft.get("identifier", 0))
                attributes = []

                for trait in nft.get("traits", []):
                    attributes.append(
                        Trait(
                            trait_type=trait.get("trait_type", "Unknown"),
                            value=str(trait.get("value", "")),
                            display_type=trait.get("display_type"),
                        )
                    )

                tokens.append(
                    TokenData(
                        token_id=token_id,
                        name=nft.get("name", f"#{token_id}"),
                        description=nft.get("description", ""),
                        image_url=nft.get("image_url", ""),
                        attributes=attributes,
                        external_url=nft.get("external_url"),
                    )
                )
            except (ValueError, KeyError):
                continue

        # Note: If OpenSea doesn't provide total_supply, we fallback to len(tokens).
        # This may underestimate the actual supply if limit parameter restricted fetching.
        # For accurate rarity calculations on large collections, ensure you fetch enough tokens.
        reported_supply = col.get("total_supply")
        total_supply = int(reported_supply) if reported_supply else len(tokens)

        return CollectionData(
            name=col.get("name", "Unknown"),
            slug=col.get("collection", "unknown"),
            contract_address=col.get("contracts", [{}])[0].get("address", "") if col.get("contracts") else "",
            total_supply=total_supply,
            description=col.get("description", ""),
            image_url=col.get("image_url", ""),
            tokens=tokens,
        )

    def fetch_token_metadata(self, contract_address: str, token_id: int) -> Optional[TokenData]:
        """Fetch single token metadata from Alchemy.

        Args:
            contract_address: Contract address
            token_id: Token ID

        Returns:
            TokenData or None
        """
        if not requests or not self.alchemy_key:
            return None

        cache_key = f"token_{contract_address}_{token_id}"
        cached = self._load_cache(cache_key, max_age=86400)  # 24h cache
        if cached:
            return self._parse_token_data(cached, token_id)

        try:
            url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{self.alchemy_key}/getNFTMetadata"
            params = {
                "contractAddress": contract_address,
                "tokenId": str(token_id),
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            self._save_cache(cache_key, data)
            return self._parse_token_data(data, token_id)

        except Exception as e:
            if self.verbose:
                print(f"Alchemy fetch error: {e}")
            return None

    def _parse_token_data(self, data: Dict, token_id: int) -> TokenData:
        """Parse Alchemy response into TokenData."""
        metadata = data.get("metadata", {})
        attributes = []

        for attr in metadata.get("attributes", []):
            attributes.append(
                Trait(
                    trait_type=attr.get("trait_type", "Unknown"),
                    value=str(attr.get("value", "")),
                    display_type=attr.get("display_type"),
                )
            )

        return TokenData(
            token_id=token_id,
            name=data.get("title", metadata.get("name", f"#{token_id}")),
            description=data.get("description", metadata.get("description", "")),
            image_url=data.get("media", [{}])[0].get("gateway", metadata.get("image", "")),
            attributes=attributes,
            external_url=metadata.get("external_url"),
        )

    def clear_cache(self, pattern: str = None) -> int:
        """Clear cache files.

        Args:
            pattern: Optional pattern to match (e.g., 'opensea')

        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            if pattern is None or pattern in cache_file.name:
                cache_file.unlink()
                count += 1
        return count


def main():
    """CLI entry point for testing."""
    fetcher = MetadataFetcher(verbose=True)

    print("=== NFT Metadata Fetcher ===")
    print(f"Cache directory: {fetcher.cache_dir}")

    # Test with a known collection
    print("\nFetching sample collection (pudgypenguins)...")
    collection = fetcher.fetch_collection_opensea("pudgypenguins", limit=10)

    if collection:
        print(f"\nCollection: {collection.name}")
        print(f"Total Supply: {collection.total_supply}")
        print(f"Fetched: {len(collection.tokens)} tokens")

        if collection.tokens:
            token = collection.tokens[0]
            print(f"\nSample Token: {token.name}")
            print(f"Attributes: {len(token.attributes)}")
            for attr in token.attributes[:5]:
                print(f"  - {attr.trait_type}: {attr.value}")
    else:
        print("Failed to fetch collection (API key may be required)")


if __name__ == "__main__":
    main()
