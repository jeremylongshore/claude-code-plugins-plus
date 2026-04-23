# 📊 OpenBB Terminal - AI-Powered Investment Research

**Professional-grade financial analysis powered by OpenBB Platform** - Comprehensive equity research, cryptocurrency analysis, macroeconomic insights, and portfolio management, all integrated with Claude's AI capabilities.

---

## 🎯 What This Plugin Does

Transform Claude Code into a powerful investment research terminal using OpenBB's open-source financial data platform.

**Features**:
- 📈 **Equity Analysis** - Stocks, fundamentals, technicals, analyst ratings
- 💰 **Crypto Analysis** - On-chain metrics, DeFi, whale tracking, sentiment
- 🌍 **Macro Economics** - GDP, inflation, rates, employment data
- 💼 **Portfolio Management** - Performance tracking, optimization, rebalancing
- 📊 **Options Analysis** - Chains, Greeks, strategies, unusual activity
- 🤖 **AI Research** - Automated investment thesis generation

---

## 🚀 Quick Start

### Installation

```bash
# Add marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install OpenBB Terminal plugin
/plugin install openbb-terminal@claude-code-plugins-plus
```

### Prerequisites

```bash
# Install OpenBB Platform (Python 3.9.21 - 3.12)
pip install openbb

# Optional: Install with specific data providers
pip install openbb[all]  # All providers
pip install openbb[yfinance]  # Just Yahoo Finance
```

### Basic Usage

```bash
# Analyze a stock
/openbb-equity AAPL

# Check crypto market
/openbb-crypto BTC

# Review portfolio
/openbb-portfolio --analyze

# Macro overview
/openbb-macro --country=US

# Options analysis
/openbb-options SPY

# AI research report
/openbb-research TSLA --depth=deep
```

---

## FREE Data Sources: No Paid Subscriptions Required

**Use OpenBB Terminal with 100% free data providers** - no Bloomberg, Refinitiv, or premium API costs.

### Quick Comparison

| Data Type | Paid Providers | FREE Providers |
|-----------|---------------|----------------|
| **Stock Data** | Bloomberg ($20K+/year) | Yahoo Finance: **$0** |
| **Crypto Data** | CoinMetrics ($500+/mo) | CoinGecko API: **$0** |
| **Options Data** | Intrinio ($200+/mo) | CBOE/NASDAQ (free): **$0** |
| **Macro Data** | Refinitiv ($1K+/mo) | FRED (Federal Reserve): **$0** |
| **Fundamentals** | FactSet ($12K+/year) | Alpha Vantage (free tier): **$0** |

**Annual Savings: $25,000-50,000** for professional-grade data.

### Why Free Data Providers?

**Benefits:**
- **Zero Cost:** No subscription fees or API charges
- **Professional Quality:** Same data hedge funds use
- **No Rate Limits:** (with Yahoo Finance and FRED)
- **Real-Time Data:** 15-min delay for stocks, real-time for crypto
- **Global Coverage:** 50K+ stocks, 10K+ cryptos, 180+ countries

**Free Provider Ecosystem:**
- **Yahoo Finance** - Stocks, ETFs, indices, historical data
- **Alpha Vantage** - Fundamentals, technicals, forex (500 calls/day free)
- **FRED (Federal Reserve)** - 817K economic time series
- **CoinGecko** - 10K+ cryptos, free API
- **CBOE/NASDAQ** - Options chains (15-min delay)
- **SEC EDGAR** - 10-K, 10-Q, insider trades
- **Census Bureau** - US economic data
- **World Bank** - Global development indicators

### Setup Guide (Free Tier Only)

#### 1. Install OpenBB with Free Providers

```bash
# Install OpenBB Platform
pip install openbb

# Install ONLY free provider packages
pip install openbb[yfinance]  # Yahoo Finance (FREE)

# No need for paid providers!
```

#### 2. Configure Free API Keys (Optional)

```python
from openbb import obb

# Alpha Vantage (FREE tier: 500 calls/day)
# Get free key at: https://www.alphavantage.co/support/#api-key
obb.user.credentials.alpha_vantage_api_key = "YOUR_FREE_KEY"

# FRED (FREE, unlimited)
# Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html
obb.user.credentials.fred_api_key = "YOUR_FREE_KEY"

# Save configuration
obb.user.save()
```

**No credit card required for any of these keys.**

#### 3. Use Free Data Sources

```python
from openbb import obb

# Stock data (Yahoo Finance - FREE)
stock_data = obb.equity.price.historical(
    symbol="AAPL",
    provider="yfinance"  # FREE
)

# Crypto data (CoinGecko - FREE)
crypto_data = obb.crypto.price.historical(
    symbol="BTC",
    provider="coingecko"  # FREE
)

# Macro data (FRED - FREE)
gdp_data = obb.economy.gdp(
    country="US",
    provider="fred"  # FREE
)

# Options data (CBOE - FREE)
options_chains = obb.derivatives.options.chains(
    symbol="SPY",
    provider="cboe"  # FREE
)
```

### Cost Comparison

#### Premium Approach (Paid)

**Annual Subscriptions:**
- Bloomberg Terminal: $24,000/year
- Refinitiv Eikon: $12,000/year
- FactSet: $12,000/year
- Intrinio: $2,400/year
- CoinMetrics Pro: $6,000/year
- **Total: $56,400/year**

#### Free Approach (This Plugin)

**Annual Subscriptions:**
- Yahoo Finance: $0
- Alpha Vantage (free tier): $0
- FRED: $0
- CoinGecko: $0
- SEC EDGAR: $0
- **Total: $0/year**

**Savings: $56,400/year** with comparable data quality.

### Free vs Paid: Data Quality Comparison

| Metric | Paid (Bloomberg) | FREE (Yahoo + FRED) |
|--------|------------------|---------------------|
| **Stock Prices** | Real-time | 15-min delay ⚠️ |
| **Historical Data** | 30+ years | 20+ years ✅ |
| **Fundamentals** | Instant updates | Daily updates ✅ |
| **Macro Data** | Proprietary | Official (Fed, Census) ✅ |
| **Options Chains** | Real-time | 15-min delay ⚠️ |
| **Crypto Data** | Premium exchanges | CoinGecko aggregate ✅ |
| **Cost** | $24K/year | $0/year ✅ |

**15-min delay is acceptable for 99% of investors** (day traders excluded).

### Migration Examples

#### Before (Paid Premium)

```python
# Using Bloomberg (requires $24K/year subscription)
import blpapi

session = blpapi.Session()
session.start()
# ... Bloomberg API calls
```

**Annual Cost:** $24,000

#### After (Free Providers)

```python
# Using Yahoo Finance (FREE)
from openbb import obb

data = obb.equity.price.historical(
    symbol="AAPL",
    provider="yfinance"
)
```

**Annual Cost:** $0

**Same historical data, zero cost.**

### Real Use Cases with Free Data

#### 1. Stock Portfolio Analysis

```python
from openbb import obb

# Get stock data (Yahoo Finance - FREE)
aapl = obb.equity.price.historical("AAPL", provider="yfinance")
msft = obb.equity.price.historical("MSFT", provider="yfinance")
googl = obb.equity.price.historical("GOOGL", provider="yfinance")

# Fundamentals (Alpha Vantage - FREE)
aapl_fundamentals = obb.equity.fundamental.overview(
    "AAPL",
    provider="alpha_vantage"
)
```

**Cost:** $0 (vs Bloomberg: $24K/year)

#### 2. Crypto Market Analysis

```python
# Crypto prices (CoinGecko - FREE)
btc = obb.crypto.price.historical("BTC", provider="coingecko")
eth = obb.crypto.price.historical("ETH", provider="coingecko")

# Market cap, volume, 24h change - all FREE
```

**Cost:** $0 (vs CoinMetrics: $6K/year)

#### 3. Macroeconomic Research

```python
# US GDP (FRED - FREE)
gdp = obb.economy.gdp(country="US", provider="fred")

# Inflation (FRED - FREE)
cpi = obb.economy.cpi(country="US", provider="fred")

# Unemployment (FRED - FREE)
unemployment = obb.economy.unemployment(country="US", provider="fred")
```

**Cost:** $0 (vs Refinitiv: $12K/year)

### Free Tier Limitations

**Alpha Vantage Free Tier:**
- 500 API calls/day (enough for most users)
- 5 API calls/minute
- Solution: Cache data locally

**Yahoo Finance:**
- No official rate limits (generous)
- 15-minute delay on real-time data
- Solution: Perfect for investors (not day traders)

**CoinGecko:**
- 10-50 calls/minute (free)
- Solution: More than enough for crypto analysis

### When Free Data Is NOT Enough

**Use paid providers if:**
- You're a day trader (need real-time data)
- You trade options actively (need instant chains)
- You need proprietary alternative data
- Your firm requires Bloomberg for compliance
- You manage $10M+ AUM professionally

**For everyone else:** Free data providers are sufficient.

### Hybrid Approach: Mostly Free

**Best of both worlds:** Use free data 95% of the time, paid for critical needs.

```python
from openbb import obb

# Default to FREE providers
obb.user.preferences.data_source = "yfinance"  # FREE

# Only use paid when specifically needed
critical_data = obb.equity.price.historical(
    symbol="AAPL",
    provider="polygon"  # Paid (only when required)
)
```

**Cost Reduction:** 95% savings ($1,200/year vs $24K/year)

### Resources

- **Yahoo Finance:** [finance.yahoo.com](https://finance.yahoo.com) (FREE forever)
- **Alpha Vantage:** [alphavantage.co](https://www.alphavantage.co) (FREE tier)
- **FRED API:** [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api) (FREE)
- **CoinGecko:** [coingecko.com/api](https://www.coingecko.com/api) (FREE tier)
- **OpenBB Docs:** [docs.openbb.co](https://docs.openbb.co/platform)

**Bottom Line:** For 99% of investors, free data providers offer Bloomberg-quality data at $0/year.

---

## ⚠️ Rate Limits & API Requirements

**IMPORTANT:** Tom (@TomLucidor) asked us to document the REAL constraints. Here they are - no marketing, just facts.

### Free API Comparison Table

| Provider | Daily Limit | Per-Minute | Registration | API Key | IP Tracking | Best For |
|----------|-------------|------------|--------------|---------|-------------|----------|
| **Yahoo Finance** | ~2,000/hour | ~100/min | ❌ No | ❌ No | ⚠️ Soft bans | Stock quotes, historical data |
| **Alpha Vantage** | **25/day** | **5/min** | ✅ Email | ✅ Required | ✅ Yes | Fundamentals, technicals |
| **FRED** | Unlimited | 120/min | ✅ Email | ✅ Required | ❌ No | Economic data |
| **SEC EDGAR** | Unlimited | **10/sec** | ❌ No | ❌ No | ⚠️ User-Agent | Company filings |
| **CoinGecko** | Unlimited | **50/min** | ❌ Optional | ❌ Optional | ⚠️ Soft limits | Crypto data |
| **IEX Cloud** | 50K/month | 100/sec | ✅ Email | ✅ Required | ❌ No | Stock data (free tier) |

### Detailed Limits by Provider

#### 1. Alpha Vantage (Fundamentals & Technicals)

**FREE TIER REALITY:**
- ❌ **NOT 500/day** (that's outdated info from 2018)
- ✅ **Actually 25 API calls/day** (since 2022)
- ✅ **5 calls/minute max**
- ✅ **Email signup required** (no credit card)
- ✅ **Single IP per API key**

**Registration Steps:**
1. Go to: https://www.alphavantage.co/support/#api-key
2. Enter email (no verification link, instant key)
3. Copy API key (starts with uppercase letters)
4. Add to OpenBB: `obb.user.credentials.alpha_vantage_api_key = "KEY"`

**Agent Strategy for 25/day Limit:**
```python
# Strategy 1: Cache aggressively (24-hour TTL)
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_fundamentals(symbol):
    # Cached for full day
    return obb.equity.fundamental.overview(
        symbol=symbol,
        provider="alpha_vantage"
    )

# Strategy 2: Batch symbols intelligently
symbols_to_analyze = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]

# Don't use all 25 calls on 25 stocks!
# Use 1 call for overview, then cache
for symbol in symbols_to_analyze[:25]:  # Max 25
    data = get_fundamentals(symbol)  # Only fetches once per symbol

# Strategy 3: Fallback chain
def get_stock_data(symbol):
    try:
        # Try Alpha Vantage first (most detailed)
        return obb.equity.price.historical(symbol, provider="alpha_vantage")
    except RateLimitError:
        # Fallback to Yahoo Finance (unlimited)
        return obb.equity.price.historical(symbol, provider="yfinance")
```

**When You Hit the Limit:**
- Error: `"Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 25 calls per day."`
- Wait time: 24 hours until reset (resets at midnight UTC)
- Workaround: Use Yahoo Finance for price data, only use Alpha Vantage for fundamentals

**Upgrade Path:**
- $49.99/month: 75 calls/minute, 100K calls/month
- Probably not worth it - use Yahoo Finance instead

#### 2. Yahoo Finance (Stock Quotes & Historical Data)

**FREE TIER REALITY:**
- ✅ **~2,000 requests/hour** (undocumented soft limit)
- ✅ **~100 requests/minute**
- ✅ **No registration** (truly anonymous)
- ✅ **No API key** (uses Python library yfinance)
- ⚠️ **IP tracking** (can get soft-banned for aggressive scraping)

**How It Actually Works:**
```python
# Yahoo Finance doesn't have "official" API
# Uses yfinance library which scrapes website

import yfinance as yf

# This doesn't count against Alpha Vantage limit
ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1y")  # FREE, unlimited (sort of)
```

**Agent Strategy for IP-Based Limits:**
```python
# Strategy 1: Respect rate limits (self-impose)
import time

class YFinanceCoordinator:
    def __init__(self):
        self.last_request = 0
        self.min_interval = 0.1  # 100ms between requests

    def get_data(self, symbol):
        # Wait if needed
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        # Make request
        data = yf.Ticker(symbol).history(period="1d")
        self.last_request = time.time()
        return data

# Strategy 2: Batch downloads (yfinance supports this!)
symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
data = yf.download(
    tickers=symbols,
    period="1mo",
    group_by='ticker',
    threads=True  # Parallel downloads (faster but more aggressive)
)

# Strategy 3: Cache locally
import pandas as pd
from datetime import datetime, timedelta

def get_cached_data(symbol, cache_hours=6):
    cache_file = f"/tmp/yf_{symbol}.csv"

    # Check cache age
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < cache_hours * 3600:
            return pd.read_csv(cache_file)

    # Fetch fresh data
    data = yf.Ticker(symbol).history(period="1y")
    data.to_csv(cache_file)
    return data
```

**When You Get Soft-Banned:**
- Symptom: Empty DataFrames or 404 errors
- Duration: Usually 1 hour
- Workaround: Use residential proxy or wait
- Prevention: Add 100ms delay between requests

#### 3. SEC EDGAR (Company Filings)

**FREE TIER REALITY:**
- ✅ **Unlimited requests** (government data, public domain)
- ⚠️ **10 requests/second limit** (hard limit since 2021)
- ⚠️ **User-Agent header REQUIRED** (must include email or get 403)
- ✅ **No registration**
- ✅ **No API key**

**Registration Requirements:**
None! But you MUST set a User-Agent header with your email:

```python
import requests

headers = {
    'User-Agent': 'YourCompany yourname@email.com'  # REQUIRED
}

# This works
response = requests.get(
    'https://www.sec.gov/cgi-bin/browse-edgar',
    headers=headers
)

# This gets 403 Forbidden
response = requests.get(
    'https://www.sec.gov/cgi-bin/browse-edgar'  # Missing User-Agent
)
```

**Agent Strategy for 10/sec Limit:**
```python
import time
from collections import deque

class EDGARRateLimiter:
    def __init__(self):
        self.requests = deque(maxlen=10)  # Track last 10 requests

    def make_request(self, url):
        # Wait if we've made 10 requests in last second
        if len(self.requests) == 10:
            elapsed = time.time() - self.requests[0]
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

        # Make request
        self.requests.append(time.time())
        return requests.get(url, headers={
            'User-Agent': 'OpenBB Terminal research@example.com'
        })

# Use with OpenBB
edgar = EDGARRateLimiter()
filings = edgar.make_request(
    f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AAPL'
)
```

#### 4. CoinGecko (Cryptocurrency Data)

**FREE TIER REALITY:**
- ✅ **Unlimited requests/day** (generous free tier)
- ⚠️ **50 calls/minute** (soft limit)
- ✅ **No registration** (optional for higher limits)
- ✅ **No API key** (optional)

**With Free API Key (Optional):**
- 30-50 calls/minute (still free)
- More stable rate limits
- Get key at: https://www.coingecko.com/en/api

**Agent Strategy:**
```python
# CoinGecko is actually generous - just add small delay
import time

def get_crypto_data(coin_id):
    time.sleep(1.2)  # 50/min = 1.2s per request
    return obb.crypto.price.historical(
        symbol=coin_id,
        provider="coingecko"
    )
```

### Multi-Agent Resource Management (Single IP)

**Scenario: 5 AI Agents Analyzing 100 Stocks**

```python
# DON'T: Each agent hammers APIs independently
# BAD - Will hit all rate limits in minutes!
for agent in agents:
    for stock in stocks:
        data = agent.fetch_data(stock)  # 500 API calls!

# DO: Centralized quota coordinator
class FinancialDataCoordinator:
    def __init__(self):
        self.alpha_vantage_calls_today = 0
        self.alpha_vantage_max = 25
        self.yfinance_last_request = 0
        self.cache = {}

    def get_data(self, symbol, agent_id):
        # Check cache first
        if symbol in self.cache:
            return self.cache[symbol]

        # Try Yahoo Finance (unlimited-ish)
        try:
            data = self.fetch_yfinance(symbol)
            self.cache[symbol] = data
            return data
        except RateLimitError:
            pass

        # Fallback to Alpha Vantage (use quota wisely)
        if self.alpha_vantage_calls_today < self.alpha_vantage_max:
            data = self.fetch_alpha_vantage(symbol)
            self.alpha_vantage_calls_today += 1
            self.cache[symbol] = data
            return data

        # Out of quota - return cached or error
        raise QuotaExceededError(f"Out of API calls. Used {self.alpha_vantage_calls_today}/25 Alpha Vantage calls today")

# All 5 agents share the same coordinator
coordinator = FinancialDataCoordinator()
for agent in agents:
    agent.data_source = coordinator
```

### Upgrade Paths (When Free Tier Isn't Enough)

| Your Problem | Solution | Cost |
|--------------|----------|------|
| Alpha Vantage 25/day too low | Upgrade to $49.99/mo | $600/year (still way cheaper than Bloomberg) |
| Yahoo Finance soft bans | Use IEX Cloud 50K/month free | $0 |
| Need real-time data | Upgrade to IEX Cloud $9/mo | $108/year |
| Need 100% uptime | Use Polygon.io $29/mo | $348/year |
| Bloomberg-level features | Still 10x cheaper | $600-3,000/year vs $24K+ |

### Summary: Can You Run 10 Agents on One IP?

**✅ YES** - if you're smart about it:

| Provider | Single IP Strategy | Max Agents Supported |
|----------|-------------------|---------------------|
| Yahoo Finance | Shared cache, 100ms delays | 10-20 agents |
| Alpha Vantage | Centralized quota (25/day total) | Unlimited agents (shared quota) |
| FRED | No limits! | Unlimited |
| SEC EDGAR | 10/sec shared limit | 5-10 agents |
| CoinGecko | 50/min shared | 10+ agents |

**Key: Agents must coordinate, not compete for quota.**

---

## 💡 Core Commands (6)

### 1. `/openbb-equity` - Stock Analysis

Complete equity analysis with fundamentals, technicals, and AI insights.

```bash
# Basic analysis
/openbb-equity AAPL

# Fundamental focus
/openbb-equity MSFT --analysis=fundamental

# Technical with custom period
/openbb-equity NVDA --analysis=technical --period=6m

# Complete deep-dive
/openbb-equity GOOGL --analysis=all --period=1y
```

**Provides**:
- Historical price data (OHLCV)
- Company fundamentals (P/E, EPS, ROE, margins)
- Analyst ratings and price targets
- Technical indicators (SMA, RSI, volume)
- AI-powered investment insights

---

### 2. `/openbb-crypto` - Cryptocurrency Analysis

Comprehensive crypto market analysis with on-chain data.

```bash
# Bitcoin analysis
/openbb-crypto BTC

# Ethereum DeFi metrics
/openbb-crypto ETH --metrics=defi

# Altcoin vs Bitcoin
/openbb-crypto LINK --vs=BTC --period=90d

# Social sentiment check
/openbb-crypto DOGE --metrics=social
```

**Provides**:
- Real-time price and volume data
- On-chain metrics (active addresses, hash rate, holders)
- DeFi analytics (TVL, staking, protocols)
- Social sentiment (Twitter, Reddit, news)
- Whale activity tracking
- AI market analysis

---

### 3. `/openbb-macro` - Macroeconomic Analysis

Global economic indicators and market implications.

```bash
# US macro overview
/openbb-macro --country=US --indicators=all

# UK inflation focus
/openbb-macro --country=UK --indicators=inflation

# China GDP analysis
/openbb-macro --country=CN --indicators=gdp
```

**Provides**:
- GDP growth rates and forecasts
- Inflation metrics (CPI, PPI, PCE)
- Interest rates and central bank policy
- Employment data (unemployment, NFP)
- Market impact analysis

---

### 4. `/openbb-portfolio` - Portfolio Management

Performance tracking, risk analysis, and optimization.

```bash
# Analyze current portfolio
/openbb-portfolio --analyze

# Optimize allocation
/openbb-portfolio --optimize

# Compare to benchmark
/openbb-portfolio --benchmark=SPY
```

**Provides**:
- Total return and performance metrics
- Risk analysis (volatility, Sharpe, max drawdown)
- Asset allocation breakdown
- Rebalancing recommendations
- Position-level P/L tracking

---

### 5. `/openbb-options` - Options Analysis

Options chains, Greeks, and strategy analysis.

```bash
# Options chain analysis
/openbb-options AAPL

# Covered call strategy
/openbb-options SPY --strategy=covered-call

# Custom expiry
/openbb-options TSLA --expiry=30d

# Unusual activity scanner
/openbb-options NVDA --unusual-activity
```

**Provides**:
- Call/put options chains
- Greeks (Delta, Gamma, Theta, Vega)
- Implied volatility analysis
- Strategy recommendations
- Unusual options activity alerts

---

### 6. `/openbb-research` - AI Investment Research

Comprehensive AI-powered research reports.

```bash
# Deep research report
/openbb-research AAPL --depth=deep

# Quick thesis
/openbb-research MSFT --depth=quick --focus=thesis

# Risk analysis
/openbb-research TSLA --focus=risks

# Opportunity scanner
/openbb-research AMD --focus=opportunities
```

**Generates**:
- Executive summary
- Investment thesis
- Financial analysis
- Valuation assessment
- Risk factors
- Catalysts and price targets
- Actionable recommendations

---

## 🤖 AI Agents (4)

### 1. `equity-analyst`

Expert stock analyst specializing in fundamental and technical analysis.

**Expertise**:
- Financial statement analysis
- DCF and relative valuation models
- Technical indicators and chart patterns
- Investment thesis generation
- Risk assessment

**Use with**: `/openbb-equity`, `/openbb-research`

---

### 2. `crypto-analyst`

Cryptocurrency and digital asset specialist.

**Expertise**:
- On-chain analysis (network metrics, whale tracking)
- Tokenomics evaluation
- DeFi protocol assessment
- Market cycle analysis
- Crypto-specific technical analysis

**Use with**: `/openbb-crypto`, `/openbb-research`

---

### 3. `portfolio-manager`

Portfolio construction and risk management expert.

**Expertise**:
- Asset allocation optimization
- Risk-adjusted return maximization
- Rebalancing strategies
- Position sizing
- Performance attribution

**Use with**: `/openbb-portfolio`, all analysis commands

---

### 4. `macro-economist`

Macroeconomic analysis and policy expert.

**Expertise**:
- Business cycle analysis
- Central bank policy interpretation
- Inflation and growth dynamics
- Asset class implications
- Geopolitical risk assessment

**Use with**: `/openbb-macro`, `/openbb-research`

---

## 📚 Real-World Examples

### Example 1: Stock Deep-Dive

```bash
# Step 1: Fundamental + technical analysis
/openbb-equity AAPL --analysis=all --period=1y

# Step 2: Get AI agent insights
Ask equity-analyst: "Analyze AAPL based on the data above. What's your investment recommendation?"

# Step 3: Check macro context
/openbb-macro --country=US --indicators=all

# Step 4: Generate comprehensive report
/openbb-research AAPL --depth=deep
```

**Output**: Complete investment case with buy/hold/sell recommendation and price targets.

---

### Example 2: Crypto Portfolio Optimization

```bash
# Analyze holdings
/openbb-crypto BTC
/openbb-crypto ETH --metrics=defi
/openbb-crypto SOL --metrics=on-chain

# Get agent recommendations
Ask crypto-analyst: "I hold BTC (50%), ETH (30%), SOL (20%). Should I rebalance?"

# Check macro impact
/openbb-macro --indicators=inflation  # Crypto as inflation hedge?

# Portfolio integration
/openbb-portfolio --analyze  # See crypto in broader context
```

---

### Example 3: Options Income Strategy

```bash
# Find covered call opportunity
/openbb-equity SPY --analysis=technical

# Check options chain
/openbb-options SPY --strategy=covered-call

# Analyze risk/reward
Ask equity-analyst: "SPY at $450. Is selling $470 calls for $2 premium a good covered call?"

# Monitor position
/openbb-portfolio --analyze
```

---

### Example 4: Macro-Driven Portfolio Positioning

```bash
# Assess economic regime
/openbb-macro --country=US --indicators=all

# Get macro interpretation
Ask macro-economist: "Based on this data, are we early/mid/late cycle? What's the recession risk?"

# Adjust portfolio
Ask portfolio-manager: "Given this macro outlook, how should I position? What sectors to overweight?"

# Execute changes
/openbb-equity XLK  # Tech sector
/openbb-equity XLE  # Energy sector
/openbb-portfolio --optimize
```

---

## 🔧 Configuration

### OpenBB API Keys (Optional)

For premium data, configure API keys:

```python
from openbb import obb

# Set credentials
obb.user.credentials.fmp_api_key = "YOUR_KEY"  # Financial Modeling Prep
obb.user.credentials.polygon_api_key = "YOUR_KEY"  # Polygon.io
obb.user.credentials.alpha_vantage_api_key = "YOUR_KEY"  # Alpha Vantage

# Save configuration
obb.user.save()
```

### Data Providers

OpenBB supports 100+ data providers:
- **Free**: Yahoo Finance, Alpha Vantage (limited)
- **Freemium**: Polygon, FMP, Intrinio
- **Premium**: Bloomberg, Refinitiv, FactSet

See [OpenBB docs](https://docs.openbb.co/platform/reference) for full list.

---

## 📊 Data Coverage

### Equity Data
- **Stocks**: 50,000+ global equities
- **Indices**: S&P 500, Nasdaq, Dow, international indices
- **ETFs**: 3,000+ ETFs and sector funds
- **Historical**: Up to 20+ years of data

### Cryptocurrency
- **Assets**: 10,000+ cryptocurrencies
- **Exchanges**: Binance, Coinbase, Kraken, 20+ more
- **DeFi**: 1,000+ protocols on Ethereum, BSC, Polygon
- **On-Chain**: BTC, ETH, and major L1s

### Macroeconomic
- **Countries**: 180+ countries
- **Indicators**: 200+ economic data series
- **Central Banks**: Fed, ECB, BOJ, BOE, PBOC
- **Frequency**: Daily, monthly, quarterly

### Options
- **Equities**: All optionable US stocks
- **Indices**: SPX, NDX, RUT
- **ETFs**: SPY, QQQ, IWM, sector ETFs
- **Expirations**: All available dates

---

## 🎯 Use Cases

### For Individual Investors
- **Stock Screening**: Find undervalued stocks with `/openbb-equity`
- **Crypto Trading**: Track market sentiment with `/openbb-crypto`
- **Portfolio Tracking**: Monitor performance with `/openbb-portfolio`
- **Options Income**: Generate income with `/openbb-options`

### For Financial Analysts
- **Research Reports**: Auto-generate with `/openbb-research`
- **Earnings Analysis**: Deep-dive fundamentals
- **Macro Forecasting**: Economic scenario planning
- **Comp Analysis**: Compare valuation multiples

### For Quants
- **Factor Analysis**: Extract data for backtests
- **Risk Modeling**: Calculate portfolio VaR
- **Algo Development**: API integration for strategies
- **Performance Attribution**: Decompose returns

### For Portfolio Managers
- **Asset Allocation**: Optimize with `/openbb-portfolio`
- **Rebalancing**: Systematic rebalance triggers
- **Risk Management**: Monitor drawdowns
- **Client Reporting**: Automated performance reports

---

## 🔗 Integration

### With Other Plugins

```bash
# With ai-commit-gen (track research as commits)
/openbb-research AAPL --depth=deep
/commit  # Commit research notes

# With overnight-dev (run backtests overnight)
/overnight-dev "Backtest AAPL trading strategy using OpenBB data"

# With git-commit-smart (version research)
/gc  # Smart commit research findings
```

### With External Tools

- **Excel/Sheets**: Export data via pandas `.to_csv()`
- **Jupyter Notebooks**: Run OpenBB commands in notebooks
- **Trading Platforms**: Use data for order execution
- **Portfolio Trackers**: Import holdings and performance

---

## ⚙️ Advanced Features

### Custom Analysis Workflows

Create custom research pipelines:

```python
# Multi-stock comparison
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    /openbb-equity {ticker} --analysis=all
    Ask equity-analyst: "Quick assessment of {ticker}"

# Sector rotation analysis
sectors = ["XLK", "XLE", "XLF", "XLV", "XLI"]
for sector in sectors:
    /openbb-equity {sector}
    /openbb-macro --impact=sector

# Crypto basket strategy
cryptos = ["BTC", "ETH", "SOL", "AVAX"]
for crypto in cryptos:
    /openbb-crypto {crypto} --metrics=all
```

### Automated Alerts

Set up monitoring:

```python
# Price alerts
if current_price < sma_200:
    print(f"🚨 {ticker} below 200-day SMA - potential buy")

# Volatility alerts
if portfolio_vol > target_vol * 1.5:
    print("⚠️  Portfolio risk elevated - rebalance needed")

# Macro alerts
if inflation_yoy > 4.0:
    print("🔥 High inflation - consider inflation hedges")
```

---

## 📖 Documentation

- **OpenBB Platform Docs**: https://docs.openbb.co/platform
- **API Reference**: https://docs.openbb.co/platform/reference
- **Data Providers**: https://docs.openbb.co/platform/data_providers
- **GitHub**: https://github.com/OpenBB-finance/OpenBB

---

## 🚨 Important Notes

### Disclaimers

- **Not Financial Advice**: All analysis is for informational purposes only
- **Do Your Own Research**: Always verify data and consult professionals
- **Risk Disclosure**: Past performance doesn't guarantee future results
- **Data Accuracy**: Verify critical data from multiple sources

### Data Limitations

- **Free Tier**: 15-20 minute delays on some data
- **API Limits**: Rate limits apply (varies by provider)
- **Coverage**: Not all assets have complete data
- **Historical**: Survivorship bias in long-term data

---

## 🤝 Contributing

Help improve this plugin:

1. Report issues with specific commands
2. Suggest new analysis workflows
3. Share custom agent configurations
4. Contribute example use cases

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

**OpenBB Platform**: Apache 2.0 License

---

## 🙋 Support

- **Plugin Issues**: https://github.com/jeremylongshore/claude-code-plugins/issues
- **OpenBB Issues**: https://github.com/OpenBB-finance/OpenBB/issues
- **Discord**: https://discord.gg/openbb (OpenBB community)
- **Discussions**: https://github.com/jeremylongshore/claude-code-plugins/discussions

---

**Transform Claude Code into a professional investment research terminal. Install now and start analyzing!** 📊🚀
