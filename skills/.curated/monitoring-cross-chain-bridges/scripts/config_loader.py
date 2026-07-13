#!/usr/bin/env python3
"""
Configuration Loader

Load settings from settings.yaml for bridge monitor.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


# Default configuration as fallback
DEFAULT_CONFIG = {
    "apis": {
        "defillama": {
            "base_url": "https://bridges.llama.fi",
        },
        "wormhole": {
            "base_url": "https://api.wormholescan.io/api/v1",
        },
        "layerzero": {
            "base_url": "https://scan.layerzero.network/api",
        },
        "across": {
            "base_url": "https://across.to/api",
        },
    },
    "chains": {
        "ethereum": {"rpc_url": "https://eth.llamarpc.com"},
        "bsc": {"rpc_url": "https://bsc-dataseed1.binance.org"},
        "polygon": {"rpc_url": "https://polygon-rpc.com"},
        "arbitrum": {"rpc_url": "https://arb1.arbitrum.io/rpc"},
        "optimism": {"rpc_url": "https://mainnet.optimism.io"},
        "base": {"rpc_url": "https://mainnet.base.org"},
        "avalanche": {"rpc_url": "https://api.avax.network/ext/bc/C/rpc"},
    },
    "cache": {
        "bridge_list_ttl": 3600,
        "tvl_data_ttl": 300,
        "tx_status_ttl": 30,
    },
}


_config: Optional[Dict[str, Any]] = None


def _find_config_file() -> Optional[Path]:
    """Find the settings.yaml config file."""
    # Try relative to this script
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "config" / "settings.yaml"
    if config_path.exists():
        return config_path

    # Try current directory
    cwd_config = Path("config/settings.yaml")
    if cwd_config.exists():
        return cwd_config

    return None


def load_config() -> Dict[str, Any]:
    """Load configuration from settings.yaml.

    Returns:
        Configuration dictionary
    """
    global _config

    if _config is not None:
        return _config

    if not yaml:
        _config = DEFAULT_CONFIG
        return _config

    config_path = _find_config_file()
    if config_path is None:
        _config = DEFAULT_CONFIG
        return _config

    try:
        with open(config_path, "r") as f:
            _config = yaml.safe_load(f)
        return _config
    except (OSError, yaml.YAMLError):
        _config = DEFAULT_CONFIG
        return _config


def get_api_base_url(api_name: str) -> str:
    """Get API base URL from config.

    Args:
        api_name: API name (defillama, wormhole, layerzero, across)

    Returns:
        Base URL string
    """
    config = load_config()
    apis = config.get("apis", {})
    api_config = apis.get(api_name, {})
    return api_config.get("base_url", DEFAULT_CONFIG["apis"].get(api_name, {}).get("base_url", ""))


def get_chain_rpc_url(chain: str) -> Optional[str]:
    """Get RPC URL for a chain from config.

    Args:
        chain: Chain name (ethereum, bsc, polygon, etc.)

    Returns:
        RPC URL string or None
    """
    # Environment variable takes precedence
    env_url = os.environ.get(f"{chain.upper()}_RPC_URL")
    if env_url:
        return env_url

    config = load_config()
    chains = config.get("chains", {})
    chain_config = chains.get(chain.lower(), {})
    return chain_config.get("rpc_url")


def get_all_chain_rpcs() -> Dict[str, str]:
    """Get all chain RPC URLs from config.

    Returns:
        Dict mapping chain name to RPC URL
    """
    config = load_config()
    chains = config.get("chains", {})
    return {
        chain: chain_config.get("rpc_url", "") for chain, chain_config in chains.items() if chain_config.get("rpc_url")
    }


def get_cache_ttl(cache_type: str) -> int:
    """Get cache TTL in seconds.

    Args:
        cache_type: Type of cache (bridge_list_ttl, tvl_data_ttl, tx_status_ttl)

    Returns:
        TTL in seconds
    """
    config = load_config()
    cache = config.get("cache", {})
    return cache.get(cache_type, DEFAULT_CONFIG["cache"].get(cache_type, 300))


if __name__ == "__main__":
    print("=== Config Loader Test ===")
    print(f"DefiLlama URL: {get_api_base_url('defillama')}")
    print(f"Wormhole URL: {get_api_base_url('wormhole')}")
    print(f"Ethereum RPC: {get_chain_rpc_url('ethereum')}")
    print(f"All chains: {list(get_all_chain_rpcs().keys())}")
