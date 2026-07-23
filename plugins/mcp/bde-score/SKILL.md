---
name: bde-score
description: "AI-powered multi-factor stock scoring MCP server. 7-factor composite model (VIX, Volume Profile, RSI, MACD, Bollinger, OBV, ATR) with real-time Yahoo Finance data. Zero-config, no API keys required."
version: 1.0.0
author: hbhqq9
license: AGPL-3.0
compatibility: "claude-code >= 1.0"
tags:
  - stock-analysis
  - quantitative
  - multi-factor
  - mcp
  - finance
  - technical-analysis
  - scoring
allowed-tools:
  - Read
  - WebFetch
---

# BDE Score™ — MCP Stock Scoring Plugin

Multi-factor quantitative stock scoring for AI agents. Self-contained, no external API keys required.

## What it does

Analyzes stocks using a 7-factor composite model:

| Factor | Weight | What it measures |
|--------|--------|-----------------|
| Momentum | 30% | Multi-period return strength (5/10/20/60 day) |
| Mean Reversion | 20% | Deviation from 20-day moving average |
| Volume | 20% | Volume ratio anomaly detection |
| Volatility | 15% | ATR-based, lower volatility preferred |
| Trend | 15% | EMA(10/50) crossover signals |

Each stock receives a composite score (0-100) with signal classification:
- **Bullish** (>70): Strong upward momentum
- **Neutral** (40-70): Consolidation phase
- **Bearish** (<40): Downward pressure

## Tools

| Tool | Description |
|------|-------------|
| `score_stock` | Score a single stock with full factor breakdown |
| `batch_score` | Score multiple stocks (up to 20) in one call |
| `top_performers` | Top N stocks by composite score from a watchlist |
| `worst_performers` | Bottom N stocks by composite score |
| `market_overview` | Market sentiment summary with breadth indicators |

## Requirements

- Node.js >= 20
- Internet connection (for Yahoo Finance data)
- No API keys required

## Disclaimer

Technical analysis only. Not financial advice.
