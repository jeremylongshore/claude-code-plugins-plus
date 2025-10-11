---
description: Track real-time prices across crypto, stocks, forex, and commodities with multi-source feeds
shortcut: tp
---

# Track Market Price

Real-time price tracking system with institutional-grade data feeds from multiple sources for accuracy and reliability.

## Usage

When the user wants to track market prices, implement a comprehensive price monitoring system with these capabilities:

### Required Information
- **Symbol**: Asset ticker (BTC, AAPL, EUR/USD, etc.)
- **Asset Type**: crypto, stock, forex, commodity
- **Interval**: 1s, 5s, 30s, 1m, 5m (real-time streaming)
- **Exchanges**: Specific exchanges or "ALL" for aggregate
- **Alert Conditions**: Price thresholds, percentage changes
- **Duration**: How long to track (continuous or time-limited)

## Implementation

### 1. Multi-Source Price Aggregator

```javascript
class MarketPriceTracker {
    constructor() {
        this.dataSources = {
            crypto: {
                binance: 'wss://stream.binance.com:9443/ws',
                coinbase: 'wss://ws-feed.exchange.coinbase.com',
                kraken: 'wss://ws.kraken.com',
                ftx: 'wss://ftx.com/ws/',
                coingecko: 'https://api.coingecko.com/api/v3',
                messari: 'https://data.messari.io/api/v1'
            },
            stocks: {
                alphaVantage: process.env.ALPHA_VANTAGE_API,
                iex: 'https://api.iextrading.com/1.0',
                polygon: 'wss://socket.polygon.io',
                finnhub: 'wss://ws.finnhub.io',
                yahoo: 'https://query1.finance.yahoo.com/v8'
            },
            forex: {
                oanda: 'wss://stream-fxtrade.oanda.com',
                forexConnect: 'https://api-fxtrade.oanda.com/v3',
                currencyLayer: process.env.CURRENCY_LAYER_API,
                exchangeRates: 'https://api.exchangerate.host'
            },
            commodities: {
                quandl: process.env.QUANDL_API,
                metalsPrices: 'https://api.metals.live/v1',
                oilPrices: 'https://api.oilpriceapi.com/v1'
            }
        };

        this.priceCache = new Map();
        this.connections = new Map();
        this.aggregationStrategy = 'VWAP'; // Volume Weighted Average Price
    }

    async trackPrice(params) {
        const {
            symbol,
            assetType,
            interval = '1s',
            exchanges = 'ALL',
            alertConditions = [],
            duration = 'continuous'
        } = params;

        // Validate symbol format
        this.validateSymbol(symbol, assetType);

        // Initialize tracking
        const trackingSession = {
            id: crypto.randomUUID(),
            symbol,
            assetType,
            interval,
            startTime: Date.now(),
            duration,
            exchanges: this.selectExchanges(exchanges, assetType),
            alerts: this.parseAlertConditions(alertConditions),
            priceHistory: [],
            statistics: {
                high: 0,
                low: Infinity,
                open: 0,
                volume: 0,
                vwap: 0,
                changes: {
                    '1m': 0,
                    '5m': 0,
                    '15m': 0,
                    '1h': 0,
                    '24h': 0
                }
            }
        };

        // Start real-time tracking
        await this.initializeConnections(trackingSession);

        // Begin price aggregation
        this.startPriceAggregation(trackingSession);

        // Monitor alerts
        this.startAlertMonitoring(trackingSession);

        return trackingSession;
    }

    async initializeConnections(session) {
        const connections = [];

        for (const exchange of session.exchanges) {
            try {
                const connection = await this.connectToExchange(
                    exchange,
                    session.symbol,
                    session.assetType
                );

                connections.push({
                    exchange,
                    connection,
                    status: 'connected',
                    latency: 0,
                    lastUpdate: null
                });

                // Subscribe to price updates
                this.subscribeToPrice(connection, session);
            } catch (error) {
                console.error(`Failed to connect to ${exchange}:`, error);
                connections.push({
                    exchange,
                    status: 'failed',
                    error: error.message
                });
            }
        }

        session.connections = connections;
        return connections;
    }

    async connectToExchange(exchange, symbol, assetType) {
        const sourceConfig = this.dataSources[assetType][exchange];

        if (sourceConfig.startsWith('wss://')) {
            // WebSocket connection
            return this.createWebSocketConnection(sourceConfig, symbol, exchange);
        } else {
            // REST API polling
            return this.createPollingConnection(sourceConfig, symbol, exchange);
        }
    }

    createWebSocketConnection(url, symbol, exchange) {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket(url);

            ws.on('open', () => {
                // Subscribe to symbol
                const subscribeMsg = this.getSubscribeMessage(exchange, symbol);
                ws.send(JSON.stringify(subscribeMsg));
                resolve(ws);
            });

            ws.on('error', reject);

            ws.on('message', (data) => {
                this.handlePriceUpdate(exchange, data);
            });
        });
    }

    getSubscribeMessage(exchange, symbol) {
        const messages = {
            binance: {
                method: 'SUBSCRIBE',
                params: [`${symbol.toLowerCase()}@trade`, `${symbol.toLowerCase()}@depth`],
                id: 1
            },
            coinbase: {
                type: 'subscribe',
                product_ids: [symbol],
                channels: ['ticker', 'level2']
            },
            kraken: {
                event: 'subscribe',
                pair: [symbol],
                subscription: { name: 'ticker' }
            }
        };

        return messages[exchange] || {};
    }

    handlePriceUpdate(exchange, data) {
        const parsed = JSON.parse(data);
        const price = this.extractPrice(exchange, parsed);

        if (price) {
            const update = {
                exchange,
                price: price.price,
                volume: price.volume,
                timestamp: Date.now(),
                bid: price.bid,
                ask: price.ask,
                spread: price.ask - price.bid
            };

            // Update cache
            if (!this.priceCache.has(exchange)) {
                this.priceCache.set(exchange, []);
            }
            this.priceCache.get(exchange).push(update);

            // Trigger aggregation
            this.aggregatePrices();
        }
    }

    extractPrice(exchange, data) {
        const extractors = {
            binance: (d) => ({
                price: parseFloat(d.p),
                volume: parseFloat(d.q),
                bid: parseFloat(d.b),
                ask: parseFloat(d.a)
            }),
            coinbase: (d) => ({
                price: parseFloat(d.price),
                volume: parseFloat(d.volume_24h),
                bid: parseFloat(d.best_bid),
                ask: parseFloat(d.best_ask)
            }),
            kraken: (d) => ({
                price: parseFloat(d[1].c[0]),
                volume: parseFloat(d[1].v[1]),
                bid: parseFloat(d[1].b[0]),
                ask: parseFloat(d[1].a[0])
            })
        };

        return extractors[exchange]?.(data);
    }

    aggregatePrices() {
        const allPrices = [];

        for (const [exchange, prices] of this.priceCache.entries()) {
            if (prices.length > 0) {
                const recent = prices.filter(p =>
                    Date.now() - p.timestamp < 5000 // Last 5 seconds
                );
                allPrices.push(...recent);
            }
        }

        if (allPrices.length === 0) return null;

        // Calculate aggregated price based on strategy
        let aggregatedPrice;

        switch (this.aggregationStrategy) {
            case 'VWAP':
                aggregatedPrice = this.calculateVWAP(allPrices);
                break;
            case 'MEDIAN':
                aggregatedPrice = this.calculateMedian(allPrices);
                break;
            case 'WEIGHTED':
                aggregatedPrice = this.calculateWeightedAverage(allPrices);
                break;
            default:
                aggregatedPrice = this.calculateSimpleAverage(allPrices);
        }

        return {
            price: aggregatedPrice,
            sources: allPrices.length,
            timestamp: Date.now(),
            spread: this.calculateSpread(allPrices),
            confidence: this.calculateConfidence(allPrices)
        };
    }

    calculateVWAP(prices) {
        let totalValue = 0;
        let totalVolume = 0;

        for (const p of prices) {
            totalValue += p.price * p.volume;
            totalVolume += p.volume;
        }

        return totalVolume > 0 ? totalValue / totalVolume : 0;
    }

    calculateConfidence(prices) {
        if (prices.length < 2) return 0;

        const values = prices.map(p => p.price);
        const mean = values.reduce((a, b) => a + b) / values.length;
        const variance = values.reduce((sum, val) =>
            sum + Math.pow(val - mean, 2), 0) / values.length;
        const stdDev = Math.sqrt(variance);
        const coefficientOfVariation = (stdDev / mean) * 100;

        // Lower CV means higher confidence
        if (coefficientOfVariation < 0.5) return 99;
        if (coefficientOfVariation < 1) return 95;
        if (coefficientOfVariation < 2) return 90;
        if (coefficientOfVariation < 5) return 75;
        return 50;
    }

    startAlertMonitoring(session) {
        const checkInterval = this.parseInterval(session.interval);

        session.alertMonitor = setInterval(() => {
            const currentPrice = this.getCurrentPrice(session.symbol);
            if (!currentPrice) return;

            for (const alert of session.alerts) {
                if (this.checkAlertCondition(alert, currentPrice, session)) {
                    this.triggerAlert(alert, currentPrice, session);
                }
            }
        }, checkInterval);
    }

    checkAlertCondition(alert, price, session) {
        switch (alert.type) {
            case 'PRICE_ABOVE':
                return price.price > alert.threshold;

            case 'PRICE_BELOW':
                return price.price < alert.threshold;

            case 'PERCENT_CHANGE':
                const changePercent = this.calculatePercentChange(
                    session.statistics.open,
                    price.price
                );
                return Math.abs(changePercent) > alert.threshold;

            case 'VOLUME_SPIKE':
                return price.volume > session.statistics.avgVolume * alert.multiplier;

            case 'SPREAD_WIDE':
                return price.spread > alert.threshold;

            case 'VOLATILITY':
                return this.calculateVolatility(session) > alert.threshold;

            default:
                return false;
        }
    }

    triggerAlert(alert, price, session) {
        const alertData = {
            id: crypto.randomUUID(),
            type: alert.type,
            symbol: session.symbol,
            price: price.price,
            threshold: alert.threshold,
            timestamp: Date.now(),
            message: this.formatAlertMessage(alert, price, session),
            severity: alert.severity || 'INFO',
            action: alert.action || 'NOTIFY'
        };

        // Send alert through notification channels
        this.sendAlert(alertData);

        // Log alert
        if (!session.triggeredAlerts) {
            session.triggeredAlerts = [];
        }
        session.triggeredAlerts.push(alertData);

        // Execute automated actions if configured
        if (alert.action === 'AUTO_TRADE') {
            this.executeAutomatedAction(alert, price, session);
        }
    }
}
```

### 2. Price Display Interface

```javascript
class PriceDisplay {
    constructor() {
        this.displayMode = 'detailed'; // 'simple', 'detailed', 'professional'
        this.updateFrequency = 1000; // milliseconds
    }

    displayPrice(session, aggregatedPrice) {
        const display = `
╔════════════════════════════════════════════════════════════════╗
║                    REAL-TIME PRICE TRACKER                     ║
╠════════════════════════════════════════════════════════════════╣
║ Symbol:        ${session.symbol.padEnd(48)} ║
║ Asset Type:    ${session.assetType.padEnd(48)} ║
║ Current Price: ${this.formatPrice(aggregatedPrice.price).padEnd(48)} ║
║ Confidence:    ${this.formatConfidence(aggregatedPrice.confidence).padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                        PRICE METRICS                           ║
╠════════════════════════════════════════════════════════════════╣
║ 24H High:      ${this.formatPrice(session.statistics.high).padEnd(48)} ║
║ 24H Low:       ${this.formatPrice(session.statistics.low).padEnd(48)} ║
║ 24H Change:    ${this.formatChange(session.statistics.changes['24h']).padEnd(48)} ║
║ Volume:        ${this.formatVolume(session.statistics.volume).padEnd(48)} ║
║ VWAP:          ${this.formatPrice(session.statistics.vwap).padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                      EXCHANGE PRICES                           ║
╠════════════════════════════════════════════════════════════════╣
${this.formatExchangePrices(session)}
╠════════════════════════════════════════════════════════════════╣
║                         ALERTS                                 ║
╠════════════════════════════════════════════════════════════════╣
${this.formatAlerts(session)}
╚════════════════════════════════════════════════════════════════╝
`;
        return display;
    }

    formatExchangePrices(session) {
        const lines = [];
        for (const conn of session.connections) {
            if (conn.status === 'connected' && conn.lastPrice) {
                lines.push(`║ ${conn.exchange.padEnd(15)} ${this.formatPrice(conn.lastPrice).padEnd(15)} ${this.formatLatency(conn.latency).padEnd(26)} ║`);
            }
        }
        return lines.join('\n');
    }

    formatAlerts(session) {
        if (!session.alerts || session.alerts.length === 0) {
            return '║ No active alerts                                               ║';
        }

        const lines = [];
        for (const alert of session.alerts) {
            const status = alert.triggered ? '' : '⏳';
            lines.push(`║ ${status} ${alert.type}: ${alert.threshold}                                     ║`);
        }
        return lines.join('\n');
    }

    formatPrice(price) {
        if (price > 1000) {
            return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        } else if (price > 1) {
            return `$${price.toFixed(4)}`;
        } else {
            return `$${price.toFixed(8)}`;
        }
    }

    formatConfidence(confidence) {
        const bars = '█'.repeat(Math.floor(confidence / 10));
        const empty = '░'.repeat(10 - Math.floor(confidence / 10));
        return `${bars}${empty} ${confidence}%`;
    }
}
```

### 3. Advanced Analytics

```javascript
class PriceAnalytics {
    constructor() {
        this.indicators = {};
        this.patterns = [];
    }

    analyzePrice(priceHistory) {
        return {
            technicalIndicators: this.calculateTechnicalIndicators(priceHistory),
            pricePatterns: this.detectPatterns(priceHistory),
            supportResistance: this.findSupportResistance(priceHistory),
            volatility: this.analyzeVolatility(priceHistory),
            momentum: this.analyzeMomentum(priceHistory),
            marketStructure: this.analyzeMarketStructure(priceHistory)
        };
    }

    calculateTechnicalIndicators(prices) {
        return {
            sma: {
                sma20: this.calculateSMA(prices, 20),
                sma50: this.calculateSMA(prices, 50),
                sma200: this.calculateSMA(prices, 200)
            },
            ema: {
                ema12: this.calculateEMA(prices, 12),
                ema26: this.calculateEMA(prices, 26)
            },
            rsi: this.calculateRSI(prices, 14),
            macd: this.calculateMACD(prices),
            bollingerBands: this.calculateBollingerBands(prices, 20, 2),
            atr: this.calculateATR(prices, 14),
            obv: this.calculateOBV(prices),
            vwap: this.calculateDailyVWAP(prices)
        };
    }

    detectPatterns(prices) {
        const patterns = [];

        // Head and Shoulders
        if (this.detectHeadAndShoulders(prices)) {
            patterns.push({
                type: 'HEAD_AND_SHOULDERS',
                direction: 'BEARISH',
                confidence: 85
            });
        }

        // Double Top/Bottom
        const doublePattern = this.detectDoubleTopBottom(prices);
        if (doublePattern) {
            patterns.push(doublePattern);
        }

        // Triangle Patterns
        const triangle = this.detectTriangle(prices);
        if (triangle) {
            patterns.push(triangle);
        }

        // Flag/Pennant
        const flagPattern = this.detectFlagPennant(prices);
        if (flagPattern) {
            patterns.push(flagPattern);
        }

        return patterns;
    }

    findSupportResistance(prices) {
        const levels = [];
        const priceValues = prices.map(p => p.price);

        // Find local maxima and minima
        for (let i = 2; i < priceValues.length - 2; i++) {
            // Resistance (local maximum)
            if (priceValues[i] > priceValues[i-1] &&
                priceValues[i] > priceValues[i-2] &&
                priceValues[i] > priceValues[i+1] &&
                priceValues[i] > priceValues[i+2]) {
                levels.push({
                    type: 'RESISTANCE',
                    price: priceValues[i],
                    strength: this.calculateLevelStrength(prices, priceValues[i]),
                    touches: this.countTouches(prices, priceValues[i])
                });
            }

            // Support (local minimum)
            if (priceValues[i] < priceValues[i-1] &&
                priceValues[i] < priceValues[i-2] &&
                priceValues[i] < priceValues[i+1] &&
                priceValues[i] < priceValues[i+2]) {
                levels.push({
                    type: 'SUPPORT',
                    price: priceValues[i],
                    strength: this.calculateLevelStrength(prices, priceValues[i]),
                    touches: this.countTouches(prices, priceValues[i])
                });
            }
        }

        // Cluster similar levels
        return this.clusterLevels(levels);
    }
}
```

### 4. Alert Configuration

```javascript
class AlertConfiguration {
    parseAlertConditions(conditions) {
        const parsed = [];

        for (const condition of conditions) {
            if (typeof condition === 'string') {
                // Parse string format: "above 50000", "below 45000", "change 5%"
                const match = condition.match(/(\w+)\s+([0-9.]+)(%)?/);
                if (match) {
                    parsed.push(this.createAlert(match[1], parseFloat(match[2]), match[3] === '%'));
                }
            } else {
                // Object format already
                parsed.push(condition);
            }
        }

        return parsed;
    }

    createAlert(type, value, isPercent) {
        const alertTypes = {
            'above': 'PRICE_ABOVE',
            'below': 'PRICE_BELOW',
            'change': 'PERCENT_CHANGE',
            'volume': 'VOLUME_SPIKE',
            'spread': 'SPREAD_WIDE',
            'volatility': 'VOLATILITY'
        };

        return {
            type: alertTypes[type] || 'CUSTOM',
            threshold: value,
            isPercent,
            enabled: true,
            cooldown: 300000, // 5 minutes between repeat alerts
            lastTriggered: 0
        };
    }
}
```

### 5. WebSocket Manager

```javascript
class WebSocketManager {
    constructor() {
        this.connections = new Map();
        this.reconnectAttempts = new Map();
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    async manage(url, handlers) {
        const ws = new WebSocket(url);
        const connectionId = crypto.randomUUID();

        ws.on('open', () => {
            console.log(`WebSocket connected: ${url}`);
            this.connections.set(connectionId, ws);
            this.reconnectAttempts.set(connectionId, 0);
            handlers.onOpen?.(ws);
        });

        ws.on('message', (data) => {
            handlers.onMessage?.(data);
        });

        ws.on('error', (error) => {
            console.error(`WebSocket error: ${url}`, error);
            handlers.onError?.(error);
        });

        ws.on('close', () => {
            console.log(`WebSocket closed: ${url}`);
            this.connections.delete(connectionId);
            this.attemptReconnect(url, handlers, connectionId);
        });

        return connectionId;
    }

    attemptReconnect(url, handlers, connectionId) {
        const attempts = this.reconnectAttempts.get(connectionId) || 0;

        if (attempts < this.maxReconnectAttempts) {
            const delay = this.reconnectDelay * Math.pow(2, attempts);
            console.log(`Reconnecting in ${delay}ms... (attempt ${attempts + 1})`);

            setTimeout(() => {
                this.reconnectAttempts.set(connectionId, attempts + 1);
                this.manage(url, handlers);
            }, delay);
        } else {
            console.error(`Max reconnection attempts reached for ${url}`);
            handlers.onMaxReconnectFailed?.();
        }
    }
}
```

## Error Handling

```javascript
try {
    const tracker = new MarketPriceTracker();
    const session = await tracker.trackPrice({
        symbol: 'BTC/USDT',
        assetType: 'crypto',
        interval: '1s',
        exchanges: ['binance', 'coinbase', 'kraken'],
        alertConditions: [
            'above 50000',
            'below 45000',
            'change 5%',
            'volume 2x'
        ],
        duration: '24h'
    });

    // Display real-time updates
    const display = new PriceDisplay();
    setInterval(async () => {
        const price = tracker.getCurrentPrice(session.symbol);
        console.clear();
        console.log(display.displayPrice(session, price));
    }, 1000);

} catch (error) {
    console.error('Price tracking failed:', error);
    process.exit(1);
}
```

This command provides institutional-grade real-time price tracking with multi-exchange aggregation, advanced alerts, and comprehensive analytics.