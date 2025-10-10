# Getting Started with Claude Code Plugins

## What Are Plugins?

Claude Code plugins are packages that extend Claude Code functionality with custom commands, specialized agents, hooks, and MCP servers.

## Installation

### Add This Marketplace

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

### Browse Available Plugins

```bash
/plugin
```

This opens an interactive menu where you can:
- Browse all plugins from installed marketplaces
- See plugin descriptions and metadata
- Install plugins with one click

### Install Specific Plugin

```bash
/plugin install plugin-name@claude-code-plugins
```

### List Installed Plugins

```bash
/plugin list
```

### Enable/Disable Plugins

```bash
/plugin enable plugin-name
/plugin disable plugin-name
```

## Using Plugins

### Slash Commands

After installing a plugin with commands, they appear in `/help`:

```bash
/help
# Shows all available commands including plugin commands marked with (user)

/your-command
# Execute the command
```

### Subagents

Plugins can add specialized agents that Claude uses automatically:

```
"Please review this code for security issues"
# Claude may delegate to security-agent if installed
```

### Hooks

Hooks run automatically at specific events (file edits, tool usage, etc.). No manual invocation needed.

### MCP Servers

MCP servers provide additional tools and data sources. They start automatically when plugins are enabled.

## Team Setup

For team-wide plugin distribution, add to repository `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "team-plugins": {
      "source": {
        "source": "github",
        "repo": "your-org/plugins"
      }
    }
  },
  "enabledPlugins": {
    "formatter@team-plugins": true,
    "security-agent@team-plugins": true
  }
}
```

When team members trust the folder, plugins install automatically.

## Next Steps

- [Create your own plugin](creating-plugins.md)
- [Understand plugin structure](plugin-structure.md)
- [Learn about marketplaces](marketplace-guide.md)
