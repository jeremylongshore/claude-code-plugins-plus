---
name: analyze-trends
description: >
  Analyze price trends with technical indicators, pattern recognition,
  and...
shortcut: at
---
# Analyze Market Trends

Advanced trend analysis system using technical indicators, chart patterns, and market structure to identify trading opportunities.

## Usage

When the user wants to analyze market trends, implement comprehensive technical analysis with these components:

### Required Parameters
- **Symbol**: Asset to analyze
- **Timeframe**: 1m, 5m, 15m, 1h, 4h, 1d, 1w
- **Period**: How far back to analyze (e.g., "30 days", "6 months")
- **Analysis Type**: technical, fundamental, sentiment, or combined
- **Output Format**: report, signals, dashboard

## Implementation

### 1. Technical Analysis Engine

```javascript
class TrendAnalyzer {
    constructor() {
        this.indicators = new TechnicalIndicators();
        this.patterns = new PatternRecognition();
        this.marketStructure = new MarketStructureAnalysis();
        this.signals = new SignalGenerator();
    }

    async analyzeTrends(params) {
        const {
            symbol,
            timeframe = '1h',
            period = '30d',
            analysisType = 'technical',
            includeVolume = true
        } = params;

        // Fetch historical data
        const historicalData = await this.fetchHistoricalData(symbol, timeframe, period);

        // Perform analysis based on type
        const analysis = {
            timestamp: Date.now(),
            symbol,
            timeframe,
            period,
            dataPoints: historicalData.length,
            trend: await this.identifyTrend(historicalData),
            momentum: await this.analyzeMomentum(historicalData),
            volatility: await this.analyzeVolatility(historicalData),
            patterns: await this.detectPatterns(historicalData),
            indicators: await this.calculateIndicators(historicalData),
            structure: await this.analyzeStructure(historicalData),
            signals: await this.generateSignals(historicalData),
            forecast: await this.generateForecast(historicalData)
        };

        // Add volume analysis if requested
        if (includeVolume) {
            analysis.volume = await this.analyzeVolume(historicalData);
        }

        // Generate trading recommendations
        analysis.recommendations = this.generateRecommendations(analysis);

        return analysis;
    }

    async identifyTrend(data) {
        const prices = data.map(d => d.close);
        const highs = data.map(d => d.high);
        const lows = data.map(d => d.low);

        // Calculate trend using multiple methods
        const methods = {
            movingAverage: this.trendByMovingAverage(prices),
            higherHighsLows: this.trendByHigherHighsLows(highs, lows),
            linearRegression: this.trendByLinearRegression(prices),
            adx: this.trendByADX(data)
        };

        // Determine overall trend
        const trendVotes = Object.values(methods);
        const bullishCount = trendVotes.filter(v => v === 'BULLISH').length;
        const bearishCount = trendVotes.filter(v => v === 'BEARISH').length;

        let overallTrend;
        if (bullishCount > bearishCount + 1) {
            overallTrend = 'STRONG_BULLISH';
        } else if (bullishCount > bearishCount) {
            overallTrend = 'BULLISH';
        } else if (bearishCount > bullishCount + 1) {
            overallTrend = 'STRONG_BEARISH';
        } else if (bearishCount > bullishCount) {
            overallTrend = 'BEARISH';
        } else {
            overallTrend = 'NEUTRAL';
        }

        return {
            overall: overallTrend,
            strength: this.calculateTrendStrength(data),
            duration: this.calculateTrendDuration(data),
            methods,
            confidence: (Math.max(bullishCount, bearishCount) / trendVotes.length) * 100
        };
    }

    trendByMovingAverage(prices) {
        const ma20 = this.calculateSMA(prices, 20);
        const ma50 = this.calculateSMA(prices, 50);
        const ma200 = this.calculateSMA(prices, 200);

        const currentPrice = prices[prices.length - 1];

        if (currentPrice > ma20 && ma20 > ma50 && ma50 > ma200) {
            return 'BULLISH';
        } else if (currentPrice < ma20 && ma20 < ma50 && ma50 < ma200) {
            return 'BEARISH';
        } else {
            return 'NEUTRAL';
        }
    }

    trendByHigherHighsLows(highs, lows) {
        const recentHighs = highs.slice(-10);
        const recentLows = lows.slice(-10);

        let higherHighs = 0;
        let lowerLows = 0;
        let higherLows = 0;
        let lowerHighs = 0;

        for (let i = 1; i < recentHighs.length; i++) {
            if (recentHighs[i] > recentHighs[i-1]) higherHighs++;
            if (recentHighs[i] < recentHighs[i-1]) lowerHighs++;
            if (recentLows[i] > recentLows[i-1]) higherLows++;
            if (recentLows[i] < recentLows[i-1]) lowerLows++;
        }

        if (higherHighs > lowerHighs && higherLows > lowerLows) {
            return 'BULLISH';
        } else if (lowerHighs > higherHighs && lowerLows > higherLows) {
            return 'BEARISH';
        } else {
            return 'NEUTRAL';
        }
    }

    calculateTrendStrength(data) {
        const adx = this.calculateADX(data, 14);
        const currentADX = adx[adx.length - 1];

        if (currentADX > 50) return 'VERY_STRONG';
        if (currentADX > 40) return 'STRONG';
        if (currentADX > 25) return 'MODERATE';
        if (currentADX > 20) return 'WEAK';
        return 'VERY_WEAK';
    }

    async analyzeMomentum(data) {
        const prices = data.map(d => d.close);

        return {
            rsi: this.calculateRSI(prices, 14),
            stochastic: this.calculateStochastic(data, 14, 3, 3),
            macd: this.calculateMACD(prices),
            momentum: this.calculateMomentum(prices, 10),
            roc: this.calculateROC(prices, 12),
            williamsPR: this.calculateWilliamsPR(data, 14),
            cci: this.calculateCCI(data, 20),
            mfi: this.calculateMFI(data, 14),
            interpretation: this.interpretMomentum(prices)
        };
    }

    calculateRSI(prices, period = 14) {
        if (prices.length < period + 1) return null;

        const gains = [];
        const losses = [];

        for (let i = 1; i < prices.length; i++) {
            const change = prices[i] - prices[i - 1];
            gains.push(change > 0 ? change : 0);
            losses.push(change < 0 ? Math.abs(change) : 0);
        }

        const avgGain = gains.slice(-period).reduce((a, b) => a + b) / period;
        const avgLoss = losses.slice(-period).reduce((a, b) => a + b) / period;

        if (avgLoss === 0) return 100;

        const rs = avgGain / avgLoss;
        const rsi = 100 - (100 / (1 + rs));

        return {
            value: rsi,
            signal: rsi > 70 ? 'OVERBOUGHT' : rsi < 30 ? 'OVERSOLD' : 'NEUTRAL',
            divergence: this.checkDivergence(prices, rsi)
        };
    }

    calculateMACD(prices) {
        const ema12 = this.calculateEMA(prices, 12);
        const ema26 = this.calculateEMA(prices, 26);
        const macdLine = [];

        for (let i = 0; i < Math.min(ema12.length, ema26.length); i++) {
            macdLine.push(ema12[i] - ema26[i]);
        }

        const signal = this.calculateEMA(macdLine, 9);
        const histogram = [];

        for (let i = 0; i < Math.min(macdLine.length, signal.length); i++) {
            histogram.push(macdLine[i] - signal[i]);
        }

        return {
            macd: macdLine[macdLine.length - 1],
            signal: signal[signal.length - 1],
            histogram: histogram[histogram.length - 1],
            crossover: this.detectCrossover(macdLine, signal),
            trend: histogram[histogram.length - 1] > 0 ? 'BULLISH' : 'BEARISH'
        };
    }

    async detectPatterns(data) {
        const patterns = [];
        const prices = data.map(d => ({ open: d.open, high: d.high, low: d.low, close: d.close }));

        // Chart Patterns
        const chartPatterns = {
            headAndShoulders: this.detectHeadAndShoulders(prices),
            doubleTop: this.detectDoubleTop(prices),
            doubleBottom: this.detectDoubleBottom(prices),
            triangle: this.detectTriangle(prices),
            wedge: this.detectWedge(prices),
            flag: this.detectFlag(prices),
            pennant: this.detectPennant(prices),
            cup: this.detectCupAndHandle(prices)
        };

        // Candlestick Patterns
        const candlePatterns = {
            hammer: this.detectHammer(prices),
            doji: this.detectDoji(prices),
            engulfing: this.detectEngulfing(prices),
            morningStar: this.detectMorningStar(prices),
            eveningStar: this.detectEveningStar(prices),
            shootingStar: this.detectShootingStar(prices),
            harami: this.detectHarami(prices),
            threeWhiteSoldiers: this.detectThreeWhiteSoldiers(prices)
        };

        // Combine and score patterns
        for (const [name, result] of Object.entries(chartPatterns)) {
            if (result.detected) {
                patterns.push({
                    type: 'CHART',
                    name: name.toUpperCase(),
                    confidence: result.confidence,
                    direction: result.direction,
                    target: result.target,
                    stopLoss: result.stopLoss
                });
            }
        }

        for (const [name, result] of Object.entries(candlePatterns)) {
            if (result.detected) {
                patterns.push({
                    type: 'CANDLE',
                    name: name.toUpperCase(),
                    confidence: result.confidence,
                    signal: result.signal,
                    position: result.position
                });
            }
        }

        return patterns;
    }

    detectHeadAndShoulders(prices) {
        const highs = prices.map(p => p.high);
        const result = { detected: false, confidence: 0, direction: null };

        if (highs.length < 50) return result;

        // Look for pattern in recent data
        const recent = highs.slice(-50);
        const peaks = this.findPeaks(recent);

        if (peaks.length >= 3) {
            const [leftShoulder, head, rightShoulder] = peaks.slice(-3);

            // Check if middle peak is highest (head)
            if (head.value > leftShoulder.value &&
                head.value > rightShoulder.value &&
                Math.abs(leftShoulder.value - rightShoulder.value) / leftShoulder.value < 0.03) {

                result.detected = true;
                result.confidence = 85;
                result.direction = 'BEARISH';
                result.neckline = Math.min(
                    ...recent.slice(leftShoulder.index, rightShoulder.index + 1)
                );
                result.target = result.neckline - (head.value - result.neckline);
                result.stopLoss = head.value * 1.01;
            }
        }

        return result;
    }

    async analyzeVolume(data) {
        const volumes = data.map(d => d.volume);
        const prices = data.map(d => d.close);

        return {
            average: volumes.reduce((a, b) => a + b) / volumes.length,
            trend: this.analyzeVolumeTrend(volumes),
            obv: this.calculateOBV(prices, volumes),
            adl: this.calculateADL(data),
            mfi: this.calculateMFI(data, 14),
            vwap: this.calculateVWAP(data),
            volumeProfile: this.calculateVolumeProfile(data),
            accumulation: this.detectAccumulationDistribution(data),
            spikes: this.detectVolumeSpikes(volumes)
        };
    }

    calculateOBV(prices, volumes) {
        const obv = [volumes[0]];

        for (let i = 1; i < prices.length; i++) {
            if (prices[i] > prices[i - 1]) {
                obv.push(obv[i - 1] + volumes[i]);
            } else if (prices[i] < prices[i - 1]) {
                obv.push(obv[i - 1] - volumes[i]);
            } else {
                obv.push(obv[i - 1]);
            }
        }

        return {
            values: obv,
            current: obv[obv.length - 1],
            trend: this.calculateTrend(obv.slice(-20)),
            divergence: this.checkVolumePriceDivergence(prices, obv)
        };
    }

    async generateSignals(data) {
        const signals = [];
        const analysis = {
            trend: await this.identifyTrend(data),
            momentum: await this.analyzeMomentum(data),
            patterns: await this.detectPatterns(data)
        };

        // Trend-based signals
        if (analysis.trend.overall === 'STRONG_BULLISH') {
            signals.push({
                type: 'BUY',
                strength: 'STRONG',
                reason: 'Strong bullish trend confirmed',
                confidence: analysis.trend.confidence
            });
        }

        // Momentum signals
        if (analysis.momentum.rsi.value < 30) {
            signals.push({
                type: 'BUY',
                strength: 'MEDIUM',
                reason: 'RSI oversold condition',
                confidence: 70
            });
        }

        // Pattern signals
        for (const pattern of analysis.patterns) {
            if (pattern.type === 'CHART' && pattern.confidence > 80) {
                signals.push({
                    type: pattern.direction === 'BULLISH' ? 'BUY' : 'SELL',
                    strength: 'STRONG',
                    reason: `${pattern.name} pattern detected`,
                    confidence: pattern.confidence,
                    target: pattern.target,
                    stopLoss: pattern.stopLoss
                });
            }
        }

        // MACD crossover signals
        if (analysis.momentum.macd.crossover === 'BULLISH') {
            signals.push({
                type: 'BUY',
                strength: 'MEDIUM',
                reason: 'MACD bullish crossover',
                confidence: 65
            });
        }

        return this.prioritizeSignals(signals);
    }

    prioritizeSignals(signals) {
        // Sort by confidence and strength
        return signals.sort((a, b) => {
            const strengthScore = { STRONG: 3, MEDIUM: 2, WEAK: 1 };
            const scoreA = a.confidence * strengthScore[a.strength];
            const scoreB = b.confidence * strengthScore[b.strength];
            return scoreB - scoreA;
        }).slice(0, 5); // Top 5 signals
    }
}
```

### 2. Market Structure Analysis

```javascript
class MarketStructureAnalysis {
    analyzeStructure(data) {
        return {
            marketPhase: this.identifyMarketPhase(data),
            keyLevels: this.identifyKeyLevels(data),
            liquidityZones: this.findLiquidityZones(data),
            orderFlow: this.analyzeOrderFlow(data),
            marketProfile: this.createMarketProfile(data),
            supplyDemand: this.identifySupplyDemandZones(data)
        };
    }

    identifyMarketPhase(data) {
        const volatility = this.calculateVolatility(data);
        const trend = this.calculateTrendStrength(data);
        const volume = this.analyzeVolumeCharacteristics(data);

        if (volatility < 0.01 && trend < 25) {
            return {
                phase: 'ACCUMULATION',
                characteristics: 'Low volatility, sideways movement, smart money accumulating',
                tradingStrategy: 'Buy at support, sell at resistance'
            };
        } else if (trend > 40 && volume.trend === 'INCREASING') {
            return {
                phase: 'MARK_UP',
                characteristics: 'Strong trend, increasing volume, institutional buying',
                tradingStrategy: 'Trend following, buy dips'
            };
        } else if (volatility > 0.03 && trend < 25) {
            return {
                phase: 'DISTRIBUTION',
                characteristics: 'High volatility, topping pattern, smart money distributing',
                tradingStrategy: 'Take profits, short at resistance'
            };
        } else if (trend > 40 && volume.trend === 'DECREASING') {
            return {
                phase: 'MARK_DOWN',
                characteristics: 'Downtrend, panic selling, capitulation',
                tradingStrategy: 'Stay out or short rallies'
            };
        } else {
            return {
                phase: 'TRANSITION',
                characteristics: 'Changing market dynamics',
                tradingStrategy: 'Wait for confirmation'
            };
        }
    }

    identifyKeyLevels(data) {
        const levels = [];
        const highs = data.map(d => d.high);
        const lows = data.map(d => d.low);
        const closes = data.map(d => d.close);

        // Psychological levels (round numbers)
        const currentPrice = closes[closes.length - 1];
        const roundLevels = this.findRoundNumbers(currentPrice);

        // Historical support/resistance
        const historicalLevels = this.findHistoricalLevels(highs, lows, closes);

        // Volume-based levels
        const volumeLevels = this.findVolumeLevels(data);

        // Fibonacci levels
        const fibLevels = this.calculateFibonacciLevels(
            Math.min(...lows),
            Math.max(...highs)
        );

        return {
            psychological: roundLevels,
            historical: historicalLevels,
            volume: volumeLevels,
            fibonacci: fibLevels,
            combined: this.combineAndRankLevels([
                ...roundLevels,
                ...historicalLevels,
                ...volumeLevels,
                ...fibLevels
            ])
        };
    }

    findLiquidityZones(data) {
        const zones = [];
        const volumes = data.map(d => d.volume);
        const avgVolume = volumes.reduce((a, b) => a + b) / volumes.length;

        for (let i = 0; i < data.length - 10; i++) {
            const window = data.slice(i, i + 10);
            const windowVolume = window.reduce((sum, d) => sum + d.volume, 0);

            if (windowVolume > avgVolume * 10 * 1.5) {
                const highPrice = Math.max(...window.map(d => d.high));
                const lowPrice = Math.min(...window.map(d => d.low));

                zones.push({
                    type: 'HIGH_LIQUIDITY',
                    upperBound: highPrice,
                    lowerBound: lowPrice,
                    volume: windowVolume,
                    strength: windowVolume / (avgVolume * 10)
                });
            }
        }

        return zones;
    }
}
```

### 3. Display and Reporting

```javascript
class TrendReport {
    generateReport(analysis) {
        return `
╔════════════════════════════════════════════════════════════════╗
║                    TREND ANALYSIS REPORT                       ║
╠════════════════════════════════════════════════════════════════╣
║ Symbol:        ${analysis.symbol.padEnd(48)} ║
║ Timeframe:     ${analysis.timeframe.padEnd(48)} ║
║ Period:        ${analysis.period.padEnd(48)} ║
║ Data Points:   ${analysis.dataPoints.toString().padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                         TREND                                  ║
╠════════════════════════════════════════════════════════════════╣
║ Direction:     ${this.formatTrend(analysis.trend.overall).padEnd(48)} ║
║ Strength:      ${analysis.trend.strength.padEnd(48)} ║
║ Duration:      ${analysis.trend.duration.padEnd(48)} ║
║ Confidence:    ${this.formatPercentage(analysis.trend.confidence).padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                      MOMENTUM                                  ║
╠════════════════════════════════════════════════════════════════╣
║ RSI (14):      ${this.formatRSI(analysis.momentum.rsi).padEnd(48)} ║
║ MACD:          ${this.formatMACD(analysis.momentum.macd).padEnd(48)} ║
║ Stochastic:    ${this.formatStochastic(analysis.momentum.stochastic).padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                      PATTERNS                                  ║
╠════════════════════════════════════════════════════════════════╣
${this.formatPatterns(analysis.patterns)}
╠════════════════════════════════════════════════════════════════╣
║                   TOP SIGNALS                                  ║
╠════════════════════════════════════════════════════════════════╣
${this.formatSignals(analysis.signals)}
╠════════════════════════════════════════════════════════════════╣
║                 RECOMMENDATIONS                                ║
╠════════════════════════════════════════════════════════════════╣
${this.formatRecommendations(analysis.recommendations)}
╚════════════════════════════════════════════════════════════════╝
`;
    }

    formatTrend(trend) {
        const icons = {
            STRONG_BULLISH: ' Strong Bullish',
            BULLISH: ' Bullish',
            NEUTRAL: ' Neutral',
            BEARISH: ' Bearish',
            STRONG_BEARISH: ' Strong Bearish'
        };
        return icons[trend] || trend;
    }

    formatPatterns(patterns) {
        if (patterns.length === 0) {
            return '║ No significant patterns detected                               ║';
        }

        return patterns.slice(0, 3).map(p =>
            `║ ${p.name.padEnd(20)} Confidence: ${p.confidence}% ${p.direction.padEnd(20)} ║`
        ).join('\n');
    }

    formatSignals(signals) {
        if (signals.length === 0) {
            return '║ No strong signals at this time                                 ║';
        }

        return signals.slice(0, 3).map(s =>
            `║ ${s.type} - ${s.reason.padEnd(35)} [${s.confidence}%] ║`
        ).join('\n');
    }
}
```

## Error Handling

```javascript
try {
    const analyzer = new TrendAnalyzer();
    const analysis = await analyzer.analyzeTrends({
        symbol: 'BTC/USDT',
        timeframe: '4h',
        period: '30d',
        analysisType: 'technical'
    });

    const report = new TrendReport();
    console.log(report.generateReport(analysis));

} catch (error) {
    console.error('Trend analysis failed:', error);
}
```

This command provides comprehensive trend analysis with technical indicators, pattern recognition, and actionable trading signals.