# Xquik TypeScript Types: MCP: list-monitors

```typescript

interface McpMonitorList {
  monitors: {
    id: string;               // Monitor ID (use with remove-monitor, get-events monitorId filter)
    xUsername: string;        // Monitored X username
    eventTypes: string[];     // Subscribed event types
    isActive: boolean;        // Whether the monitor is currently active
    createdAt: string;        // ISO 8601 timestamp
  }[];
}

```
