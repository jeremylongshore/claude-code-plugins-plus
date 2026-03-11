# Finding Arbitrage Opportunities - Implementation Reference

## Supported Exchanges

### Centralized Exchanges (CEX)
| Exchange | Maker Fee | Taker Fee | Withdrawal |
|----------|-----------|-----------|------------|
| Binance | 0.10% | 0.10% | Variable |
| Coinbase | 0.40% | 0.60% | Variable |
| Kraken | 0.16% | 0.26% | Variable |
| KuCoin | 0.10% | 0.10% | Variable |
| OKX | 0.08% | 0.10% | Variable |

### Decentralized Exchanges (DEX)
| DEX | Fee Range | Gas (ETH) | Chains |
|-----|-----------|-----------|--------|
| Uniswap V3 | 0.01-1% | ~150k | ETH, Polygon, Arbitrum |
| SushiSwap | 0.30% | ~150k | Multi-chain |
| Curve | 0.04% | ~200k | ETH, Polygon, Arbitrum |
| Balancer | 0.01-10% | ~180k | ETH, Polygon, Arbitrum |

## Configuration

Configure price sources in `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

```yaml
# Primary data sources
data_sources:
  coingecko:
    enabled: true
    base_url: "https://api.coingecko.com/api/v3"
    rate_limit: 10  # calls per minute (free tier)

exchanges:
  - binance
  - coinbase
  - kraken
  - kucoin
  - okx
```

Environment variables for API keys:
```bash
export BINANCE_API_KEY="your-key"
export COINBASE_API_KEY="your-key"
```

## Advanced Arbitrage Types

### Triangular Arbitrage
Find profitable circular paths within a single exchange:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py triangular binance --min-profit 0.5
```

Example output:
```
Path: ETH -> BTC -> USDT -> ETH
Gross: +0.82%
Fees:  -0.30% (3 x 0.10%)
-----------------------
Net:   +0.52%
```

### Cross-Chain Opportunities
Compare prices across different blockchains:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py cross-chain USDC \
  --chains ethereum,polygon,arbitrum
```

Shows:
- Price on each chain
- Bridge fees and times
- Net profit after bridging

### Real-Time Monitoring
Continuously monitor for opportunities:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py monitor ETH USDC \
  --threshold 0.5 \
  --interval 5
```

Alert format:
```
[ALERT] ETH/USDC spread 0.62% (Binance -> Coinbase)
        Buy: $2,541.20 | Sell: $2,556.98
        Net Profit: +$12.34 (after fees)
```

### Profit Calculator
Calculate exact profit for a trade:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py calc \
  --buy-exchange binance \
  --sell-exchange coinbase \
  --pair ETH/USDC \
  --amount 10
```

Shows detailed breakdown:
- Gross profit
- Trading fees (both exchanges)
- Withdrawal fees
- Net profit
- Breakeven spread

## Educational Disclaimer

**FOR EDUCATIONAL PURPOSES ONLY**

Arbitrage trading involves significant risks:
- Opportunities may disappear before execution
- Price data may be delayed or inaccurate
- Fees can exceed profits on small trades
- Market conditions change rapidly

This tool provides analysis only. Do not trade without understanding the risks.

## Data Sources

- [CoinGecko API](https://www.coingecko.com/en/api) - Free price data
- [CCXT Library](https://github.com/ccxt/ccxt) - Unified exchange API
- [Uniswap Subgraph](https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3) - DEX data
- [Gas Tracker](https://etherscan.io/gastracker) - Ethereum gas prices
