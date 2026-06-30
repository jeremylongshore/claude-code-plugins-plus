# Xquik TypeScript Types: MCP: search-tweets

```typescript

interface McpSearchResult {
  tweets: {
    id: string;               // Tweet ID (use with lookup-tweet for full metrics)
    text: string;             // Full tweet text
    authorUsername: string;   // X username of the tweet author
    authorName: string;       // Display name of the tweet author
    createdAt: string;        // ISO 8601 timestamp when tweet was posted
    media?: { mediaUrl: string; type: string; url: string }[];  // Attached photos/videos
    // No engagement metrics. Use lookup-tweet for those
  }[];
}

```
