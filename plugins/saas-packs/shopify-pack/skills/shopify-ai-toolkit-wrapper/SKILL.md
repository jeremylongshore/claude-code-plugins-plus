---
name: shopify-ai-toolkit-wrapper
description: |
  Integrate Shopify's AI Toolkit MCP server with Claude Code for GraphQL validation,
  Liquid linting, and documentation search.
  Use when setting up Shopify MCP integration, validating GraphQL queries,
  or linting Liquid templates.
  Trigger with phrases like "shopify ai toolkit", "shopify mcp",
  "shopify claude integration", "shopify graphql validation", "shopify liquid lint".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify AI Toolkit Wrapper

## Overview

Shopify's AI Toolkit provides an official MCP (Model Context Protocol) server for developer workflows. This skill configures it for Claude Code, enabling GraphQL schema validation, Liquid template linting, and real-time Shopify documentation search without leaving your editor.

## Prerequisites

- Node.js 18+ and npm/pnpm installed
- A Shopify store with a custom app or API access token
- Access scopes appropriate for your workflow (minimum: `read_products`, `read_themes`)
- Claude Code with MCP support enabled

## Instructions

### Step 1: MCP Configuration

Create or update `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "shopify": {
      "command": "npx",
      "args": [
        "-y",
        "@shopify/ai-toolkit-mcp"
      ],
      "env": {
        "SHOPIFY_ACCESS_TOKEN": "${SHOPIFY_ACCESS_TOKEN}",
        "SHOPIFY_STORE_URL": "https://your-store.myshopify.com"
      }
    }
  }
}
```

> **Note**: The package name `@shopify/ai-toolkit-mcp` may change. Check [shopify.dev/docs](https://shopify.dev/docs) for the latest official MCP package name and configuration.

Set your environment variables:

```bash
export SHOPIFY_ACCESS_TOKEN="shpat_xxxxxxxxxxxxxxxxxxxx"
export SHOPIFY_STORE_URL="https://your-store.myshopify.com"
```

See [references/mcp-config.md](references/mcp-config.md) for advanced configuration and troubleshooting.

### Step 2: GraphQL Schema Validation

With the MCP server running, validate GraphQL queries against your store's live schema before executing them. The MCP introspects the schema and catches:

- Deprecated fields (e.g., `priceRange` should be `priceRangeV2`)
- Type mismatches in mutation inputs (e.g., `ProductInput` split into `ProductCreateInput`/`ProductUpdateInput` in 2024-10)
- Missing required fields and incorrect enum values

See [references/graphql-validation.md](references/graphql-validation.md) for common validation errors and deprecated field mappings.

### Step 3: Liquid Template Linting

The AI Toolkit checks Liquid templates for syntax errors, deprecated filters, and performance anti-patterns:

| Issue | Bad | Fix |
|-------|-----|-----|
| Deprecated filter | `img_url: '800x'` | `image_url: width: 800` |
| Scope leak | `{% include 'card' %}` | `{% render 'card', product: product %}` |
| Unbounded loop | `collections.all.products` | Add `limit: 50` or use `paginate` |

### Step 4: Documentation Search

Query Shopify's official documentation through the MCP server for up-to-date API information:

```
# Example MCP queries you can make:
# - "What fields are available on the Product object?"
# - "Show me the companyCreate mutation input shape"
# - "What scopes do I need for B2B operations?"
# - "What changed in the 2024-10 API version?"
```

This is especially useful for checking API version changes and deprecated fields without leaving your editor.

See [references/workflow-integration.md](references/workflow-integration.md) for combining MCP tools with other shopify-pack skills.

## Output

- MCP server configured and connected to your Shopify store
- GraphQL queries validated against live schema before execution
- Liquid templates linted for deprecated filters and anti-patterns
- Real-time documentation search available in Claude Code

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `MCP connection refused` | MCP server failed to start | Check Node.js version (18+), run `npx @shopify/ai-toolkit-mcp` manually to see errors |
| `Invalid access token` | Token expired or wrong format | Regenerate token in Shopify admin (Settings > Apps > Develop apps) |
| `Schema introspection failed` | Insufficient API scopes | Add `read_products` and `read_themes` scopes to your app |
| `Rate limited on doc queries` | Too many documentation requests | Space out queries; docs are cached after first fetch |
| `ENOENT: .mcp.json not found` | Config file missing or wrong location | Must be in project root or `~/.claude/.mcp.json` for global config |
| `Package not found` | MCP package name changed | Check shopify.dev/docs for the current official package name |

## Examples

### Validating a GraphQL Mutation Before Execution

You need to call `productCreate` but aren't sure which input fields changed in the latest API version. Use the MCP server to validate your query against the live schema.

See [GraphQL Validation](references/graphql-validation.md) for common validation errors and deprecated field mappings.

### Setting Up MCP for a Team Project

Configure the Shopify MCP server at project, user, and global levels so the entire team gets schema validation automatically.

See [MCP Config](references/mcp-config.md) for advanced configuration and troubleshooting.

### Combining MCP Validation with Other Shopify Skills

Chain MCP schema validation before running mutations from other shopify-pack skills like B2B or checkout extensions.

See [Workflow Integration](references/workflow-integration.md) for the combined workflow patterns.

## Resources

- [Shopify AI Toolkit](https://shopify.dev/docs/apps/build/ai)
- [MCP Server Protocol](https://modelcontextprotocol.io/docs)
- [Shopify Admin API Reference](https://shopify.dev/docs/api/admin-graphql)
- [Shopify Theme Liquid Reference](https://shopify.dev/docs/api/liquid)
- [Shopify App Scopes](https://shopify.dev/docs/api/usage/access-scopes)
