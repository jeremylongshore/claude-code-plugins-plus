#!/usr/bin/env python3
"""
DEX Factory Addresses

Factory contract addresses for detecting new pairs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

from dataclasses import dataclass
from typing import Dict, List

# PairCreated event signature for Uniswap V2 style
PAIR_CREATED_TOPIC = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"


@dataclass
class DexFactory:
    """DEX factory configuration."""

    name: str
    address: str
    version: str  # v2 or v3
    pair_created_topic: str


@dataclass
class ChainConfig:
    """Chain configuration."""

    name: str
    chain_id: int
    rpc_url: str
    native_symbol: str
    wrapped_native: str
    block_time: float
    explorer_url: str


# Chain configurations
CHAINS: Dict[str, ChainConfig] = {
    "ethereum": ChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
        native_symbol="ETH",
        wrapped_native="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        block_time=12.0,
        explorer_url="https://etherscan.io",
    ),
    "bsc": ChainConfig(
        name="BNB Chain",
        chain_id=56,
        rpc_url="https://bsc-dataseed1.binance.org",
        native_symbol="BNB",
        wrapped_native="0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        block_time=3.0,
        explorer_url="https://bscscan.com",
    ),
    "arbitrum": ChainConfig(
        name="Arbitrum One",
        chain_id=42161,
        rpc_url="https://arb1.arbitrum.io/rpc",
        native_symbol="ETH",
        wrapped_native="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        block_time=0.25,
        explorer_url="https://arbiscan.io",
    ),
    "base": ChainConfig(
        name="Base",
        chain_id=8453,
        rpc_url="https://mainnet.base.org",
        native_symbol="ETH",
        wrapped_native="0x4200000000000000000000000000000000000006",
        block_time=2.0,
        explorer_url="https://basescan.org",
    ),
    "polygon": ChainConfig(
        name="Polygon",
        chain_id=137,
        rpc_url="https://polygon-rpc.com",
        native_symbol="MATIC",
        wrapped_native="0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        block_time=2.0,
        explorer_url="https://polygonscan.com",
    ),
}


# DEX factory addresses per chain
DEX_FACTORIES: Dict[str, Dict[str, DexFactory]] = {
    "ethereum": {
        "uniswap_v2": DexFactory(
            name="Uniswap V2",
            address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
            version="v2",
            pair_created_topic=PAIR_CREATED_TOPIC,
        ),
        "uniswap_v3": DexFactory(
            name="Uniswap V3",
            address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
            version="v3",
            pair_created_topic="0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
        ),
        "sushiswap": DexFactory(
            name="SushiSwap",
            address="0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
            version="v2",
            pair_created_topic=PAIR_CREATED_TOPIC,
        ),
    },
    "bsc": {
        "pancakeswap_v2": DexFactory(
            name="PancakeSwap V2",
            address="0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
            version="v2",
            pair_created_topic=PAIR_CREATED_TOPIC,
        ),
        "pancakeswap_v3": DexFactory(
            name="PancakeSwap V3",
            address="0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
            version="v3",
            pair_created_topic="0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
        ),
    },
    "arbitrum": {
        "uniswap_v3": DexFactory(
            name="Uniswap V3",
            address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
            version="v3",
            pair_created_topic="0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
        ),
        "camelot": DexFactory(
            name="Camelot",
            address="0x6EcCab422D763aC031210895C81787E87B43A652",
            version="v2",
            pair_created_topic=PAIR_CREATED_TOPIC,
        ),
        "sushiswap": DexFactory(
            name="SushiSwap",
            address="0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
            version="v2",
            pair_created_topic=PAIR_CREATED_TOPIC,
        ),
    },
    "base": {
        "uniswap_v3": DexFactory(
            name="Uniswap V3",
            address="0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
            version="v3",
            pair_created_topic="0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
        ),
        "aerodrome": DexFactory(
            name="Aerodrome",
            address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da",
            version="v2",
            pair_created_topic=PAIR_CREATED_TOPIC,
        ),
    },
    "polygon": {
        "uniswap_v3": DexFactory(
            name="Uniswap V3",
            address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
            version="v3",
            pair_created_topic="0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
        ),
        "quickswap": DexFactory(
            name="QuickSwap",
            address="0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
            version="v2",
            pair_created_topic=PAIR_CREATED_TOPIC,
        ),
        "sushiswap": DexFactory(
            name="SushiSwap",
            address="0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
            version="v2",
            pair_created_topic=PAIR_CREATED_TOPIC,
        ),
    },
}


# Common stablecoins per chain (for base pair detection)
STABLECOINS: Dict[str, List[str]] = {
    "ethereum": [
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        "0x6B175474E89094C44Da98b954E2deC563975aA61",  # DAI
    ],
    "bsc": [
        "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",  # USDC
        "0x55d398326f99059fF775485246999027B3197955",  # USDT
        "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",  # BUSD
    ],
    "arbitrum": [
        "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC.e
        "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # USDC
        "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",  # USDT
    ],
    "base": [
        "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
        "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",  # USDbC
    ],
    "polygon": [
        "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC
        "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # USDT
        "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",  # DAI
    ],
}


def get_chain_config(chain: str) -> ChainConfig:
    """Get chain configuration."""
    chain = chain.lower()
    if chain not in CHAINS:
        raise ValueError(f"Unsupported chain: {chain}. Supported: {list(CHAINS.keys())}")
    return CHAINS[chain]


def get_dex_factories(chain: str) -> Dict[str, DexFactory]:
    """Get DEX factories for a chain."""
    chain = chain.lower()
    return DEX_FACTORIES.get(chain, {})


def get_all_factory_addresses(chain: str) -> List[str]:
    """Get all factory addresses for a chain."""
    factories = get_dex_factories(chain)
    return [f.address.lower() for f in factories.values()]


def identify_dex(chain: str, factory_address: str) -> str:
    """Identify DEX by factory address."""
    factories = get_dex_factories(chain)
    factory_address = factory_address.lower()

    for name, factory in factories.items():
        if factory.address.lower() == factory_address:
            return factory.name

    return "Unknown DEX"


def is_base_token(chain: str, address: str) -> bool:
    """Check if address is a base token (stablecoin or wrapped native)."""
    address = address.lower()
    chain_config = get_chain_config(chain)

    if address == chain_config.wrapped_native.lower():
        return True

    stables = STABLECOINS.get(chain, [])
    return address in [s.lower() for s in stables]


def main():
    """CLI entry point for testing."""
    print("=== Supported Chains ===")
    for chain_id, config in CHAINS.items():
        print(f"  {chain_id}: {config.name} (Chain ID: {config.chain_id})")

    print("\n=== DEX Factories ===")
    for chain_id, factories in DEX_FACTORIES.items():
        print(f"\n{chain_id.upper()}:")
        for name, factory in factories.items():
            print(f"  {factory.name} ({factory.version}): {factory.address[:20]}...")


if __name__ == "__main__":
    main()
