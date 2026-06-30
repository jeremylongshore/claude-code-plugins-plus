# Xquik TypeScript Types: MCP: add-webhook

```typescript

interface McpWebhookCreated {
  id: string;                 // Webhook ID
  url: string;                // HTTPS endpoint URL
  eventTypes: string[];       // Event types delivered to this webhook
  isActive: boolean;          // Whether the webhook is active
  createdAt: string;          // ISO 8601 timestamp
  secret: string;             // HMAC signing secret for verifying webhook payloads. Store securely.
}

```
