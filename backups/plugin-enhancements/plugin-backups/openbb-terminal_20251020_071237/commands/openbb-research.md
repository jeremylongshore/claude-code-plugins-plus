---
name: openbb-research
description: AI-powered investment research using OpenBB - comprehensive analysis, thesis generation, risk assessment, actionable insights
---

# OpenBB AI Investment Research

AI-powered comprehensive investment research combining OpenBB data with Claude's analytical capabilities.

## Usage

```bash
/openbb-research SYMBOL [--depth deep|quick] [--focus thesis|risks|opportunities]
```

## What This Command Does

Conducts comprehensive AI-powered investment research by combining multiple OpenBB data sources with advanced analysis.

## Workflow

### 1. Data Aggregation

```python
from openbb import obb

symbol = "AAPL"

# Gather comprehensive data
data = {
    "price": obb.equity.price.historical(symbol=symbol, period="1y"),
    "fundamentals": obb.equity.fundamental.metrics(symbol=symbol),
    "analyst": obb.equity.estimates.analyst(symbol=symbol),
    "news": obb.equity.news(symbol=symbol, limit=10),
    "peers": obb.equity.compare.peers(symbol=symbol),
    "insider": obb.equity.ownership.insider(symbol=symbol)
}
```

### 2. Investment Thesis Generation

```python
print(f"\n📋 Investment Thesis for {symbol}")
print(f"{'='*60}")

# Business Analysis
print(f"\n1. Business Quality:")
print(f"   - Competitive moats identified")
print(f"   - Revenue growth trajectory")
print(f"   - Margin trends and sustainability")
print(f"   - Market position and share")

# Financial Health
print(f"\n2. Financial Strength:")
print(f"   - Balance sheet assessment")
print(f"   - Cash flow generation")
print(f"   - Capital allocation efficiency")
print(f"   - Debt levels and coverage")

# Valuation
print(f"\n3. Valuation Assessment:")
print(f"   - P/E vs sector average")
print(f"   - PEG ratio analysis")
print(f"   - DCF model implications")
print(f"   - Historical valuation ranges")

# Catalysts
print(f"\n4. Key Catalysts:")
print(f"   - Upcoming earnings/events")
print(f"   - Product launches")
print(f"   - Regulatory developments")
print(f"   - Industry trends")
```

### 3. Risk Assessment

```python
print(f"\n⚠️  Risk Factors:")

risks = []

# Check technical risks
if data["price"].rsi[-1] > 75:
    risks.append("Overbought conditions - potential pullback risk")

# Check fundamental risks
if data["fundamentals"].debt_to_equity > 1.5:
    risks.append("High leverage - financial risk elevated")

# Check market risks
if data["price"].volatility > 50:
    risks.append("High volatility - price uncertainty")

for i, risk in enumerate(risks, 1):
    print(f"   {i}. {risk}")
```

### 4. Opportunity Analysis

```python
print(f"\n💡 Investment Opportunities:")

opportunities = []

if data["analyst"].rating_score > 4.0:
    opportunities.append("Strong analyst support - positive sentiment")

if data["insider"].net_buy_sell > 0:
    opportunities.append("Insider buying - management confidence")

if data["fundamentals"].roe > 20:
    opportunities.append("High ROE - efficient capital use")

for i, opp in enumerate(opportunities, 1):
    print(f"   {i}. {opp}")
```

### 5. Actionable Recommendations

```python
print(f"\n🎯 Recommendation:")

# Decision matrix
score = 0
score += 2 if data["analyst"].rating_score > 4.0 else 0
score += 2 if data["fundamentals"].roe > 15 else 0
score += 1 if data["price"].trend == "bullish" else 0
score -= 1 if data["fundamentals"].pe_ratio > 30 else 0

if score >= 4:
    rating = "BUY"
    action = "Consider accumulating position"
elif score >= 2:
    rating = "HOLD"
    action = "Monitor closely, hold current position"
else:
    rating = "AVOID"
    action = "Wait for better entry point"

print(f"   Rating: {rating}")
print(f"   Action: {action}")
print(f"   Confidence: {score}/5")
```

## Examples

```bash
# Deep research report
/openbb-research AAPL --depth=deep

# Quick thesis
/openbb-research MSFT --depth=quick --focus=thesis

# Risk analysis
/openbb-research TSLA --focus=risks
```

## Output Format

1. Executive Summary
2. Investment Thesis
3. Financial Analysis
4. Valuation Assessment
5. Risk Factors
6. Opportunities
7. Recommendation & Price Targets
8. Monitoring Checklist

## Integration

- Export reports to PDF/Markdown
- Track recommendations over time
- Compare with analyst consensus
- Portfolio integration via `/openbb-portfolio`
