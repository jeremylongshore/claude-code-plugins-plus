---
description: Analyze on-chain metrics and whale movements
shortcut: ac
---

# Analyze On-Chain Data

Monitor blockchain metrics, whale movements, and network health indicators.

```javascript
class OnChainAnalytics {
    async analyze(chain = 'ethereum', asset = 'ETH') {
        return {
            network: await this.getNetworkMetrics(chain),
            holders: await this.analyzeHolderDistribution(asset),
            whales: await this.trackWhaleMovements(asset),
            flows: await this.analyzeExchangeFlows(asset),
            supply: await this.getSupplyMetrics(asset)
        };
    }
}