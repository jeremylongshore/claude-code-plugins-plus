# Xquik TypeScript Types: MCP: run-extraction

```typescript

interface McpExtractionJob {
  id: string;                 // Extraction job ID (use with get-extraction for results)
  toolType: string;           // Extraction tool type used
  status: string;             // Job status
  totalResults: number;       // Number of results extracted
}

```
