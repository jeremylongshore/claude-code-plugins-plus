# Geepers

Multi-agent orchestration system with MCP tools and Claude Code plugin agents.

## Installation

### From PyPI (MCP tools)
```bash
pip install geepers

# With optional dependencies
pip install geepers[all]
pip install geepers[anthropic,openai]
```

### As Claude Code Plugin (agents)
```bash
/plugin add lukeslp/geepers
```

## What's Included

### 43 Specialized Agents

Markdown-defined agents for Claude Code that provide specialized workflows:

| Category | Agents | Purpose |
|----------|--------|---------|
| **Master** | conductor_geepers | Intelligent routing to specialists |
| **Checkpoint** | scout, repo, status, snippets, orchestrator | Session maintenance |
| **Deploy** | caddy, services, validator, orchestrator | Infrastructure |
| **Quality** | a11y, perf, api, deps, critic, orchestrator | Code audits |
| **Fullstack** | db, design, react, orchestrator | End-to-end features |
| **Research** | data, links, diag, citations, orchestrator | Data gathering |
| **Games** | game, gamedev, godot, orchestrator | Game development |
| **Corpus** | corpus, corpus_ux, orchestrator | Linguistics/NLP |
| **Web** | flask, orchestrator | Web applications |
| **Python** | pycli, orchestrator | Python projects |

### 90+ MCP Tools

Six specialized MCP servers expose tools for:

- **geepers-unified** - All tools in one server
- **geepers-providers** - 13 LLM providers (Anthropic, OpenAI, xAI, etc.)
- **geepers-data** - 29+ data sources (Census, arXiv, GitHub, NASA, etc.)
- **geepers-cache** - Redis-backed caching
- **geepers-utility** - Document parsing, citations, TTS
- **geepers-websearch** - Multi-engine web search

## Configuration

### Claude Code MCP Config

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "geepers": {
      "command": "geepers-unified"
    }
  }
}
```

### Environment Variables

```bash
# LLM Providers
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
XAI_API_KEY=...

# Data Sources
GITHUB_TOKEN=...
NASA_API_KEY=...
CENSUS_API_KEY=...
```

## Usage

### Using Agents in Claude Code

```
@geepers_scout          # Quick project reconnaissance
@geepers_caddy          # Caddy configuration changes
@geepers_orchestrator_checkpoint  # End-of-session cleanup
```

### Using MCP Tools

Once configured, tools are available via the MCP protocol.

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/lukeslp/geepers
cd geepers
pip install -e .

# Run tests
pytest
```

## License

MIT License - Luke Steuber
