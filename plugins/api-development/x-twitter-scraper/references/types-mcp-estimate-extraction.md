# Xquik TypeScript Types: MCP: estimate-extraction

```typescript

interface McpExtractionEstimate {
  allowed?: boolean;          // Whether the extraction is allowed within budget
  estimatedResults?: number;  // Estimated number of results
  creditsRequired?: string;   // Required credits, bigint string
  creditsAvailable?: string;  // Available credits, bigint string
  source?: string;            // Data source used for estimation
  resolvedXUserId?: string;   // Resolved user ID for username-based estimates
  error?: string;             // Error message if estimation failed
}

```
