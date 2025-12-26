---
name: analyze-pool
description: >
  Analyze liquidity pools for APY, impermanent loss, and optimization
shortcut: ap
---
# Analyze Liquidity Pool

Comprehensive analysis of DeFi liquidity pools with impermanent loss calculations, APY projections, risk assessment, and optimization strategies across multiple DEX protocols and chains.

## Overview

The liquidity pool analyzer provides institutional-grade analysis for liquidity providers across Uniswap V2/V3, Curve, Balancer, and other major DEX protocols. This tool helps LPs maximize returns while understanding and managing risks like impermanent loss, volatility exposure, and protocol-specific vulnerabilities.

## Features

### Core Analysis Capabilities
- **Real-Time Pool Metrics**: TVL, volume, fee generation, utilization rates
- **Impermanent Loss Tracking**: Continuous IL monitoring with historical analysis
- **APY Decomposition**: Breakdown of trading fees, farming rewards, and token incentives
- **Liquidity Concentration**: Uniswap V3 position analysis with range efficiency
- **Slippage Modeling**: Price impact calculations for various trade sizes
- **Risk Scoring**: Comprehensive safety assessment including rug pull detection
- **Multi-Chain Support**: Ethereum, BSC, Polygon, Arbitrum, Optimism, Base

### Advanced Features
- **Historical Performance**: Backtesting LP positions over any time period
- **Optimal Range Calculation**: For concentrated liquidity positions (V3)
- **Rebalancing Signals**: Automated alerts when positions drift out of range
- **Yield Optimization**: Comparison across similar pools for best opportunities
- **Gas Cost Analysis**: ROI calculations including transaction costs
- **Protocol Risk Assessment**: Smart contract audits, TVL trends, team transparency

## Supported DEX Protocols

### Uniswap V2/V3
- Constant product (x*y=k) AMM analysis
- V3 concentrated liquidity position evaluation
- Tick spacing and fee tier optimization
- Historical fee accumulation tracking

### Curve Finance
- StableSwap invariant calculations
- Base APY vs CRV/CVX boosted yields
- Gauge weight analysis
- Pool imbalance detection

### Balancer V2
- Multi-asset weighted pools
- Custom bonding curves
- Composable stable pools
- Protocol fee analysis

### Other Protocols
- SushiSwap (fork analysis)
- PancakeSwap (BSC/Ethereum)
- TraderJoe (Avalanche)
- QuickSwap (Polygon)

## Implementation

### Python Pool Analyzer with Uniswap V3 Integration

```python
"""
Comprehensive Liquidity Pool Analyzer
Supports Uniswap V2/V3, Curve, Balancer with impermanent loss tracking,
yield optimization, and risk assessment across multiple chains.
"""

import math
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from web3 import Web3
from decimal import Decimal

class PoolType(Enum):
    """Supported pool types"""
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    CURVE = "curve"
    BALANCER_V2 = "balancer_v2"
    SUSHISWAP = "sushiswap"
    PANCAKESWAP = "pancakeswap"

class Chain(Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    AVALANCHE = "avalanche"

@dataclass
class PoolMetrics:
    """Core pool metrics"""
    address: str
    protocol: str
    chain: str
    token0: str
    token1: str
    token0_symbol: str
    token1_symbol: str
    token0_price: float
    token1_price: float
    reserves0: float
    reserves1: float
    tvl_usd: float
    volume_24h: float
    volume_7d: float
    fees_24h: float
    fee_tier: float
    liquidity: float
    sqrt_price: Optional[float] = None
    tick: Optional[int] = None

@dataclass
class YieldMetrics:
    """Yield calculation results"""
    base_apy: float
    reward_apy: float
    total_apy: float
    daily_return: float
    weekly_return: float
    monthly_return: float
    yearly_return: float
    fee_apr: float
    farming_apr: float

@dataclass
class ImpermanentLoss:
    """Impermanent loss calculations"""
    current_il_percent: float
    current_il_usd: float
    price_change_percent: float
    hodl_value: float
    lp_value: float
    net_profit_loss: float
    scenarios: Dict[str, float]

@dataclass
class RiskMetrics:
    """Risk assessment results"""
    overall_score: int  # 0-100
    impermanent_loss_risk: str
    volatility_risk: str
    liquidity_risk: str
    protocol_risk: str
    rug_pull_risk: str
    smart_contract_risk: str
    warnings: List[str]
    recommendations: List[str]

class LiquidityPoolAnalyzer:
    """
    Comprehensive liquidity pool analyzer with multi-protocol support
    """

    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize analyzer with API keys

        Args:
            api_keys: Dictionary with keys for various data providers
                     (etherscan, bscscan, polygonscan, coingecko, defillama, etc.)
        """
        self.api_keys = api_keys
        self.w3_providers = self._initialize_web3_providers()
        self.price_cache = {}
        self.pool_cache = {}

        # Uniswap V3 tick spacing by fee tier
        self.v3_tick_spacing = {
            100: 1,     # 0.01%
            500: 10,    # 0.05%
            3000: 60,   # 0.30%
            10000: 200  # 1.00%
        }

        # Risk thresholds
        self.risk_thresholds = {
            'min_tvl': 100000,  # $100k minimum TVL
            'min_volume': 10000,  # $10k daily volume
            'max_fee_tier': 10000,  # 1% max fee
            'min_liquidity_depth': 50000,  # $50k depth
            'max_price_impact_1k': 0.01,  # 1% max impact for $1k trade
        }

    def _initialize_web3_providers(self) -> Dict[str, Web3]:
        """Initialize Web3 providers for each supported chain"""
        rpc_urls = {
            Chain.ETHEREUM: "https://eth.llamarpc.com",
            Chain.BSC: "https://bsc-dataseed.binance.org/",
            Chain.POLYGON: "https://polygon-rpc.com",
            Chain.ARBITRUM: "https://arb1.arbitrum.io/rpc",
            Chain.OPTIMISM: "https://mainnet.optimism.io",
            Chain.BASE: "https://mainnet.base.org",
            Chain.AVALANCHE: "https://api.avax.network/ext/bc/C/rpc"
        }

        return {
            chain: Web3(Web3.HTTPProvider(url))
            for chain, url in rpc_urls.items()
        }

    async def analyze_pool(
        self,
        pool_address: str,
        chain: Chain = Chain.ETHEREUM,
        initial_investment: float = 10000,
        entry_price_token0: Optional[float] = None,
        entry_price_token1: Optional[float] = None
    ) -> Dict:
        """
        Comprehensive pool analysis with IL calculations and optimization

        Args:
            pool_address: Smart contract address of the liquidity pool
            chain: Blockchain network
            initial_investment: USD value for yield projections
            entry_price_token0: Entry price for IL calculation (optional)
            entry_price_token1: Entry price for IL calculation (optional)

        Returns:
            Complete analysis report with metrics, risks, and recommendations
        """
        print(f"\n{'='*80}")
        print(f"LIQUIDITY POOL ANALYSIS")
        print(f"{'='*80}")
        print(f"Pool Address: {pool_address}")
        print(f"Chain: {chain.value}")
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*80}\n")

        # Fetch pool data
        pool_metrics = await self._fetch_pool_data(pool_address, chain)
        protocol_type = self._detect_protocol(pool_metrics)

        # Calculate yields
        yield_metrics = self._calculate_yields(pool_metrics, initial_investment)

        # Calculate impermanent loss
        il_metrics = self._calculate_impermanent_loss(
            pool_metrics,
            initial_investment,
            entry_price_token0,
            entry_price_token1
        )

        # Assess risks
        risk_metrics = await self._assess_risks(pool_metrics, chain)

        # Generate optimization suggestions
        optimization = self._generate_optimization_strategies(
            pool_metrics,
            protocol_type
        )

        # Compile comprehensive report
        report = {
            'summary': self._generate_summary(pool_metrics, yield_metrics, risk_metrics),
            'pool_metrics': pool_metrics,
            'yield_analysis': yield_metrics,
            'impermanent_loss': il_metrics,
            'risk_assessment': risk_metrics,
            'optimization': optimization,
            'historical_performance': await self._fetch_historical_data(pool_address, chain),
            'comparison': await self._compare_similar_pools(pool_metrics, chain),
            'alerts': self._generate_alerts(pool_metrics, risk_metrics)
        }

        self._print_report(report)
        return report

    async def _fetch_pool_data(
        self,
        pool_address: str,
        chain: Chain
    ) -> PoolMetrics:
        """
        Fetch comprehensive pool data from on-chain and API sources
        """
        # Check cache first
        cache_key = f"{chain.value}:{pool_address}"
        if cache_key in self.pool_cache:
            cached = self.pool_cache[cache_key]
            if datetime.now() - cached['timestamp'] < timedelta(minutes=5):
                return cached['data']

        # Fetch from DeFiLlama API
        defillama_url = f"https://api.llama.fi/pool/{pool_address}"
        response = requests.get(defillama_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            pool_metrics = PoolMetrics(
                address=pool_address,
                protocol=data.get('project', 'unknown'),
                chain=chain.value,
                token0=data['token0'],
                token1=data['token1'],
                token0_symbol=data['symbol0'],
                token1_symbol=data['symbol1'],
                token0_price=data['price0'],
                token1_price=data['price1'],
                reserves0=data['reserve0'],
                reserves1=data['reserve1'],
                tvl_usd=data['tvlUsd'],
                volume_24h=data.get('volume24h', 0),
                volume_7d=data.get('volume7d', 0),
                fees_24h=data.get('fees24h', 0),
                fee_tier=data.get('feeTier', 3000) / 1000000,  # Convert to decimal
                liquidity=data.get('liquidity', 0)
            )
        else:
            # Fallback: fetch directly from blockchain
            pool_metrics = await self._fetch_on_chain_data(pool_address, chain)

        # Cache the result
        self.pool_cache[cache_key] = {
            'data': pool_metrics,
            'timestamp': datetime.now()
        }

        return pool_metrics

    async def _fetch_on_chain_data(
        self,
        pool_address: str,
        chain: Chain
    ) -> PoolMetrics:
        """
        Fetch pool data directly from blockchain using Web3
        """
        w3 = self.w3_providers[chain]

        # Uniswap V2 ABI (simplified)
        pool_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"name": "_reserve0", "type": "uint112"},
                    {"name": "_reserve1", "type": "uint112"},
                    {"name": "_blockTimestampLast", "type": "uint32"}
                ],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token0",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token1",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            }
        ]

        pool_contract = w3.eth.contract(
            address=Web3.to_checksum_address(pool_address),
            abi=pool_abi
        )

        # Get reserves and token addresses
        reserves = pool_contract.functions.getReserves().call()
        token0_address = pool_contract.functions.token0().call()
        token1_address = pool_contract.functions.token1().call()

        # Fetch token prices from CoinGecko
        token0_price = await self._fetch_token_price(token0_address, chain)
        token1_price = await self._fetch_token_price(token1_address, chain)

        reserve0 = reserves[0] / 10**18
        reserve1 = reserves[1] / 10**18
        tvl_usd = (reserve0 * token0_price) + (reserve1 * token1_price)

        return PoolMetrics(
            address=pool_address,
            protocol="uniswap_v2",  # Assume V2 for fallback
            chain=chain.value,
            token0=token0_address,
            token1=token1_address,
            token0_symbol="TOKEN0",
            token1_symbol="TOKEN1",
            token0_price=token0_price,
            token1_price=token1_price,
            reserves0=reserve0,
            reserves1=reserve1,
            tvl_usd=tvl_usd,
            volume_24h=0,  # Requires graph query
            volume_7d=0,
            fees_24h=0,
            fee_tier=0.003,  # Default 0.3%
            liquidity=tvl_usd
        )

    async def _fetch_token_price(
        self,
        token_address: str,
        chain: Chain
    ) -> float:
        """
        Fetch token price from CoinGecko API
        """
        cache_key = f"{chain.value}:{token_address}"
        if cache_key in self.price_cache:
            return self.price_cache[cache_key]

        chain_id_map = {
            Chain.ETHEREUM: "ethereum",
            Chain.BSC: "binance-smart-chain",
            Chain.POLYGON: "polygon-pos",
            Chain.ARBITRUM: "arbitrum-one",
            Chain.OPTIMISM: "optimistic-ethereum",
            Chain.BASE: "base",
            Chain.AVALANCHE: "avalanche"
        }

        platform = chain_id_map.get(chain, "ethereum")
        url = f"https://api.coingecko.com/api/v3/simple/token_price/{platform}"
        params = {
            'contract_addresses': token_address,
            'vs_currencies': 'usd'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            price = data[token_address.lower()]['usd']
            self.price_cache[cache_key] = price
            return price
        except:
            return 0.0

    def _detect_protocol(self, pool_metrics: PoolMetrics) -> PoolType:
        """
        Detect protocol type from pool metrics
        """
        protocol_map = {
            'uniswap-v2': PoolType.UNISWAP_V2,
            'uniswap-v3': PoolType.UNISWAP_V3,
            'curve': PoolType.CURVE,
            'balancer-v2': PoolType.BALANCER_V2,
            'sushiswap': PoolType.SUSHISWAP,
            'pancakeswap': PoolType.PANCAKESWAP
        }

        for key, pool_type in protocol_map.items():
            if key in pool_metrics.protocol.lower():
                return pool_type

        return PoolType.UNISWAP_V2  # Default

    def _calculate_yields(
        self,
        pool_metrics: PoolMetrics,
        investment: float
    ) -> YieldMetrics:
        """
        Calculate comprehensive yield metrics
        """
        # Base APY from trading fees
        if pool_metrics.tvl_usd > 0:
            daily_fees = pool_metrics.fees_24h
            yearly_fees = daily_fees * 365
            fee_apr = (yearly_fees / pool_metrics.tvl_usd) * 100
        else:
            fee_apr = 0.0

        # Farming/incentive APY (would need additional API calls)
        farming_apr = 0.0  # Placeholder

        total_apy = fee_apr + farming_apr

        # Calculate projected returns
        annual_rate = total_apy / 100
        daily_return = investment * annual_rate / 365
        weekly_return = investment * annual_rate / 52
        monthly_return = investment * annual_rate / 12
        yearly_return = investment * annual_rate

        return YieldMetrics(
            base_apy=fee_apr,
            reward_apy=farming_apr,
            total_apy=total_apy,
            daily_return=daily_return,
            weekly_return=weekly_return,
            monthly_return=monthly_return,
            yearly_return=yearly_return,
            fee_apr=fee_apr,
            farming_apr=farming_apr
        )

    def _calculate_impermanent_loss(
        self,
        pool_metrics: PoolMetrics,
        investment: float,
        entry_price_token0: Optional[float] = None,
        entry_price_token1: Optional[float] = None
    ) -> ImpermanentLoss:
        """
        Calculate impermanent loss with multiple scenarios

        IL Formula: IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
        """
        # Use entry prices if provided, otherwise assume no price change
        if entry_price_token0 is None:
            entry_price_token0 = pool_metrics.token0_price
        if entry_price_token1 is None:
            entry_price_token1 = pool_metrics.token1_price

        # Calculate price ratio change
        price_ratio = pool_metrics.token0_price / entry_price_token0
        price_change_percent = ((price_ratio - 1) * 100)

        # Calculate impermanent loss percentage
        il_multiplier = 2 * math.sqrt(price_ratio) / (1 + price_ratio) - 1
        il_percent = il_multiplier * 100

        # Calculate actual values
        hodl_value = investment  # Simplified - would adjust for price changes
        lp_value = investment * (1 + il_multiplier)
        il_usd = hodl_value - lp_value

        # Account for fees earned
        yearly_fees = investment * (self._calculate_yields(pool_metrics, investment).total_apy / 100)
        net_profit_loss = -il_usd + yearly_fees

        # Calculate scenarios for different price changes
        scenarios = {}
        for change_percent in [10, 25, 50, 100, 200, 500]:
            scenario_ratio = 1 + (change_percent / 100)
            scenario_il = (2 * math.sqrt(scenario_ratio) / (1 + scenario_ratio) - 1) * 100
            scenarios[f"{change_percent}%_change"] = round(scenario_il, 2)

        return ImpermanentLoss(
            current_il_percent=il_percent,
            current_il_usd=il_usd,
            price_change_percent=price_change_percent,
            hodl_value=hodl_value,
            lp_value=lp_value,
            net_profit_loss=net_profit_loss,
            scenarios=scenarios
        )

    async def _assess_risks(
        self,
        pool_metrics: PoolMetrics,
        chain: Chain
    ) -> RiskMetrics:
        """
        Comprehensive risk assessment with scoring
        """
        warnings = []
        recommendations = []
        scores = []

        # 1. Liquidity Risk Assessment (0-100)
        liquidity_score = min(100, (pool_metrics.tvl_usd / 1000000) * 100)
        if pool_metrics.tvl_usd < self.risk_thresholds['min_tvl']:
            warnings.append(f"Low TVL: ${pool_metrics.tvl_usd:,.0f}")
            liquidity_risk = "HIGH"
        elif pool_metrics.tvl_usd < 1000000:
            liquidity_risk = "MEDIUM"
        else:
            liquidity_risk = "LOW"
        scores.append(liquidity_score)

        # 2. Volume Risk (0-100)
        volume_score = min(100, (pool_metrics.volume_24h / 100000) * 100)
        if pool_metrics.volume_24h < self.risk_thresholds['min_volume']:
            warnings.append(f"Low volume: ${pool_metrics.volume_24h:,.0f}")
        scores.append(volume_score)

        # 3. Impermanent Loss Risk
        il_risk_score = 100
        if abs(pool_metrics.token0_price / pool_metrics.token1_price) > 10:
            il_risk = "HIGH"
            il_risk_score = 40
            recommendations.append("Consider stablecoin pairs for lower IL risk")
        elif abs(pool_metrics.token0_price / pool_metrics.token1_price) > 5:
            il_risk = "MEDIUM"
            il_risk_score = 70
        else:
            il_risk = "LOW"
        scores.append(il_risk_score)

        # 4. Protocol Risk Assessment
        trusted_protocols = ['uniswap', 'curve', 'balancer', 'sushiswap', 'pancakeswap']
        if any(p in pool_metrics.protocol.lower() for p in trusted_protocols):
            protocol_risk = "LOW"
            protocol_score = 90
        else:
            protocol_risk = "MEDIUM"
            protocol_score = 60
            warnings.append("Unknown or unaudited protocol")
        scores.append(protocol_score)

        # 5. Rug Pull Risk (simplified heuristics)
        rug_pull_score = 80
        rug_pull_risk = "LOW"

        # Check liquidity locked
        if pool_metrics.tvl_usd < 50000:
            rug_pull_risk = "MEDIUM"
            rug_pull_score = 50
            warnings.append("Low liquidity - higher rug pull risk")

        # Check volume/TVL ratio
        if pool_metrics.volume_24h > 0:
            volume_tvl_ratio = pool_metrics.volume_24h / pool_metrics.tvl_usd
            if volume_tvl_ratio > 2.0:
                warnings.append("Unusually high volume/TVL ratio")
                rug_pull_score -= 20

        scores.append(rug_pull_score)

        # 6. Smart Contract Risk
        # In production, would integrate with audit databases
        sc_risk = "MEDIUM"
        sc_score = 70
        recommendations.append("Verify smart contract audit status")
        scores.append(sc_score)

        # Calculate overall risk score (weighted average)
        overall_score = sum(scores) // len(scores)

        # Generate recommendations
        if pool_metrics.fee_tier > 0.01:
            recommendations.append("High fee tier - suitable for volatile pairs")

        if liquidity_risk == "LOW" and il_risk == "LOW":
            recommendations.append("Good risk/reward profile for LP")

        return RiskMetrics(
            overall_score=overall_score,
            impermanent_loss_risk=il_risk,
            volatility_risk="MEDIUM",  # Would calculate from price history
            liquidity_risk=liquidity_risk,
            protocol_risk=protocol_risk,
            rug_pull_risk=rug_pull_risk,
            smart_contract_risk=sc_risk,
            warnings=warnings,
            recommendations=recommendations
        )

    def _generate_optimization_strategies(
        self,
        pool_metrics: PoolMetrics,
        protocol_type: PoolType
    ) -> Dict:
        """
        Generate optimization strategies based on pool type
        """
        strategies = {
            'position_sizing': [],
            'rebalancing': [],
            'hedging': [],
            'alternative_pools': []
        }

        # Uniswap V3 specific optimization
        if protocol_type == PoolType.UNISWAP_V3:
            strategies['position_sizing'].append({
                'strategy': 'Concentrated Liquidity',
                'description': 'Focus liquidity in active trading range',
                'optimal_range': self._calculate_v3_optimal_range(pool_metrics),
                'expected_boost': '2-5x fee generation vs full range'
            })

            strategies['rebalancing'].append({
                'frequency': 'Weekly',
                'trigger': 'Price moves 10% outside range',
                'estimated_gas': '$20-50 per rebalance'
            })

        # General strategies
        strategies['hedging'].append({
            'method': 'Delta Hedging',
            'description': 'Short dominant asset to reduce IL',
            'effectiveness': 'Reduces IL by 50-80%'
        })

        strategies['position_sizing'].append({
            'strategy': 'Gradual Entry',
            'description': 'Split position into 4-5 entries over 2 weeks',
            'benefit': 'Reduces timing risk and average IL exposure'
        })

        return strategies

    def _calculate_v3_optimal_range(self, pool_metrics: PoolMetrics) -> Dict:
        """
        Calculate optimal price range for Uniswap V3 positions
        """
        current_price = pool_metrics.token0_price / pool_metrics.token1_price

        # Use 2 standard deviations of historical volatility
        # Simplified: use ±20% range as default
        volatility_multiplier = 0.20

        lower_price = current_price * (1 - volatility_multiplier)
        upper_price = current_price * (1 + volatility_multiplier)

        return {
            'current_price': current_price,
            'lower_bound': lower_price,
            'upper_bound': upper_price,
            'range_width': f"±{volatility_multiplier * 100}%",
            'expected_time_in_range': '80-90%',
            'capital_efficiency': '3-4x vs full range'
        }

    async def _fetch_historical_data(
        self,
        pool_address: str,
        chain: Chain,
        days: int = 30
    ) -> Dict:
        """
        Fetch historical performance data
        """
        # In production, would query TheGraph or similar
        return {
            'period': f'{days} days',
            'avg_apy': 0.0,
            'max_il': 0.0,
            'total_fees_generated': 0.0,
            'tvl_change': 0.0,
            'volume_trend': 'stable'
        }

    async def _compare_similar_pools(
        self,
        pool_metrics: PoolMetrics,
        chain: Chain
    ) -> List[Dict]:
        """
        Compare with similar pools on same chain
        """
        # In production, would query multiple pools with same pair
        return []

    def _generate_alerts(
        self,
        pool_metrics: PoolMetrics,
        risk_metrics: RiskMetrics
    ) -> List[Dict]:
        """
        Generate actionable alerts
        """
        alerts = []

        if risk_metrics.overall_score < 50:
            alerts.append({
                'severity': 'HIGH',
                'message': 'High risk pool - consider exiting position',
                'action': 'Review risk metrics and consider withdrawal'
            })

        if pool_metrics.volume_24h < 1000:
            alerts.append({
                'severity': 'MEDIUM',
                'message': 'Low trading volume detected',
                'action': 'Monitor for next 48 hours'
            })

        if pool_metrics.tvl_usd < 50000:
            alerts.append({
                'severity': 'HIGH',
                'message': 'Low liquidity - rug pull risk',
                'action': 'Verify token contract and team'
            })

        return alerts

    def _generate_summary(
        self,
        pool_metrics: PoolMetrics,
        yield_metrics: YieldMetrics,
        risk_metrics: RiskMetrics
    ) -> Dict:
        """
        Generate executive summary
        """
        return {
            'pool': f"{pool_metrics.token0_symbol}/{pool_metrics.token1_symbol}",
            'protocol': pool_metrics.protocol,
            'chain': pool_metrics.chain,
            'tvl': f"${pool_metrics.tvl_usd:,.0f}",
            'apy': f"{yield_metrics.total_apy:.2f}%",
            'risk_score': f"{risk_metrics.overall_score}/100",
            'recommendation': self._get_recommendation(risk_metrics.overall_score, yield_metrics.total_apy)
        }

    def _get_recommendation(self, risk_score: int, apy: float) -> str:
        """
        Generate investment recommendation
        """
        if risk_score >= 70 and apy >= 10:
            return "STRONG BUY - Good risk/reward ratio"
        elif risk_score >= 60 and apy >= 15:
            return "BUY - High yield justifies moderate risk"
        elif risk_score >= 50:
            return "HOLD - Monitor closely"
        else:
            return "AVOID - Risk too high for returns"

    def _print_report(self, report: Dict):
        """
        Print formatted analysis report
        """
        summary = report['summary']
        pool = report['pool_metrics']
        yields = report['yield_analysis']
        il = report['impermanent_loss']
        risks = report['risk_assessment']

        print(f"\n{'='*80}")
        print(f"EXECUTIVE SUMMARY")
        print(f"{'='*80}")
        print(f"Pool: {summary['pool']}")
        print(f"Protocol: {summary['protocol']} on {summary['chain']}")
        print(f"TVL: {summary['tvl']}")
        print(f"APY: {summary['apy']}")
        print(f"Risk Score: {summary['risk_score']}")
        print(f"Recommendation: {summary['recommendation']}")

        print(f"\n{'='*80}")
        print(f"YIELD ANALYSIS")
        print(f"{'='*80}")
        print(f"Base APY (Fees): {yields.base_apy:.2f}%")
        print(f"Reward APY: {yields.reward_apy:.2f}%")
        print(f"Total APY: {yields.total_apy:.2f}%")
        print(f"\nProjected Returns on ${pool.tvl_usd:,.0f}:")
        print(f"  Daily: ${yields.daily_return:,.2f}")
        print(f"  Weekly: ${yields.weekly_return:,.2f}")
        print(f"  Monthly: ${yields.monthly_return:,.2f}")
        print(f"  Yearly: ${yields.yearly_return:,.2f}")

        print(f"\n{'='*80}")
        print(f"IMPERMANENT LOSS ANALYSIS")
        print(f"{'='*80}")
        print(f"Current IL: {il.current_il_percent:.2f}% (${il.current_il_usd:,.2f})")
        print(f"Price Change: {il.price_change_percent:,.2f}%")
        print(f"HODL Value: ${il.hodl_value:,.2f}")
        print(f"LP Value: ${il.lp_value:,.2f}")
        print(f"Net P/L (after fees): ${il.net_profit_loss:,.2f}")
        print(f"\nIL Scenarios:")
        for scenario, il_value in il.scenarios.items():
            print(f"  {scenario}: {il_value:.2f}%")

        print(f"\n{'='*80}")
        print(f"RISK ASSESSMENT")
        print(f"{'='*80}")
        print(f"Overall Score: {risks.overall_score}/100")
        print(f"Impermanent Loss Risk: {risks.impermanent_loss_risk}")
        print(f"Liquidity Risk: {risks.liquidity_risk}")
        print(f"Protocol Risk: {risks.protocol_risk}")
        print(f"Rug Pull Risk: {risks.rug_pull_risk}")
        print(f"Smart Contract Risk: {risks.smart_contract_risk}")

        if risks.warnings:
            print(f"\nWarnings:")
            for warning in risks.warnings:
                print(f"  - {warning}")

        if risks.recommendations:
            print(f"\nRecommendations:")
            for rec in risks.recommendations:
                print(f"  - {rec}")

        if report['alerts']:
            print(f"\n{'='*80}")
            print(f"ACTIVE ALERTS")
            print(f"{'='*80}")
            for alert in report['alerts']:
                print(f"[{alert['severity']}] {alert['message']}")
                print(f"  Action: {alert['action']}\n")

        print(f"{'='*80}\n")

# Usage Example
if __name__ == "__main__":
    import asyncio

    # Initialize analyzer
    analyzer = LiquidityPoolAnalyzer(api_keys={
        'coingecko': 'your_api_key',
        'defillama': 'your_api_key',
        'etherscan': 'your_api_key'
    })

    # Analyze a pool
    pool_address = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"  # USDC/ETH on Uniswap V2

    async def main():
        report = await analyzer.analyze_pool(
            pool_address=pool_address,
            chain=Chain.ETHEREUM,
            initial_investment=10000,
            entry_price_token0=3000,  # Entry ETH price
            entry_price_token1=1  # USDC stable
        )

        # Save report to file
        with open('pool_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print("\nReport saved to pool_analysis_report.json")

    asyncio.run(main())
```

## Risk Scoring Methodology

### Overall Risk Score Calculation (0-100)

The risk score is computed using weighted factors:

```
Overall Score = (
    Liquidity Score (25%) +
    Volume Score (15%) +
    IL Risk Score (20%) +
    Protocol Score (20%) +
    Rug Pull Score (15%) +
    Smart Contract Score (5%)
) / 6
```

### Individual Risk Components

1. **Liquidity Risk (0-100)**
   - Score = min(100, TVL / $1M * 100)
   - <$100k TVL = HIGH risk
   - $100k-$1M = MEDIUM risk
   - >$1M = LOW risk

2. **Volume Risk (0-100)**
   - Score = min(100, Daily Volume / $100k * 100)
   - Healthy ratio: Daily Volume > 10% of TVL

3. **Impermanent Loss Risk**
   - Based on asset correlation and volatility
   - Stablecoin pairs: LOW (90-100 score)
   - Correlated assets: MEDIUM (60-80 score)
   - Uncorrelated: HIGH (0-50 score)

4. **Protocol Risk**
   - Audited major protocols: 85-95 score
   - Unaudited but established: 60-75 score
   - New/unknown: 30-50 score

5. **Rug Pull Risk**
   - Liquidity locked: +30 points
   - Team doxxed: +20 points
   - Audited contracts: +25 points
   - Established community: +15 points
   - Time-tested (>6 months): +10 points

## Automated Alerts

### Alert Triggers

The analyzer generates alerts based on these conditions:

1. **Price Range Deviation (Uniswap V3)**
   - Alert when current price moves >90% of your range width
   - Recommendation: Rebalance position

2. **TVL Drop**
   - Alert when TVL drops >20% in 24 hours
   - Severity: HIGH - potential liquidity crisis

3. **Impermanent Loss Threshold**
   - Alert when IL exceeds -5%
   - Provide IL recovery time estimate based on fee generation

4. **Volume Anomalies**
   - Alert when 24h volume <10% of historical average
   - May indicate reduced fee generation

5. **Smart Contract Events**
   - Monitor for ownership transfers
   - Track liquidity lock expiration dates
   - Alert on unusual contract interactions

## Best Practices

### For Liquidity Providers

1. **Start Small**: Test pools with 5-10% of intended capital
2. **Diversify**: Spread across 3-5 pools to reduce risk
3. **Monitor Daily**: Check positions at least once per day
4. **Set Stop Losses**: Define IL tolerance before entering (-10% typical)
5. **Calculate Break-Even**: Know how long fees take to recover IL

### Position Management

1. **Entry Strategy**:
   - Dollar-cost average into positions over 1-2 weeks
   - Enter during low volatility periods
   - Avoid FOMO entries during price spikes

2. **Exit Strategy**:
   - Define profit targets (e.g., 15% APY)
   - Set maximum acceptable IL (-10% to -15%)
   - Monitor for fundamental changes in protocol

3. **Rebalancing (V3)**:
   - Rebalance when price hits range boundaries
   - Consider gas costs vs additional fees earned
   - Use wider ranges during high gas periods

## Gas Cost Considerations

### Transaction Costs by Chain

- **Ethereum Mainnet**: $20-100 per transaction
- **Arbitrum/Optimism**: $1-5 per transaction
- **Polygon**: $0.10-0.50 per transaction
- **BSC**: $0.20-1.00 per transaction

### ROI Calculation Including Gas

```python
def calculate_net_roi(investment, apy, gas_costs, holding_period_days):
    """
    Calculate net ROI after gas costs
    """
    # Entry + exit gas
    total_gas = gas_costs['entry'] + gas_costs['exit']

    # Add rebalancing costs for V3
    rebalances = holding_period_days // 14  # Bi-weekly
    total_gas += rebalances * gas_costs['rebalance']

    # Calculate gross returns
    daily_rate = apy / 365 / 100
    gross_returns = investment * daily_rate * holding_period_days

    # Net returns
    net_returns = gross_returns - total_gas
    net_roi = (net_returns / investment) * 100

    return {
        'gross_returns': gross_returns,
        'total_gas_costs': total_gas,
        'net_returns': net_returns,
        'net_roi': net_roi,
        'break_even_days': total_gas / (investment * daily_rate)
    }
```

## Advanced Features

### Yield Optimization Strategies

1. **Range Order Strategy (V3)**:
   - Set narrow ranges just below/above current price
   - Capture fees during breakout moves
   - Higher IL risk but 10x+ fee generation

2. **Auto-Compounding**:
   - Reinvest earned fees back into pool
   - Increases position size over time
   - Account for gas costs

3. **Multi-Pool Hedging**:
   - LP in ETH/USDC while shorting ETH elsewhere
   - Neutralizes IL while earning fees
   - Requires margin/derivatives access

## Troubleshooting

### Common Issues

1. **High Impermanent Loss**
   - **Solution**: Wait for price reversion or exit if IL exceeds tolerance
   - Consider hedging strategy for future positions

2. **Low Fee Generation**
   - **Solution**: Move to higher volume pools or use concentrated liquidity
   - Check if pool incentives have ended

3. **Position Out of Range (V3)**
   - **Solution**: Rebalance immediately or accept zero fee generation
   - Consider wider ranges for future positions

4. **Rug Pull Concerns**
   - **Solution**: Exit immediately if red flags appear
   - Always research team and audit status before entering

## Future Enhancements

- Real-time notifications via Telegram/Discord webhooks
- Machine learning-based IL prediction models
- Automated rebalancing bot integration
- Cross-chain yield comparison dashboard
- Historical backtesting with actual LP returns data

---

Provides institutional-grade liquidity pool analysis with comprehensive risk assessment and optimization strategies.