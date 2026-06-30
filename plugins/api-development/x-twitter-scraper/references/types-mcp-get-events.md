# Xquik TypeScript Types: MCP: get-events

```typescript

interface McpEventList {
  events: {
    id: string;               // Event ID (use with get-event for full details)
    xUsername: string;        // Username of the monitored account
    eventType: string;        // Event type (tweet.new, tweet.reply, etc.)
    eventData: unknown;       // Full event payload (tweet text, author, metrics)
    monitoredAccountId: string; // ID of the monitored account
    createdAt: string;        // ISO 8601 when event was recorded
    occurredAt: string;       // ISO 8601 when event occurred on X
  }[];
  hasMore: boolean;           // Whether more results are available
  nextCursor?: string;        // Pass as afterCursor to fetch the next page
}

```
