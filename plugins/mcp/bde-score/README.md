# BDE Score

**Multi-factor quantitative stock scoring MCP server with transparent 5-factor analysis. No API keys required.**

## Overview

BDE Score is a self-contained MCP server that provides quantitative stock analysis using a transparent 5-factor model. Unlike black-box systems, every scoring decision is explainable.

**Key Features:**

- 📊 **5-Factor Scoring Model** — Momentum (30%), Mean Reversion (20%), Volume (20%), Volatility (15%), Trend (15%)
- 🔌 **Self-Contained** — No external API keys, no paid services. Fetches data from public sources.
- 🧮 **Transparent Math** — Every factor is documented and explainable via the `explain_factors` tool
- 🏪 **Multi-Market** — Supports US stocks, with extensible architecture for global markets
- 📈 **Portfolio Ranking** — Score and compare multiple stocks at once
- 🌡️ **Market Sentiment** — Aggregate breadth analysis across a universe of stocks

## What's Included

This plugin provides **4 MCP tools**:

| Tool | Description |
|------|-------------|
| `analyze_stock` | Score a single stock with the 5-factor model and detailed breakdown |
| `analyze_portfolio` | Score and rank multiple stocks, sorted by composite score |
| `get_market_sentiment` | Aggregate market sentiment with breadth analysis |
| `explain_factors` | Educational tool — explains how each factor works |

## Installation

### 1. Install Dependencies

```bash
cd plugins/mcp/bde-score
pnpm install
```

### 2. Configure MCP Server

Add to your Claude Code MCP configuration (`~/.claude/mcp_config.json`):

```json
{
  "mcpServers": {
    "bde-score": {
      "command": "node",
      "args": [
        "/absolute/path/to/plugins/mcp/bde-score/src/index.js"
      ]
    }
  }
}
```

**Important:** Replace `/absolute/path/to` with your actual installation path.

### 3. Restart Claude Code

Restart Claude Code to load the MCP server.

## Usage Examples

### Analyze a single stock

```
Use the bde-score analyze_stock tool for NVDA
```

Returns composite score (0-100), signal (BULLISH/NEUTRAL/BEARISH), and factor breakdown.

### Compare multiple stocks

```
Analyze my portfolio: AAPL, MSFT, GOOG, AMZN, NVDA, META
```

Returns all stocks ranked by score with signal classification.

### Check market sentiment

```
What's the overall market sentiment for major tech stocks?
```

Returns aggregate sentiment, market breadth, top/worst performers.

### Learn the model

```
Explain how the BDE Score factors work
```

## Scoring Model

### Signal Classification

| Signal | Score Range | Meaning |
|--------|-------------|---------|
| BULLISH | ≥ 70 | Strong multi-factor confirmation |
| MILDLY_BULLISH | 55–69 | Positive factors outweigh negative |
| NEUTRAL | 45–54 | Mixed signals, no clear direction |
| MILDLY_BEARISH | 30–44 | Negative factors outweigh positive |
| BEARISH | < 30 | Strong bearish confirmation |

### Factor Weights

| Factor | Weight | What It Measures |
|--------|--------|------------------|
| Momentum | 30% | Multi-period return strength (5/10/20/60 day) |
| Mean Reversion | 20% | Deviation from 20-day MA (oversold detection) |
| Volume | 20% | Volume ratio vs 20-day average with direction |
| Volatility | 15% | ATR-based risk measure (lower = safer) |
| Trend | 15% | EMA10/EMA50 crossover signal |

## Architecture

```
src/
├── index.js        # MCP server entry point (stdio transport)
├── scoring.js      # 5-factor scoring engine (pure JS, no deps)
└── market-data.js  # Market data fetcher (public APIs, no keys)
```

The server is fully self-contained:
- `scoring.js` implements all factor calculations in pure JavaScript
- `market-data.js` fetches OHLCV data from Yahoo Finance public endpoint
- `index.js` wires everything together as a proper MCP server with stdio transport

No external API keys. No paid services. No ephemeral tunnel URLs.

## Testing

```bash
node --test test/
```

## Disclaimer

⚠️ **Technical Analysis Only — Not financial advice.** This tool uses historical price data and technical indicators. Past performance does not predict future results. Always do your own research before making investment decisions.

## License

AGPL-3.0