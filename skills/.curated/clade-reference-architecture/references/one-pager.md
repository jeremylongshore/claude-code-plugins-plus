# clade-reference-architecture — One-Pager

Complete guide to building Claude Code plugins — skills, commands, agents, and MCP servers.

## The Problem

Claude Code's plugin system has four distinct extension points (skills, commands, agents, MCP servers), each with its own file structure, frontmatter schema, and runtime behavior. Without a single reference, developers waste time piecing together docs, guessing at YAML fields, and debugging plugin loading issues.

## The Solution

A unified architecture reference covering all four plugin types with annotated examples: SKILL.md frontmatter and body structure, slash command setup with `$ARGUMENTS`, agent configuration with `model`/`maxTurns`/`capabilities`, MCP server scaffolding with `@modelcontextprotocol/sdk`, and hook configuration in `.claude/settings.json`. Includes the path variable reference (`CLAUDE_SKILL_DIR`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`).

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Plugin authors extending Claude Code with custom capabilities |
| **What** | File structure, frontmatter spec, and code templates for all 4 plugin types plus hooks |
| **When** | When building a new Claude Code plugin or adding extension points to an existing one |

## Key Features

1. **Skill and command templates** — Complete YAML frontmatter with all valid fields, proper `allowed-tools` syntax, and `$ARGUMENTS` substitution for commands
2. **MCP server scaffold** — Working TypeScript MCP server using `@modelcontextprotocol/sdk` with `tools/list` and `tools/call` handlers
3. **Path variable reference** — `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` with context-specific usage guidance

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
