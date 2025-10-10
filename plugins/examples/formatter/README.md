# Formatter Plugin

Automatically formats code files after editing using hooks.

## Installation

```bash
/plugin install formatter@claude-code-plugins
```

## Requirements

- Node.js and npm installed
- Prettier (will be used via npx if available)

## What It Does

Automatically runs Prettier on JavaScript, TypeScript, JSON, CSS, and Markdown files after Claude edits them.

## How It Works

Uses a PostToolUse hook that:
1. Detects Write or Edit tool usage
2. Runs a formatting script
3. Applies Prettier to supported file types

## Learning Objectives

This plugin demonstrates:
- Hook configuration
- Event-driven automation
- Script integration
- Using ${CLAUDE_PLUGIN_ROOT} variable

## Files

- `.claude-plugin/plugin.json` - Plugin manifest
- `hooks/hooks.json` - Hook configuration
- `scripts/format.sh` - Formatting script

## License

MIT
