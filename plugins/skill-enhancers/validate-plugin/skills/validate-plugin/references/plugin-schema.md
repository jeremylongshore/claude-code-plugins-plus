# Official Anthropic plugin.json Schema

Source: https://code.claude.com/docs/en/plugins-reference

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Plugin identifier (required if manifest exists) |

## Metadata Fields (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Semver version (e.g., "1.0.0") |
| `description` | string | What the plugin does |
| `author` | string/object | Author name or {name, email} |
| `homepage` | string | URL to plugin homepage |
| `repository` | string | URL to source code |
| `license` | string | SPDX license identifier |
| `keywords` | string[] | Discovery keywords |

## Component Path Fields (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `commands` | string | Path to commands directory (e.g., "./commands") |
| `agents` | string | Path to agents directory |
| `skills` | string | Path to skills directory |
| `hooks` | string | Path to hooks config |
| `mcpServers` | object | MCP server configurations |
| `outputStyles` | string | Path to output styles |
| `lspServers` | object | LSP server configurations |

## Invalid Fields (Not in Spec)

These fields are NOT part of the official Anthropic spec and will be rejected:
- `displayName` - use `name` instead
- `category` - marketplace-only field
- `tags` - marketplace-only field
- `requires` - not in spec
- `documentation` - not in spec
- `mcp_servers` - wrong case, use `mcpServers`
