# ZAI CLI

Z.AI vision, search, reader, and GitHub exploration via CLI and MCP.

## What It Does

Access Z.AI capabilities via `npx zai-cli`:

- **Vision**: Image/video analysis, OCR, UI-to-code, error diagnosis (GLM-4.6V)
- **Search**: Real-time web search with domain/recency filtering
- **Reader**: Web page to markdown extraction
- **Repo**: GitHub code search and reading via ZRead
- **Tools**: MCP tool discovery and raw calls
- **Code**: TypeScript tool chaining

## Installation

### Via Claude Code Plugin Marketplace

```bash
/plugin install zai-cli@claude-code-plugins-plus
```

### Via n-skills Marketplace

```bash
/plugin marketplace add numman-ali/n-skills
/plugin install zai-cli@n-skills
```

## Requirements

- Node.js 18+
- Z.AI API key (get one at https://z.ai/manage-apikey/apikey-list)

## Setup

```bash
export Z_AI_API_KEY="your-api-key"
```

## Usage

| Command | Purpose | Help |
|---------|---------|------|
| vision | Analyze images, screenshots, videos | `--help` for 8 subcommands |
| search | Real-time web search | `--help` for filtering options |
| read | Fetch web pages as markdown | `--help` for format options |
| repo | GitHub code search and reading | `--help` for tree/search/read |
| tools | List available MCP tools | |
| tool | Show tool schema | |
| call | Raw MCP tool invocation | |
| code | TypeScript tool chaining | |
| doctor | Check setup and connectivity | |

## Quick Start

```bash
# Analyze an image
npx zai-cli vision analyze ./screenshot.png "What errors do you see?"

# Search the web
npx zai-cli search "React 19 new features" --count 5

# Read a web page
npx zai-cli read https://docs.example.com/api

# Explore a GitHub repo
npx zai-cli repo search facebook/react "server components"
npx zai-cli repo tree openai/codex --path codex-rs --depth 2

# Check setup
npx zai-cli doctor
```

## Files

```
zai-cli/
├── .claude-plugin/
│   └── plugin.json         # Plugin metadata
├── skills/
│   ├── SKILL.md            # Main skill definition
│   └── references/
│       └── advanced.md     # Advanced features (MCP, code mode)
├── LICENSE                 # Apache 2.0
└── README.md               # This file
```

## Output

Default: **data-only** (raw output for token efficiency).
Use `--output-format json` for `{ success, data, timestamp }` wrapping.

## Resources

- **ZAI CLI Package**: https://github.com/numman-ali/zai-cli
- **n-skills Marketplace**: https://github.com/numman-ali/n-skills
- **Z.AI API Keys**: https://z.ai/manage-apikey/apikey-list

## License

Apache 2.0 - See LICENSE file
