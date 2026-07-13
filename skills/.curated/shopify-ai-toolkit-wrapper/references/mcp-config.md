Complete MCP configuration for Shopify AI Toolkit with troubleshooting.

## Configuration Locations

MCP servers can be configured at three levels:

| Location | Scope | File |
|----------|-------|------|
| Project | This project only | `.mcp.json` in project root |
| User | All projects for this user | `~/.claude/.mcp.json` |
| Workspace | Shared via version control | `.claude/mcp.json` (committed) |

## Minimal Configuration

```json
{
  "mcpServers": {
    "shopify": {
      "command": "npx",
      "args": ["-y", "@shopify/ai-toolkit-mcp"],
      "env": {
        "SHOPIFY_ACCESS_TOKEN": "${SHOPIFY_ACCESS_TOKEN}",
        "SHOPIFY_STORE_URL": "https://your-store.myshopify.com"
      }
    }
  }
}
```

> **Package name note**: The package `@shopify/ai-toolkit-mcp` is a placeholder. Check [shopify.dev/docs](https://shopify.dev/docs) for the current official MCP package name. It may also be published as `@shopify/dev-mcp`, `@shopify/cli-mcp`, or similar.

## Environment Variables

Set these before starting Claude Code:

```bash
# Required
export SHOPIFY_ACCESS_TOKEN="shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export SHOPIFY_STORE_URL="https://your-store.myshopify.com"

# Optional (if using a Shopify Partner app)
export SHOPIFY_API_KEY="your-api-key"
export SHOPIFY_API_SECRET="your-api-secret"
```

### Generating an Access Token

1. Go to Shopify Admin > Settings > Apps and sales channels > Develop apps
2. Click "Create an app"
3. Configure Admin API scopes (minimum: `read_products`, `read_themes`)
4. Install the app and copy the Admin API access token

Token format: `shpat_` followed by 32 hex characters.

## Advanced Configuration

```json
{
  "mcpServers": {
    "shopify": {
      "command": "npx",
      "args": ["-y", "@shopify/ai-toolkit-mcp"],
      "env": {
        "SHOPIFY_ACCESS_TOKEN": "${SHOPIFY_ACCESS_TOKEN}",
        "SHOPIFY_STORE_URL": "${SHOPIFY_STORE_URL}",
        "SHOPIFY_API_VERSION": "2025-01",
        "LOG_LEVEL": "debug"
      },
      "timeout": 30000
    }
  }
}
```

## Multi-Store Configuration

For agencies or developers working across multiple stores:

```json
{
  "mcpServers": {
    "shopify-production": {
      "command": "npx",
      "args": ["-y", "@shopify/ai-toolkit-mcp"],
      "env": {
        "SHOPIFY_ACCESS_TOKEN": "${SHOPIFY_PROD_TOKEN}",
        "SHOPIFY_STORE_URL": "https://production-store.myshopify.com"
      }
    },
    "shopify-staging": {
      "command": "npx",
      "args": ["-y", "@shopify/ai-toolkit-mcp"],
      "env": {
        "SHOPIFY_ACCESS_TOKEN": "${SHOPIFY_STAGING_TOKEN}",
        "SHOPIFY_STORE_URL": "https://staging-store.myshopify.com"
      }
    }
  }
}
```

## Troubleshooting

### MCP Server Fails to Start

```bash
# Test the MCP server directly
npx @shopify/ai-toolkit-mcp

# Common errors:
# "ENOENT" → Node.js not in PATH, ensure Node 18+
# "MODULE_NOT_FOUND" → Package name changed, check Shopify docs
# "EACCES" → Permission issue, try: npm config set prefix ~/.npm-global
```

### Connection Timeout

```bash
# Increase timeout in .mcp.json
# Default is usually 10s, bump to 30s for first-time installs
"timeout": 30000

# Or pre-install the package
npm install -g @shopify/ai-toolkit-mcp
# Then use the global path instead of npx
```

### Token Validation Errors

```bash
# Verify token works
curl -s "https://your-store.myshopify.com/admin/api/2025-01/shop.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  | jq '.shop.name'

# If 401: Token is invalid or expired → regenerate in admin
# If 403: Token lacks required scopes → update app permissions
```

### Environment Variable Not Resolving

The `${VAR_NAME}` syntax in `.mcp.json` reads from the shell environment. If variables are not resolving:

```bash
# Check they are exported (not just set)
export SHOPIFY_ACCESS_TOKEN="shpat_xxx"  # This works
SHOPIFY_ACCESS_TOKEN="shpat_xxx"          # This does NOT work with MCP

# Add to shell profile for persistence
echo 'export SHOPIFY_ACCESS_TOKEN="shpat_xxx"' >> ~/.bashrc
```
