# Crypto Portfolio Tracker Plugin

Professional-grade cryptocurrency portfolio tracking and analysis for Claude Code, providing institutional-quality metrics, risk assessment, and optimization recommendations.

## Features

###  Position Tracking
- **Real-time price updates** from multiple exchanges (CoinGecko, Binance, Coinbase)
- **Comprehensive PnL calculations** with entry/exit tracking
- **Multi-exchange support** for accurate pricing
- **Stop-loss and take-profit monitoring**
- **Position history** with complete audit trail
- **Alert system** for significant price movements

###  Portfolio Analysis
- **Risk metrics**: Sharpe ratio, Sortino ratio, maximum drawdown
- **Volatility analysis**: Daily, weekly, monthly, and annual
- **Correlation matrix**: Identify over-concentrated positions
- **Value at Risk (VaR)**: 95% and 99% confidence levels
- **Herfindahl Index**: Measure portfolio concentration
- **Performance attribution**: Understand what's driving returns

###  Rebalancing Engine
- **Optimal allocation** calculations using Modern Portfolio Theory
- **Automated rebalancing** recommendations
- **Tax-aware** trading suggestions
- **Cost estimation** for rebalancing actions
- **Threshold-based** or time-based rebalancing

###  Advanced Analytics
- **Risk-adjusted returns** optimization
- **Diversification scoring**
- **Market regime detection**
- **Drawdown analysis**
- **Monte Carlo simulations** for future scenarios

## Installation

```bash
/plugin install crypto-portfolio-tracker@claude-code-plugins-plus
```

## Usage

### Track a New Position

```
/track-position

I'll help you track a crypto position. Please provide:
- Symbol (BTC, ETH, etc.)
- Entry price
- Quantity
- Entry date
- Target price (optional)
- Stop loss (optional)
```

### Analyze Portfolio

```
/portfolio-analysis

Analyzing your complete crypto portfolio...
- Calculating risk metrics
- Evaluating diversification
- Generating rebalancing recommendations
```

### Set Price Alerts

```
/set-alert BTC above 50000
/set-alert ETH below 2000
/set-alert SOL volatility 20%
```

## Configuration

Create a `.crypto-portfolio.json` configuration file in your project root:

```json
{
  "priceFeeds": {
    "primary": "coingecko",
    "fallback": ["binance", "coinbase"],
    "updateInterval": 300
  },
  "alerts": {
    "profitTarget": 0.20,
    "lossWarning": -0.10,
    "criticalLoss": -0.25,
    "volatilitySpike": 0.15
  },
  "rebalancing": {
    "strategy": "threshold",
    "threshold": 0.15,
    "frequency": "monthly",
    "minTradeSize": 100,
    "taxStrategy": "FIFO"
  },
  "riskManagement": {
    "maxPositionSize": 0.30,
    "maxDrawdown": 0.35,
    "stopLossDefault": 0.25
  }
}
```

## Commands

### Position Management

| Command | Description | Shortcut |
|---------|-------------|----------|
| `/track-position` | Track a new crypto position | `tp` |
| `/update-position` | Update an existing position | `up` |
| `/close-position` | Close and record a position | `cp` |
| `/position-history` | View position history | `ph` |

### Analytics

| Command | Description | Shortcut |
|---------|-------------|----------|
| `/portfolio-analysis` | Full portfolio analysis | `pa` |
| `/risk-metrics` | Calculate risk metrics | `rm` |
| `/correlation-matrix` | View correlations | `cm` |
| `/rebalancing-plan` | Get rebalancing suggestions | `rp` |

### Alerts & Monitoring

| Command | Description | Shortcut |
|---------|-------------|----------|
| `/set-alert` | Set price alerts | `sa` |
| `/view-alerts` | View active alerts | `va` |
| `/alert-history` | View triggered alerts | `ah` |

## Database Schema

The plugin uses a structured database to track all portfolio data:

```sql
-- Main positions table
CREATE TABLE crypto_positions (
    id UUID PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    entry_date TIMESTAMP NOT NULL,
    current_price DECIMAL(20,8),
    target_price DECIMAL(20,8),
    stop_loss DECIMAL(20,8),
    status VARCHAR(20) DEFAULT 'open',
    exchange VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Position history for tracking changes
CREATE TABLE position_history (
    id UUID PRIMARY KEY,
    position_id UUID REFERENCES crypto_positions(id),
    price DECIMAL(20,8) NOT NULL,
    value DECIMAL(20,8) NOT NULL,
    pnl DECIMAL(20,8) NOT NULL,
    pnl_percentage DECIMAL(10,4) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts configuration
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    position_id UUID REFERENCES crypto_positions(id),
    alert_type VARCHAR(50) NOT NULL,
    condition VARCHAR(20) NOT NULL,
    threshold DECIMAL(20,8) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Integration

The plugin integrates with multiple cryptocurrency data sources:

### CoinGecko API
- Real-time prices for 10,000+ cryptocurrencies
- Historical price data
- Market cap and volume information

### Binance API
- Real-time trading data
- Order book depth
- 24-hour statistics

### Coinbase API
- Institutional-grade price feeds
- Historical OHLCV data
- Real-time WebSocket streams

## Risk Metrics Explained

### Sharpe Ratio
Measures risk-adjusted returns. Values:
- < 0: Poor (returns below risk-free rate)
- 0-0.5: Suboptimal
- 0.5-1.0: Acceptable
- 1.0-2.0: Good
- > 2.0: Excellent

### Value at Risk (VaR)
Statistical measure of potential loss:
- 95% VaR: Maximum loss expected 95% of the time
- 99% VaR: Maximum loss expected 99% of the time

### Maximum Drawdown
Largest peak-to-trough decline:
- < 10%: Low risk
- 10-20%: Moderate risk
- 20-30%: Elevated risk
- > 30%: High risk

### Herfindahl Index
Measures portfolio concentration:
- < 0.15: Well diversified
- 0.15-0.25: Moderate concentration
- > 0.25: High concentration

## Performance Optimization

### Caching Strategy
- Price data cached for 5 minutes
- Historical data cached for 24 hours
- Correlation matrices cached for 1 hour

### Rate Limiting
- Automatic rate limit handling
- Exponential backoff on API errors
- Fallback to secondary data sources

### Batch Operations
- Batch price updates for efficiency
- Grouped database writes
- Optimized correlation calculations

## Security Considerations

### API Key Management
- Store API keys in environment variables
- Never commit keys to version control
- Use read-only keys where possible

### Data Privacy
- Local database storage by default
- Optional encryption for sensitive data
- No third-party data sharing

### Input Validation
- Sanitize all user inputs
- Validate cryptocurrency symbols
- Check numerical bounds

## Troubleshooting

### Common Issues

**Price data not updating**
- Check API key configuration
- Verify internet connectivity
- Check rate limits

**Incorrect PnL calculations**
- Verify entry prices and dates
- Check for stock splits or airdrops
- Ensure correct quantity tracking

**High correlation warnings**
- Review asset selection
- Consider adding uncorrelated assets
- Check time period for correlation calculation

## Advanced Features

### Tax Reporting
- FIFO/LIFO cost basis tracking
- Capital gains calculations
- Export to TurboTax/CoinTracker format

### Backtesting
- Test strategies on historical data
- Monte Carlo simulations
- Walk-forward analysis

### Automation
- Automated rebalancing execution
- Stop-loss order placement
- DCA (Dollar Cost Averaging) scheduling

## Performance Benchmarks

- Position tracking: < 100ms
- Portfolio analysis: < 2 seconds for 50 positions
- Correlation calculation: < 500ms for 20 assets
- Rebalancing optimization: < 1 second

## Contributing

This plugin is part of the Claude Code Plugins marketplace. To contribute:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

- GitHub Issues: [Report bugs](https://github.com/jeremylongshore/claude-code-plugins/issues)
- Discord: Join the Claude Code community
- Documentation: [Full API docs](https://docs.claude-code-plugins.com)

## Changelog

### v1.0.0 (2024-10-11)
- Initial release
- Position tracking with real-time updates
- Portfolio analysis with risk metrics
- Rebalancing recommendations
- Alert system
- Multi-exchange price feeds

---

*Built with ️ for crypto investors by Intent Solutions IO*