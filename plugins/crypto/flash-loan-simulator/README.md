# Flash Loan Simulator Plugin

Simulate and analyze flash loan strategies including arbitrage, liquidations, and collateral swaps across major DeFi protocols.

## Features

- **Strategy Simulation** - Model complex multi-step flash loan transactions
- **Profitability Analysis** - Calculate net profit after all fees and costs
- **Risk Assessment** - Identify execution risks and competition levels
- **Protocol Support** - Aave V3, dYdX, Balancer, Uniswap V3
- **Gas Optimization** - Estimate gas costs and optimize strategies
- **Historical Testing** - Backtest strategies against historical data

## Installation

```bash
/plugin install flash-loan-simulator@claude-code-plugins-plus
```

## FREE RPC Endpoints: No Alchemy Required

**Run flash loan simulations using free public RPC endpoints** - no Alchemy subscription needed.

### Quick Comparison

| RPC Provider | Paid (Alchemy) | FREE (Public RPCs) |
|--------------|---------------|-------------------|
| **Monthly Cost** | $49-199/mo | **$0/mo** |
| **Requests/day** | 300M-1500M | 1M-10M (sufficient) |
| **Rate Limit** | 660 req/sec | 25-100 req/sec |
| **Setup** | Credit card required | No signup |

**Annual Savings: $588-2,388** for flash loan development.

### Why Free RPCs Work for Flash Loan Simulations

**Simulation Requirements:**
- Read blockchain state (getBlock, getTransaction, call)
- Query DeFi protocol data (Aave, Uniswap, Balancer)
- Gas estimation (estimateGas)
- Historical data for backtesting

**Free RPCs provide:**
- 25-100 requests/second (more than enough for simulations)
- Archive node access (historical data)
- Multi-chain support (Ethereum, Polygon, Arbitrum)
- 99.9% uptime

**You DON'T need Alchemy's premium features for simulations** (webhooks, NFT API, trace API are for production, not testing).

### Free RPC Provider Catalog

#### 1. Ankr (Best for Multi-Chain)

**What:** Public RPC endpoints for 15+ chains

**Limits:**
- Ethereum: 30 requests/second
- No rate limits on queries
- Archive data available

**Setup:**
```json
{
  "rpcEndpoint": "https://rpc.ankr.com/eth"
}
```

**Cost:** $0 (no API key required)

**Chains:** Ethereum, Polygon, Arbitrum, Optimism, BSC, Avalanche

#### 2. Infura Free Tier

**What:** Free tier with 100K requests/day

**Limits:**
- 100,000 requests/day (sufficient for development)
- 10 requests/second
- Requires free account (no credit card)

**Setup:**
```json
{
  "rpcEndpoint": "https://mainnet.infura.io/v3/YOUR_FREE_KEY"
}
```

**Get Free Key:** [infura.io/register](https://infura.io/register) (no payment required)

**Cost:** $0 (free tier)

#### 3. Chainstack Free Plan

**What:** 3M requests/month free

**Limits:**
- 3,000,000 requests/month
- 25 requests/second
- Free account (no card)

**Setup:**
```json
{
  "rpcEndpoint": "https://nd-XXX-XXX-XXX.p2pify.com/YOUR_FREE_KEY"
}
```

**Get Free Key:** [chainstack.com/pricing](https://chainstack.com/pricing)

**Cost:** $0 (free plan)

#### 4. Public Ethereum RPC (Fastest Setup)

**What:** Community-run public endpoints

**Limits:**
- Variable rate limits
- May be slower during peak times
- No signup required

**Setup:**
```json
{
  "rpcEndpoint": "https://eth.llamarpc.com"
}
```

**Cost:** $0 (completely free)

**Alternatives:**
- `https://ethereum.publicnode.com`
- `https://cloudflare-eth.com`
- `https://rpc.flashbots.net` (MEV-protected)

### Configuration with Free RPCs

#### Option 1: Ankr (Recommended - No Signup)

```json
{
  "protocols": {
    "aave": { "enabled": true, "fee": 0.0009 },
    "dydx": { "enabled": true, "fee": 0 },
    "balancer": { "enabled": true, "fee": 0.001 }
  },
  "simulation": {
    "slippageTolerance": 0.01,
    "gasPrice": "auto",
    "minProfitUSD": 50
  },
  "rpcEndpoint": "https://rpc.ankr.com/eth"
}
```

**Cost:** $0 (vs Alchemy $49/mo)

#### Option 2: Infura Free Tier (Best Features)

```json
{
  "rpcEndpoint": "https://mainnet.infura.io/v3/YOUR_FREE_KEY"
}
```

**Setup Steps:**
1. Sign up at [infura.io](https://infura.io) (free, no card)
2. Create project
3. Copy API key
4. Paste into config

**Cost:** $0 for 100K requests/day

#### Option 3: Multi-Chain Setup (All Free)

```json
{
  "networks": {
    "ethereum": "https://rpc.ankr.com/eth",
    "polygon": "https://rpc.ankr.com/polygon",
    "arbitrum": "https://rpc.ankr.com/arbitrum",
    "optimism": "https://rpc.ankr.com/optimism"
  }
}
```

**Cost:** $0 across all chains

### Cost Comparison: Flash Loan Development

#### Paid Approach (Alchemy)

**Annual Subscriptions:**
- Alchemy Growth: $49/mo → $588/year
- Alchemy Scale: $199/mo → $2,388/year (if high usage)

**Advantages:**
- 660 requests/second
- Advanced analytics dashboard
- Dedicated support

#### Free Approach (Public RPCs)

**Annual Subscriptions:**
- Ankr: $0
- Infura free tier: $0
- Public RPCs: $0
- **Total: $0/year**

**Advantages:**
- 25-100 requests/second (sufficient for simulations)
- Archive data for backtesting
- No rate limit concerns for development

**Savings: $588-2,388/year** with identical simulation quality.

### Real Use Case Examples

#### Flash Loan Arbitrage Simulation

```javascript
const { ethers } = require('ethers');

// Before (Alchemy - Paid)
const provider = new ethers.providers.JsonRpcProvider(
  `https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}`  // $49-199/mo
);

// After (Ankr - FREE)
const provider = new ethers.providers.JsonRpcProvider(
  'https://rpc.ankr.com/eth'  // $0/mo
);

// Same simulation capability, zero cost
const uniswapPrice = await uniswapContract.getAmountsOut(...);
const sushiswapPrice = await sushiswapContract.getAmountsOut(...);
const profit = calculateArbitrage(uniswapPrice, sushiswapPrice);
```

**Cost:** $0 (vs $49-199/mo)

#### Aave Liquidation Simulation

```javascript
// Using free Infura RPC
const provider = new ethers.providers.JsonRpcProvider(
  `https://mainnet.infura.io/v3/${INFURA_FREE_KEY}`  // $0 (free tier)
);

const aaveContract = new ethers.Contract(AAVE_ADDRESS, ABI, provider);

// Simulate liquidation
const healthFactor = await aaveContract.getUserAccountData(user);
if (healthFactor < 1e18) {
  const liquidationProfit = calculateLiquidationProfit(...);
  console.log(`Profit: $${liquidationProfit}`);
}
```

**Cost:** $0 (100K requests/day free)

### Performance Comparison

| Metric | Alchemy (Paid) | Free RPCs |
|--------|---------------|-----------|
| **Response Time** | 50-100ms | 100-300ms ⚠️ |
| **Requests/sec** | 660 | 25-100 |
| **Uptime** | 99.99% | 99.9% |
| **Archive Data** | ✅ | ✅ |
| **Cost** | $49-199/mo | $0 |

**For simulations, 100-300ms response time is acceptable** (not production trading).

### When Free RPCs Are NOT Enough

**Use paid Alchemy if:**
- You're deploying live flash loan bots (need <50ms latency)
- You need >100 requests/second
- You require webhooks for mempool monitoring
- Your firm needs enterprise SLA

**For 99% of flash loan learning/simulation:** Free RPCs are sufficient.

### Hybrid Approach

**Best of both worlds:** Use free RPCs for development, Alchemy only for production.

```javascript
const RPC_ENDPOINTS = {
  development: 'https://rpc.ankr.com/eth',  // $0
  production: `https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}`  // $49/mo
};

const provider = new ethers.providers.JsonRpcProvider(
  RPC_ENDPOINTS[process.env.NODE_ENV]
);
```

**Cost Reduction:** $588/year → $49/year (92% savings)

### Resources

- **Ankr RPCs:** [rpc.ankr.com](https://rpc.ankr.com) (FREE, no signup)
- **Infura Free:** [infura.io/pricing](https://infura.io/pricing) (100K req/day)
- **Chainstack Free:** [chainstack.com/pricing](https://chainstack.com/pricing) (3M req/month)
- **Public RPCs List:** [chainlist.org](https://chainlist.org) (community endpoints)

**Bottom Line:** For flash loan simulations and learning, free public RPCs save $588-2,388/year with no quality loss.

---

## Usage

The flash loan agent automatically activates when you discuss:
- Flash loan strategies and simulations
- DeFi arbitrage opportunities
- Liquidation strategies
- Collateral swaps and refinancing
- Multi-protocol DeFi transactions

### Example Queries

```
Simulate a flash loan arbitrage between Uniswap and SushiSwap for ETH

Calculate profitability of liquidating this Aave position

What's the optimal flash loan amount for this arbitrage opportunity?

Simulate a collateral swap from USDC to ETH on Aave V3

Build a flash loan strategy to arbitrage these 3 DEXes
```

## Supported Strategies

1. **Simple Arbitrage**: DEX price discrepancies
2. **Liquidation**: Undercollateralized position liquidations
3. **Collateral Swap**: Position refinancing
4. **Self-Liquidation**: Efficient position closing
5. **Debt Refinancing**: Moving debt between protocols
6. **Triangular Arbitrage**: Multi-asset circular trading

## Configuration

Create a `.flashloan-config.json` file:

```json
{
  "protocols": {
    "aave": {
      "enabled": true,
      "fee": 0.0009
    },
    "dydx": {
      "enabled": true,
      "fee": 0
    },
    "balancer": {
      "enabled": true,
      "fee": 0.001
    }
  },
  "simulation": {
    "slippageTolerance": 0.01,
    "gasPrice": "auto",
    "minProfitUSD": 50
  },
  "rpcEndpoint": "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY"
}
```

## Flash Loan Providers

| Provider | Fee | Assets | Chains |
|----------|-----|--------|--------|
| Aave V3 | 0.09% | All markets | ETH, Polygon, Arbitrum, Optimism |
| dYdX | 0% | ETH, USDC, DAI, WBTC | Ethereum |
| Balancer | 0.01-0.1% | Pool tokens | ETH, Polygon, Arbitrum |
| Uniswap V3 | Implicit | Any pair | ETH, Polygon, Arbitrum, Optimism |

## Risk Warnings

️ **Critical Considerations**:
- Smart contract code must be thoroughly audited
- Gas costs can eliminate profitability
- Front-running by MEV bots is common
- Slippage can cause unexpected losses
- Protocol risks (bugs, exploits)
- Requires advanced Solidity development skills
- **For educational purposes only**

## Simulation Tools

- Tenderly (transaction simulation)
- Foundry (forked network testing)
- Hardhat (mainnet forking)
- Flashbots (MEV protection)

## License

MIT License - See LICENSE file for details

## Support

- GitHub Issues: [Report bugs](https://github.com/jeremylongshore/claude-code-plugins/issues)
- Documentation: [Full docs](https://docs.claude-code-plugins.com)

---

*Built with ️ for DeFi developers by Intent Solutions IO*
