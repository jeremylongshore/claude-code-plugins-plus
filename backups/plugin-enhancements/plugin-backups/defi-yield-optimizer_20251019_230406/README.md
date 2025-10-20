# DeFi Yield Optimizer Plugin

Optimize DeFi yield farming strategies across multiple protocols and chains with risk assessment, auto-compound calculations, and portfolio optimization.

## Features

###  Multi-Protocol Support
- **Lending**: Aave, Compound, Venus, Benqi
- **DEXs**: Uniswap, Sushiswap, PancakeSwap, QuickSwap
- **Stableswaps**: Curve, Ellipsis
- **Yield Aggregators**: Yearn, Beefy, Harvest
- **Leveraged Farming**: Alpaca, Tarot

###  Chain Coverage
- **Ethereum**: Main DeFi hub
- **BSC**: High APY opportunities
- **Polygon**: Low gas costs
- **Arbitrum**: L2 efficiency
- **Avalanche**: Fast finality
- **Fantom**: High yields

###  Optimization Features
- **Risk-Adjusted Returns**: Balance APY with risk
- **Portfolio Allocation**: Optimal diversification
- **Auto-Compound Analysis**: Frequency optimization
- **Impermanent Loss Calculation**: LP risk assessment
- **Gas Cost Optimization**: Net APY calculations

###  Risk Assessment
- **Protocol Risk**: Age, audits, TVL analysis
- **Smart Contract Risk**: Complexity scoring
- **Liquidity Risk**: Exit strategy evaluation
- **Composability Risk**: Protocol dependencies
- **Market Risk**: Volatility and correlation

## Installation

```bash
/plugin install defi-yield-optimizer@claude-code-plugins-plus
```

## Usage

### Basic Yield Optimization

```
/optimize-yield

I'll optimize your DeFi yield strategy:
- Capital: $10,000
- Risk tolerance: Medium
- Duration: 30 days
- Strategy: Balanced
```

### Advanced Configuration

```
/optimize-yield 50000 high

Optimizing for $50,000 with high risk:
- Chains: All supported
- Include leveraged: Yes
- Auto-compound: Enabled
- Min APY: 20%
```

### Portfolio Rebalancing

```
/rebalance-portfolio

Analyzing current positions:
- Calculating new optimal allocation
- Considering gas costs
- Minimizing impermanent loss
```

## Configuration

Create a `.defi-yield.json` configuration file:

```json
{
  "optimizer": {
    "minTVL": 1000000,
    "maxRiskScore": 7,
    "includeNewProtocols": false,
    "maxAllocationPerProtocol": 0.3,
    "slippageTolerance": 0.01
  },
  "chains": {
    "ethereum": {
      "enabled": true,
      "gasPrice": "auto",
      "maxGas": 100
    },
    "bsc": {
      "enabled": true,
      "gasPrice": 5,
      "maxGas": 10
    },
    "polygon": {
      "enabled": true,
      "gasPrice": 30,
      "maxGas": 5
    }
  },
  "strategies": {
    "stable": {
      "maxRisk": 3,
      "minAPY": 5,
      "stablecoinOnly": true
    },
    "balanced": {
      "maxRisk": 6,
      "minAPY": 10,
      "diversification": 0.7
    },
    "aggressive": {
      "maxRisk": 9,
      "minAPY": 20,
      "leverageAllowed": true
    }
  },
  "autoCompound": {
    "enabled": true,
    "checkFrequency": 86400,
    "minProfit": 10
  }
}
```

## Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `/optimize-yield` | Find optimal yield strategies | `oy` |
| `/compare-protocols` | Compare protocol yields | `cp` |
| `/calculate-compound` | Auto-compound calculator | `cc` |
| `/assess-risk` | Risk assessment tool | `ar` |
| `/track-portfolio` | Monitor active positions | `tp` |

## Strategy Types

### Stable Strategy
- Focus on stablecoin pairs
- Minimal impermanent loss
- Lower APY but consistent
- Risk score: 1-3

### Balanced Strategy
- Mix of stable and volatile
- Moderate risk/reward
- Diversified allocation
- Risk score: 4-6

### Aggressive Strategy
- High APY targets
- Leveraged positions allowed
- Concentrated bets
- Risk score: 7-10

## Risk Scoring System

### Risk Components
```
Total Risk = Protocol Risk + Asset Risk + Strategy Risk + Time Risk

Protocol Risk (0-3):
- Established (>1 year): 0
- Growing (6-12 months): 1
- New (3-6 months): 2
- Very New (<3 months): 3

Asset Risk (0-3):
- Stablecoins: 0
- Blue chips (BTC, ETH): 1
- Major alts: 2
- Small caps: 3

Strategy Risk (0-3):
- Simple lending: 0
- LP provision: 1
- Leveraged farming: 2
- Complex strategies: 3

Time Risk (0-1):
- No lock: 0
- Locked periods: 1
```

## APY Calculations

### Net APY Formula
```
Net APY = Base APY + Reward APY - Fees - Gas Impact

Where:
- Base APY: Trading fees or lending interest
- Reward APY: Token incentives
- Fees: Protocol fees (performance, withdrawal)
- Gas Impact: (Gas cost * Frequency) / Principal * 100
```

### Impermanent Loss
```
IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1

Example:
- 1.25x price change = 0.6% IL
- 1.5x price change = 2.0% IL
- 2x price change = 5.7% IL
- 3x price change = 13.4% IL
```

## Portfolio Optimization

### Modern Portfolio Theory
- Maximize Sharpe ratio
- Efficient frontier calculation
- Correlation analysis
- Risk-return optimization

### Diversification Metrics
- Protocol diversification
- Chain diversification
- Asset diversification
- Strategy diversification

### Rebalancing Triggers
- Allocation drift > 10%
- Risk score change
- APY degradation > 20%
- New opportunity > current + 5%

## Auto-Compound Optimization

### Optimal Frequency
```javascript
function optimalFrequency(principal, apy, gasCost) {
  // Find frequency that maximizes net return
  const frequencies = [1, 7, 14, 30, 90];
  return frequencies.reduce((best, freq) => {
    const compounds = 365 / freq;
    const gasYearly = compounds * gasCost;
    const netAPY = (1 + apy/compounds)^compounds - 1 - gasYearly/principal;
    return netAPY > best.apy ? {freq, apy: netAPY} : best;
  }, {freq: 365, apy: apy});
}
```

## Safety Features

### Protocol Validation
- Check audit status
- Verify TVL thresholds
- Monitor exploit history
- Track governance changes

### Position Limits
- Max allocation per protocol
- Minimum liquidity requirements
- Concentration warnings
- Correlation limits

### Exit Strategies
- Liquidity depth analysis
- Slippage estimation
- Emergency exit paths
- Gas reserve calculation

## Common Strategies

### Stablecoin Farming
```
USDC/USDT on Curve
- APY: 5-15%
- Risk: Very Low
- IL: Minimal
```

### Blue Chip LPs
```
ETH/USDC on Uniswap V3
- APY: 20-40%
- Risk: Medium
- IL: Moderate
```

### Leveraged Yield
```
3x Leveraged on Alpaca
- APY: 50-100%+
- Risk: High
- Liquidation risk
```

### Delta Neutral
```
Long spot + Short perp
- APY: 20-30%
- Risk: Low
- Market neutral
```

## Troubleshooting

### Low APY Results
- Increase risk tolerance
- Include more chains
- Lower minimum TVL
- Check gas settings

### High Risk Warnings
- Review protocol age
- Check audit status
- Reduce leverage
- Increase diversification

### Gas Optimization
- Use L2 chains
- Batch transactions
- Optimize compound frequency
- Consider gas tokens

## Performance Metrics

- Opportunity scanning: < 5 seconds
- Portfolio optimization: < 2 seconds
- Risk calculation: < 500ms
- APY accuracy: ±2%
- Gas estimation: ±10%

## Best Practices

### For Beginners
- Start with stable strategy
- Use established protocols
- Small test amounts first
- Monitor daily

### For Advanced Users
- Leverage monitoring tools
- Custom risk parameters
- Cross-chain strategies
- Active rebalancing

### Risk Management
- Never invest more than you can lose
- Diversify across protocols
- Keep emergency funds liquid
- Regular security reviews

## Contributing

Part of Claude Code Plugins marketplace.

1. Fork repository
2. Add protocol integration
3. Test thoroughly
4. Submit PR

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: [Report bugs](https://github.com/jeremylongshore/claude-code-plugins/issues)
- Discord: Claude Code community
- Documentation: [Full docs](https://docs.claude-code-plugins.com)

## Changelog

### v1.0.0 (2024-10-11)
- Initial release
- Multi-protocol support
- Portfolio optimization
- Risk assessment
- Auto-compound calculator
- 6 chain support

---

*Built with ️ for DeFi farmers by Intent Solutions IO*