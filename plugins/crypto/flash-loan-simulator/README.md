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
