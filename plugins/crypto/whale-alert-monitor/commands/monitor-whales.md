---
description: Monitor whale transactions in real-time
shortcut: mw
---

# Monitor Whale Activity

Track large transactions and whale wallet movements.

```javascript
class WhaleMonitor {
    async monitor(threshold = 1000000) {
        const alerts = await this.scanForLargeTransactions(threshold);
        return {
            alerts,
            summary: this.generateSummary(alerts),
            impact: this.assessMarketImpact(alerts)
        };
    }
}
```