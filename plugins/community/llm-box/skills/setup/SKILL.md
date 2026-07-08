---
name: setup
description: Install and configure llm-box, including the MCP server connection for Claude Code.
invocation: user
---

# llm-box Setup

## Prerequisites

- Go 1.21+ (for building from source) OR a pre-built binary

## Installation

### Option 1: Install Script (Linux/macOS)

```bash
curl -sL https://raw.githubusercontent.com/alib8b8/llm-box/main/install.sh -o install.sh
bash install.sh
```

### Option 2: Go Install

```bash
go install github.com/alib8b8/llm-box/cmd/llm-box@latest
```

### Option 3: Download from Releases

Download the binary for your platform:
https://github.com/alib8b8/llm-box/releases

## Verify Installation

```bash
llm-box list
```

## MCP Server

The plugin includes a pre-configured MCP server in `.mcp.json`:

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

Claude Code will automatically start the MCP server when the plugin is activated.

## Configuration

Create `~/.llm-box/config.yaml`:

```yaml
safe_mode: false
default_model: "ollama://llama3"
api_keys:
  openai: "your-api-key"
  deepseek: "your-api-key"
```

## Troubleshooting

1. Check if llm-box is in PATH: `which llm-box`
2. Verify version: `llm-box --version`
3. Test MCP server: `llm-box --mcp-server`