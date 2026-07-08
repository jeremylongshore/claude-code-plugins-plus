# Grok Remote MCP Server

HTTP/SSE transport layer for llm-box MCP server, enabling Grok web integration.

## Quick Start

```bash
# Start the Remote MCP server
go run ./grok-mcp-server --port 8080

# Or if llm-box is built
llm-box --mcp-remote --port 8080
```

## Endpoints

| Endpoint | Transport | Description |
|----------|-----------|-------------|
| `GET /sse` | SSE | Connect for SSE event stream |
| `POST /sse?sessionId=ID` | SSE | Send messages to existing session |
| `POST /mcp` | Streamable HTTP | Send JSON-RPC, get response |
| `GET /health` | - | Health check |

## Connecting to Grok

### Grok Web (grok.com)

1. Start the Remote MCP server locally
2. Go to **grok.com/connectors**
3. Add a custom MCP connector:
   - Type: Remote MCP
   - Transport: Streamable HTTP or SSE
   - URL: `http://localhost:8080/mcp` or `http://localhost:8080/sse`

### Grok Build CLI

For local development, use the stdio MCP server via `.mcp.json`:

```json
{
  "mcpServers": {
    "llm-box": {
      "type": "stdio",
      "command": "llm-box",
      "args": ["--mcp-server"]
    }
  }
}
```

### xAI API Function Calling

Use `tools.json` as the `tools` parameter in xAI API chat completions:

```python
import openai

client = openai.OpenAI(
    api_key="your-xai-api-key",
    base_url="https://api.x.ai/v1"
)

with open("tools.json") as f:
    tools = json.load(f)["tools"]

response = client.chat.completions.create(
    model="grok-3",
    messages=[{"role": "user", "content": "Fetch weather for Beijing"}],
    tools=tools
)
```

## Architecture

```
Grok Web / API
    │
    ├── SSE Transport ──┐
    │                    │
    └── Streamable HTTP ┤
                         │
                    ┌────▼────┐
                    │ main.go │  (HTTP/SSE proxy)
                    └────┬────┘
                         │ spawns
                    ┌────▼────────┐
                    │ llm-box     │  (stdio MCP server)
                    │ --mcp-server│
                    └─────────────┘
```

The Remote MCP server acts as a transport proxy:
- Accepts HTTP/SSE connections from Grok
- Spawns the existing `llm-box --mcp-server` stdio process
- Translates between HTTP/SSE and stdio JSON-RPC

This design reuses the proven stdio MCP implementation without modification.

## Available Tools

| Tool | Description |
|------|-------------|
| `create_workflow` | Generate YAML workflow from plain English |
| `run_workflow` | Execute workflow from YAML file |
| `run_workflow_yaml` | Execute workflow from raw YAML |
| `list_nodes` | List all available nodes |
| `validate_workflow` | Validate workflow without executing |
