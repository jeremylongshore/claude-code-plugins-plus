# Analytics Event Types Reference

Complete documentation of all event types emitted by the Claude Code Analytics Daemon.

## Event Structure

All events share a common base structure:

```typescript
interface BaseEvent {
  type: string;           // Event type identifier
  timestamp: number;      // Unix timestamp (milliseconds)
  conversationId: string; // Unique conversation identifier
}
```

## Event Types

### 1. Plugin Activation

**Type**: `plugin.activation`

**Description**: Emitted when a plugin is activated or installed in a conversation.

**Fields**:
- `pluginName` (string): Plugin identifier (e.g., "terraform-specialist")
- `pluginVersion` (string, optional): Semantic version (e.g., "1.2.0")
- `marketplace` (string, optional): Marketplace slug (e.g., "claude-code-plugins-plus")

**Example**:
```json
{
  "type": "plugin.activation",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "pluginName": "terraform-specialist",
  "pluginVersion": "1.0.0",
  "marketplace": "claude-code-plugins-plus"
}
```

**Use Cases**:
- Track most popular plugins
- Measure plugin adoption rates
- Identify plugin combinations
- Monitor marketplace distribution

---

### 2. Skill Trigger

**Type**: `skill.trigger`

**Description**: Emitted when an Agent Skill is activated based on conversation context.

**Fields**:
- `skillName` (string): Skill identifier (e.g., "terraform-plan-analyzer")
- `pluginName` (string): Parent plugin name
- `triggerPhrase` (string, optional): User phrase that triggered the skill

**Example**:
```json
{
  "type": "skill.trigger",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "skillName": "terraform-plan-analyzer",
  "pluginName": "terraform-specialist",
  "triggerPhrase": "analyze this terraform plan"
}
```

**Use Cases**:
- Measure skill effectiveness
- Identify popular skills
- Optimize skill trigger phrases
- Track skill usage patterns

---

### 3. LLM Call

**Type**: `llm.call`

**Description**: Emitted when Claude API is invoked during conversation.

**Fields**:
- `model` (string): Model identifier (e.g., "claude-sonnet-4-5")
- `inputTokens` (number, optional): Input token count
- `outputTokens` (number, optional): Output token count
- `totalTokens` (number, optional): Total token count

**Example**:
```json
{
  "type": "llm.call",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "model": "claude-sonnet-4-5",
  "inputTokens": 1500,
  "outputTokens": 800,
  "totalTokens": 2300
}
```

**Use Cases**:
- Monitor API usage
- Calculate cost estimates
- Track token consumption trends
- Optimize prompt efficiency

---

### 4. Cost Update

**Type**: `cost.update`

**Description**: Emitted when API costs are calculated for a conversation.

**Fields**:
- `model` (string): Model identifier
- `inputCost` (number): Cost for input tokens
- `outputCost` (number): Cost for output tokens
- `totalCost` (number): Total cost for the call
- `currency` (string): Currency code (e.g., "USD")

**Example**:
```json
{
  "type": "cost.update",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "model": "claude-sonnet-4-5",
  "inputCost": 0.0045,
  "outputCost": 0.012,
  "totalCost": 0.0165,
  "currency": "USD"
}
```

**Use Cases**:
- Track spending per conversation
- Calculate ROI for automation
- Budget forecasting
- Cost optimization insights

---

### 5. Rate Limit Warning

**Type**: `rate_limit.warning`

**Description**: Emitted when approaching or hitting API rate limits.

**Fields**:
- `service` (string): Service identifier (e.g., "anthropic-api")
- `limit` (number): Rate limit ceiling
- `current` (number): Current usage count
- `resetAt` (number, optional): Unix timestamp when limit resets

**Example**:
```json
{
  "type": "rate_limit.warning",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "service": "anthropic-api",
  "limit": 1000,
  "current": 950,
  "resetAt": 1703350800000
}
```

**Use Cases**:
- Prevent rate limit errors
- Throttle requests proactively
- Plan API capacity
- Alert on high usage

---

### 6. Conversation Created

**Type**: `conversation.created`

**Description**: Emitted when a new conversation file is detected.

**Fields**:
- `title` (string, optional): Conversation title

**Example**:
```json
{
  "type": "conversation.created",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "title": "Deploy infrastructure with Terraform"
}
```

**Use Cases**:
- Track conversation volume
- Measure user engagement
- Identify peak usage times
- Analyze conversation topics

---

### 7. Conversation Updated

**Type**: `conversation.updated`

**Description**: Emitted when a conversation file is modified (new messages added).

**Fields**:
- `messageCount` (number): Total number of messages in conversation

**Example**:
```json
{
  "type": "conversation.updated",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "messageCount": 12
}
```

**Use Cases**:
- Monitor conversation length
- Detect long-running sessions
- Measure conversation depth
- Track engagement patterns

---

## Event Flow Example

Typical event sequence for a plugin-powered conversation:

```
1. conversation.created
   ↓
2. plugin.activation (terraform-specialist)
   ↓
3. llm.call (initial message)
   ↓
4. cost.update ($0.0025)
   ↓
5. conversation.updated (messageCount: 2)
   ↓
6. skill.trigger (terraform-plan-analyzer)
   ↓
7. llm.call (skill response)
   ↓
8. cost.update ($0.0045)
   ↓
9. conversation.updated (messageCount: 4)
```

## WebSocket Connection

**Endpoint**: `ws://localhost:3456` (default)

**Configuration**:
- `CCP_ANALYTICS_PORT` - Custom port (default: 3456)
- `CCP_ANALYTICS_HOST` - Custom host (default: localhost)

**Connection Example**:
```javascript
const ws = new WebSocket('ws://localhost:3456');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`[${data.type}]`, data);
};
```

## TypeScript Definitions

See [src/types.ts](./src/types.ts) for complete TypeScript definitions.

## Dashboard Integration

Events are designed for real-time dashboard consumption:

1. **Usage Analytics**: plugin.activation, skill.trigger
2. **Cost Tracking**: cost.update, llm.call
3. **Rate Limiting**: rate_limit.warning
4. **Engagement Metrics**: conversation.created, conversation.updated

## Privacy & Security

- All events are **local only** - no data leaves your machine
- Conversation content is **never transmitted** (only metadata)
- WebSocket server is **unauthenticated** (localhost binding only)
- Production deployments should add authentication layer
