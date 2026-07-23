# ADR: bde-score — MCP Server Architecture for Multi-Market Stock Scoring

**Author:** hbhqq9
**Date:** 2026-07-23
**Status:** Accepted

## Context

BDE Score needs to serve stock analysis to AI agents via the Model Context Protocol. The system must:
- Work both as a local Claude Code plugin (stdio transport, zero dependencies) and as a remote MCP server (Streamable HTTP, with compliance metadata)
- Cover 73 stocks across 3 markets (US, HK, A-shares) with a unified scoring model
- Comply with EU AI Act Art.50 transparency requirements (explainable scores, audit trails)

The local plugin (this submission) focuses on zero-dependency local execution. The remote server adds API key auth, x402 payment protocol, and AGL receipt generation.

## Decision

We use a dual-architecture MCP server:

1. **Local plugin (this submission):** Self-contained Node.js MCP server using stdio transport. Fetches data directly from Yahoo Finance's public API (no API key required). Implements 5-factor scoring in pure JavaScript.

2. **Remote server:** Python FastMCP server behind Cloudflare Tunnel, using Streamable HTTP transport. Adds AGL Receipt Schema v2.0 for audit compliance, x402 payment middleware, and FutuOpenD/Sina Finance data sources for HK/CN markets.

Both expose the same conceptual tools with compatible output formats.

## Alternatives considered

| Alternative | Why rejected |
|-------------|-------------|
| REST API only (no MCP) | AI agents cannot discover or call REST APIs natively; MCP is the standard for AI tool integration |
| Single unified codebase (Python only) | Local plugin must work without Python installation; Claude Code users expect Node.js plugins |
| SSE transport (deprecated) | MCP spec now recommends Streamable HTTP; SSE is deprecated for new servers |
| External data API dependency for local plugin | Would require API keys, breaking the zero-config local experience |

## Consequences

**Positive:**

- Local plugin works with zero configuration — `npm install && npm start`
- Remote server provides enterprise-grade compliance (AGL receipts, x402 payments)
- Both architectures serve the same user base through their preferred deployment model
- Yahoo Finance data is free and requires no authentication

**Negative / accepted tradeoffs:**

- Two codebases (Node.js + Python) increase maintenance burden — accepted because the audiences differ (local developers vs enterprise/compliance users)
- Yahoo Finance rate limits may cause local plugin failures under heavy use — accepted because free tier is for personal/research use
- HK/CN market data in local plugin is limited to Yahoo Finance coverage (less comprehensive than FutuOpenD) — accepted tradeoff for zero-config experience

## Tool-permission scope

| Tool | Why it's needed |
|------|----------------|
| `fetch` (network) | Read-only HTTP requests to Yahoo Finance public API for stock data |
| `console.error` (stderr) | MCP protocol logging on stderr (stdout is reserved for JSON-RPC) |
| No file system access | Plugin operates purely in-memory; no files written |
| No Bash/shell access | Pure JavaScript execution; no subprocess spawning |
