# Xquik TypeScript Types: Trends

```typescript

interface Trend {
  name: string;
  description?: string;
  rank?: number;
  query?: string;
}

interface TrendList {
  trends: Trend[];
  total: number;
  woeid: number;
}

```
