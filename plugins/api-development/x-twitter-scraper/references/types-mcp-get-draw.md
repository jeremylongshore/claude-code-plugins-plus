# Xquik TypeScript Types: MCP: get-draw

```typescript

interface McpDrawDetails {
  draw: {
    id: string;               // Draw ID
    status: string;           // Draw status (completed, failed)
    createdAt: string;        // ISO 8601 timestamp
    drawnAt?: string;         // ISO 8601 timestamp when winners were drawn
    totalEntries: number;     // Total reply count before filtering
    validEntries: number;     // Entries remaining after filters applied
    tweetId: string;          // Giveaway tweet ID
    tweetUrl: string;         // Full URL of the giveaway tweet
    tweetText: string;        // Giveaway tweet text
    tweetAuthorUsername: string; // Username of the giveaway tweet author
    tweetLikeCount: number;   // Tweet like count at draw time
    tweetRetweetCount: number; // Tweet retweet count at draw time
    tweetReplyCount: number;  // Tweet reply count at draw time
    tweetQuoteCount: number;  // Tweet quote count at draw time
  };
  winners: {
    position: number;         // Winner position (1-based)
    authorUsername: string;   // X username of the winner
    tweetId: string;          // Tweet ID of the winning reply
    isBackup: boolean;        // Whether this is a backup winner
  }[];
}

```
