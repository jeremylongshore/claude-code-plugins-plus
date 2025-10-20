# Crypto Derivatives Tracker Plugin

Track cryptocurrency futures, options, and perpetual swaps with funding rates, open interest, liquidations, and advanced derivatives market analysis.

## Features

- **Perpetual Swaps** - Funding rates, long/short ratios, liquidation levels
- **Futures Analysis** - Open interest, basis trading, contango/backwardation
- **Options Intelligence** - IV, options flow, put/call ratio, Greeks
- **Market Metrics** - Total OI, leverage ratios, volume analysis
- **Trading Signals** - Funding extremes, OI divergence, liquidation cascades
- **Multi-Exchange** - Binance, Bybit, OKX, Deribit, and more

## Installation

```bash
/plugin install crypto-derivatives-tracker@claude-code-plugins-plus
```

## Usage

The derivatives agent automatically activates when you discuss:
- Futures, options, or perpetual swaps
- Funding rates and open interest
- Derivatives trading strategies
- Liquidation analysis
- Basis trading opportunities

### Example Queries

```
What's the current funding rate for BTC perpetuals?

Show me open interest across all BTC futures

Analyze options flow for ETH expiring Friday

Is there a basis trading opportunity for BTC?

Where are the major liquidation levels?

Compare funding rates across Binance, Bybit, and OKX
```

## Supported Markets

### Centralized Exchanges
- **Binance Futures** - Largest volume, USDT and coin-margined
- **Bybit** - Popular perpetuals, good liquidity
- **OKX** - Comprehensive derivatives suite
- **Deribit** - Largest crypto options exchange
- **Kraken Futures** - Regulated US options
- **BitMEX** - Crypto perpetuals pioneer

### Decentralized Protocols
- **dYdX** - Perpetuals on Ethereum/StarkEx
- **GMX** - Perpetuals on Arbitrum/Avalanche
- **Synthetix** - Synthetic assets and perps
- **Perpetual Protocol** - vAMM-based
- **Drift Protocol** - Solana perpetuals

## Configuration

Create a `.derivatives-config.json` file:

```json
{
  "exchanges": ["binance", "bybit", "okx", "deribit"],
  "assets": ["BTC", "ETH", "SOL"],
  "monitoring": {
    "fundingRateAlert": 0.1,
    "oiChangeAlert": 0.15,
    "liquidationThreshold": 10000000
  },
  "trading": {
    "riskLevel": "medium",
    "maxLeverage": 5,
    "defaultPositionSize": 0.02
  }
}
```

## Key Metrics Explained

### Funding Rates
- **Positive funding**: Longs pay shorts (bullish sentiment)
- **Negative funding**: Shorts pay longs (bearish sentiment)
- **Extreme rates** (>0.1% 8-hour): Contrarian opportunity

### Open Interest (OI)
- **Rising OI + Rising Price**: Strong bullish trend
- **Rising OI + Falling Price**: Strong bearish trend
- **Falling OI + Rising Price**: Short covering
- **Falling OI + Falling Price**: Long liquidations

### Futures Basis
- **Contango** (positive): Futures > spot (normal)
- **Backwardation** (negative): Futures < spot (high demand)
- **Cash-and-carry**: Buy spot + sell futures

### Options Greeks
- **Delta**: Price sensitivity
- **Gamma**: Rate of delta change
- **Vega**: Volatility sensitivity
- **Theta**: Time decay

## Trading Strategies

### 1. Funding Rate Arbitrage
Long spot + Short perpetual when funding > 0.1%

### 2. Basis Trading
Buy spot + Sell quarterly futures when basis > 5% annualized

### 3. Liquidation Hunting
Target clusters of liquidations for potential cascades

### 4. Options Volatility Trading
Buy straddles when IV low, sell spreads when IV high

### 5. Options Flow Following
Track smart money positioning via unusual options activity

## Data Sources

- **Coinglass**: OI, funding, liquidations
- **Glassnode**: On-chain + derivatives
- **Laevitas**: Advanced analytics
- **Exchange APIs**: Binance, Deribit, Bybit, OKX
- **The Graph**: DEX derivatives data

## Risk Management

️ **Critical Considerations**:
- Derivatives use leverage - high risk of liquidation
- Funding costs accumulate in perpetuals
- Options can expire worthless (theta decay)
- Exchange counterparty risk
- Volatile markets can gap through stop losses

### Best Practices
1. Use appropriate position sizing
2. Monitor liquidation prices continuously
3. Account for funding costs
4. Spread positions across exchanges
5. Keep most funds in cold storage

## Risk Disclaimer

️ **Crypto derivatives are extremely risky instruments.**

Users should:
- Fully understand leverage and liquidation mechanics
- Only trade with funds they can afford to lose
- Use proper position sizing and risk management
- Be aware of exchange counterparty risk
- Understand funding costs and time decay
- Consider tax implications

**This plugin provides analysis only** - not financial advice. Trading derivatives involves substantial risk of loss.

## License

MIT License - See LICENSE file for details

## Support

- GitHub Issues: [Report bugs](https://github.com/jeremylongshore/claude-code-plugins/issues)
- Documentation: [Full docs](https://docs.claude-code-plugins.com)

---

*Built with ️ for derivatives traders by Intent Solutions IO*
