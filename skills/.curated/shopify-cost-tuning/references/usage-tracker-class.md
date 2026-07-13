A class for tracking GraphQL query costs and REST API call counts, with reporting and optimization recommendations.

```typescript
class ShopifyUsageTracker {
  private graphqlCosts: number[] = [];
  private restCalls: number = 0;
  private startOfPeriod: Date = new Date();

  trackGraphqlCost(extensions: any): void {
    if (extensions?.cost?.actualQueryCost) {
      this.graphqlCosts.push(extensions.cost.actualQueryCost);
    }
  }

  trackRestCall(): void {
    this.restCalls++;
  }

  getReport(): UsageReport {
    const totalGraphqlCost = this.graphqlCosts.reduce((a, b) => a + b, 0);
    const avgCost = totalGraphqlCost / (this.graphqlCosts.length || 1);

    return {
      period: {
        start: this.startOfPeriod,
        end: new Date(),
      },
      graphql: {
        totalQueries: this.graphqlCosts.length,
        totalCost: totalGraphqlCost,
        averageCost: Math.round(avgCost),
        maxSingleCost: Math.max(...this.graphqlCosts, 0),
      },
      rest: {
        totalCalls: this.restCalls,
      },
      recommendation: avgCost > 500
        ? "High average query cost — optimize field selection"
        : avgCost > 100
        ? "Moderate cost — consider bulk operations for large queries"
        : "Efficient usage",
    };
  }
}
```
