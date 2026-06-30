# Xquik TypeScript Types: MCP: run-draw

```typescript

interface McpDrawResult {
  id: string;                 // Draw ID (use with get-draw for full details)
  tweetId: string;            // Giveaway tweet ID
  totalEntries: number;       // Total reply count before filtering
  validEntries: number;       // Valid entries after filtering
  winners: {
    position: number;         // Winner position (1-based)
    authorUsername: string;   // X username of the winner
    tweetId: string;          // Tweet ID of the winning reply
    isBackup: boolean;        // Whether this is a backup winner
  }[];
}

```
