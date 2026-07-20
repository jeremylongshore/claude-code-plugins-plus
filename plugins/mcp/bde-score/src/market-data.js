/**
 * BDE Score™ - Market Data Fetcher
 * 
 * Fetches stock price data from free public sources.
 * Uses Yahoo Finance's public query endpoint (no API key required).
 * 
 * Falls back gracefully when data is unavailable.
 */

const YAHOO_CHART_URL = 'https://query1.finance.yahoo.com/v8/finance/chart/';
const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BDE-Score-MCP/1.0';
const REQUEST_TIMEOUT_MS = 10000;

/**
 * Fetch historical OHLCV data for a symbol from Yahoo Finance.
 * 
 * @param {string} symbol - Stock ticker (e.g. "AAPL", "MSFT")
 * @param {number} [range=60] - Number of trading days to fetch
 * @returns {Promise<Object|null>} { closes, highs, lows, volumes, symbol } or null on failure
 */
export async function fetchStockData(symbol, range = 60) {
  try {
    // Yahoo Finance uses calendar days, ~1.5x trading days
    const calendarDays = Math.ceil(range * 1.5);
    const url = `${YAHOO_CHART_URL}${encodeURIComponent(symbol)}?range=3mo&interval=1d`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    const response = await fetch(url, {
      headers: { 'User-Agent': USER_AGENT },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const result = data?.chart?.result?.[0];
    if (!result) return null;

    const quotes = result?.indicators?.quote?.[0];
    if (!quotes || !quotes.close) return null;

    // Filter out null values (market holidays, etc.)
    const validIndices = [];
    for (let i = 0; i < quotes.close.length; i++) {
      if (quotes.close[i] != null && quotes.high[i] != null && quotes.low[i] != null) {
        validIndices.push(i);
      }
    }

    if (validIndices.length < 5) return null;

    // Take the last `range` valid data points
    const selected = validIndices.slice(-range);

    return {
      symbol: symbol.toUpperCase(),
      name: result?.meta?.shortName || result?.meta?.symbol || symbol,
      closes: selected.map(i => quotes.close[i]),
      highs: selected.map(i => quotes.high[i]),
      lows: selected.map(i => quotes.low[i]),
      volumes: selected.map(i => quotes.volume?.[i] || 0),
      currency: result?.meta?.currency || 'USD',
      exchangeTimezone: result?.meta?.exchangeTimezoneName || 'America/New_York',
    };
  } catch {
    return null;
  }
}

/**
 * Fetch data for multiple symbols in parallel with rate limiting.
 */
export async function fetchMultipleStocks(symbols, range = 60) {
  const results = [];
  
  // Process in batches of 5 to avoid rate limiting
  for (let i = 0; i < symbols.length; i += 5) {
    const batch = symbols.slice(i, i + 5);
    const batchResults = await Promise.all(
      batch.map(async (symbol) => {
        const data = await fetchStockData(symbol, range);
        return { symbol, data };
      })
    );
    results.push(...batchResults);
    
    // Small delay between batches
    if (i + 5 < symbols.length) {
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }

  return results;
}

/**
 * Validate that a symbol string looks like a valid ticker.
 */
export function isValidSymbol(symbol) {
  return /^[A-Za-z0-9.\-]{1,10}$/.test(symbol);
}