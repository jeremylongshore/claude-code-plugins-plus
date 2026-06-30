# Xquik TypeScript Types: MCP: get-trends

```typescript

interface McpTrends {
  woeid: number;
  total: number;
  trends: {
    name: string;             // Trend name or hashtag
    rank?: number;            // Trend rank position
    description?: string;     // Trend description or context
    query?: string;           // Search query to find tweets for this trend
  }[];
}

```
