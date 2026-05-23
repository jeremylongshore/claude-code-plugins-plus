# Examples

## Example 1: BTC Options Sentiment Dashboard

Generate a comprehensive sentiment snapshot for Bitcoin options covering
put/call ratios, max pain, and open interest concentration.

**Command:**

```bash
python options_flow.py btc --summary --expiry nearest-3
```

**Output:**

```
BTC Options Sentiment Snapshot
══════════════════════════════════════════════════════════════
Underlying: BTC/USD @ $104,250
Timestamp:  2026-03-17T14:30:00Z
Source:     Deribit

Aggregate Put/Call Ratio
────────────────────────
  By Volume:         0.62  (Bullish — calls dominating)
  By Open Interest:  0.71  (Moderately Bullish)
  7-Day Average:     0.78
  30-Day Average:    0.85
  Signal: Volume P/C ratio 21% below 30-day average → unusual call buying

Max Pain Analysis (Nearest 3 Expiries)
────────────────────────────────────────
  Expiry       Max Pain    Distance   Magnet Strength
  2026-03-21   $102,000    -2.2%      Strong (3 days to expiry)
  2026-03-28   $100,000    -4.1%      Moderate
  2026-04-25   $105,000    +0.7%      Weak (far expiry)

Top 5 Strikes by Open Interest
──────────────────────────────
  Strike      Type   OI (contracts)  Notional ($M)   IV
  $110,000    Call   12,450          $1,298          52.3%
  $100,000    Put    11,200          $1,168          54.1%
  $120,000    Call    9,800          $1,022          58.7%
  $105,000    Call    8,650          $902            49.8%
  $ 95,000    Put    7,300          $761            56.2%

Interpretation:
  Heavy call OI at $110K-$120K suggests institutional upside positioning.
  Put protection concentrated at $100K and $95K as downside hedges.
  Call-heavy OI skew supports bullish medium-term outlook.
```

## Example 2: Detecting Institutional Block Trades

Filter for large-notional block trades that indicate institutional positioning
rather than retail activity.

**Command:**

```bash
python options_flow.py btc --blocks \
  --min-notional 500000 \
  --period 24h \
  --format table
```

**Output:**

```
BTC Block Trades (>$500K notional, last 24h)
══════════════════════════════════════════════════════════════

  Time (UTC)   Direction  Strike    Expiry      Size    Premium    IV     Notional
  ─────────────────────────────────────────────────────────────────────────────────
  14:22:05     BUY CALL   $120,000  2026-06-27  500     $1,850    61.2%  $925,000
  13:45:30     BUY PUT    $ 95,000  2026-04-25  800     $720      55.8%  $576,000
  11:02:18     SELL CALL  $130,000  2026-09-26  1,200   $980      64.5%  $1,176,000
  09:15:44     BUY CALL   $110,000  2026-06-27  650     $3,200    53.1%  $2,080,000
  08:30:02     BUY CALL   $115,000  2026-04-25  400     $1,450    56.9%  $580,000
  04:18:55     BUY PUT    $ 90,000  2026-06-27  900     $640      58.3%  $576,000

Summary:
  Total blocks: 6
  Net direction: Bullish (4 call buys vs 1 put buy, 1 call sell)
  Largest: $2.08M notional call buy at $110K June expiry
  Notable: $1.17M covered call sell at $130K Sept → institution capping upside

Flow Analysis:
  The $2.08M call purchase at $110K June expiry is 3.2 standard deviations
  above the 30-day average block size. Combined with the $925K call at $120K,
  institutions are positioning for a $110K-$120K move by Q2.

  The $1.17M call SELL at $130K Sept suggests a large holder is writing
  covered calls, capping their upside exposure at $130K. This is consistent
  with a moderately bullish but not euphoric institutional stance.
```

## Example 3: Implied Volatility Term Structure Analysis

Generate the IV term structure curve to detect vol compression or expansion
that may precede a directional move.

**Command:**

```bash
python options_flow.py eth --iv-curve --strikes atm --format json
```

**Output (formatted for readability):**

```json
{
  "underlying": "ETH/USD",
  "spotPrice": 3850.00,
  "timestamp": "2026-03-17T14:30:00Z",
  "termStructure": [
    {
      "expiry": "2026-03-21",
      "daysToExpiry": 4,
      "atmStrike": 3850,
      "iv": 72.5,
      "ivChange7d": +8.2,
      "signal": "elevated"
    },
    {
      "expiry": "2026-03-28",
      "daysToExpiry": 11,
      "atmStrike": 3850,
      "iv": 65.3,
      "ivChange7d": +3.1,
      "signal": "normal"
    },
    {
      "expiry": "2026-04-25",
      "daysToExpiry": 39,
      "atmStrike": 3850,
      "iv": 58.7,
      "ivChange7d": -1.2,
      "signal": "normal"
    },
    {
      "expiry": "2026-06-27",
      "daysToExpiry": 102,
      "atmStrike": 3850,
      "iv": 55.2,
      "ivChange7d": -0.5,
      "signal": "normal"
    },
    {
      "expiry": "2026-09-26",
      "daysToExpiry": 193,
      "atmStrike": 3850,
      "iv": 54.8,
      "ivChange7d": +0.3,
      "signal": "normal"
    }
  ],
  "analysis": {
    "shape": "inverted",
    "nearTermPremium": 17.7,
    "interpretation": "Near-term IV (72.5%) is 17.7 points above far-term (54.8%). Inverted term structure indicates the market expects a significant move within the next 1-2 weeks. Historical precedent: ETH IV inversions of >15 points have preceded 10%+ moves within 10 days in 78% of cases over the past 12 months."
  }
}
```

## Example 4: Open Interest Heatmap Data

Build an open interest heatmap showing position concentration across strikes
and expiration dates.

**Command:**

```bash
python options_flow.py btc --oi-heatmap --format csv > btc_oi_heatmap.csv
```

**CSV output (excerpt):**

```csv
expiry,strike,call_oi,put_oi,total_oi,dominant_side,concentration_pct
2026-03-21,95000,120,2450,2570,PUT,1.8
2026-03-21,100000,850,4200,5050,PUT,3.5
2026-03-21,105000,3100,1800,4900,CALL,3.4
2026-03-21,110000,5200,600,5800,CALL,4.0
2026-03-28,95000,300,3100,3400,PUT,2.4
2026-03-28,100000,1200,5500,6700,PUT,4.7
2026-03-28,105000,4800,2200,7000,CALL,4.9
2026-03-28,110000,7500,900,8400,CALL,5.9
2026-04-25,100000,2000,8200,10200,PUT,7.1
2026-04-25,110000,9800,1100,10900,CALL,7.6
2026-04-25,120000,12450,400,12850,CALL,9.0
```

**Interpretation:**

```
Hotspots (highest concentration):
  1. $120K Call, Apr 25: 12,450 OI (9.0%) → major upside target
  2. $110K Call, Apr 25: 9,800 OI (7.6%) → secondary resistance
  3. $100K Put, Apr 25: 8,200 OI (7.1%) → major support level

Market positioning map:
  Below $100K: Put-heavy (downside protection zone)
  $100K-$105K: Mixed (battle zone)
  Above $105K: Call-heavy (upside conviction zone)
  $120K+: Extreme call concentration (strong conviction target)
```

## Example 5: Unusual Activity Alerts

Flag trades that deviate significantly from historical baselines, indicating
potential insider knowledge or large directional bets.

**Command:**

```bash
python options_flow.py btc --unusual --threshold 2.0 --period 7d
```

**Output:**

```
Unusual Options Activity Report — BTC
══════════════════════════════════════════════════════════════
Period: 2026-03-10 to 2026-03-17
Threshold: >2.0 standard deviations from 30-day rolling average

ALERT 1 — HIGH SEVERITY (3.2 sigma)
  Instrument: BTC-25APR26-120000-C
  Activity:   1,850 contracts traded (vs 30-day avg: 320/day)
  Direction:  Net BUY (aggressor: buyer on 87% of volume)
  Premium:    $2.4M total premium spent
  IV Impact:  IV rose from 56% to 61% during the session
  Timeframe:  Concentrated in a 45-minute window (09:00-09:45 UTC)
  Signal:     Institutional call accumulation ahead of major expiry

ALERT 2 — MODERATE SEVERITY (2.4 sigma)
  Instrument: BTC-28MAR26-95000-P
  Activity:   920 contracts traded (vs 30-day avg: 180/day)
  Direction:  Net BUY (aggressor: buyer on 72% of volume)
  Premium:    $380K total premium spent
  IV Impact:  IV unchanged (absorbed by market makers)
  Timeframe:  Spread across full session
  Signal:     Protective put buying, possibly hedging a large spot position

ALERT 3 — MODERATE SEVERITY (2.1 sigma)
  Instrument: BTC-25APR26-110000-C / BTC-25APR26-130000-C (spread)
  Activity:   600 contracts of bull call spread
  Direction:  BUY 110K/SELL 130K (defined risk bullish)
  Max Profit: $20K per spread if BTC > $130K at expiry
  Premium:    $1.1M net debit
  Signal:     Institutional risk-defined bet on $110K-$130K range by April

No further alerts above threshold.
```

## Example 6: Multi-Exchange Comparison

Compare options data across Deribit, OKX, and Bybit to find arbitrage
opportunities or exchange-specific positioning.

**Command:**

```bash
python options_flow.py btc --compare-exchanges --strike 110000 --expiry 2026-04-25
```

**Output:**

```
Cross-Exchange Comparison: BTC $110K Call, Apr 25 2026
══════════════════════════════════════════════════════════════

  Metric           Deribit      OKX          Bybit
  ──────────────────────────────────────────────────
  Bid              $3,180       $3,150       $3,140
  Ask              $3,220       $3,280       $3,310
  Spread           $40 (1.3%)   $130 (4.1%)  $170 (5.4%)
  IV (mid)         53.1%        53.8%        54.2%
  24h Volume       1,240        380          95
  Open Interest    9,800        2,100        450
  Last Trade       14:28 UTC    14:15 UTC    13:02 UTC

Analysis:
  Deribit: Tightest spreads, highest liquidity. Primary price discovery venue.
  OKX: Slight IV premium (+0.7%) — may indicate local demand from Asian flow.
  Bybit: Widest spreads, lowest volume. Not recommended for large orders.

  Arb opportunity: Buy on Bybit ($3,140 ask) / Sell on Deribit ($3,180 bid)
  = $40/contract edge. However, cross-exchange settlement risk and fees likely
  consume most of this edge. Only viable for market makers with both venues.
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
