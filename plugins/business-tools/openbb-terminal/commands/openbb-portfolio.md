---
name: openbb-portfolio
description: Portfolio analysis and optimization using OpenBB - performance tracking,...
---
# OpenBB Portfolio Analysis

Comprehensive portfolio management and optimization using OpenBB Platform.

## Usage

```bash
/openbb-portfolio [--analyze] [--optimize] [--benchmark SPY]
```

## What This Command Does

Analyzes portfolio performance, calculates risk metrics, and provides optimization recommendations.

## Key Features

### Portfolio Metrics
- **Returns**: Total return, annualized, Sharpe ratio, Sortino ratio
- **Risk**: Volatility, max drawdown, VaR, conditional VaR
- **Allocation**: Asset mix, sector exposure, geographic distribution
- **Performance Attribution**: Contribution analysis by position

### Workflow

```python
from openbb import obb
import pandas as pd

# Define portfolio (can load from file or define inline)
portfolio = {
    "AAPL": {"shares": 50, "cost_basis": 150.00},
    "MSFT": {"shares": 30, "cost_basis": 300.00},
    "GOOGL": {"shares": 20, "cost_basis": 2500.00},
    "BTC-USD": {"shares": 0.5, "cost_basis": 45000.00}
}

# Calculate current values
total_value = 0
positions = []

for symbol, data in portfolio.items():
    current_price = obb.equity.price.quote(symbol=symbol).price
    position_value = current_price * data["shares"]
    total_value += position_value

    pnl = (current_price - data["cost_basis"]) * data["shares"]
    pnl_pct = (current_price / data["cost_basis"] - 1) * 100

    positions.append({
        "symbol": symbol,
        "shares": data["shares"],
        "cost_basis": data["cost_basis"],
        "current_price": current_price,
        "value": position_value,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "weight": 0  # Calculate after total_value known
    })

# Calculate weights
for pos in positions:
    pos["weight"] = (pos["value"] / total_value) * 100

# Display portfolio
print(f"\n💼 Portfolio Overview")
print(f"{'='*80}")
print(f"Total Value: ${total_value:,.2f}\n")
print(f"{'Symbol':<10} {'Shares':>10} {'Price':>12} {'Value':>15} {'P/L %':>10} {'Weight':>10}")
print(f"{'-'*80}")

for pos in positions:
    print(f"{pos['symbol']:<10} {pos['shares']:>10.2f} ${pos['current_price']:>11.2f} "
          f"${pos['value']:>14.2f} {pos['pnl_pct']:>9.1f}% {pos['weight']:>9.1f}%")
```

### Risk Analysis

```python
# Calculate portfolio-level risk metrics
returns = []
for symbol in portfolio.keys():
    hist = obb.equity.price.historical(symbol=symbol, period="1y")
    returns.append(hist.to_dataframe()['close'].pct_change())

portfolio_returns = pd.concat(returns, axis=1).mean(axis=1)
portfolio_vol = portfolio_returns.std() * (252 ** 0.5) * 100  # Annualized

# Sharpe Ratio (assuming 4% risk-free rate)
risk_free_rate = 0.04
sharpe = (portfolio_returns.mean() * 252 - risk_free_rate) / (portfolio_returns.std() * (252 ** 0.5))

# Max Drawdown
cumulative = (1 + portfolio_returns).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max
max_dd = drawdown.min() * 100

print(f"\n📊 Risk Metrics:")
print(f"Annualized Volatility: {portfolio_vol:.2f}%")
print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Max Drawdown: {max_dd:.2f}%")
```

### Portfolio Optimization

```python
print(f"\n🎯 Optimization Recommendations:")

# Diversification score
diversification = 100 - max([pos['weight'] for pos in positions])
print(f"Diversification Score: {diversification:.0f}/100")

if diversification < 70:
    print("⚠️  Portfolio concentrated - consider adding positions")

# Rebalancing suggestions
target_weight = 100 / len(positions)
rebalance_needed = []

for pos in positions:
    diff = abs(pos['weight'] - target_weight)
    if diff > 10:
        action = "Reduce" if pos['weight'] > target_weight else "Increase"
        rebalance_needed.append(f"{action} {pos['symbol']}: {pos['weight']:.1f}% → {target_weight:.1f}%")

if rebalance_needed:
    print(f"\n🔄 Rebalancing Suggestions:")
    for suggestion in rebalance_needed:
        print(f"  • {suggestion}")
```

## Examples

```bash
# Analyze current portfolio
/openbb-portfolio --analyze

# Optimize allocation
/openbb-portfolio --optimize

# Compare to SPY benchmark
/openbb-portfolio --benchmark=SPY
```

## Integration

- Import positions from CSV/Excel
- Export reports to PDF
- Sync with brokerage accounts (via supported integrations)
- Tax-loss harvesting analysis
