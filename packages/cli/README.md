# @claude-code-plugins/ccp

> Command-line tool for installing and managing Claude Code plugins from [claudecodeplugins.io](https://claudecodeplugins.io)

[![npm version](https://img.shields.io/npm/v/@claude-code-plugins/ccp.svg)](https://www.npmjs.com/package/@claude-code-plugins/ccp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **One-Command Installation**: Install plugins with a single command
- **Universal Compatibility**: Works with npm, bun, pnpm, and deno
- **Built-in Diagnostics**: `ccp doctor` checks your Claude Code installation
- **Cross-Platform**: Supports Linux, macOS, and Windows
- **Zero Configuration**: Automatically detects Claude Code paths

## Installation

You don't need to install this package globally. Just use your preferred package manager:

### npm / npx
```bash
npx @claude-code-plugins/ccp install <plugin-name>
```

### Bun
```bash
bunx @claude-code-plugins/ccp install <plugin-name>
```

### pnpm
```bash
pnpx @claude-code-plugins/ccp install <plugin-name>
```

### Deno
```bash
deno run -A npm:@claude-code-plugins/ccp install <plugin-name>
```

## Quick Start

### Install a Plugin

```bash
npx @claude-code-plugins/ccp install devops-pack
```

### List Installed Plugins

```bash
npx @claude-code-plugins/ccp list
```

### Run Diagnostics

```bash
npx @claude-code-plugins/ccp doctor
```

### Search for Plugins

```bash
npx @claude-code-plugins/ccp search terraform
```

## Commands

### `ccp install <plugin>`

Install a plugin from the marketplace.

**Options:**
- `-y, --yes` - Skip confirmation prompts
- `--global` - Install globally for all projects (default: project-local if in a project)

**Example:**
```bash
npx @claude-code-plugins/ccp install python-pro
```

### `ccp list`

List installed plugins.

**Options:**
- `-a, --all` - Show all available plugins (not just installed)

**Example:**
```bash
npx @claude-code-plugins/ccp list --all
```

### `ccp doctor`

Run diagnostics on your Claude Code installation and plugins.

**Options:**
- `--json` - Output results as JSON

**Example:**
```bash
npx @claude-code-plugins/ccp doctor
```

**Sample Output:**
```
🔍 Claude Code Plugins - System Diagnostics

System Environment:
  ✓ Node.js Version: v22.20.0 (supported)
  ✓ Operating System: linux 6.8.0-86-generic
  ✓ Package Managers: npm, bun

Claude Code Installation:
  ✓ Claude Config Directory: /home/user/.claude
  ✓ Plugins Directory: /home/user/.claude/plugins
  ✓ Marketplaces Directory: /home/user/.claude/marketplaces

Plugins:
  ✓ Installed Plugins: 5 total (3 global, 2 local)

Marketplace:
  ✓ Marketplace Catalog: Installed
  ✓ Catalog Freshness: Up to date

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary:
  ✓ 9 passed

✨ All checks passed! Your Claude Code setup is healthy.
```

### `ccp search <query>`

Search for plugins in the marketplace.

**Example:**
```bash
npx @claude-code-plugins/ccp search terraform
```

*Note: Search functionality coming soon. For now, visit [claudecodeplugins.io](https://claudecodeplugins.io) to browse plugins.*

### `ccp analytics`

View plugin usage analytics (Coming Soon).

**Options:**
- `--json` - Output as JSON

### `ccp marketplace`

Manage marketplace connection and setup.

**Options:**
- `--verify` - Verify marketplace installation and show detailed status

**Example:**
```bash
# Check marketplace status
npx @claude-code-plugins/ccp marketplace

# Verify installation with detailed diagnostics
npx @claude-code-plugins/ccp marketplace --verify
```

**Sample Output (Not Installed):**
```
📦 Claude Code Plugins Marketplace

⚠️  Marketplace not added yet

📋 Setup Instructions:

1. Open Claude Code (terminal or desktop app)
2. Run this command:

   /plugin marketplace add jeremylongshore/claude-code-plugins

3. Wait for confirmation (usually < 5 seconds)
4. Verify installation:

   npx @claude-code-plugins/ccp marketplace --verify
```

**Sample Output (Installed):**
```
📦 Claude Code Plugins Marketplace

✓ Marketplace is already added!

🔍 Marketplace Status:

Installation:
  ✓ Marketplace added
  Location: /home/user/.claude/marketplaces/claude-code-plugins-plus

  ✓ Catalog found
  File: /home/user/.claude/marketplaces/claude-code-plugins-plus/.claude-plugin/marketplace.json
```

### `ccp marketplace-add`

Guide you through adding the marketplace to Claude Code.

**Example:**
```bash
npx @claude-code-plugins/ccp marketplace-add
```

### `ccp marketplace-remove`

Guide you through removing the marketplace from Claude Code.

**Example:**
```bash
npx @claude-code-plugins/ccp marketplace-remove
```

## Package Manager Performance

| Package Manager | Startup Time | Market Share |
|----------------|--------------|--------------|
| Bun (bunx)     | ~0.05s       | ~5%          |
| Deno           | ~0.1s        | ~5%          |
| pnpm (pnpx)    | ~0.5s        | ~10%         |
| npm (npx)      | ~2-5s        | ~80%         |

**Recommendation**: For fastest performance, use `bunx` if you have Bun installed.

## Configuration

No configuration required! The CLI automatically:

- Detects your Claude Code installation directory
- Finds your global plugins directory (`~/.claude/plugins`)
- Detects project-local plugins (`.claude-plugin/` directory)
- Creates necessary directories if they don't exist

### Supported Paths

**Linux & macOS:**
- Config: `~/.claude`
- Plugins: `~/.claude/plugins`
- Marketplaces: `~/.claude/marketplaces`

**Windows:**
- Config: `%APPDATA%\Claude`
- Plugins: `%APPDATA%\Claude\plugins`
- Marketplaces: `%APPDATA%\Claude\marketplaces`

## Requirements

- Node.js 18.0.0 or higher
- Claude Code installed and run at least once

## Troubleshooting

### "Claude Code config directory not found"

Ensure Claude Code is installed and has been run at least once. The CLI looks for:
- Linux/macOS: `~/.claude`
- Windows: `%APPDATA%\Claude`

Run `ccp doctor` to diagnose installation issues.

### Permission Errors

If you get permission errors during installation:

1. Try installing locally (project-level) instead of globally
2. Check that you have write permissions to the Claude directories
3. Run `ccp doctor` to check your setup

### Plugin Not Found

If a plugin can't be found:

1. Check the plugin name spelling
2. Run `ccp list --all` to see available plugins
3. Visit [claudecodeplugins.io](https://claudecodeplugins.io) to browse the full marketplace
4. Ensure your marketplace catalog is up to date

## Development

### Setup

```bash
npm install
npm run build
```

### Testing

```bash
npm test
```

### Build

```bash
npm run build
```

This compiles TypeScript to JavaScript in the `dist/` directory.

## Architecture

The CLI is built with:

- **Commander.js** - CLI framework
- **Chalk** - Terminal styling
- **Ora** - Loading spinners
- **fs-extra** - File system operations
- **axios** - HTTP requests

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT © [Intent Solutions IO](https://intentsolutions.io)

## Links

- **Website**: [claudecodeplugins.io](https://claudecodeplugins.io)
- **GitHub**: [jeremylongshore/claude-code-plugins](https://github.com/jeremylongshore/claude-code-plugins)
- **Issues**: [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)
- **Marketplace**: [Browse Plugins](https://claudecodeplugins.io)

---

**Built with ❤️ for the Claude Code community**
