---
name: openbb-options
description: Options analysis using OpenBB - chain data, Greeks, implied volatility,...
---
# OpenBB Options Analysis

Options chain analysis, Greeks calculations, and strategy optimization using OpenBB Platform.

## Usage

```bash
/openbb-options TICKER [--strategy covered-call|put|spread] [--expiry 30d]
```

## Key Features

### Options Data
- Options chains (calls/puts, all strikes)
- Greeks (Delta, Gamma, Theta, Vega, Rho)
- Implied volatility smile/skew
- Open interest and volume analysis
- Unusual options activity

### Workflow

```python
from openbb import obb

ticker = "AAPL"
expiry = "2024-12-20"

# Get options chain
chain = obb.derivatives.options.chains(symbol=ticker, expiration=expiry)

# Analyze call options
calls = chain[chain['option_type'] == 'call']
print(f"\n📞 Call Options for {ticker} (Exp: {expiry})")
print(f"{'Strike':>8} {'Last':>8} {'IV':>8} {'Delta':>8} {'OI':>10} {'Volume':>10}")

for _, opt in calls.iterrows():
    print(f"${opt['strike']:>7.2f} ${opt['last']:>7.2f} {opt['iv']:>7.1f}% "
          f"{opt['delta']:>7.3f} {opt['open_interest']:>9,} {opt['volume']:>9,}")

# Greeks summary
print(f"\n🔢 Portfolio Greeks:")
print(f"Net Delta: {calls['delta'].sum():.2f}")
print(f"Net Gamma: {calls['gamma'].sum():.4f}")
print(f"Net Theta: {calls['theta'].sum():.2f} (daily decay)")
print(f"Net Vega: {calls['vega'].sum():.2f} (per 1% IV move)")
```

### Strategy Analysis

```python
# Covered Call Strategy
stock_price = obb.equity.price.quote(symbol=ticker).price
strike = stock_price * 1.05  # 5% OTM

call_premium = chain[(chain['strike'] == strike) & (chain['option_type'] == 'call')]['last'].iloc[0]

print(f"\n📊 Covered Call Strategy ({ticker}):")
print(f"Stock Price: ${stock_price:.2f}")
print(f"Sell Call: ${strike:.2f} strike")
print(f"Premium: ${call_premium:.2f}")
print(f"Max Profit: ${(strike - stock_price + call_premium):.2f} ({((strike - stock_price + call_premium) / stock_price * 100):.1f}%)")
print(f"Breakeven: ${(stock_price - call_premium):.2f}")
```

### Unusual Activity

```python
# Detect unusual options activity
unusual = chain[chain['volume'] > chain['open_interest'] * 2]
print(f"\n🚨 Unusual Activity ({len(unusual)} contracts):")

for _, opt in unusual.head(5).iterrows():
    print(f"{opt['option_type'].upper()} ${opt['strike']:.2f} - "
          f"Vol: {opt['volume']:,} (OI: {opt['open_interest']:,})")
```

## Examples

```bash
/openbb-options SPY --strategy=covered-call
/openbb-options TSLA --expiry=14d
/openbb-options NVDA --unusual-activity
```
