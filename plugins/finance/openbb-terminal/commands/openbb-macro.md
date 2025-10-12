---
name: openbb-macro
description: Macroeconomic analysis using OpenBB - GDP, inflation, interest rates, employment, global economic indicators
---

# OpenBB Macroeconomic Analysis

Analyze global macroeconomic trends and indicators using OpenBB Platform.

## Usage

```bash
/openbb-macro [--country US|UK|EU|CN|JP] [--indicators gdp|inflation|rates|employment|all]
```

## What This Command Does

Retrieves and analyzes macroeconomic indicators to understand economic trends and market implications.

## Key Features

### Economic Indicators
- **GDP**: Growth rates, forecasts, components
- **Inflation**: CPI, PPI, PCE, core inflation
- **Interest Rates**: Federal funds, treasury yields, central bank rates
- **Employment**: Unemployment, NFP, job openings, labor participation
- **Consumer**: Confidence, spending, retail sales
- **Manufacturing**: PMI, industrial production, capacity utilization

### Workflow

```python
from openbb import obb

# GDP Analysis
gdp_data = obb.economy.gdp(country="US")
print(f"GDP Growth: {gdp_data.growth_rate:.2f}%")
print(f"GDP per Capita: ${gdp_data.gdp_per_capita:,.0f}")

# Inflation Data
cpi = obb.economy.cpi(country="US")
print(f"CPI (YoY): {cpi.yoy_change:.2f}%")
print(f"Core CPI: {cpi.core_cpi:.2f}%")

# Interest Rates
rates = obb.economy.fed_rates()
print(f"Fed Funds Rate: {rates.current_rate:.2f}%")
print(f"10Y Treasury: {rates.treasury_10y:.2f}%")

# Employment
employment = obb.economy.employment()
print(f"Unemployment Rate: {employment.unemployment_rate:.1f}%")
print(f"NFP (last month): {employment.nfp_change:+,}")
```

### Market Impact Analysis

```python
# Analyze impact on markets
print("\n💡 Market Implications:")

if cpi.yoy_change > 3.0:
    print("⚠️  High inflation - Fed likely to maintain hawkish stance")
    print("   → Negative for growth stocks, positive for commodities")

if employment.unemployment_rate < 4.0:
    print("🔥 Tight labor market - wage pressures building")
    print("   → Could sustain inflation, support consumer stocks")

if rates.current_rate > 5.0:
    print("💸 High interest rates - restrictive monetary policy")
    print("   → Headwind for equities, tailwind for bonds")
```

## Examples

```bash
# US macro overview
/openbb-macro --country=US --indicators=all

# UK inflation focus
/openbb-macro --country=UK --indicators=inflation

# China GDP analysis
/openbb-macro --country=CN --indicators=gdp
```

## Integration

- Correlate with equity performance via `/openbb-equity`
- Impact crypto markets via `/openbb-crypto`
- Portfolio positioning via `/openbb-portfolio`
