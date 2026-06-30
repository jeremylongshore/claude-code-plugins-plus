# Xquik TypeScript Types: MCP: score-tweet

```typescript

interface McpScoreTweet {
  totalChecks: number;        // Total number of checks performed
  passedCount: number;        // Number of checks that passed
  topSuggestion: string;      // Highest-impact improvement suggestion
  checklist: {
    factor: string;           // What was checked
    passed: boolean;          // Whether the check passed
    suggestion?: string;      // Improvement suggestion (present only if failed)
  }[];
}

```
