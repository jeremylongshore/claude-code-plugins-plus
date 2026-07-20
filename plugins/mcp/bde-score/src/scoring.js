/**
 * BDE Score™ - 5-Factor Quantitative Scoring Engine
 * 
 * Pure JavaScript implementation of the multi-factor stock scoring model.
 * No external dependencies, no API keys required.
 * 
 * Factors:
 *   1. Momentum (30%) - Multi-period return strength
 *   2. Mean Reversion (20%) - Deviation from 20-day moving average
 *   3. Volume (20%) - Volume ratio anomaly detection
 *   4. Volatility (15%) - ATR-based, lower volatility preferred
 *   5. Trend (15%) - EMA crossover signals
 * 
 * Each factor outputs 0-100. Weighted composite determines final score.
 * Signal classification: Bullish (>70), Neutral (40-70), Bearish (<40)
 */

// ============================================================
// Configuration
// ============================================================
const FACTOR_WEIGHTS = {
  momentum: 0.30,
  meanReversion: 0.20,
  volume: 0.20,
  volatility: 0.15,
  trend: 0.15,
};

const MOMENTUM_PERIODS = [5, 10, 20, 60];
const MEAN_REVERSION_WINDOW = 20;
const MEAN_REVERSION_THRESHOLD = 0.05;
const VOLUME_LOOKBACK = 20;
const VOLUME_SPIKE_THRESHOLD = 1.5;
const ATR_PERIOD = 14;
const VOLATILITY_WINDOW = 20;
const EMA_SHORT = 10;
const EMA_LONG = 50;

// ============================================================
// Utility functions
// ============================================================

function clamp(value, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

/**
 * Calculate Exponential Moving Average
 */
function calcEMA(values, period) {
  if (values.length < period) return null;
  const k = 2 / (period + 1);
  let ema = values.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < values.length; i++) {
    ema = values[i] * k + ema * (1 - k);
  }
  return ema;
}

/**
 * Calculate simple moving average of last N values
 */
function calcSMA(values, period) {
  if (values.length < period) return null;
  const slice = values.slice(-period);
  return slice.reduce((a, b) => a + b, 0) / period;
}

/**
 * Calculate Average True Range
 */
function calcATR(highs, lows, closes, period) {
  if (closes.length < period + 1) return null;
  const trueRanges = [];
  for (let i = 1; i < closes.length; i++) {
    const tr = Math.max(
      highs[i] - lows[i],
      Math.abs(highs[i] - closes[i - 1]),
      Math.abs(lows[i] - closes[i - 1])
    );
    trueRanges.push(tr);
  }
  if (trueRanges.length < period) return null;
  return calcSMA(trueRanges, period);
}

// ============================================================
// Factor Calculations
// ============================================================

/**
 * Factor 1: Momentum (30% weight)
 * Evaluates multi-period return strength.
 * Higher returns across multiple timeframes = higher score.
 */
function calcMomentumScore(closes) {
  if (closes.length < 5) return 50;

  const scores = [];
  for (const period of MOMENTUM_PERIODS) {
    if (closes.length < period + 1) {
      scores.push(50);
      continue;
    }
    const returnPct = (closes[closes.length - 1] - closes[closes.length - 1 - period]) / closes[closes.length - 1 - period];
    
    // Map return to 0-100 score
    // -10% -> 10, 0% -> 50, +10% -> 90
    const score = clamp(50 + returnPct * 400);
    scores.push(score);
  }

  // Multi-period confirmation bonus
  const positiveCount = scores.filter(s => s > 50).length;
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
  const bonus = positiveCount >= 3 ? 5 : 0;
  
  return clamp(avg + bonus);
}

/**
 * Factor 2: Mean Reversion (20% weight)
 * Detects oversold conditions - stocks below MA20 get higher scores.
 */
function calcMeanReversionScore(closes) {
  if (closes.length < MEAN_REVERSION_WINDOW) return 50;

  const ma20 = calcSMA(closes, MEAN_REVERSION_WINDOW);
  if (!ma20) return 50;

  const current = closes[closes.length - 1];
  const deviation = (current - ma20) / ma20;

  // Negative deviation (below MA) = higher score (potential buy)
  // deviation of -5% -> score ~80
  // deviation of +5% -> score ~20
  const score = clamp(50 - deviation * 600);
  return score;
}

/**
 * Factor 3: Volume (20% weight)
 * Volume ratio compared to 20-day average.
 * Higher volume = stronger conviction in the move.
 */
function calcVolumeScore(volumes, closes) {
  if (volumes.length < VOLUME_LOOKBACK) return 50;

  const avgVolume = calcSMA(volumes, VOLUME_LOOKBACK);
  if (!avgVolume || avgVolume === 0) return 50;

  const currentVolume = volumes[volumes.length - 1];
  const volumeRatio = currentVolume / avgVolume;

  // Combine volume strength with price direction
  const priceUp = closes.length >= 2 && closes[closes.length - 1] > closes[closes.length - 2];
  
  let score;
  if (volumeRatio >= VOLUME_SPIKE_THRESHOLD) {
    // High volume - direction matters
    score = priceUp ? 75 : 30;
  } else if (volumeRatio >= 1.0) {
    score = priceUp ? 60 : 40;
  } else {
    // Low volume = neutral/indecisive
    score = 45;
  }

  return clamp(score);
}

/**
 * Factor 4: Volatility (15% weight)
 * Lower volatility preferred (safety factor).
 * Uses ATR normalized by price.
 */
function calcVolatilityScore(highs, lows, closes) {
  if (closes.length < VOLATILITY_WINDOW + 1) return 50;

  const atr = calcATR(highs, lows, closes, ATR_PERIOD);
  if (!atr) return 50;

  const currentPrice = closes[closes.length - 1];
  const atrPct = (atr / currentPrice) * 100;

  // Lower ATR% = safer = higher score
  // atrPct of 0.5% -> score ~85
  // atrPct of 2% -> score ~65
  // atrPct of 5% -> score ~35
  const score = clamp(90 - atrPct * 11);
  return score;
}

/**
 * Factor 5: Trend (15% weight)
 * EMA crossover signal.
 * EMA10 > EMA50 = bullish trend.
 */
function calcTrendScore(closes) {
  if (closes.length < EMA_LONG) return 50;

  const emaShort = calcEMA(closes, EMA_SHORT);
  const emaLong = calcEMA(closes, EMA_LONG);
  if (!emaShort || !emaLong) return 50;

  const diff = (emaShort - emaLong) / emaLong;

  // Strong uptrend (EMA short well above EMA long) = high score
  // diff of +5% -> score ~85
  // diff of 0% -> score ~50
  // diff of -5% -> score ~15
  const score = clamp(50 + diff * 700);
  return score;
}

// ============================================================
// Signal Classification
// ============================================================

function classifySignal(compositeScore) {
  if (compositeScore >= 70) return 'BULLISH';
  if (compositeScore >= 55) return 'MILDLY_BULLISH';
  if (compositeScore >= 45) return 'NEUTRAL';
  if (compositeScore >= 30) return 'MILDLY_BEARISH';
  return 'BEARISH';
}

// ============================================================
// Main Scoring Function
// ============================================================

/**
 * Analyze a single stock with the 5-factor BDE model.
 * 
 * @param {Object} params
 * @param {string} params.symbol - Stock ticker symbol
 * @param {number[]} params.closes - Closing prices (oldest to newest)
 * @param {number[]} params.highs - High prices
 * @param {number[]} params.lows - Low prices
 * @param {number[]} params.volumes - Trading volumes
 * @param {string} [params.name] - Optional stock name
 * @returns {Object} Complete analysis result
 */
export function analyzeStock({ symbol, closes, highs, lows, volumes, name }) {
  if (!closes || closes.length < 5) {
    return {
      symbol,
      name: name || symbol,
      error: 'Insufficient data - need at least 5 data points',
      compositeScore: null,
      signal: 'UNKNOWN',
    };
  }

  // Calculate individual factor scores
  const factorScores = {
    momentum: calcMomentumScore(closes),
    meanReversion: calcMeanReversionScore(closes),
    volume: calcVolumeScore(volumes || closes.map(() => 1000000), closes),
    volatility: calcVolatilityScore(
      highs || closes.map(c => c * 1.01),
      lows || closes.map(c => c * 0.99),
      closes
    ),
    trend: calcTrendScore(closes),
  };

  // Weighted composite
  const compositeScore = Object.entries(FACTOR_WEIGHTS).reduce(
    (sum, [factor, weight]) => sum + factorScores[factor] * weight,
    0
  );

  const signal = classifySignal(compositeScore);
  const currentPrice = closes[closes.length - 1];
  const priceChange5d = closes.length >= 6
    ? ((currentPrice - closes[closes.length - 6]) / closes[closes.length - 6] * 100)
    : null;
  const priceChange20d = closes.length >= 21
    ? ((currentPrice - closes[closes.length - 21]) / closes[closes.length - 21] * 100)
    : null;

  return {
    symbol,
    name: name || symbol,
    compositeScore: Math.round(compositeScore * 10) / 10,
    signal,
    factorScores: {
      momentum: Math.round(factorScores.momentum * 10) / 10,
      meanReversion: Math.round(factorScores.meanReversion * 10) / 10,
      volume: Math.round(factorScores.volume * 10) / 10,
      volatility: Math.round(factorScores.volatility * 10) / 10,
      trend: Math.round(factorScores.trend * 10) / 10,
    },
    weights: FACTOR_WEIGHTS,
    price: {
      current: currentPrice,
      change5d: priceChange5d !== null ? Math.round(priceChange5d * 100) / 100 : null,
      change20d: priceChange20d !== null ? Math.round(priceChange20d * 100) / 100 : null,
    },
    dataPoints: closes.length,
    timestamp: new Date().toISOString(),
    disclaimer: 'Technical Analysis Only - Not financial advice.',
  };
}

/**
 * Analyze multiple stocks and rank them.
 */
export function analyzePortfolio(stocks) {
  const results = stocks
    .map(stock => analyzeStock(stock))
    .filter(r => !r.error)
    .sort((a, b) => b.compositeScore - a.compositeScore);

  return {
    analyzedAt: new Date().toISOString(),
    totalStocks: results.length,
    bullish: results.filter(r => r.signal === 'BULLISH').length,
    neutral: results.filter(r => ['MILDLY_BULLISH', 'NEUTRAL', 'MILDLY_BEARISH'].includes(r.signal)).length,
    bearish: results.filter(r => r.signal === 'BEARISH').length,
    rankings: results,
    disclaimer: 'Technical Analysis Only - Not financial advice.',
  };
}

/**
 * Get market sentiment summary from a set of scores.
 */
export function getMarketSentiment(results) {
  if (!results || results.length === 0) {
    return { sentiment: 'UNKNOWN', details: 'No data available' };
  }

  const avgScore = results.reduce((sum, r) => sum + r.compositeScore, 0) / results.length;
  const bullishCount = results.filter(r => r.signal === 'BULLISH').length;
  const bearishCount = results.filter(r => r.signal === 'BEARISH').length;
  const breadth = (bullishCount - bearishCount) / results.length;

  let sentiment;
  if (avgScore >= 65 && breadth > 0.3) sentiment = 'STRONGLY_BULLISH';
  else if (avgScore >= 55 && breadth > 0) sentiment = 'BULLISH';
  else if (avgScore >= 45 && breadth >= -0.1) sentiment = 'NEUTRAL';
  else if (avgScore >= 35) sentiment = 'BEARISH';
  else sentiment = 'STRONGLY_BEARISH';

  // Sort by compositeScore descending to rank performers
  const sorted = [...results].sort((a, b) => b.compositeScore - a.compositeScore);

  return {
    sentiment,
    avgScore: Math.round(avgScore * 10) / 10,
    breadth: Math.round(breadth * 100) / 100,
    bullishCount,
    bearishCount,
    totalAnalyzed: results.length,
    topPerformers: sorted.slice(0, 5).map(r => ({
      symbol: r.symbol,
      score: r.compositeScore,
      signal: r.signal,
    })),
    worstPerformers: sorted.slice(-5).reverse().map(r => ({
      symbol: r.symbol,
      score: r.compositeScore,
      signal: r.signal,
    })),
    timestamp: new Date().toISOString(),
    disclaimer: 'Technical Analysis Only - Not financial advice.',
  };
}