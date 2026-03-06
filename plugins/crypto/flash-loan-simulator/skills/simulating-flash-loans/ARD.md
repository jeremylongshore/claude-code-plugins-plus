# ARD: Flash Loan Simulator

## Architectural Overview

### Pattern: Strategy Simulation with Protocol Abstraction

The flash loan simulator uses a **strategy-protocol abstraction pattern** where different flash loan strategies are composed from protocol-agnostic building blocks, enabling simulation across multiple providers and chains.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FLASH LOAN SIMULATOR                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│  │   User      │───▶│   Strategy   │───▶│   Simulation        │   │
│  │   Input     │    │   Builder    │    │   Engine            │   │
│  └─────────────┘    └──────┬───────┘    └──────────┬──────────┘   │
│                            │                       │              │
│                            ▼                       ▼              │
│                   ┌────────────────┐    ┌─────────────────────┐   │
│                   │ Protocol       │    │   Profitability     │   │
│                   │ Abstraction    │    │   Calculator        │   │
│                   └───────┬────────┘    └─────────────────────┘   │
│                           │                                       │
│         ┌─────────────────┼─────────────────┐                    │
│         ▼                 ▼                 ▼                    │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐               │
│  │  Aave V3   │   │   dYdX     │   │  Balancer  │               │
│  │  Adapter   │   │  Adapter   │   │  Adapter   │               │
│  └────────────┘   └────────────┘   └────────────┘               │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           ▼                                       │
│                   ┌────────────────┐                             │
│                   │   RPC Layer    │                             │
│                   │   (Multi-Chain)│                             │
│                   └───────┬────────┘                             │
│                           │                                       │
│                           ▼                                       │
│                   ┌────────────────┐    ┌─────────────────────┐   │
│                   │   Formatter    │───▶│   Output            │   │
│                   │                │    │   (Table/JSON)      │   │
│                   └────────────────┘    └─────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow

1. **Strategy Selection**: User chooses strategy type and parameters
2. **Protocol Resolution**: Identify best flash loan provider
3. **Price Discovery**: Fetch current DEX prices
4. **Simulation**: Execute virtual transaction steps
5. **Profit Calculation**: Sum revenues, subtract all costs
6. **Risk Assessment**: Score competition and execution risk
7. **Output**: Present results with recommendations

## Progressive Disclosure Strategy

### Level 1: Quick Profitability Check (Default)
```bash
python flash_simulator.py arbitrage ETH USDC 100 --provider aave
```
Output: Simple profit/loss with recommendation.

### Level 2: Detailed Breakdown
```bash
python flash_simulator.py arbitrage ETH USDC 100 --breakdown
```
Output: Step-by-step costs and revenues.

### Level 3: Multi-Provider Comparison
```bash
python flash_simulator.py arbitrage ETH USDC 100 --compare-providers
```
Output: Aave vs dYdX vs Balancer comparison.

### Level 4: Risk Analysis
```bash
python flash_simulator.py arbitrage ETH USDC 100 --risk-analysis
```
Output: MEV competition, execution risk, protocol risk scores.

### Level 5: Full Simulation
```bash
python flash_simulator.py arbitrage ETH USDC 100 --full --output json
```
Output: Complete analysis with all details.

## Tool Permission Strategy

```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:flashloan-*)
```

### Rationale
- **Read/Write/Edit**: Configuration and output management
- **Grep/Glob**: Search for contract addresses and ABIs
- **Bash(crypto:flashloan-*)**: Scoped to flash loan simulation scripts

### Prohibited
- No unrestricted Bash execution
- No private key or wallet access
- No actual transaction signing
- No mainnet execution capabilities

## Directory Structure

```
plugins/crypto/flash-loan-simulator/
├── .claude-plugin/
│   └── plugin.json
├── README.md
└── skills/
    └── simulating-flash-loans/
        ├── PRD.md
        ├── ARD.md
        ├── SKILL.md
        ├── scripts/
        │   ├── flash_simulator.py      # Main CLI entry point
        │   ├── strategy_engine.py      # Strategy simulation logic
        │   ├── protocol_adapters.py    # Aave, dYdX, Balancer adapters
        │   ├── profit_calculator.py    # Profitability calculations
        │   ├── risk_assessor.py        # Risk scoring engine
        │   └── formatters.py           # Output formatting
        ├── references/
        │   ├── errors.md
        │   ├── examples.md
        │   └── implementation.md
        └── config/
            └── settings.yaml
```

## Protocol Adapter Architecture

### Flash Loan Provider Abstraction

```python
class FlashLoanProvider(ABC):
    """Abstract base for flash loan providers."""

    @abstractmethod
    def get_fee(self, asset: str, amount: Decimal) -> Decimal:
        """Get flash loan fee for asset and amount."""
        pass

    @abstractmethod
    def get_max_loan(self, asset: str) -> Decimal:
        """Get maximum available loan for asset."""
        pass

    @abstractmethod
    def get_supported_assets(self) -> List[str]:
        """Get list of supported assets."""
        pass

    @abstractmethod
    def simulate_loan(self, params: LoanParams) -> SimulationResult:
        """Simulate flash loan execution."""
        pass


class AaveV3Provider(FlashLoanProvider):
    """Aave V3 flash loan provider adapter."""

    FEE_RATE = Decimal("0.0009")  # 0.09%

    POOL_ADDRESSES = {
        "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    }

    def get_fee(self, asset: str, amount: Decimal) -> Decimal:
        return amount * self.FEE_RATE


class DydxProvider(FlashLoanProvider):
    """dYdX flash loan provider adapter (0% fee)."""

    FEE_RATE = Decimal("0")  # Free flash loans!

    SUPPORTED_ASSETS = ["ETH", "USDC", "DAI", "WBTC"]

    def get_fee(self, asset: str, amount: Decimal) -> Decimal:
        return Decimal("0")  # dYdX has 0% flash loan fee


class BalancerProvider(FlashLoanProvider):
    """Balancer flash loan provider adapter."""

    FEE_RATE = Decimal("0.0001")  # 0.01% (configurable per pool)
```

### Strategy Pattern

```python
class FlashLoanStrategy(ABC):
    """Abstract base for flash loan strategies."""

    @abstractmethod
    def simulate(self, params: StrategyParams) -> StrategyResult:
        """Run strategy simulation."""
        pass

    @abstractmethod
    def calculate_profit(self, result: StrategyResult) -> ProfitBreakdown:
        """Calculate net profit after all costs."""
        pass


class SimpleArbitrageStrategy(FlashLoanStrategy):
    """Two-DEX arbitrage: buy low, sell high."""

    def simulate(self, params: StrategyParams) -> StrategyResult:
        # 1. Flash loan from provider
        # 2. Buy on low-price DEX
        # 3. Sell on high-price DEX
        # 4. Repay loan + fee
        # 5. Keep profit
        pass


class LiquidationStrategy(FlashLoanStrategy):
    """Liquidate undercollateralized positions."""

    def simulate(self, params: StrategyParams) -> StrategyResult:
        # 1. Flash loan debt asset
        # 2. Repay borrower's debt
        # 3. Receive collateral + bonus
        # 4. Swap collateral to debt asset
        # 5. Repay flash loan
        # 6. Keep bonus
        pass
```

## Data Flow Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                 │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT                                                            │
│  ─────                                                            │
│  Strategy: arbitrage                                              │
│  Token: ETH → USDC → ETH                                         │
│  Amount: 100 ETH                                                  │
│  Provider: aave                                                   │
│                                                                   │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    PRICE DISCOVERY                           │ │
│  │                                                              │ │
│  │  Uniswap V3: ETH/USDC = 2,543.22                            │ │
│  │  SushiSwap:  ETH/USDC = 2,538.50                            │ │
│  │  Curve:      ETH/USDC = 2,540.00                            │ │
│  │  ───────────────────────────────────────────                │ │
│  │  Spread: $4.72 (0.19%)                                      │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    SIMULATION ENGINE                         │ │
│  │                                                              │ │
│  │  Step 1: Flash borrow 100 ETH from Aave                     │ │
│  │  Step 2: Sell 100 ETH on Uniswap → 254,322 USDC            │ │
│  │  Step 3: Buy ETH on SushiSwap → 100.186 ETH                │ │
│  │  Step 4: Repay 100 ETH + 0.09 ETH fee                      │ │
│  │  Step 5: Profit = 0.096 ETH                                 │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    PROFIT CALCULATION                        │ │
│  │                                                              │ │
│  │  Gross Profit:      0.186 ETH ($472.50)                     │ │
│  │  Flash Loan Fee:   -0.090 ETH ($228.89)                     │ │
│  │  Gas Cost:         -0.012 ETH ($30.50)                      │ │
│  │  ──────────────────────────────────────                     │ │
│  │  Net Profit:        0.084 ETH ($213.11)                     │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    RISK ASSESSMENT                           │ │
│  │                                                              │ │
│  │  MEV Competition:   HIGH (many bots target this pair)       │ │
│  │  Execution Risk:    MEDIUM (slippage on large trades)       │ │
│  │  Protocol Risk:     LOW (Aave V3 well-audited)              │ │
│  │  ──────────────────────────────────────                     │ │
│  │  Overall Viability: MODERATE                                 │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                       │
│           ▼                                                       │
│  OUTPUT                                                           │
│  ──────                                                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  SIMULATION RESULT                                          │ │
│  │  ────────────────────────────────────────────────────────── │ │
│  │  Strategy:        Simple Arbitrage (Uniswap → SushiSwap)   │ │
│  │  Loan Amount:     100 ETH                                   │ │
│  │  Provider:        Aave V3 (0.09% fee)                       │ │
│  │  Net Profit:      $213.11 (0.084 ETH)                       │ │
│  │  ROI:             0.084%                                    │ │
│  │  Risk Level:      MODERATE                                  │ │
│  │                                                              │ │
│  │  ⚠️  WARNING: High MEV competition on this pair.            │ │
│  │     Consider using Flashbots for execution.                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Error Handling Strategy

### Error Categories

| Category | Examples | Response |
|----------|----------|----------|
| RPC Error | Connection timeout, rate limit | Fallback to backup RPC |
| Price Error | Stale data, no liquidity | Clear warning, abort sim |
| Strategy Error | Invalid parameters | User-friendly error message |
| Protocol Error | Contract call failed | Show revert reason |
| Calculation Error | Overflow, division by zero | Safe defaults with warning |

### Graceful Degradation

```python
class SimulationError(Exception):
    """Base simulation error with recovery hints."""

    def __init__(self, message: str, recoverable: bool, hint: str):
        self.message = message
        self.recoverable = recoverable
        self.hint = hint


class RPCManager:
    """RPC connection manager with automatic fallback."""

    PROVIDERS = [
        "https://rpc.ankr.com/eth",
        "https://eth.llamarpc.com",
        "https://ethereum.publicnode.com",
    ]

    async def call_with_fallback(self, method: str, params: list):
        for rpc in self.PROVIDERS:
            try:
                return await self._call(rpc, method, params)
            except RPCError:
                continue
        raise AllRPCsFailedError("All RPC providers failed")
```

## Composability & Stacking

### Compatible Skills

| Skill | Integration | Data Flow |
|-------|-------------|-----------|
| dex-aggregator-router | Route optimization | Shares DEX price data |
| gas-fee-optimizer | Gas estimation | Provides gas price input |
| liquidity-pool-analyzer | Pool metrics | Shares liquidity data |
| arbitrage-opportunity-finder | Opportunity feed | Sends arbitrage signals |

### Stacking Example

```bash
# Find arbitrage → Simulate flash loan → Assess risk
python arbitrage_finder.py --output opportunities.json
python flash_simulator.py --opportunities opportunities.json --simulate-all
```

## Performance & Scalability

### Caching Strategy

| Data Type | TTL | Storage |
|-----------|-----|---------|
| Protocol ABIs | 24h | File cache |
| Token metadata | 24h | File cache |
| DEX prices | 30s | Memory |
| Gas prices | 15s | Memory |
| Simulation results | 0 | No cache (real-time) |

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Simple simulation | <3s | Single strategy |
| Full analysis | <10s | All providers + risk |
| Batch simulation | <30s | 10 strategies |
| Memory usage | <200MB | Peak during simulation |

## Testing Strategy

### Unit Tests
- Protocol adapter fee calculations
- Profit calculation math
- Risk scoring algorithms
- Gas estimation accuracy

### Integration Tests
- RPC connectivity (mocked)
- Multi-provider comparison
- Strategy composition

### Acceptance Tests
- Simulation matches historical actual profits (±10%)
- All strategy types complete without error
- Free RPC tier sufficient for basic usage

## Security & Compliance

### Safety Measures
- **No execution**: Simulation only, never signs transactions
- **No private keys**: Tool cannot access wallets
- **Read-only RPC**: Only view functions, no state changes
- **Educational disclaimer**: Clear warnings about real risks

### Data Handling
- No sensitive data storage
- API keys in environment variables only
- No transaction broadcasting

## Dependencies

### Python Packages
```
web3>=6.0.0            # Ethereum interaction
httpx>=0.24.0          # Async HTTP client
pydantic>=2.0          # Data validation
rich>=13.0             # Terminal formatting
```

### External Services
- Free RPC endpoints (Ankr, Chainstack free tier, Infura free tier)
- DeFiLlama API (protocol TVL)
- Etherscan API (gas oracle)

### Protocol Contracts (Read-Only)
- Aave V3 Pool
- dYdX Solo Margin
- Balancer Vault
- Uniswap V3 Router
