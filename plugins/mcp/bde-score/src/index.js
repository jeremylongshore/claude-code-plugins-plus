#!/usr/bin/env node

/**
 * BDE Score™ - MCP Server
 * 
 * A self-contained MCP server providing multi-factor quantitative stock scoring.
 * Uses stdio transport to communicate with Claude Code.
 * 
 * Tools:
 *   - analyze_stock: Score a single stock with the 5-factor model
 *   - analyze_portfolio: Score and rank multiple stocks
 *   - get_market_sentiment: Aggregate sentiment from a universe of stocks
 *   - explain_factors: Educational - explain how each factor works
 * 
 * Copyright (C) 2026 BDE Score™
 * Licensed under AGPL-3.0
 * Repository: https://github.com/hbhqq9/bde-score
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { analyzeStock, analyzePortfolio, getMarketSentiment } from './scoring.js';
import { fetchStockData, fetchMultipleStocks, isValidSymbol } from './market-data.js';

// ============================================================
// Server Setup
// ============================================================

const server = new Server(
  {
    name: 'bde-score',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// ============================================================
// Tool Definitions
// ============================================================

const TOOLS = [
  {
    name: 'analyze_stock',
    description: 'Analyze a single stock using the BDE 5-factor quantitative scoring model. Factors: Momentum (30%), Mean Reversion (20%), Volume (20%), Volatility (15%), Trend (15%). Returns a composite score (0-100) with signal classification (BULLISH/NEUTRAL/BEARISH) and detailed factor breakdown. Fetches real-time market data automatically.',
    inputSchema: {
      type: 'object',
      properties: {
        symbol: {
          type: 'string',
          description: 'Stock ticker symbol (e.g. "AAPL", "MSFT", "00700.HK")',
        },
        range: {
          type: 'number',
          description: 'Number of trading days of historical data to use (default: 60, max: 200)',
          default: 60,
        },
      },
      required: ['symbol'],
    },
  },
  {
    name: 'analyze_portfolio',
    description: 'Analyze and rank multiple stocks using the BDE 5-factor model. Returns all stocks sorted by composite score with signal classification. Useful for screening and comparing stocks.',
    inputSchema: {
      type: 'object',
      properties: {
        symbols: {
          type: 'array',
          items: { type: 'string' },
          description: 'Array of stock ticker symbols (e.g. ["AAPL", "MSFT", "GOOG", "NVDA"])',
        },
        range: {
          type: 'number',
          description: 'Number of trading days of historical data (default: 60)',
          default: 60,
        },
      },
      required: ['symbols'],
    },
  },
  {
    name: 'get_market_sentiment',
    description: 'Get aggregate market sentiment from a universe of stocks. Analyzes multiple stocks and returns overall market sentiment (STRONGLY_BULLISH to STRONGLY_BEARISH), market breadth, top/worst performers. Default universe: major US tech stocks.',
    inputSchema: {
      type: 'object',
      properties: {
        symbols: {
          type: 'array',
          items: { type: 'string' },
          description: 'Array of stock ticker symbols to analyze. If omitted, uses a default universe of 15 major US stocks.',
        },
      },
      required: [],
    },
  },
  {
    name: 'explain_factors',
    description: 'Explain the BDE Score 5-factor model: what each factor measures, how scores are calculated, and how to interpret results. Educational tool - no market data needed.',
    inputSchema: {
      type: 'object',
      properties: {
        factor: {
          type: 'string',
          enum: ['all', 'momentum', 'mean_reversion', 'volume', 'volatility', 'trend'],
          description: 'Which factor to explain. "all" explains the entire model. Default: "all".',
          default: 'all',
        },
      },
      required: [],
    },
  },
];

// ============================================================
// Tool Handlers
// ============================================================

const DEFAULT_UNIVERSE = [
  'AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA',
  'AMD', 'AVGO', 'INTC', 'V', 'MA', 'JNJ', 'UNH', 'SPY',
];

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'analyze_stock': {
        const symbol = args?.symbol;
        if (!symbol || !isValidSymbol(symbol)) {
          return errorResult('Invalid symbol. Use a standard ticker like "AAPL" or "MSFT".');
        }

        const range = Math.min(Math.max(args?.range || 60, 10), 200);
        
        const stockData = await fetchStockData(symbol, range);
        if (!stockData) {
          return errorResult(
            `Could not fetch data for "${symbol}". The symbol may not exist, or the market data service is temporarily unavailable.`
          );
        }

        const result = analyzeStock({
          symbol: stockData.symbol,
          name: stockData.name,
          closes: stockData.closes,
          highs: stockData.highs,
          lows: stockData.lows,
          volumes: stockData.volumes,
        });

        return successResult(result);
      }

      case 'analyze_portfolio': {
        const symbols = args?.symbols;
        if (!Array.isArray(symbols) || symbols.length === 0) {
          return errorResult('Provide at least one stock symbol in the "symbols" array.');
        }
        if (symbols.length > 20) {
          return errorResult('Maximum 20 symbols per request to avoid rate limiting.');
        }

        // Validate all symbols
        const invalid = symbols.filter(s => !isValidSymbol(s));
        if (invalid.length > 0) {
          return errorResult(`Invalid symbols: ${invalid.join(', ')}. Use standard tickers.`);
        }

        const range = Math.min(Math.max(args?.range || 60, 10), 200);
        const fetched = await fetchMultipleStocks(symbols, range);
        
        const validStocks = fetched
          .filter(f => f.data !== null)
          .map(f => ({
            symbol: f.data.symbol,
            name: f.data.name,
            closes: f.data.closes,
            highs: f.data.highs,
            lows: f.data.lows,
            volumes: f.data.volumes,
          }));

        const failed = fetched.filter(f => f.data === null).map(f => f.symbol);
        
        const result = analyzePortfolio(validStocks);
        if (failed.length > 0) {
          result.failedSymbols = failed;
          result.note = `${failed.length} symbol(s) could not be fetched: ${failed.join(', ')}`;
        }

        return successResult(result);
      }

      case 'get_market_sentiment': {
        const symbols = args?.symbols || DEFAULT_UNIVERSE;
        if (!Array.isArray(symbols) || symbols.length === 0) {
          return errorResult('Provide at least one stock symbol.');
        }
        if (symbols.length > 20) {
          return errorResult('Maximum 20 symbols per request.');
        }

        const fetched = await fetchMultipleStocks(symbols, 60);
        
        const results = fetched
          .filter(f => f.data !== null)
          .map(f => analyzeStock({
            symbol: f.data.symbol,
            name: f.data.name,
            closes: f.data.closes,
            highs: f.data.highs,
            lows: f.data.lows,
            volumes: f.data.volumes,
          }));

        const sentiment = getMarketSentiment(results);
        sentiment.isDefaultUniverse = !args?.symbols;

        return successResult(sentiment);
      }

      case 'explain_factors': {
        const factor = args?.factor || 'all';
        return successResult(explainFactors(factor));
      }

      default:
        return errorResult(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal server error';
    return errorResult(message);
  }
});

// ============================================================
// Helper Functions
// ============================================================

function successResult(data) {
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(data, null, 2),
      },
    ],
  };
}

function errorResult(message) {
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({ error: message }, null, 2),
      },
    ],
    isError: true,
  };
}

function explainFactors(factor) {
  const explanations = {
    momentum: {
      factor: 'Momentum',
      weight: '30%',
      description: 'Measures the strength and direction of price movement across multiple timeframes (5, 10, 20, 60 days). Stocks with consistent upward price movement across multiple periods score higher.',
      interpretation: 'Score >70: Strong upward momentum. Score <30: Weak or negative momentum.',
    },
    mean_reversion: {
      factor: 'Mean Reversion',
      weight: '20%',
      description: 'Measures how far the current price has deviated from the 20-day moving average. Stocks trading significantly below their average (oversold) score higher, as they may be due for a bounce.',
      interpretation: 'Score >70: Oversold (price well below MA20). Score <30: Overbought (price well above MA20).',
    },
    volume: {
      factor: 'Volume',
      weight: '20%',
      description: 'Compares current trading volume to the 20-day average. High volume combined with upward price movement indicates strong buying conviction. Low volume suggests indecision.',
      interpretation: 'Score >70: High volume with bullish price action. Score <30: High volume with bearish action (selling pressure).',
    },
    volatility: {
      factor: 'Volatility',
      weight: '15%',
      description: 'Uses Average True Range (ATR) normalized by price. Lower volatility stocks score higher as they represent lower risk. This is a safety/quality factor.',
      interpretation: 'Score >70: Low volatility (stable price). Score <30: High volatility (erratic price swings).',
    },
    trend: {
      factor: 'Trend',
      weight: '15%',
      description: 'Uses the crossover of 10-day and 50-day Exponential Moving Averages (EMA). When the short-term EMA is above the long-term EMA, the stock is in an uptrend.',
      interpretation: 'Score >70: Strong uptrend (EMA10 well above EMA50). Score <30: Downtrend (EMA10 below EMA50).',
    },
  };

  if (factor === 'all') {
    return {
      model: 'BDE Score™ 5-Factor Model',
      version: '1.0.0',
      overview: 'A quantitative scoring system that evaluates stocks across 5 independent factors. Each factor produces a score from 0-100. The weighted composite determines the overall BDE Score.',
      weights: {
        'Momentum': '30% - Price movement strength',
        'Mean Reversion': '20% - Oversold/overbought detection',
        'Volume': '20% - Trading activity conviction',
        'Volatility': '15% - Risk/stability measure',
        'Trend': '15% - Moving average crossover',
      },
      signalThresholds: {
        'BULLISH': 'Score >= 70',
        'MILDLY_BULLISH': 'Score 55-69',
        'NEUTRAL': 'Score 45-54',
        'MILDLY_BEARISH': 'Score 30-44',
        'BEARISH': 'Score < 30',
      },
      factors: explanations,
      disclaimer: 'Technical Analysis Only - Not financial advice. Past performance does not predict future results.',
    };
  }

  const key = factor.replace(/-/g, '_');
  if (!explanations[key]) {
    return { error: `Unknown factor: ${factor}. Valid factors: all, momentum, mean_reversion, volume, volatility, trend` };
  }

  return explanations[key];
}

// ============================================================
// Start Server
// ============================================================

const transport = new StdioServerTransport();
await server.connect(transport);

// Log to stderr (not stdout - stdout is for MCP protocol)
console.error('[bde-score] MCP server started on stdio transport');
console.error('[bde-score] Tools: analyze_stock, analyze_portfolio, get_market_sentiment, explain_factors');