# PRD: Flash Loan Simulator

## Summary

**One-liner**: Simulate and analyze flash loan strategies with profitability calculations and risk assessment
**Domain**: Cryptocurrency / DeFi / Flash Loans
**Users**: DeFi Developers, Arbitrage Researchers, Smart Contract Auditors

## Problem Statement

Flash loans are powerful DeFi primitives that allow borrowing any amount without collateral, provided the loan is repaid within the same transaction. However, evaluating flash loan strategies is challenging:

1. No easy way to simulate complex multi-step transactions before deployment
2. Profitability calculations require accounting for gas, fees, and slippage
3. Competition from MEV bots makes many strategies unprofitable
4. Risk assessment requires understanding multiple protocols simultaneously
5. Real execution on mainnet is expensive and risky for testing
6. Historical backtesting requires archive node access and complex setup

## Target Users

### Persona 1: DeFi Developer
- **Profile**: Building flash loan arbitrage bots or liquidation systems
- **Pain Points**: Testing on mainnet is expensive; needs simulation before deployment
- **Goals**: Validate profitability; optimize gas usage; identify edge cases
- **Usage Pattern**: Daily simulation runs during development cycle

### Persona 2: Arbitrage Researcher
- **Profile**: Analyzes DeFi protocols for arbitrage opportunities
- **Pain Points**: Manual calculation of multi-hop arbitrage is error-prone
- **Goals**: Quickly evaluate opportunities; backtest historical scenarios
- **Usage Pattern**: Continuous opportunity scanning and analysis

### Persona 3: Smart Contract Auditor
- **Profile**: Reviews DeFi protocols for vulnerabilities
- **Pain Points**: Needs to simulate attack vectors without executing them
- **Goals**: Understand flash loan attack scenarios; verify protocol safety
- **Usage Pattern**: Deep-dive analysis during security audits

## User Stories

### Critical (P0)

1. **As a DeFi developer**, I want to simulate a flash loan arbitrage between two DEXs, so that I can verify profitability before deploying my contract.
   - **Acceptance Criteria**:
     - Input: Token pair, loan amount, source DEX, target DEX
     - Output: Expected profit/loss after all fees
     - Includes gas cost estimation at current prices
     - Shows breakdown of each transaction step

2. **As a researcher**, I want to calculate liquidation profitability on Aave, so that I can identify profitable opportunities.
   - **Acceptance Criteria**:
     - Input: Borrower address or health factor threshold
     - Output: Liquidation bonus minus costs
     - Shows collateral and debt values
     - Estimates competition level

3. **As a developer**, I want to compare flash loan providers, so that I can choose the cheapest option.
   - **Acceptance Criteria**:
     - Compare Aave (0.09%), dYdX (0%), Balancer (variable)
     - Account for available liquidity per asset
     - Show total cost including gas differences

### Important (P1)

4. **As a researcher**, I want to simulate triangular arbitrage, so that I can evaluate multi-hop strategies.
   - **Acceptance Criteria**:
     - Support 3+ DEX paths
     - Calculate cumulative slippage
     - Show optimal route and amounts

5. **As a developer**, I want to backtest strategies against historical data, so that I can validate my approach.
   - **Acceptance Criteria**:
     - Input: Strategy parameters, date range
     - Output: Historical profit/loss per opportunity
     - Shows win rate and average profit

### Nice-to-Have (P2)

6. **As an auditor**, I want to simulate flash loan attack scenarios, so that I can test protocol security.
   - **Acceptance Criteria**:
     - Template attack patterns (price manipulation, governance, etc.)
     - Safe simulation without actual execution
     - Detailed transaction trace

## Functional Requirements

### Core Features

- **REQ-1**: Flash Loan Provider Support
  - Aave V3 (0.09% fee, multi-chain)
  - dYdX (0% fee, ETH mainnet)
  - Balancer (variable fee, multi-chain)
  - Uniswap V3 flash swaps (implicit fee)

- **REQ-2**: Strategy Simulation Engine
  - Simple arbitrage (2 DEX)
  - Triangular arbitrage (3+ DEX)
  - Liquidation profitability
  - Collateral swap simulation
  - Debt refinancing analysis

- **REQ-3**: Profitability Calculator
  - Gross profit from price differences
  - Flash loan fee deduction
  - Gas cost estimation (EIP-1559)
  - Slippage impact modeling
  - Net profit/loss after all costs

- **REQ-4**: Risk Assessment
  - MEV competition analysis
  - Execution risk scoring
  - Protocol risk factors
  - Liquidity depth checks

- **REQ-5**: RPC Configuration
  - Free public RPCs (Ankr, Chainstack, Infura)
  - Custom RPC endpoint support
  - Multi-chain configuration
  - Automatic fallback

### Supported Strategies

| Strategy | Description | Complexity |
|----------|-------------|------------|
| Simple Arbitrage | Buy low on DEX A, sell high on DEX B | Low |
| Triangular Arbitrage | A→B→C→A circular trading | Medium |
| Liquidation | Repay debt, claim collateral bonus | Medium |
| Collateral Swap | Replace collateral without closing position | Medium |
| Self-Liquidation | Efficiently close own position | Low |
| Debt Refinancing | Move debt to better rates | High |

## Non-Goals

- **NOT** executing real flash loans (simulation only)
- **NOT** generating production-ready Solidity code
- **NOT** real-time opportunity alerts (analysis only)
- **NOT** MEV protection or Flashbots integration
- **NOT** managing private keys or signing transactions

## API Integrations

| API | Purpose | Auth | Rate Limits |
|-----|---------|------|-------------|
| Ankr RPC | Free blockchain queries | None | 30 req/sec |
| Chainstack Free | RPC | API Key | 25 req/sec |
| DeFiLlama | TVL and protocol data | None | Generous |
| Etherscan | Gas oracle, contract ABIs | API Key | 5 req/sec |
| Infura Free | RPC with archive data | API Key | 10 req/sec |
| The Graph | DEX subgraph queries | None | Varies |

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Simulation Accuracy | Within 5% of actual profit | Backtest vs. historical |
| Strategy Coverage | 6 strategy types | Feature completeness |
| Response Time | <5 seconds per simulation | Performance monitoring |
| Free RPC Usage | 100% usable without paid tier | User feedback |

## UX Flow

```
1. User Input
   ├── Strategy type (arbitrage, liquidation, etc.)
   ├── Parameters (tokens, amounts, DEXs)
   ├── Chain (Ethereum, Polygon, Arbitrum)
   └── RPC endpoint (default: free public)

2. Data Collection
   ├── Fetch current prices from DEXs
   ├── Query protocol state (Aave positions, etc.)
   ├── Get gas prices and estimates
   └── Check liquidity depth

3. Simulation Engine
   ├── Calculate gross profit
   ├── Deduct flash loan fees
   ├── Subtract gas costs
   ├── Apply slippage model
   └── Compute net profit/loss

4. Risk Analysis
   ├── Score MEV competition risk
   ├── Check execution feasibility
   ├── Assess protocol risks
   └── Rate overall viability

5. Results Output
   ├── Profit/loss breakdown
   ├── Step-by-step transaction flow
   ├── Risk assessment summary
   └── Recommendations
```

## Constraints & Assumptions

### Constraints
- Free RPC endpoints have rate limits (25-100 req/sec)
- Historical simulations require archive node access
- Gas estimates are approximations (actual may vary ±20%)
- Price data has latency (not real-time MEV-competitive)

### Assumptions
- User understands DeFi and flash loan concepts
- User has access to RPC endpoint (free or paid)
- Simulation results are for analysis, not execution
- Market conditions change; simulations are point-in-time

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Stale price data | High | Medium | Clear timestamp warnings |
| RPC rate limiting | Medium | Low | Multi-provider fallback |
| Inaccurate gas estimate | Medium | Medium | Add safety margin to calculations |
| Strategy already exploited | High | Low | Competition scoring in output |
| Protocol changes | Low | High | Version-aware protocol configs |

## Educational Disclaimer

**IMPORTANT**: This tool is for **educational and research purposes only**. Flash loan strategies involve significant risks:

- Smart contract bugs can cause total loss of funds
- MEV bots compete for the same opportunities
- Gas costs can exceed profits
- Protocol exploits may have legal implications

Users should:
- Never deploy unaudited code
- Start with testnets before mainnet
- Understand the risks fully
- Consult legal counsel if needed

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-15 | Claude | Initial PRD |
