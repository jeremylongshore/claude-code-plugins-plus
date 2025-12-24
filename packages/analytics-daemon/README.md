# Claude Code Analytics Daemon

Local analytics daemon that monitors Claude Code conversation files for real-time plugin usage tracking and dashboard integration.

## Features

- **File Watching**: Monitors `~/.claude/conversations/` for new and updated conversation files
- **Event Detection**: Tracks plugin activations, skill triggers, LLM calls, costs, and rate limits
- **Real-time Broadcasting**: WebSocket server broadcasts events to connected dashboards
- **Zero Cloud Dependencies**: Runs entirely locally, no data leaves your machine

## Installation

```bash
cd packages/analytics-daemon
pnpm install
pnpm build
```

## Usage

### Start the Daemon

```bash
# From packages/analytics-daemon/
pnpm start

# Or run directly
node dist/index.js

# Or use the CLI command
ccp-analytics
```

### Configuration

Environment variables:

```bash
# WebSocket server port (default: 3456)
export CCP_ANALYTICS_PORT=3456

# WebSocket server host (default: localhost)
export CCP_ANALYTICS_HOST=localhost
```

### Connect to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:3456');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};
```

## Event Types

### Plugin Activation
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

### Skill Trigger
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

### LLM Call
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

### Cost Update
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

### Rate Limit Warning
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

### Conversation Events
```json
{
  "type": "conversation.created",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "title": "Deploy infrastructure with Terraform"
}

{
  "type": "conversation.updated",
  "timestamp": 1703347200000,
  "conversationId": "abc123",
  "messageCount": 12
}
```

## Architecture

```
┌─────────────────────────────────────┐
│  ~/.claude/conversations/*.json     │
│  (Claude Code conversation files)   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  ConversationWatcher (Chokidar)     │
│  - Detects file changes             │
│  - Parses conversation JSON         │
│  - Extracts plugin/skill data       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Event Emitter                      │
│  - plugin.activation                │
│  - skill.trigger                    │
│  - llm.call                         │
│  - cost.update                      │
│  - rate_limit.warning               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  AnalyticsServer (WebSocket)        │
│  - Broadcasts events to clients     │
│  - ws://localhost:3456              │
└─────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Dashboard / Client Applications    │
│  - Real-time visualizations         │
│  - Usage analytics                  │
│  - Cost tracking                    │
└─────────────────────────────────────┘
```

## Development

```bash
# Watch mode (auto-rebuild on changes)
pnpm dev

# Build
pnpm build

# Run tests
pnpm test
```

## API Reference

See [src/types.ts](./src/types.ts) for complete TypeScript definitions of all events and interfaces.

## Security & Privacy

- **Local Only**: No data is sent to external servers
- **WebSocket Auth**: Currently unauthenticated (localhost only)
- **File Permissions**: Requires read access to `~/.claude/conversations/`

## License

MIT
