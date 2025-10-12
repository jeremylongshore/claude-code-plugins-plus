---
name: openbb-equity
description: Comprehensive equity analysis using OpenBB - historical prices, fundamentals, technical indicators, insider trading, analyst ratings, and AI-powered insights
---

# OpenBB Equity Analysis

Perform comprehensive stock analysis using the OpenBB Platform.

## Usage

```bash
/openbb-equity TICKER [--analysis fundamental|technical|all] [--period 1y]
```

## What This Command Does

Retrieves and analyzes equity data for any stock ticker using OpenBB's comprehensive data sources.

## Workflow

### 1. Check OpenBB Installation

First, verify OpenBB is installed:

```python
try:
    from openbb import obb
    print("✅ OpenBB installed")
except ImportError:
    print("⚠️  Installing OpenBB...")
    import subprocess
    subprocess.run(["pip", "install", "openbb"], check=True)
    from openbb import obb
```

### 2. Parse Arguments

```python
# Parse user input
import sys
ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"
analysis_type = "all"  # fundamental, technical, or all
period = "1y"  # 1d, 1w, 1m, 3m, 6m, 1y, 5y

# Parse flags
for arg in sys.argv[2:]:
    if arg.startswith("--analysis="):
        analysis_type = arg.split("=")[1]
    elif arg.startswith("--period="):
        period = arg.split("=")[1]
```

### 3. Retrieve Historical Price Data

```python
# Get historical prices
price_data = obb.equity.price.historical(
    symbol=ticker,
    interval="1d",
    period=period
)

df = price_data.to_dataframe()
print(f"\n📈 Historical Prices for {ticker}")
print(f"Period: {period}")
print(f"Latest Close: ${df['close'].iloc[-1]:.2f}")
print(f"52-Week High: ${df['high'].max():.2f}")
print(f"52-Week Low: ${df['low'].min():.2f}")
print(f"YTD Return: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
```

### 4. Fundamental Analysis (if requested)

```python
if analysis_type in ["fundamental", "all"]:
    print(f"\n📊 Fundamental Analysis for {ticker}")

    # Company profile
    try:
        profile = obb.equity.profile(symbol=ticker)
        print(f"\nCompany: {profile.name}")
        print(f"Sector: {profile.sector}")
        print(f"Industry: {profile.industry}")
        print(f"Market Cap: ${profile.market_cap / 1e9:.2f}B")
    except:
        print("Profile data not available")

    # Financial metrics
    try:
        metrics = obb.equity.fundamental.metrics(symbol=ticker)
        print(f"\nKey Metrics:")
        print(f"P/E Ratio: {metrics.pe_ratio:.2f}")
        print(f"EPS: ${metrics.eps:.2f}")
        print(f"Dividend Yield: {metrics.dividend_yield:.2%}")
        print(f"ROE: {metrics.roe:.2%}")
    except:
        print("Metrics data not available")

    # Analyst ratings
    try:
        ratings = obb.equity.estimates.analyst(symbol=ticker)
        print(f"\nAnalyst Consensus:")
        print(f"Buy: {ratings.buy_count}")
        print(f"Hold: {ratings.hold_count}")
        print(f"Sell: {ratings.sell_count}")
        print(f"Target Price: ${ratings.target_price:.2f}")
    except:
        print("Analyst ratings not available")
```

### 5. Technical Analysis (if requested)

```python
if analysis_type in ["technical", "all"]:
    print(f"\n📉 Technical Analysis for {ticker}")

    # Calculate technical indicators
    import pandas as pd

    # Simple Moving Averages
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['SMA_200'] = df['close'].rolling(window=200).mean()

    current_price = df['close'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1]
    sma_50 = df['SMA_50'].iloc[-1]
    sma_200 = df['SMA_200'].iloc[-1]

    print(f"\nMoving Averages:")
    print(f"Current Price: ${current_price:.2f}")
    print(f"SMA 20: ${sma_20:.2f} {'🟢' if current_price > sma_20 else '🔴'}")
    print(f"SMA 50: ${sma_50:.2f} {'🟢' if current_price > sma_50 else '🔴'}")
    print(f"SMA 200: ${sma_200:.2f} {'🟢' if current_price > sma_200 else '🔴'}")

    # RSI calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    rsi = df['RSI'].iloc[-1]
    print(f"\nRSI (14): {rsi:.2f}")
    if rsi > 70:
        print("⚠️  Overbought territory")
    elif rsi < 30:
        print("🟢 Oversold territory - potential buy")
    else:
        print("Neutral zone")

    # Volume analysis
    avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
    current_volume = df['volume'].iloc[-1]
    print(f"\nVolume:")
    print(f"Current: {current_volume:,.0f}")
    print(f"20-day Avg: {avg_volume:,.0f}")
    print(f"Relative: {(current_volume / avg_volume):.2f}x")
```

### 6. AI-Powered Insights

Generate investment insights using Claude's analysis:

```python
# Prepare summary for AI analysis
summary = {
    "ticker": ticker,
    "current_price": current_price,
    "52w_high": df['high'].max(),
    "52w_low": df['low'].min(),
    "ytd_return": ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100,
    "technical": {
        "sma_position": "bullish" if current_price > sma_200 else "bearish",
        "rsi": rsi,
        "volume_trend": "high" if current_volume > avg_volume else "normal"
    }
}

print(f"\n🤖 AI Analysis for {ticker}:")
print("\nBased on the data above, here's my assessment:")
print(f"- Trend: {'Bullish' if current_price > sma_200 else 'Bearish'} (price {'above' if current_price > sma_200 else 'below'} 200-day SMA)")
print(f"- Momentum: {'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'} (RSI: {rsi:.1f})")
print(f"- Volume: {'Elevated' if current_volume > avg_volume * 1.5 else 'Normal'} trading activity")
print(f"\n💡 Recommendation: Consider {summary} in context of your investment strategy and risk tolerance.")
```

### 7. Generate Report

Create a formatted analysis report:

```python
print(f"\n{'='*60}")
print(f"EQUITY ANALYSIS REPORT: {ticker}")
print(f"{'='*60}")
print(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Data Source: OpenBB Platform")
print(f"\nAnalysis Type: {analysis_type.upper()}")
print(f"Period Analyzed: {period}")
print(f"\n{'='*60}")
```

## Examples

### Basic equity analysis
```bash
/openbb-equity AAPL
```

### Fundamental analysis only
```bash
/openbb-equity TSLA --analysis=fundamental
```

### Technical analysis with custom period
```bash
/openbb-equity NVDA --analysis=technical --period=6m
```

### Complete analysis
```bash
/openbb-equity GOOGL --analysis=all --period=1y
```

## Data Coverage

- **Price Data**: Historical OHLCV, real-time quotes
- **Fundamentals**: Income statements, balance sheets, cash flow, ratios
- **Technical**: SMA, EMA, RSI, MACD, Bollinger Bands, volume
- **Analyst Data**: Ratings, price targets, recommendations
- **Insider Trading**: Recent insider transactions
- **News**: Latest company news and sentiment

## Tips

1. **Compare Multiple Stocks**: Run for different tickers to compare
2. **Track Over Time**: Save reports to monitor changes
3. **Combine with AI Agents**: Use with equity-analyst agent for deeper insights
4. **Export Data**: Save dataframes to CSV for further analysis
5. **Set Alerts**: Monitor key technical levels (support/resistance)

## Integration with Other Commands

```bash
# Compare with crypto
/openbb-crypto BTC --compare=equity

# Portfolio context
/openbb-portfolio --add=AAPL

# Macro correlation
/openbb-macro --impact=equity
```

## Requirements

- OpenBB Platform installed (`pip install openbb`)
- Python 3.9.21 - 3.12
- Optional: API keys for premium data providers (configured in OpenBB)

## Notes

- Free tier provides delayed data (15-20 minutes)
- Premium data requires API keys (configured via `obb.user.credentials`)
- All financial data is for informational purposes only
- Not financial advice - always do your own research
