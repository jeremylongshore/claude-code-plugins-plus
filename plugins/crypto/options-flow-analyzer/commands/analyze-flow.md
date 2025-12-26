---
name: analyze-flow
description: >
  Analyze institutional options flow and detect smart money movements
shortcut: af
---
# Analyze Options Flow

Track institutional options flow, unusual options activity, and smart money movements with advanced flow analysis.

## Usage

When analyzing options flow, implement comprehensive tracking of institutional activity:

### Required Parameters
- **Symbol**: Underlying ticker or "ALL" for market-wide
- **Timeframe**: real-time, 1d, 5d, 30d
- **Flow Type**: calls, puts, both
- **Min Premium**: Minimum trade value to track
- **Sentiment**: bullish, bearish, neutral, all

## Implementation

### 1. Options Flow Analyzer

```javascript
class OptionsFlowAnalyzer {
    constructor() {
        this.dataSources = {
            primary: process.env.OPTIONS_FLOW_API,
            cboe: 'https://www.cboe.com/api',
            opra: process.env.OPRA_FEED,
            unusual: process.env.UNUSUAL_WHALES_API
        };

        this.flowThresholds = {
            institutional: 1000000,  // $1M premium
            unusual: 100000,         // $100K premium
            retail: 10000           // $10K premium
        };
    }

    async analyzeFlow(params) {
        const {
            symbol = 'ALL',
            timeframe = '1d',
            flowType = 'both',
            minPremium = 100000,
            sentiment = 'all'
        } = params;

        const analysis = {
            timestamp: Date.now(),
            symbol,
            timeframe,
            flowSummary: await this.getFlowSummary(symbol, timeframe),
            unusualActivity: await this.detectUnusualActivity(symbol, minPremium),
            smartMoney: await this.identifySmartMoney(symbol),
            volumeAnalysis: await this.analyzeVolume(symbol),
            gammaExposure: await this.calculateGammaExposure(symbol),
            dealerPositioning: await this.analyzeDealerPositioning(symbol),
            flowSignals: await this.generateFlowSignals(symbol),
            riskMetrics: await this.calculateRiskMetrics(symbol)
        };

        return analysis;
    }

    async getFlowSummary(symbol, timeframe) {
        const flows = await this.fetchOptionsFlow(symbol, timeframe);

        const summary = {
            totalVolume: 0,
            totalPremium: 0,
            callVolume: 0,
            putVolume: 0,
            callPremium: 0,
            putPremium: 0,
            putCallRatio: 0,
            premiumRatio: 0,
            largestTrades: [],
            mostActive: [],
            sentiment: 'NEUTRAL'
        };

        for (const flow of flows) {
            summary.totalVolume += flow.volume;
            summary.totalPremium += flow.premium;

            if (flow.type === 'CALL') {
                summary.callVolume += flow.volume;
                summary.callPremium += flow.premium;
            } else {
                summary.putVolume += flow.volume;
                summary.putPremium += flow.premium;
            }
        }

        summary.putCallRatio = summary.putVolume / summary.callVolume;
        summary.premiumRatio = summary.callPremium / summary.putPremium;
        summary.largestTrades = this.findLargestTrades(flows, 10);
        summary.mostActive = this.findMostActiveStrikes(flows);
        summary.sentiment = this.calculateSentiment(summary);

        return summary;
    }

    async detectUnusualActivity(symbol, minPremium) {
        const unusual = [];
        const flows = await this.fetchRecentFlow(symbol);
        const historicalAvg = await this.getHistoricalAverages(symbol);

        for (const flow of flows) {
            if (flow.premium < minPremium) continue;

            const signals = [];

            // Volume spike detection
            if (flow.volume > historicalAvg.volume * 5) {
                signals.push({
                    type: 'VOLUME_SPIKE',
                    magnitude: flow.volume / historicalAvg.volume,
                    significance: 'HIGH'
                });
            }

            // Premium size detection
            if (flow.premium > this.flowThresholds.institutional) {
                signals.push({
                    type: 'INSTITUTIONAL_SIZE',
                    premium: flow.premium,
                    significance: 'VERY_HIGH'
                });
            }

            // Sweep detection
            if (flow.exchanges.length > 3 && flow.timeSpan < 1000) {
                signals.push({
                    type: 'SWEEP',
                    exchanges: flow.exchanges.length,
                    significance: 'HIGH'
                });
            }

            // Opening position detection
            if (flow.openInterestChange > flow.volume * 0.8) {
                signals.push({
                    type: 'OPENING_POSITION',
                    size: flow.volume,
                    significance: 'MEDIUM'
                });
            }

            if (signals.length > 0) {
                unusual.push({
                    ...flow,
                    signals,
                    unusualScore: this.calculateUnusualScore(signals)
                });
            }
        }

        return unusual.sort((a, b) => b.unusualScore - a.unusualScore);
    }

    async identifySmartMoney(symbol) {
        const smartMoneyFlows = [];
        const flows = await this.fetchInstitutionalFlow(symbol);

        for (const flow of flows) {
            const smartMoneySignals = [];

            // Near-the-money large trades
            if (Math.abs(flow.strike - flow.spot) / flow.spot < 0.05 &&
                flow.premium > 500000) {
                smartMoneySignals.push('NEAR_MONEY_LARGE');
            }

            // Out-of-money sweep
            if (flow.moneyness < -0.1 && flow.isSweep) {
                smartMoneySignals.push('OTM_SWEEP');
            }

            // Complex spread detection
            if (flow.legs && flow.legs.length > 1) {
                smartMoneySignals.push('COMPLEX_SPREAD');
            }

            // Delta-neutral strategies
            if (Math.abs(flow.netDelta) < 0.1 && flow.premium > 100000) {
                smartMoneySignals.push('DELTA_NEUTRAL');
            }

            if (smartMoneySignals.length > 0) {
                smartMoneyFlows.push({
                    ...flow,
                    smartMoneyType: smartMoneySignals,
                    confidence: this.calculateSmartMoneyConfidence(smartMoneySignals)
                });
            }
        }

        return smartMoneyFlows;
    }

    async calculateGammaExposure(symbol) {
        const strikes = await this.fetchOptionChain(symbol);
        const spot = await this.getSpotPrice(symbol);

        let totalGamma = 0;
        let callGamma = 0;
        let putGamma = 0;
        const gammaProfile = [];

        for (const strike of strikes) {
            const strikeGamma = this.calculateStrikeGamma(strike, spot);
            totalGamma += strikeGamma.net;
            callGamma += strikeGamma.call;
            putGamma += strikeGamma.put;

            gammaProfile.push({
                strike: strike.strike,
                gamma: strikeGamma.net,
                type: strikeGamma.net > 0 ? 'LONG' : 'SHORT',
                impact: Math.abs(strikeGamma.net * 100 * spot * spot * 0.01)
            });
        }

        return {
            totalGamma,
            callGamma,
            putGamma,
            gammaFlip: this.findGammaFlipPoint(gammaProfile, spot),
            maxPain: this.calculateMaxPain(strikes),
            gammaProfile: gammaProfile.sort((a, b) => a.strike - b.strike),
            dealerHedgingZones: this.identifyHedgingZones(gammaProfile, spot)
        };
    }

    calculateStrikeGamma(strike, spot) {
        const callGamma = strike.callVolume * this.blackScholesGamma(
            spot,
            strike.strike,
            strike.timeToExpiry,
            strike.impliedVol,
            'CALL'
        );

        const putGamma = strike.putVolume * this.blackScholesGamma(
            spot,
            strike.strike,
            strike.timeToExpiry,
            strike.impliedVol,
            'PUT'
        );

        // Market maker short gamma (they sold options)
        return {
            call: -callGamma,
            put: -putGamma,
            net: -(callGamma + putGamma)
        };
    }

    blackScholesGamma(S, K, T, sigma, type) {
        const d1 = (Math.log(S / K) + (0.05 + sigma * sigma / 2) * T) /
                   (sigma * Math.sqrt(T));
        const phi = Math.exp(-d1 * d1 / 2) / Math.sqrt(2 * Math.PI);

        return phi / (S * sigma * Math.sqrt(T));
    }

    async analyzeDealerPositioning(symbol) {
        const positioning = {
            netDelta: 0,
            netGamma: 0,
            netVanna: 0,
            netCharm: 0,
            hedgingPressure: 'NEUTRAL',
            criticalLevels: []
        };

        const chain = await this.fetchOptionChain(symbol);
        const spot = await this.getSpotPrice(symbol);

        for (const strike of chain) {
            const greeks = this.calculateGreeks(strike, spot);
            positioning.netDelta += greeks.delta * strike.netOpenInterest;
            positioning.netGamma += greeks.gamma * strike.netOpenInterest;
            positioning.netVanna += greeks.vanna * strike.netOpenInterest;
            positioning.netCharm += greeks.charm * strike.netOpenInterest;
        }

        // Determine hedging pressure
        if (positioning.netGamma < -1000000) {
            positioning.hedgingPressure = 'SHORT_GAMMA_SQUEEZE_RISK';
        } else if (positioning.netGamma > 1000000) {
            positioning.hedgingPressure = 'LONG_GAMMA_DAMPENING';
        }

        // Find critical levels
        positioning.criticalLevels = this.findCriticalLevels(chain, spot);

        return positioning;
    }

    async generateFlowSignals(symbol) {
        const signals = [];
        const analysis = {
            flow: await this.getFlowSummary(symbol, '1d'),
            unusual: await this.detectUnusualActivity(symbol, 100000),
            gamma: await this.calculateGammaExposure(symbol)
        };

        // Bullish signals
        if (analysis.flow.premiumRatio > 2 && analysis.flow.callVolume > analysis.flow.putVolume * 1.5) {
            signals.push({
                type: 'BULLISH_FLOW',
                strength: 'STRONG',
                confidence: 85,
                reason: 'Heavy call buying with premium skew'
            });
        }

        // Bearish signals
        if (analysis.flow.putCallRatio > 1.5 && analysis.unusual.length > 5) {
            signals.push({
                type: 'BEARISH_FLOW',
                strength: 'MEDIUM',
                confidence: 70,
                reason: 'Elevated put buying with unusual activity'
            });
        }

        // Squeeze signals
        if (analysis.gamma.totalGamma < -2000000) {
            signals.push({
                type: 'GAMMA_SQUEEZE_SETUP',
                strength: 'HIGH',
                confidence: 80,
                direction: analysis.gamma.gammaFlip > symbol.spot ? 'UP' : 'DOWN',
                target: analysis.gamma.gammaFlip
            });
        }

        // Institutional accumulation
        const institutionalFlows = analysis.unusual.filter(f => f.premium > 1000000);
        if (institutionalFlows.length > 3) {
            signals.push({
                type: 'INSTITUTIONAL_ACCUMULATION',
                strength: 'HIGH',
                confidence: 75,
                totalPremium: institutionalFlows.reduce((sum, f) => sum + f.premium, 0)
            });
        }

        return signals;
    }
}
```

### 2. Flow Display Interface

```javascript
class FlowDisplay {
    displayAnalysis(analysis) {
        return `
╔════════════════════════════════════════════════════════════════╗
║                   OPTIONS FLOW ANALYSIS                        ║
╠════════════════════════════════════════════════════════════════╣
║ Symbol:        ${analysis.symbol.padEnd(48)} ║
║ Timeframe:     ${analysis.timeframe.padEnd(48)} ║
║ Sentiment:     ${this.formatSentiment(analysis.flowSummary.sentiment).padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                     FLOW SUMMARY                               ║
╠════════════════════════════════════════════════════════════════╣
║ Call Volume:   ${this.formatNumber(analysis.flowSummary.callVolume).padEnd(48)} ║
║ Put Volume:    ${this.formatNumber(analysis.flowSummary.putVolume).padEnd(48)} ║
║ P/C Ratio:     ${analysis.flowSummary.putCallRatio.toFixed(2).padEnd(48)} ║
║ Call Premium:  ${this.formatMoney(analysis.flowSummary.callPremium).padEnd(48)} ║
║ Put Premium:   ${this.formatMoney(analysis.flowSummary.putPremium).padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                  UNUSUAL ACTIVITY                              ║
╠════════════════════════════════════════════════════════════════╣
${this.formatUnusualActivity(analysis.unusualActivity)}
╠════════════════════════════════════════════════════════════════╣
║                    SMART MONEY                                 ║
╠════════════════════════════════════════════════════════════════╣
${this.formatSmartMoney(analysis.smartMoney)}
╠════════════════════════════════════════════════════════════════╣
║                  GAMMA EXPOSURE                                ║
╠════════════════════════════════════════════════════════════════╣
║ Net Gamma:     ${this.formatGamma(analysis.gammaExposure.totalGamma).padEnd(48)} ║
║ Gamma Flip:    ${this.formatPrice(analysis.gammaExposure.gammaFlip).padEnd(48)} ║
║ Max Pain:      ${this.formatPrice(analysis.gammaExposure.maxPain).padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                     SIGNALS                                    ║
╠════════════════════════════════════════════════════════════════╣
${this.formatSignals(analysis.flowSignals)}
╚════════════════════════════════════════════════════════════════╝
`;
    }

    formatUnusualActivity(unusual) {
        if (!unusual || unusual.length === 0) {
            return '║ No unusual activity detected                                   ║';
        }

        return unusual.slice(0, 3).map(activity => {
            const signals = activity.signals.map(s => s.type).join(', ');
            return `║ ${activity.symbol} ${activity.strike}${activity.type[0]} ` +
                   `$${this.formatMoney(activity.premium)} ${signals.padEnd(20)} ║`;
        }).join('\n');
    }

    formatSmartMoney(smartMoney) {
        if (!smartMoney || smartMoney.length === 0) {
            return '║ No smart money flows detected                                  ║';
        }

        return smartMoney.slice(0, 3).map(flow => {
            return `║ ${flow.smartMoneyType[0].padEnd(20)} ` +
                   `$${this.formatMoney(flow.premium)} ` +
                   `Confidence: ${flow.confidence}% ║`;
        }).join('\n');
    }

    formatSignals(signals) {
        if (!signals || signals.length === 0) {
            return '║ No strong signals at this time                                 ║';
        }

        return signals.slice(0, 3).map(signal => {
            return `║ ${signal.type.padEnd(25)} ` +
                   `${signal.strength} [${signal.confidence}%] ║`;
        }).join('\n');
    }
}
```

### 3. Real-Time Flow Monitoring

```javascript
class FlowMonitor {
    constructor() {
        this.analyzer = new OptionsFlowAnalyzer();
        this.alerts = [];
        this.watchlist = new Set();
    }

    async startMonitoring(params) {
        console.log('Starting options flow monitoring...');

        const monitoringInterval = setInterval(async () => {
            try {
                const flows = await this.analyzer.fetchRealtimeFlow();

                for (const flow of flows) {
                    // Check for alerts
                    if (this.shouldAlert(flow)) {
                        await this.triggerAlert(flow);
                    }

                    // Update watchlist
                    if (this.watchlist.has(flow.symbol)) {
                        await this.updateWatchlist(flow);
                    }

                    // Log significant flows
                    if (flow.premium > 500000) {
                        this.logSignificantFlow(flow);
                    }
                }
            } catch (error) {
                console.error('Flow monitoring error:', error);
            }
        }, 5000); // Check every 5 seconds

        return monitoringInterval;
    }

    shouldAlert(flow) {
        // Institutional size
        if (flow.premium > 1000000) return true;

        // Unusual volume
        if (flow.volumeRatio > 10) return true;

        // Sweep orders
        if (flow.isSweep && flow.premium > 250000) return true;

        // Near expiry large trades
        if (flow.daysToExpiry < 3 && flow.premium > 100000) return true;

        return false;
    }

    async triggerAlert(flow) {
        const alert = {
            timestamp: Date.now(),
            symbol: flow.symbol,
            type: flow.type,
            strike: flow.strike,
            expiry: flow.expiry,
            premium: flow.premium,
            volume: flow.volume,
            signals: this.identifyAlertSignals(flow),
            importance: this.calculateImportance(flow)
        };

        this.alerts.push(alert);

        // Console notification
        console.log(`\n FLOW ALERT: ${alert.symbol} ${alert.strike}${alert.type[0]} ` +
                   `$${this.formatMoney(alert.premium)} - ${alert.signals.join(', ')}`);

        // Could send to webhook/email here
        return alert;
    }

    identifyAlertSignals(flow) {
        const signals = [];

        if (flow.premium > 1000000) signals.push('INSTITUTIONAL');
        if (flow.isSweep) signals.push('SWEEP');
        if (flow.volumeRatio > 10) signals.push('UNUSUAL_VOLUME');
        if (flow.atBid) signals.push('SOLD');
        if (flow.atAsk) signals.push('BOUGHT');
        if (flow.daysToExpiry < 7) signals.push('NEAR_EXPIRY');

        return signals;
    }
}
```

## Error Handling

```javascript
try {
    const analyzer = new OptionsFlowAnalyzer();
    const analysis = await analyzer.analyzeFlow({
        symbol: 'SPY',
        timeframe: '1d',
        flowType: 'both',
        minPremium: 100000,
        sentiment: 'all'
    });

    const display = new FlowDisplay();
    console.log(display.displayAnalysis(analysis));

    // Start real-time monitoring
    const monitor = new FlowMonitor();
    monitor.watchlist.add('SPY');
    monitor.watchlist.add('QQQ');
    await monitor.startMonitoring();

} catch (error) {
    console.error('Flow analysis failed:', error);
}
```

This command provides comprehensive options flow analysis with institutional tracking, unusual activity detection, and smart money identification.