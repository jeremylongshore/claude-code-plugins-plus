/**
 * BDE Score - Scoring engine tests
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { analyzeStock, analyzePortfolio, getMarketSentiment } from '../src/scoring.js';

// Generate synthetic price data for testing
function generateUptrendData(days = 60, startPrice = 100) {
  const closes = [];
  const highs = [];
  const lows = [];
  const volumes = [];
  let price = startPrice;
  
  for (let i = 0; i < days; i++) {
    price *= 1 + (Math.random() * 0.02 - 0.005); // slight uptrend
    closes.push(price);
    highs.push(price * (1 + Math.random() * 0.015));
    lows.push(price * (1 - Math.random() * 0.015));
    volumes.push(1000000 + Math.random() * 500000);
  }
  
  return { closes, highs, lows, volumes };
}

function generateDowntrendData(days = 60, startPrice = 100) {
  const closes = [];
  const highs = [];
  const lows = [];
  const volumes = [];
  let price = startPrice;
  
  for (let i = 0; i < days; i++) {
    price *= 1 - (Math.random() * 0.02 - 0.005); // slight downtrend
    closes.push(price);
    highs.push(price * (1 + Math.random() * 0.015));
    lows.push(price * (1 - Math.random() * 0.015));
    volumes.push(1000000 + Math.random() * 500000);
  }
  
  return { closes, highs, lows, volumes };
}

describe('analyzeStock', () => {
  it('should return a valid score for uptrending stock', () => {
    const data = generateUptrendData(60, 100);
    const result = analyzeStock({ symbol: 'TEST', ...data });
    
    assert.equal(result.symbol, 'TEST');
    assert.ok(result.compositeScore > 0);
    assert.ok(result.compositeScore <= 100);
    assert.ok(['BULLISH', 'MILDLY_BULLISH', 'NEUTRAL', 'MILDLY_BEARISH', 'BEARISH'].includes(result.signal));
    assert.ok(result.factorScores.momentum >= 0);
    assert.ok(result.factorScores.momentum <= 100);
    assert.equal(result.disclaimer, 'Technical Analysis Only - Not financial advice.');
  });

  it('should return a valid score for downtrending stock', () => {
    const data = generateDowntrendData(60, 100);
    const result = analyzeStock({ symbol: 'DOWN', ...data });
    
    assert.equal(result.symbol, 'DOWN');
    assert.ok(result.compositeScore >= 0);
    assert.ok(result.compositeScore <= 100);
    assert.ok(result.disclaimer);
  });

  it('should handle insufficient data gracefully', () => {
    const result = analyzeStock({ symbol: 'TINY', closes: [1, 2, 3], highs: [1, 2, 3], lows: [1, 2, 3], volumes: [1, 2, 3] });
    assert.ok(result.error);
    assert.equal(result.compositeScore, null);
  });

  it('should include all factor scores', () => {
    const data = generateUptrendData(60);
    const result = analyzeStock({ symbol: 'TEST', ...data });
    
    assert.ok('momentum' in result.factorScores);
    assert.ok('meanReversion' in result.factorScores);
    assert.ok('volume' in result.factorScores);
    assert.ok('volatility' in result.factorScores);
    assert.ok('trend' in result.factorScores);
  });

  it('should include price info', () => {
    const data = generateUptrendData(60);
    const result = analyzeStock({ symbol: 'TEST', ...data });
    
    assert.ok(result.price.current > 0);
    assert.ok(typeof result.price.change5d === 'number' || result.price.change5d === null);
  });
});

describe('analyzePortfolio', () => {
  it('should rank stocks by composite score', () => {
    const stocks = [
      { symbol: 'A', ...generateUptrendData(60, 100) },
      { symbol: 'B', ...generateDowntrendData(60, 100) },
      { symbol: 'C', ...generateUptrendData(60, 100) },
    ];
    
    const result = analyzePortfolio(stocks);
    
    assert.ok(result.rankings.length === 3);
    // Verify sorted descending
    for (let i = 1; i < result.rankings.length; i++) {
      assert.ok(result.rankings[i - 1].compositeScore >= result.rankings[i].compositeScore);
    }
    assert.ok(result.totalStocks === 3);
  });
});

describe('getMarketSentiment', () => {
  it('should compute aggregate sentiment', () => {
    const results = [
      analyzeStock({ symbol: 'A', ...generateUptrendData(60) }),
      analyzeStock({ symbol: 'B', ...generateUptrendData(60) }),
    ];
    
    const sentiment = getMarketSentiment(results);
    
    assert.ok(sentiment.sentiment);
    assert.ok(typeof sentiment.avgScore === 'number');
    assert.ok(typeof sentiment.breadth === 'number');
    assert.ok(sentiment.topPerformers.length > 0);
  });

  it('should handle empty input', () => {
    const sentiment = getMarketSentiment([]);
    assert.equal(sentiment.sentiment, 'UNKNOWN');
  });
});