---
description: Calculate cryptocurrency taxes and generate reports
shortcut: ct
---

# Calculate Crypto Taxes

Calculate capital gains/losses using FIFO, LIFO, or specific identification methods.

## Implementation

```javascript
class CryptoTaxCalculator {
    async calculateTaxes(transactions, method = 'FIFO', taxYear = 2024) {
        const lots = this.organizeLots(transactions);
        const taxEvents = [];

        for (const sale of this.getSales(transactions)) {
            const costBasis = this.calculateCostBasis(sale, lots, method);
            const gain = sale.proceeds - costBasis;

            taxEvents.push({
                date: sale.date,
                asset: sale.asset,
                proceeds: sale.proceeds,
                costBasis,
                gain,
                type: this.getGainType(sale.date, costBasis.purchaseDate),
                taxRate: this.getTaxRate(gain, sale.holdingPeriod)
            });
        }

        return {
            summary: this.generateSummary(taxEvents),
            events: taxEvents,
            forms: this.generateTaxForms(taxEvents, taxYear),
            totalTax: this.calculateTotalTax(taxEvents)
        };
    }

    calculateCostBasis(sale, lots, method) {
        switch (method) {
            case 'FIFO':
                return this.fifoMethod(sale, lots);
            case 'LIFO':
                return this.lifoMethod(sale, lots);
            case 'HIFO':
                return this.hifoMethod(sale, lots);
            default:
                return this.specificMethod(sale, lots);
        }
    }
}
```

Calculate crypto taxes with various accounting methods.