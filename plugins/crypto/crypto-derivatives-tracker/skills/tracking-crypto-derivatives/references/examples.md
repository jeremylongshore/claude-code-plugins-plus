# Usage Examples

## CLI Examples

### Funding Rate Analysis

**Basic funding rate check:**

```bash
python derivatives_tracker.py funding BTC
```

Output:

```
======================================================================
                     BTC FUNDING RATE ANALYSIS
======================================================================

Exchange      Current  Annualized  Next Payment
--------------------------------------------------
Binance      +0.0100%     +10.95%         4h 23m
Bybit        +0.0095%     +10.40%         4h 23m
OKX          +0.0088%      +9.64%         4h 23m
Deribit      +0.0082%      +8.98%         4h 23m
BitMEX       +0.0078%      +8.54%         4h 23m
--------------------------------------------------

Weighted Average: +0.0089%
Annualized: +9.70%
Spread (max-min): 0.0022%

Sentiment: 🟢 Moderate Bullish
```

**JSON export:**

```bash
python derivatives_tracker.py funding BTC --format json
```

### Open Interest Analysis

**Basic OI check:**

```bash
python derivatives_tracker.py oi BTC
```

Output:

```
======================================================================
                    BTC OPEN INTEREST ANALYSIS
======================================================================

Exchange          OI (USD)   24h Chg     7d Chg   Share
------------------------------------------------------------
Binance           $6.20B      +3.2%      +8.5%   41.3%
Bybit             $3.85B      +2.8%      +6.2%   25.7%
OKX               $2.40B      +1.5%      +4.8%   16.0%
Deribit           $1.50B      +4.2%     +12.1%   10.0%
BitMEX            $1.05B      +0.8%      +2.4%    7.0%
------------------------------------------------------------

Total OI: $15.00B
24h Change: +2.9%
7d Change: +7.8%

Long/Short Ratio: 1.05 (51.2% long)
Trend: Moderate Increasing
Dominant Exchange: Binance (41.3%)
```

**With divergence analysis:**

```bash
python derivatives_tracker.py oi BTC --price-change 3.5
```

Output includes:

```
────────────────────────────────────────────────────────────────────────
DIVERGENCE ANALYSIS
────────────────────────────────────────────────────────────────────────

🔍 Divergence Detected!
   OI:    up (+2.9%)
   Price: up (+3.5%)
   Signal: BULLISH
   Rising OI confirms bullish trend - new longs entering
   Confidence: medium
```

### Liquidation Monitoring

**Basic liquidation summary:**

```bash
python derivatives_tracker.py liquidations BTC
```

Output:

```
======================================================================
                     BTC LIQUIDATION MONITOR
======================================================================

   Current Price: $67,500
------------------------------------------------------------

24h Liquidations:
   Total:  $125.5M
   Longs:  $75.3M
   Shorts: $50.2M

Cascade Risk: 🟡 MEDIUM

────────────────────────────────────────────────────────────────────────
LIQUIDATION HEATMAP
────────────────────────────────────────────────────────────────────────

LONG LIQUIDATIONS (below $67,500):
  $   65,000 ████████████ $120M ⚠️ HIGH
  $   63,000 ████████ $80M MEDIUM
  $   60,000 ██████ $60M MEDIUM
  $   58,000 ██ $20M LOW

SHORT LIQUIDATIONS (above $67,500):
  $   70,000 ██████████ $100M HIGH
  $   72,000 ████████ $80M MEDIUM
  $   75,000 ██████ $60M MEDIUM
  $   78,000 ██ $20M LOW
```

**With large liquidation history:**

```bash
python derivatives_tracker.py liquidations BTC --large
```

Adds:

```
────────────────────────────────────────────────────────────────────────
RECENT LARGE LIQUIDATIONS (>$1M)
────────────────────────────────────────────────────────────────────────

Exchange   Side   Price        Value       When
------------------------------------------------------------
Binance    long   $67,200       $5.2M       23m ago
Bybit      long   $66,850       $3.8M        1h ago
OKX        short  $68,100       $2.9M        2h ago
```

### Options Analysis

**Basic options summary:**

```bash
python derivatives_tracker.py options BTC
```

Output:

```
======================================================================
                      BTC OPTIONS ANALYSIS
======================================================================

Expiry: 2025-01-31
Exchange: Deribit

Implied Volatility:
   ATM IV: 55.5%
   Interpretation: NORMAL
   IV Rank: 52nd percentile

Put/Call Analysis:
   PCR (Volume): 0.85
   PCR (OI): 0.92
   Sentiment: 🟢 BULLISH

Max Pain:
   Price: $66,000
   Distance: -2.2% from current

Open Interest:
   Calls: $2.80B
   Puts:  $2.58B

Overall Sentiment: 🟢 BULLISH
Expiry Pressure: LOW
```

**With max pain levels and options flow:**

```bash
python derivatives_tracker.py options BTC --max-pain --flow
```

### Basis Analysis

**Basic basis/spread check:**

```bash
python derivatives_tracker.py basis BTC
```

Output:

```
======================================================================
                       BTC BASIS ANALYSIS
======================================================================

   Spot Price: $67,500
------------------------------------------------------------

Expiry        Futures     Basis     Annual   Days
------------------------------------------------------------
2025-01-31   $68,175     +1.00%     +13.0%     28
2025-02-28   $68,850     +2.00%     +13.1%     56
2025-03-28   $69,863     +3.50%     +15.2%     84
2025-06-27   $71,550     +6.00%     +13.1%    168
------------------------------------------------------------

Market Structure: Moderate Contango
Average Basis: +3.13%
Average Annualized: +13.6%
Best Carry: 2025-03-28 (+15.2% annualized)

────────────────────────────────────────────────────────────────────────
TERM STRUCTURE
────────────────────────────────────────────────────────────────────────
2025-01-31   ▲ ++++++ +13.0%
2025-02-28   ▲ ++++++ +13.1%
2025-03-28   ▲ +++++++ +15.2%
2025-06-27   ▲ ++++++ +13.1%
```

**With carry trade scanner:**

```bash
python derivatives_tracker.py basis BTC --carry
```

### Multi-Asset Dashboard

**Quick market overview:**

```bash
python derivatives_tracker.py dashboard BTC ETH SOL
```

Output:

```
======================================================================
                    CRYPTO DERIVATIVES DASHBOARD
======================================================================

======================================================================
                              BTC
======================================================================

📊 FUNDING
   Rate: +0.0089% (+9.70% annual)
   Sentiment: 🟢 Bullish

📈 OPEN INTEREST
   Total: $15.0B (+2.9% 24h)
   Long/Short: 1.05 (51% long)
   Trend: Moderate Increasing

💥 LIQUIDATIONS (24h)
   Total: $125.5M
   Longs: $75.3M | Shorts: $50.2M
   Cascade Risk: 🟡 MEDIUM

======================================================================
                              ETH
======================================================================

📊 FUNDING
   Rate: +0.0072% (+7.88% annual)
   Sentiment: 🟢 Bullish

📈 OPEN INTEREST
   Total: $8.2B (+1.8% 24h)
   Long/Short: 1.02 (50.5% long)
   Trend: Weak Increasing

💥 LIQUIDATIONS (24h)
   Total: $45.2M
   Longs: $28.1M | Shorts: $17.1M
   Cascade Risk: 🟢 LOW

======================================================================
                              SOL
======================================================================

📊 FUNDING
   Rate: +0.0156% (+17.08% annual)
   Sentiment: 🟢 Strong Bullish

📈 OPEN INTEREST
   Total: $2.1B (+5.2% 24h)
   Long/Short: 1.15 (53.5% long)
   Trend: Strong Increasing

💥 LIQUIDATIONS (24h)
   Total: $32.8M
   Longs: $8.2M | Shorts: $24.6M
   Cascade Risk: 🟢 LOW
```

## Programmatic Usage

### Funding Rate Arbitrage Detection

```python
from funding_tracker import FundingTracker

tracker = FundingTracker()

# Find arbitrage opportunities
opportunities = tracker.get_arbitrage_opportunities(
    symbols=["BTC", "ETH", "SOL"],
    min_spread=0.02
)

for opp in opportunities:
    print(f"{opp['symbol']}: Long {opp['long_exchange']} "
          f"({opp['long_rate']:+.4%}), "
          f"Short {opp['short_exchange']} "
          f"({opp['short_rate']:+.4%})")
    print(f"  Spread: {opp['spread']:.4%} per 8h")
    print(f"  Annualized: {opp['profit_annual_pct']:.1f}%")
```

### OI Divergence Trading Signals

```python
from oi_analyzer import OIAnalyzer

analyzer = OIAnalyzer()

# Check for OI/price divergence
price_change_24h = 3.5  # From your data source

divergence = analyzer.detect_divergence("BTC", price_change_24h)

if divergence:
    if divergence.signal == "bullish":
        print("Strong bullish trend confirmed by OI")
    elif divergence.signal == "short_squeeze":
        print("Rally may be weak - shorts covering")
    elif divergence.signal == "long_liquidation":
        print("Selloff may find support - longs washing out")
```

### Liquidation Level Alerts

```python
from liquidation_monitor import LiquidationMonitor

monitor = LiquidationMonitor()
current_price = Decimal("67500")

summary = monitor.get_summary("BTC", current_price)

# Alert on high cascade risk
if summary.cascade_risk in ["high", "critical"]:
    print(f"⚠️ High liquidation risk!")
    print(f"   ${float(summary.total_24h_usd)/1e6:.0f}M liquidated in 24h")

# Find nearest levels
if summary.nearest_long_level:
    lvl = summary.nearest_long_level
    distance = (float(current_price) - float(lvl.price)) / float(current_price) * 100
    print(f"Nearest long liquidations: ${lvl.price:,.0f} ({distance:.1f}% below)")
```

### Options IV Percentile Tracking

```python
from options_analyzer import OptionsAnalyzer

analyzer = OptionsAnalyzer()

analysis = analyzer.analyze("BTC", current_price=Decimal("67500"))

if analysis.iv_interpretation == "high":
    print(f"IV elevated at {analysis.snapshot.atm_iv:.1f}%")
    print("Consider premium selling strategies")
elif analysis.iv_interpretation == "low":
    print(f"IV compressed at {analysis.snapshot.atm_iv:.1f}%")
    print("Consider premium buying strategies")

# Check put/call sentiment
if analysis.overall_sentiment == "bullish":
    print("Options flow indicates bullish positioning")
```

### Basis Carry Trade Scanner

```python
from basis_calculator import BasisCalculator

calc = BasisCalculator()

# Find carry opportunities across assets
opportunities = calc.find_carry_opportunities(
    symbols=["BTC", "ETH"],
    min_yield=5.0  # Minimum 5% annualized
)

for opp in opportunities:
    print(f"\n{opp.symbol} {opp.expiry}")
    print(f"  Strategy: {opp.strategy}")
    print(f"  Yield: {opp.annualized_yield:.1f}% annualized")
    print(f"  Risk: {opp.risk_notes}")
```

## Integration Patterns

### Combine with Price Alerts

```python
# Pseudo-code for alert system integration
def check_derivatives_alerts(symbol, price, price_change_24h):
    alerts = []

    # Funding
    funding = FundingTracker().analyze(symbol)
    if funding.is_extreme:
        alerts.append(f"Extreme funding: {funding.weighted_avg:+.4%}")

    # OI divergence
    oi = OIAnalyzer()
    div = oi.detect_divergence(symbol, price_change_24h)
    if div and div.confidence == "high":
        alerts.append(f"OI divergence: {div.signal}")

    # Liquidations
    liq = LiquidationMonitor().get_summary(symbol, Decimal(str(price)))
    if liq.cascade_risk == "critical":
        alerts.append(f"Critical liquidation risk!")

    return alerts
```

### JSON Export for Dashboards

```python
from formatters import JSONFormatter

json_fmt = JSONFormatter()

# Export complete dashboard data
dashboard = json_fmt.derivatives_dashboard(
    symbol="BTC",
    funding=funding_data,
    oi=oi_data,
    liquidations=liq_data,
    options=options_data,
    basis=basis_data
)

# Write to file or send to API
with open("derivatives_dashboard.json", "w") as f:
    f.write(dashboard)
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
