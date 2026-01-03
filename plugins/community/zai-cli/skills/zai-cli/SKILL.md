---
name: zai-cli
description: |
  Z.AI CLI providing vision, search, reader, and GitHub exploration via CLI and MCP.
  Use when user needs image/video analysis, OCR, UI-to-code conversion, error diagnosis,
  real-time web search, web page to markdown extraction, or GitHub code exploration.
  Trigger with phrases like "analyze this image", "search the web for", "read this page",
  "explore this repo", or "use zai". Requires Z_AI_API_KEY.
allowed-tools: Read, Write, Edit, Bash, WebFetch
version: 1.0.0
license: Apache-2.0
author: Numman Ali <numman.ali@gmail.com>
---
---

# ZAI CLI

Access Z.AI capabilities via `npx zai-cli`. The CLI is self-documenting - use `--help` at any level.

## Setup

```bash
export Z_AI_API_KEY="your-api-key"
```

Get a key at: https://z.ai/manage-apikey/apikey-list

## Commands

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
npx zai-cli read https://docs.example.com/api --with-images-summary --no-gfm

# Explore a GitHub repo
npx zai-cli repo search facebook/react "server components"
npx zai-cli repo search openai/codex "config" --language en
npx zai-cli repo tree openai/codex --path codex-rs --depth 2

# Check setup
npx zai-cli doctor
```

## Output

Default: **data-only** (raw output for token efficiency).
Use `--output-format json` for `{ success, data, timestamp }` wrapping.

## Advanced

For raw MCP tool calls (`tools`, `tool`, `call`), Code Mode, and performance tuning (cache/retries),
see `references/advanced.md`.
