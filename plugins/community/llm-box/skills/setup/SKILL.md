---
name: setup
description: Install and configure aflare, including the MCP server connection for Claude Code.
invocation: user
allowed-tools: Read, Edit, Write, Bash
version: 0.6.0
author: aflare
license: AGPL-3.0
compatibility: claude-code >= 0.7.0
tags: [setup, installation, configuration, mcp]
---

## Overview

This skill installs and configures aflare, an AI-powered terminal workflow engine, and sets up the MCP server connection for Claude Code integration. It handles binary installation, PATH configuration, and MCP server setup.

## Prerequisites

- Go 1.21+ (for building from source) OR a pre-built binary
- Git (for cloning or installing)
- Bash shell (Linux/macOS) or PowerShell (Windows)

## Instructions

### Step 1: Install aflare

Choose one of the following installation methods:

**Option 1: Install Script (Linux/macOS)**
```bash
curl -sL https://raw.githubusercontent.com/alib8b8/aflare/main/install.sh -o install.sh
bash install.sh
```

**Option 2: Go Install**
```bash
go install github.com/alib8b8/aflare/cmd/aflare@latest
```

**Option 3: Download from Releases**
Download the binary for your platform:
https://github.com/alib8b8/aflare/releases

### Step 2: Verify Installation

```bash
aflare --version
aflare list
```

### Step 3: Configure MCP Server

The MCP server is pre-configured in `.mcp.json`:

```json
{
  "mcpServers": {
    "aflare": {
      "type": "stdio",
      "command": "aflare",
      "args": ["--mcp-server"]
    }
  }
}
```

Claude Code will automatically start the MCP server when the plugin is activated.

### Step 4: Create Configuration (Optional)

Create `~/.aflare/config.yaml`:

```yaml
safe_mode: false
default_model: "ollama://llama3"
api_keys:
  openai: "your-api-key"
  deepseek: "your-api-key"
```

## Output

After successful setup:
- aflare CLI is installed and available in PATH
- MCP server is configured for Claude Code
- Configuration file created at `~/.aflare/config.yaml`
- Verify with: `aflare --version`

## Examples

**Example 1: Fresh Install on Linux**
```bash
curl -sL https://raw.githubusercontent.com/alib8b8/aflare/main/install.sh -o install.sh
bash install.sh
aflare --version
```

**Example 2: Update via Go**
```bash
go install github.com/alib8b8/aflare/cmd/aflare@latest
aflare --version
```

**Example 3: Configure API Keys**
```bash
mkdir -p ~/.aflare
cat > ~/.aflare/config.yaml <<EOF
safe_mode: false
default_model: "deepseek-chat"
api_keys:
  deepseek: "sk-your-key"
  openai: "sk-your-key"
EOF
```

## Resources

- **GitHub**: https://github.com/alib8b8/aflare
- **Releases**: https://github.com/alib8b8/aflare/releases
- **Documentation**: https://github.com/alib8b8/aflare/blob/main/README.md
- **Issues**: https://github.com/alib8b8/aflare/issues
- **Troubleshooting**:
  - Check PATH: `which aflare`
  - Verify version: `aflare --version`
  - Test MCP server: `aflare --mcp-server`
- **License**: AGPL-3.0