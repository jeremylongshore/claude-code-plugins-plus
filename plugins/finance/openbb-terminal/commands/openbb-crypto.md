---
name: openbb-crypto
description: Cryptocurrency market analysis using OpenBB - price data, on-chain metrics,...
---
# OpenBB Cryptocurrency Analysis

Comprehensive cryptocurrency analysis using OpenBB Platform's crypto data sources.

## Usage

```bash
/openbb-crypto SYMBOL [--vs USD|BTC|ETH] [--metrics on-chain|defi|social] [--period 30d]
```

## What This Command Does

Analyzes cryptocurrency markets with price data, on-chain metrics, DeFi analytics, and sentiment analysis.

## Workflow

### 1. Setup OpenBB Connection

```python
from openbb import obb
import pandas as pd
from datetime import datetime, timedelta

# Parse arguments
symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "BTC"
vs_currency = "USD"  # USD, BTC, ETH
metrics_type = "all"  # on-chain, defi, social, all
period = "30d"  # 7d, 30d, 90d, 1y

# Parse flags
for arg in sys.argv[2:]:
    if arg.startswith("--vs="):
        vs_currency = arg.split("=")[1].upper()
    elif arg.startswith("--metrics="):
        metrics_type = arg.split("=")[1]
    elif arg.startswith("--period="):
        period = arg.split("=")[1]
```

### 2. Retrieve Price Data

```python
# Get historical crypto prices
crypto_data = obb.crypto.price.historical(
    symbol=f"{symbol}{vs_currency}",
    interval="1d",
    period=period
)

df = crypto_data.to_dataframe()

print(f"\n₿ Crypto Analysis: {symbol}/{vs_currency}")
print(f"{'='*60}")

current_price = df['close'].iloc[-1]
period_high = df['high'].max()
period_low = df['low'].min()
period_return = ((current_price / df['close'].iloc[0]) - 1) * 100

print(f"\n💰 Price Overview:")
print(f"Current Price: ${current_price:,.2f}")
print(f"{period} High: ${period_high:,.2f}")
print(f"{period} Low: ${period_low:,.2f}")
print(f"{period} Return: {period_return:+.2f}%")
print(f"24h Volume: ${df['volume'].iloc[-1]:,.0f}")
```

### 3. Technical Indicators

```python
# Calculate crypto-specific indicators
print(f"\n📊 Technical Indicators:")

# Moving averages
df['MA_7'] = df['close'].rolling(window=7).mean()
df['MA_30'] = df['close'].rolling(window=30).mean()
df['MA_90'] = df['close'].rolling(window=90).mean()

ma_7 = df['MA_7'].iloc[-1]
ma_30 = df['MA_30'].iloc[-1]
ma_90 = df['MA_90'].iloc[-1]

print(f"MA 7:  ${ma_7:,.2f} {'🟢' if current_price > ma_7 else '🔴'}")
print(f"MA 30: ${ma_30:,.2f} {'🟢' if current_price > ma_30 else '🔴'}")
print(f"MA 90: ${ma_90:,.2f} {'🟢' if current_price > ma_90 else '🔴'}")

# Volatility
returns = df['close'].pct_change()
volatility = returns.std() * (365 ** 0.5) * 100  # Annualized

print(f"\nVolatility (ann.): {volatility:.1f}%")

# RSI
delta = df['close'].diff()
gain = delta.where(delta > 0, 0).rolling(window=14).mean()
loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))
rsi = df['RSI'].iloc[-1]

print(f"RSI (14): {rsi:.1f}")
if rsi > 70:
    print("  ⚠️  Overbought - potential sell signal")
elif rsi < 30:
    print("  🟢 Oversold - potential buy signal")
```

### 4. On-Chain Metrics (if available)

```python
if metrics_type in ["on-chain", "all"]:
    print(f"\n⛓️  On-Chain Metrics:")

    try:
        # Network activity
        network_data = obb.crypto.onchain.active_addresses(symbol=symbol)
        print(f"Active Addresses (24h): {network_data.active_addresses:,}")
        print(f"Transaction Count: {network_data.tx_count:,}")
        print(f"Transaction Volume: ${network_data.tx_volume:,.0f}")

        # Hash rate (for PoW coins)
        if symbol in ["BTC", "ETH", "LTC", "DOGE"]:
            hash_data = obb.crypto.onchain.hashrate(symbol=symbol)
            print(f"\nHash Rate: {hash_data.hashrate / 1e18:.2f} EH/s")
            print(f"Mining Difficulty: {hash_data.difficulty:,.0f}")

        # Holder distribution
        holders = obb.crypto.onchain.holders(symbol=symbol)
        print(f"\nTop 10 Holders: {holders.top_10_pct:.1f}%")
        print(f"Top 100 Holders: {holders.top_100_pct:.1f}%")

    except Exception as e:
        print(f"On-chain data not available for {symbol}")
```

### 5. DeFi Metrics (if applicable)

```python
if metrics_type in ["defi", "all"] and symbol in ["ETH", "BNB", "AVAX", "SOL"]:
    print(f"\n🏦 DeFi Metrics:")

    try:
        defi_data = obb.crypto.defi.tvl(chain=symbol)
        print(f"Total Value Locked: ${defi_data.tvl / 1e9:.2f}B")
        print(f"Protocol Count: {defi_data.protocol_count}")
        print(f"Top Protocol: {defi_data.top_protocol}")
        print(f"  - TVL: ${defi_data.top_protocol_tvl / 1e9:.2f}B")

        # Staking data
        staking = obb.crypto.defi.staking(symbol=symbol)
        print(f"\nStaking:")
        print(f"Total Staked: {staking.total_staked_pct:.1f}%")
        print(f"Avg APY: {staking.avg_apy:.2f}%")
    except:
        print(f"DeFi data not available for {symbol}")
```

### 6. Social Sentiment & News

```python
if metrics_type in ["social", "all"]:
    print(f"\n📱 Social Sentiment:")

    try:
        social_data = obb.crypto.social.sentiment(symbol=symbol)
        print(f"Twitter Mentions (24h): {social_data.twitter_mentions:,}")
        print(f"Reddit Posts (24h): {social_data.reddit_posts:,}")
        print(f"Sentiment Score: {social_data.sentiment_score:.2f}/5.0")

        sentiment_emoji = "🟢" if social_data.sentiment_score > 3.5 else "🟡" if social_data.sentiment_score > 2.5 else "🔴"
        print(f"Overall Sentiment: {sentiment_emoji}")

        # Recent news
        news = obb.crypto.news(symbol=symbol, limit=3)
        print(f"\n📰 Latest News:")
        for i, article in enumerate(news[:3], 1):
            print(f"{i}. {article.title}")
            print(f"   {article.source} - {article.published_date}")
    except:
        print("Social/news data not available")
```

### 7. Whale Activity Tracker

```python
print(f"\n🐋 Whale Activity (Large Transfers):")

try:
    # Get large transactions (>$100k)
    whales = obb.crypto.onchain.large_transactions(
        symbol=symbol,
        min_value=100000,
        limit=5
    )

    if len(whales) > 0:
        print(f"Last {len(whales)} large transfers:")
        for tx in whales:
            print(f"  ${tx.value_usd:,.0f} - {tx.from_address[:10]}...→ {tx.to_address[:10]}...")
            print(f"    {tx.timestamp} ({tx.exchange if tx.exchange else 'Unknown'})")
    else:
        print("No significant whale activity detected")
except:
    print("Whale tracking not available")
```

### 8. AI-Powered Market Analysis

```python
print(f"\n🤖 AI Market Analysis for {symbol}:")
print(f"\n📈 Trend Analysis:")

# Determine trend
if current_price > ma_7 > ma_30 > ma_90:
    trend = "Strong Uptrend"
    trend_emoji = "🚀"
elif current_price > ma_30:
    trend = "Bullish"
    trend_emoji = "📈"
elif current_price < ma_7 < ma_30 < ma_90:
    trend = "Strong Downtrend"
    trend_emoji = "📉"
else:
    trend = "Consolidating"
    trend_emoji = "↔️"

print(f"{trend_emoji} Market Trend: {trend}")

# Risk assessment
if volatility > 100:
    risk = "Very High"
    risk_emoji = "🔴"
elif volatility > 60:
    risk = "High"
    risk_emoji = "🟡"
else:
    risk = "Moderate"
    risk_emoji = "🟢"

print(f"{risk_emoji} Volatility Risk: {risk}")

# Trading signals
print(f"\n💡 Trading Signals:")
signals = []

if rsi < 30:
    signals.append("🟢 RSI oversold - potential buy zone")
if rsi > 70:
    signals.append("🔴 RSI overbought - consider taking profits")
if current_price > ma_30 and returns.iloc[-1] > 0.05:
    signals.append("🚀 Strong momentum detected")
if df['volume'].iloc[-1] > df['volume'].rolling(20).mean().iloc[-1] * 2:
    signals.append("📊 Unusual volume spike")

if signals:
    for signal in signals:
        print(f"  {signal}")
else:
    print("  No strong signals detected - market in equilibrium")
```

### 9. Price Targets & Support/Resistance

```python
print(f"\n🎯 Key Levels:")

# Calculate support and resistance
high_30d = df['high'].tail(30).max()
low_30d = df['low'].tail(30).min()
pivot = (high_30d + low_30d + current_price) / 3

resistance_1 = 2 * pivot - low_30d
support_1 = 2 * pivot - high_30d

print(f"Resistance: ${resistance_1:,.2f} ({((resistance_1/current_price - 1) * 100):+.1f}%)")
print(f"Current:    ${current_price:,.2f}")
print(f"Support:    ${support_1:,.2f} ({((support_1/current_price - 1) * 100):+.1f}%)")
```

## Examples

### Basic crypto analysis
```bash
/openbb-crypto BTC
```

### Ethereum DeFi metrics
```bash
/openbb-crypto ETH --metrics=defi
```

### Altcoin vs BTC
```bash
/openbb-crypto LINK --vs=BTC --period=90d
```

### Social sentiment check
```bash
/openbb-crypto DOGE --metrics=social
```

## Supported Cryptocurrencies

- **Major**: BTC, ETH, BNB, SOL, ADA, XRP, DOT, AVAX
- **DeFi**: UNI, AAVE, LINK, COMP, MKR, SNX
- **Meme**: DOGE, SHIB, PEPE
- **Layer 2**: MATIC, ARB, OP
- **1000+ more via OpenBB data providers**

## Data Sources

- Price data: Multiple exchanges (Binance, Coinbase, etc.)
- On-chain: Glassnode, Santiment, IntoTheBlock
- DeFi: DeFi Llama, The Graph
- Social: LunarCrush, Santiment

## Tips

1. **Compare to BTC**: Use `--vs=BTC` to see altcoin strength vs Bitcoin
2. **Track Whales**: Monitor large transfers for market-moving activity
3. **DeFi Context**: Check TVL and staking for ecosystem health
4. **Sentiment Analysis**: Social metrics can predict short-term moves
5. **Correlation**: Compare multiple cryptos to find divergences

## Integration

```bash
# Portfolio tracking
/openbb-portfolio --add-crypto=BTC,ETH,SOL

# Compare with equity markets
/openbb-macro --crypto-correlation

# AI research
/openbb-research --crypto --symbol=BTC
```

## Notes

- Cryptocurrency markets are 24/7
- High volatility - use appropriate risk management
- Not financial advice - DYOR (Do Your Own Research)
- Consider transaction costs and slippage for trading
