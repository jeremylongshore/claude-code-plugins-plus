---
name: scan-movers
description: >
  Scan for top market movers across crypto, stocks, and forex with
  real-time...
shortcut: sm
---
# Scan Market Movers

Comprehensive market scanner identifying top gainers, losers, volume leaders, and unusual activity across multiple asset classes.

## Usage

When the user wants to scan for market movers, implement a real-time scanning system with these capabilities:

### Scan Parameters
- **Markets**: crypto, stocks, forex, all
- **Timeframe**: 1h, 4h, 24h, 7d, 30d
- **Categories**: gainers, losers, volume, volatility, unusual
- **Limit**: Top N results (default: 20)
- **Filters**: Market cap, volume thresholds, price ranges
- **Sort**: By percentage, volume, market cap, volatility

## Implementation

### 1. Market Scanner Engine

```javascript
class MarketMoversScanner {
    constructor() {
        this.dataSources = {
            crypto: {
                coingecko: 'https://api.coingecko.com/api/v3',
                coinmarketcap: process.env.CMC_API_KEY,
                messari: 'https://data.messari.io/api/v1',
                binance: 'https://api.binance.com/api/v3'
            },
            stocks: {
                yahoo: 'https://query1.finance.yahoo.com/v1',
                alphavantage: process.env.ALPHA_VANTAGE_API,
                iex: 'https://api.iextrading.com/1.0',
                polygon: process.env.POLYGON_API_KEY
            },
            forex: {
                oanda: process.env.OANDA_API_KEY,
                fixer: process.env.FIXER_API_KEY,
                currencylayer: process.env.CURRENCY_LAYER_API
            }
        };

        this.scanCache = new Map();
        this.updateInterval = 60000; // 1 minute
        this.lastUpdate = {};
    }

    async scanMarkets(params) {
        const {
            markets = 'all',
            timeframe = '24h',
            categories = ['gainers', 'losers', 'volume'],
            limit = 20,
            filters = {},
            sortBy = 'percentage'
        } = params;

        // Initialize scan results
        const results = {
            timestamp: Date.now(),
            timeframe,
            markets: markets === 'all' ? ['crypto', 'stocks', 'forex'] : [markets],
            data: {
                gainers: [],
                losers: [],
                volumeLeaders: [],
                volatilityLeaders: [],
                unusual: [],
                breakouts: [],
                newHighs: [],
                newLows: []
            },
            statistics: {},
            alerts: []
        };

        // Scan each market
        for (const market of results.markets) {
            const marketData = await this.scanMarket(market, timeframe, filters);
            results.data = this.mergeMarketData(results.data, marketData);
        }

        // Process categories
        for (const category of categories) {
            results.data[category] = await this.processCategory(
                category,
                results.data,
                limit,
                sortBy
            );
        }

        // Calculate statistics
        results.statistics = this.calculateStatistics(results.data);

        // Identify alerts
        results.alerts = this.identifyAlerts(results.data);

        return results;
    }

    async scanMarket(market, timeframe, filters) {
        const cacheKey = `${market}_${timeframe}`;

        // Check cache
        if (this.scanCache.has(cacheKey)) {
            const cached = this.scanCache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.updateInterval) {
                return cached.data;
            }
        }

        // Fetch fresh data
        let marketData;
        switch (market) {
            case 'crypto':
                marketData = await this.scanCrypto(timeframe, filters);
                break;
            case 'stocks':
                marketData = await this.scanStocks(timeframe, filters);
                break;
            case 'forex':
                marketData = await this.scanForex(timeframe, filters);
                break;
            default:
                throw new Error(`Unsupported market: ${market}`);
        }

        // Update cache
        this.scanCache.set(cacheKey, {
            timestamp: Date.now(),
            data: marketData
        });

        return marketData;
    }

    async scanCrypto(timeframe, filters) {
        const assets = [];

        try {
            // Fetch from CoinGecko
            const cgData = await this.fetchCoinGeckoData(timeframe);

            for (const coin of cgData) {
                if (this.applyFilters(coin, filters)) {
                    assets.push({
                        symbol: coin.symbol.toUpperCase(),
                        name: coin.name,
                        market: 'crypto',
                        price: coin.current_price,
                        change: this.getChangeForTimeframe(coin, timeframe),
                        volume: coin.total_volume,
                        marketCap: coin.market_cap,
                        high24h: coin.high_24h,
                        low24h: coin.low_24h,
                        ath: coin.ath,
                        athDate: coin.ath_date,
                        circulatingSupply: coin.circulating_supply,
                        rank: coin.market_cap_rank,
                        sparkline: coin.sparkline_in_7d?.price || [],
                        metrics: {
                            volatility: this.calculateVolatility(coin),
                            momentum: this.calculateMomentum(coin),
                            relativeVolume: coin.total_volume / coin.market_cap,
                            priceScore: this.calculatePriceScore(coin)
                        }
                    });
                }
            }

            // Fetch from Binance for real-time data
            const binanceData = await this.fetchBinanceData();
            this.enrichWithBinanceData(assets, binanceData);

        } catch (error) {
            console.error('Error scanning crypto:', error);
        }

        return assets;
    }

    async fetchCoinGeckoData(timeframe) {
        const periods = {
            '1h': '1h',
            '24h': '24h',
            '7d': '7d',
            '30d': '30d'
        };

        const response = await fetch(
            `${this.dataSources.crypto.coingecko}/coins/markets?` +
            `vs_currency=usd&order=market_cap_desc&per_page=500&` +
            `price_change_percentage=${periods[timeframe] || '24h'},7d,30d&` +
            `sparkline=true`
        );

        return response.json();
    }

    async fetchBinanceData() {
        const response = await fetch(
            `${this.dataSources.crypto.binance}/ticker/24hr`
        );
        const data = await response.json();

        const processed = {};
        for (const ticker of data) {
            if (ticker.symbol.endsWith('USDT')) {
                const symbol = ticker.symbol.replace('USDT', '');
                processed[symbol] = {
                    price: parseFloat(ticker.lastPrice),
                    change24h: parseFloat(ticker.priceChangePercent),
                    volume: parseFloat(ticker.volume),
                    quoteVolume: parseFloat(ticker.quoteVolume),
                    count: parseInt(ticker.count),
                    weightedAvgPrice: parseFloat(ticker.weightedAvgPrice)
                };
            }
        }

        return processed;
    }

    getChangeForTimeframe(coin, timeframe) {
        const changeMap = {
            '1h': coin.price_change_percentage_1h_in_currency,
            '24h': coin.price_change_percentage_24h,
            '7d': coin.price_change_percentage_7d_in_currency,
            '30d': coin.price_change_percentage_30d_in_currency
        };

        return changeMap[timeframe] || coin.price_change_percentage_24h || 0;
    }

    calculateVolatility(asset) {
        if (!asset.sparkline_in_7d?.price || asset.sparkline_in_7d.price.length < 2) {
            return 0;
        }

        const prices = asset.sparkline_in_7d.price;
        const returns = [];

        for (let i = 1; i < prices.length; i++) {
            returns.push((prices[i] - prices[i-1]) / prices[i-1]);
        }

        const mean = returns.reduce((a, b) => a + b) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;

        return Math.sqrt(variance) * 100; // Percentage volatility
    }

    calculateMomentum(asset) {
        const weights = {
            '24h': 0.4,
            '7d': 0.3,
            '30d': 0.3
        };

        const momentum =
            (asset.price_change_percentage_24h || 0) * weights['24h'] +
            (asset.price_change_percentage_7d_in_currency || 0) * weights['7d'] +
            (asset.price_change_percentage_30d_in_currency || 0) * weights['30d'];

        return momentum;
    }

    calculatePriceScore(asset) {
        // Score based on price position relative to range
        const range = asset.high_24h - asset.low_24h;
        if (range === 0) return 50;

        const position = (asset.current_price - asset.low_24h) / range;
        return position * 100;
    }

    async scanStocks(timeframe, filters) {
        const assets = [];

        try {
            // Fetch major indices components
            const indices = ['SPY', 'QQQ', 'DIA']; // S&P 500, NASDAQ, Dow ETFs
            const stockList = await this.fetchStockList(indices);

            for (const symbol of stockList) {
                const stockData = await this.fetchStockData(symbol, timeframe);

                if (stockData && this.applyFilters(stockData, filters)) {
                    assets.push({
                        symbol: stockData.symbol,
                        name: stockData.name,
                        market: 'stocks',
                        price: stockData.price,
                        change: stockData.changePercent,
                        volume: stockData.volume,
                        marketCap: stockData.marketCap,
                        high52w: stockData.week52High,
                        low52w: stockData.week52Low,
                        pe: stockData.peRatio,
                        eps: stockData.eps,
                        dividend: stockData.dividendYield,
                        beta: stockData.beta,
                        metrics: {
                            rsi: stockData.rsi,
                            volumeRatio: stockData.volume / stockData.avgVolume,
                            priceToHigh: stockData.price / stockData.week52High,
                            earningsGrowth: stockData.earningsGrowth
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error scanning stocks:', error);
        }

        return assets;
    }

    async processCategory(category, data, limit, sortBy) {
        let categoryData = [];

        switch (category) {
            case 'gainers':
                categoryData = this.findTopGainers(data, limit);
                break;
            case 'losers':
                categoryData = this.findTopLosers(data, limit);
                break;
            case 'volume':
                categoryData = this.findVolumeLeaders(data, limit);
                break;
            case 'volatility':
                categoryData = this.findVolatilityLeaders(data, limit);
                break;
            case 'unusual':
                categoryData = this.findUnusualActivity(data, limit);
                break;
            case 'breakouts':
                categoryData = this.findBreakouts(data, limit);
                break;
            case 'momentum':
                categoryData = this.findMomentumPlays(data, limit);
                break;
        }

        return this.sortResults(categoryData, sortBy);
    }

    findTopGainers(data, limit) {
        const allAssets = [...data.gainers, ...data.losers, ...data.volumeLeaders];
        const uniqueAssets = this.removeDuplicates(allAssets);

        return uniqueAssets
            .filter(asset => asset.change > 0)
            .sort((a, b) => b.change - a.change)
            .slice(0, limit)
            .map(asset => ({
                ...asset,
                category: 'GAINER',
                signal: this.generateSignal(asset, 'GAINER')
            }));
    }

    findTopLosers(data, limit) {
        const allAssets = [...data.gainers, ...data.losers, ...data.volumeLeaders];
        const uniqueAssets = this.removeDuplicates(allAssets);

        return uniqueAssets
            .filter(asset => asset.change < 0)
            .sort((a, b) => a.change - b.change)
            .slice(0, limit)
            .map(asset => ({
                ...asset,
                category: 'LOSER',
                signal: this.generateSignal(asset, 'LOSER')
            }));
    }

    findVolumeLeaders(data, limit) {
        const allAssets = this.getAllAssets(data);

        return allAssets
            .filter(asset => asset.metrics?.volumeRatio > 2)
            .sort((a, b) => b.metrics.volumeRatio - a.metrics.volumeRatio)
            .slice(0, limit)
            .map(asset => ({
                ...asset,
                category: 'VOLUME_LEADER',
                volumeMultiple: asset.metrics.volumeRatio.toFixed(2) + 'x',
                signal: this.generateSignal(asset, 'VOLUME')
            }));
    }

    findUnusualActivity(data, limit) {
        const allAssets = this.getAllAssets(data);
        const unusual = [];

        for (const asset of allAssets) {
            const signals = [];

            // Check for unusual volume
            if (asset.metrics?.volumeRatio > 5) {
                signals.push('EXTREME_VOLUME');
            }

            // Check for large price movement
            if (Math.abs(asset.change) > 20) {
                signals.push('LARGE_MOVE');
            }

            // Check for volatility spike
            if (asset.metrics?.volatility > 10) {
                signals.push('HIGH_VOLATILITY');
            }

            // Check for new highs/lows
            if (asset.price >= asset.high52w * 0.95) {
                signals.push('NEAR_52W_HIGH');
            }
            if (asset.price <= asset.low52w * 1.05) {
                signals.push('NEAR_52W_LOW');
            }

            if (signals.length > 0) {
                unusual.push({
                    ...asset,
                    category: 'UNUSUAL',
                    signals,
                    unusualScore: signals.length * 25
                });
            }
        }

        return unusual
            .sort((a, b) => b.unusualScore - a.unusualScore)
            .slice(0, limit);
    }

    findBreakouts(data, limit) {
        const allAssets = this.getAllAssets(data);
        const breakouts = [];

        for (const asset of allAssets) {
            const breakoutSignals = [];

            // Volume breakout
            if (asset.metrics?.volumeRatio > 3 && asset.change > 5) {
                breakoutSignals.push({
                    type: 'VOLUME_BREAKOUT',
                    strength: 'HIGH'
                });
            }

            // Price breakout (near 52-week high)
            if (asset.high52w && asset.price > asset.high52w * 0.98) {
                breakoutSignals.push({
                    type: 'PRICE_BREAKOUT',
                    strength: 'VERY_HIGH',
                    target: asset.high52w * 1.1
                });
            }

            // Momentum breakout
            if (asset.metrics?.momentum > 15) {
                breakoutSignals.push({
                    type: 'MOMENTUM_BREAKOUT',
                    strength: 'MEDIUM'
                });
            }

            if (breakoutSignals.length > 0) {
                breakouts.push({
                    ...asset,
                    category: 'BREAKOUT',
                    breakoutSignals,
                    breakoutScore: this.calculateBreakoutScore(breakoutSignals)
                });
            }
        }

        return breakouts
            .sort((a, b) => b.breakoutScore - a.breakoutScore)
            .slice(0, limit);
    }

    generateSignal(asset, category) {
        const signals = {
            strength: 'MEDIUM',
            action: 'WATCH',
            confidence: 50,
            reasons: []
        };

        // Analyze based on category
        if (category === 'GAINER') {
            if (asset.change > 20) {
                signals.strength = 'STRONG';
                signals.action = 'MOMENTUM_PLAY';
                signals.confidence = 75;
                signals.reasons.push('Strong upward momentum');
            }
            if (asset.metrics?.volumeRatio > 3) {
                signals.confidence += 10;
                signals.reasons.push('High volume confirmation');
            }
        } else if (category === 'LOSER') {
            if (asset.change < -20) {
                signals.strength = 'STRONG';
                signals.action = 'OVERSOLD_BOUNCE';
                signals.confidence = 60;
                signals.reasons.push('Potential oversold bounce');
            }
        } else if (category === 'VOLUME') {
            signals.strength = 'HIGH';
            signals.action = 'INVESTIGATE';
            signals.confidence = 70;
            signals.reasons.push('Unusual volume activity');
        }

        return signals;
    }

    identifyAlerts(data) {
        const alerts = [];

        // Market-wide alerts
        const gainersCount = data.gainers?.filter(a => a.change > 10).length || 0;
        const losersCount = data.losers?.filter(a => a.change < -10).length || 0;

        if (gainersCount > 50) {
            alerts.push({
                type: 'MARKET_RALLY',
                message: `Strong market rally detected: ${gainersCount} assets up >10%`,
                severity: 'INFO'
            });
        }

        if (losersCount > 50) {
            alerts.push({
                type: 'MARKET_SELLOFF',
                message: `Market selloff detected: ${losersCount} assets down >10%`,
                severity: 'WARNING'
            });
        }

        // Individual asset alerts
        for (const category of Object.values(data)) {
            if (!Array.isArray(category)) continue;

            for (const asset of category) {
                if (asset.change > 50) {
                    alerts.push({
                        type: 'EXTREME_GAIN',
                        symbol: asset.symbol,
                        message: `${asset.symbol} up ${asset.change.toFixed(2)}% - extreme movement`,
                        severity: 'HIGH'
                    });
                }

                if (asset.change < -30) {
                    alerts.push({
                        type: 'EXTREME_LOSS',
                        symbol: asset.symbol,
                        message: `${asset.symbol} down ${Math.abs(asset.change).toFixed(2)}% - potential crash`,
                        severity: 'CRITICAL'
                    });
                }

                if (asset.metrics?.volumeRatio > 10) {
                    alerts.push({
                        type: 'VOLUME_EXPLOSION',
                        symbol: asset.symbol,
                        message: `${asset.symbol} volume ${asset.metrics.volumeRatio.toFixed(1)}x average`,
                        severity: 'HIGH'
                    });
                }
            }
        }

        return alerts;
    }
}
```

### 2. Display Interface

```javascript
class MoversDisplay {
    displayResults(results) {
        const output = `
╔════════════════════════════════════════════════════════════════╗
║                    MARKET MOVERS SCANNER                       ║
╠════════════════════════════════════════════════════════════════╣
║ Timeframe:     ${results.timeframe.padEnd(48)} ║
║ Markets:       ${results.markets.join(', ').padEnd(48)} ║
║ Last Update:   ${new Date(results.timestamp).toLocaleString().padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                      TOP GAINERS                               ║
╠════════════════════════════════════════════════════════════════╣
${this.formatMovers(results.data.gainers, 'gain')}
╠════════════════════════════════════════════════════════════════╣
║                      TOP LOSERS                                ║
╠════════════════════════════════════════════════════════════════╣
${this.formatMovers(results.data.losers, 'loss')}
╠════════════════════════════════════════════════════════════════╣
║                    VOLUME LEADERS                              ║
╠════════════════════════════════════════════════════════════════╣
${this.formatVolumeLeaders(results.data.volumeLeaders)}
╠════════════════════════════════════════════════════════════════╣
║                   UNUSUAL ACTIVITY                             ║
╠════════════════════════════════════════════════════════════════╣
${this.formatUnusual(results.data.unusual)}
╠════════════════════════════════════════════════════════════════╣
║                      ALERTS                                    ║
╠════════════════════════════════════════════════════════════════╣
${this.formatAlerts(results.alerts)}
╚════════════════════════════════════════════════════════════════╝
`;
        return output;
    }

    formatMovers(movers, type) {
        if (!movers || movers.length === 0) {
            return '║ No significant movers found                                    ║';
        }

        const lines = [];
        for (const mover of movers.slice(0, 5)) {
            const changeStr = type === 'gain'
                ? `+${mover.change.toFixed(2)}%`
                : `${mover.change.toFixed(2)}%`;

            const emoji = type === 'gain' ? '' : '';

            lines.push(
                `║ ${emoji} ${mover.symbol.padEnd(8)} ${changeStr.padEnd(10)} ` +
                `$${this.formatPrice(mover.price).padEnd(12)} ${this.formatVolume(mover.volume).padEnd(12)} ║`
            );
        }

        return lines.join('\n');
    }

    formatVolumeLeaders(leaders) {
        if (!leaders || leaders.length === 0) {
            return '║ No volume leaders found                                        ║';
        }

        const lines = [];
        for (const leader of leaders.slice(0, 5)) {
            lines.push(
                `║  ${leader.symbol.padEnd(8)} ${leader.volumeMultiple.padEnd(6)} ` +
                `${this.formatChange(leader.change).padEnd(10)} Signal: ${leader.signal.action.padEnd(15)} ║`
            );
        }

        return lines.join('\n');
    }

    formatUnusual(unusual) {
        if (!unusual || unusual.length === 0) {
            return '║ No unusual activity detected                                   ║';
        }

        const lines = [];
        for (const item of unusual.slice(0, 3)) {
            const signals = item.signals.join(', ');
            lines.push(
                `║ ️ ${item.symbol.padEnd(8)} ${signals.padEnd(45)} ║`
            );
        }

        return lines.join('\n');
    }

    formatAlerts(alerts) {
        if (!alerts || alerts.length === 0) {
            return '║ No alerts at this time                                         ║';
        }

        const lines = [];
        const severityEmoji = {
            'INFO': 'ℹ️',
            'WARNING': '️',
            'HIGH': '',
            'CRITICAL': ''
        };

        for (const alert of alerts.slice(0, 3)) {
            const emoji = severityEmoji[alert.severity] || 'ℹ️';
            lines.push(
                `║ ${emoji} ${alert.message.padEnd(55)} ║`
            );
        }

        return lines.join('\n');
    }

    formatPrice(price) {
        if (price > 10000) return price.toFixed(0);
        if (price > 100) return price.toFixed(2);
        if (price > 1) return price.toFixed(4);
        return price.toFixed(8);
    }

    formatVolume(volume) {
        if (volume > 1e9) return `${(volume / 1e9).toFixed(2)}B`;
        if (volume > 1e6) return `${(volume / 1e6).toFixed(2)}M`;
        if (volume > 1e3) return `${(volume / 1e3).toFixed(2)}K`;
        return volume.toFixed(0);
    }

    formatChange(change) {
        const formatted = change.toFixed(2);
        if (change > 0) return `+${formatted}%`;
        return `${formatted}%`;
    }
}
```

### 3. Real-Time Updates

```javascript
class RealTimeScanner {
    constructor() {
        this.scanner = new MarketMoversScanner();
        this.display = new MoversDisplay();
        this.updateInterval = 30000; // 30 seconds
        this.isRunning = false;
    }

    async start(params) {
        this.isRunning = true;
        console.log('Starting real-time market scanner...');

        while (this.isRunning) {
            try {
                // Scan markets
                const results = await this.scanner.scanMarkets(params);

                // Clear console and display
                console.clear();
                console.log(this.display.displayResults(results));

                // Check for critical alerts
                this.checkCriticalAlerts(results.alerts);

                // Wait for next update
                await this.sleep(this.updateInterval);

            } catch (error) {
                console.error('Scanner error:', error);
                await this.sleep(5000); // Retry after 5 seconds
            }
        }
    }

    checkCriticalAlerts(alerts) {
        const critical = alerts.filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH');

        if (critical.length > 0) {
            console.log('\n CRITICAL ALERTS:');
            for (const alert of critical) {
                console.log(`- ${alert.message}`);
            }
            // Could trigger notifications here
        }
    }

    stop() {
        this.isRunning = false;
        console.log('Scanner stopped.');
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

### 4. Advanced Filtering

```javascript
class ScannerFilters {
    applyFilters(asset, filters) {
        // Market cap filter
        if (filters.minMarketCap && asset.marketCap < filters.minMarketCap) {
            return false;
        }
        if (filters.maxMarketCap && asset.marketCap > filters.maxMarketCap) {
            return false;
        }

        // Volume filter
        if (filters.minVolume && asset.volume < filters.minVolume) {
            return false;
        }

        // Price filter
        if (filters.minPrice && asset.price < filters.minPrice) {
            return false;
        }
        if (filters.maxPrice && asset.price > filters.maxPrice) {
            return false;
        }

        // Change filter
        if (filters.minChange && asset.change < filters.minChange) {
            return false;
        }
        if (filters.maxChange && asset.change > filters.maxChange) {
            return false;
        }

        // Custom filters
        if (filters.excludeStablecoins && this.isStablecoin(asset.symbol)) {
            return false;
        }

        if (filters.onlyTop100 && asset.rank > 100) {
            return false;
        }

        return true;
    }

    isStablecoin(symbol) {
        const stablecoins = ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'USDD'];
        return stablecoins.includes(symbol.toUpperCase());
    }

    createSmartFilters(scanType) {
        const filters = {
            dayTrading: {
                minVolume: 10000000,
                minPrice: 0.01,
                maxPrice: 100000,
                minChange: 2,
                excludeStablecoins: true
            },
            swingTrading: {
                minMarketCap: 100000000,
                minVolume: 5000000,
                minChange: 5,
                onlyTop100: true
            },
            pennyStocks: {
                maxPrice: 5,
                minVolume: 1000000,
                minChange: 10
            },
            blueChips: {
                minMarketCap: 10000000000,
                minVolume: 100000000
            }
        };

        return filters[scanType] || {};
    }
}
```

## Error Handling

```javascript
try {
    const scanner = new RealTimeScanner();

    await scanner.start({
        markets: 'all',
        timeframe: '24h',
        categories: ['gainers', 'losers', 'volume', 'unusual'],
        limit: 20,
        filters: {
            minVolume: 1000000,
            excludeStablecoins: true
        },
        sortBy: 'percentage'
    });

    // Graceful shutdown
    process.on('SIGINT', () => {
        scanner.stop();
        process.exit(0);
    });

} catch (error) {
    console.error('Failed to start scanner:', error);
    process.exit(1);
}
```

This command provides comprehensive market scanning with real-time updates, advanced filtering, and alert detection across multiple asset classes.