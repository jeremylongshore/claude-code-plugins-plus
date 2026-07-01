# Xquik MCP Server Setup

Connect AI agents and IDEs to Xquik via the Model Context Protocol. The MCP server uses the same API key as the REST API.

| Setting | Value |
|---------|-------|
| Protocol | HTTP (StreamableHTTP) |
| Endpoint | `https://xquik.com/mcp` |
| Auth header | `x-api-key` |

> **Security:** Use a scoped, revocable API key - not your primary account key. Where your platform supports environment variable interpolation (for example, `${XQUIK_API_KEY}`), prefer that over hardcoding. If interpolation is not supported, use the client's secure secret store. Rotate keys periodically from the Xquik dashboard account page. Never commit API keys to version control.

Use native HTTP MCP clients or OAuth connectors only. Do not proxy Xquik API keys through third-party local bridge packages, local proxy commands, or command-line adapters.

## Contents

- [Claude.ai (Web)](#claudeai-web)
- [Claude Desktop](#claude-desktop)
- [Claude Code](#claude-code)
- [ChatGPT](#chatgpt)
- [Codex CLI](#codex-cli)
- [Cursor](#cursor)
- [VS Code](#vs-code)
- [Windsurf](#windsurf)
- [OpenCode](#opencode)
- [MCP Server Architecture](#mcp-server-architecture)
- [After Setup](#after-setup)

## Claude.ai (Web)

Claude.ai supports MCP connectors natively via OAuth. Add Xquik as a connector from **Settings > Feature Preview > Integrations > Add More > Xquik**. The OAuth 2.1 flow handles authentication automatically. No API key needed.

## Claude Desktop

Claude.ai (web) is the recommended Claude client because it supports Xquik via OAuth in the hosted UI. Avoid local bridge setups that pass API keys in command-line arguments; local process listings can expose argv values.

For desktop workflows, use Claude Code, Cursor, VS Code, Windsurf, OpenCode, or another HTTP MCP client that stores headers in a config file or secure settings store.

## Claude Code

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "xquik": {
      "type": "http",
      "url": "https://xquik.com/mcp",
      "headers": {
        "x-api-key": "${XQUIK_API_KEY}"
      }
    }
  }
}
```

## ChatGPT

2 ways to connect ChatGPT to Xquik:

### Option 1: Agents SDK

Use the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/mcp/) for programmatic access:

```python
from agents.mcp import MCPServerStreamableHttp

def load_secret(name: str) -> str:
    """Read from your agent or platform secret store."""
    raise RuntimeError(f"Configure {name} in your secret store.")

api_key = load_secret("XQUIK_API_KEY")

async with MCPServerStreamableHttp(
    url="https://xquik.com/mcp",
    headers={"x-api-key": api_key},
    params={},
) as xquik:
    # use xquik as a tool provider
    pass
```

### Option 2: Developer Mode

ChatGPT Developer Mode supports MCP connectors via OAuth. Add Xquik from **Settings > Developer Mode > MCP Tools > Add**. Enter `https://xquik.com/mcp` as the endpoint. OAuth handles authentication automatically.

## Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.xquik]
url = "https://xquik.com/mcp"
http_headers = { "x-api-key" = "${XQUIK_API_KEY}" }
```

## Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "xquik": {
      "url": "https://xquik.com/mcp",
      "headers": {
        "x-api-key": "${XQUIK_API_KEY}"
      }
    }
  }
}
```

## VS Code

Add to `.vscode/mcp.json` (project) or use **MCP: Open User Configuration** (global):

```json
{
  "servers": {
    "xquik": {
      "type": "http",
      "url": "https://xquik.com/mcp",
      "headers": {
        "x-api-key": "${XQUIK_API_KEY}"
      }
    }
  }
}
```

## Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "xquik": {
      "serverUrl": "https://xquik.com/mcp",
      "headers": {
        "x-api-key": "${XQUIK_API_KEY}"
      }
    }
  }
}
```

## OpenCode

Add to `opencode.json`:

```json
{
  "mcp": {
    "xquik": {
      "type": "remote",
      "url": "https://xquik.com/mcp",
      "headers": {
        "x-api-key": "${XQUIK_API_KEY}"
      }
    }
  }
}
```

## MCP Server Architecture

The MCP server (v2) at `https://xquik.com/mcp` provides 2 structured API tools:

| Tool | Description | Usage |
|------|-------------|------|
| `explore` | Search the API endpoint catalog (read-only, no network calls) | Included |
| `xquik` | Send confirmed Xquik API requests | Varies by endpoint |

The agent sends structured API requests through the MCP server, which handles authentication and execution for the documented REST API. Supported endpoints across the documented categories are accessible through the `xquik` tool. Private reads, writes, and persistent resources require explicit user confirmation before use. Plan and credit changes are dashboard-only.

## After Setup

### Workflow Patterns

| Workflow | Steps (via `xquik` tool) |
|----------|--------------------------|
| Set up real-time alerts | Confirm target, event types, destination, and ongoing usage -> `POST /monitors` -> `POST /webhooks` -> `POST /webhooks/{id}/test` |
| Run a giveaway | Confirm tweet URL and rules -> `POST /draws` |
| Bulk extraction | `POST /extractions/estimate` -> `POST /extractions` -> `GET /extractions/{id}` |
| Compose optimized tweet | `POST /compose` (step=compose -> refine -> score) |

### Example Prompts

Try these with your AI agent:

- "Monitor @vercel for new tweets and quote tweets after I confirm the ongoing usage"
- "How many followers does @elonmusk have?"
- "Search for tweets mentioning xquik"
- "What does this tweet say? https://x.com/elonmusk/status/1893456789012345678"
- "Does @elonmusk follow @SpaceX back?"
- "Pick 3 winners from this tweet: https://x.com/burakbayir/status/1893456789012345678"
- "Estimate usage for extracting all followers of @elonmusk."
- "What's trending in the US right now?"
- "What's trending on Hacker News today?"
- "Help me write a tweet about launching my product"
- "Set up a webhook at https://my-server.com/events for new tweets after I confirm the destination"
- "What is my current credit balance?"
