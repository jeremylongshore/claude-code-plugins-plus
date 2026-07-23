# PRD: bde-score

**Author:** hbhqq9
**Date:** 2026-07-23
**Status:** Active

## Problem

AI agents (Claude, Cursor, Windsurf) need transparent, explainable stock scoring across multiple markets (US, HK, A-shares). Existing financial MCP servers either cover a single market, rely on opaque black-box models, or lack regulatory compliance metadata. With the EU AI Act Art.50 taking effect August 2, 2026, AI agents assisting with financial analysis must provide explainable, auditable outputs — but no open-source MCP server currently offers this.

## Target users

| User | Context | Primary need |
|------|---------|--------------|
| AI agents (Claude/Cursor) | User asks for stock analysis or comparison | Transparent multi-factor scores with audit trail |
| Quantitative researchers | Need cross-market comparable scores | Single scoring model covering US/HK/CN simultaneously |
| Compliance officers | EU AI Act Art.50 deadline approaching | Machine-readable compliance metadata per analysis |
| Portfolio managers | Screening and ranking stocks | Quick screening by score threshold with sector breakdown |

## Success criteria

1. Any MCP client can retrieve BDE scores for 73 stocks across 3 markets with a single tool call
2. Every tool response includes factor-level breakdown (7 factors) and signal classification
3. Every response carries AGL Receipt Schema v2.0 audit metadata for regulatory compliance
4. Plugin installs and runs locally via stdio transport with zero external API key dependencies

## Functional requirements

- **FR-1:** Expose 5 MCP tools (score_stock, batch_score, top_performers, worst_performers, market_overview) via stdio transport for local Claude Code usage
- **FR-2:** Expose 6 MCP tools (get_bde_score, get_stock_analysis, get_multi_market_comparison, get_stock_screener, get_sector_analysis, get_esg_analysis) via Streamable HTTP for remote MCP clients
- **FR-3:** Fetch real-time OHLCV data from Yahoo Finance (local plugin) or FutuOpenD/Sina Finance (remote server) with automatic fallback
- **FR-4:** Generate immutable AGL Receipt Schema v2.0 audit records for every tool invocation (remote server only)

## Out of scope

- Trading execution or order placement
- Investment suitability assessments or financial advice
- Real-time streaming prices (scores are calculated on-demand from daily OHLCV)
- Cryptocurrency or forex markets (equities only)
