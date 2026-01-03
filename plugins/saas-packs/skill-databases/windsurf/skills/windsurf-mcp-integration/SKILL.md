---
name: windsurf-mcp-integration
description: |
  Integrate MCP servers with Windsurf for extended capabilities. Activate when users mention
  "mcp integration", "model context protocol", "external tools", "mcp server",
  or "cascade tools". Handles MCP server configuration and integration.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf MCP Integration

Integrate Model Context Protocol servers for extended AI capabilities.

## Directory Structure

```
project-root/
    .windsurf/
        mcp/
            config.json                  # MCP configuration
                # Enabled servers
                # Connection settings
                # Authentication

            servers/
                filesystem.json          # Filesystem MCP server
                    # Allowed paths
                    # Operation permissions
                    # Sandbox settings

                database.json            # Database MCP server
                    # Connection strings
                    # Query permissions
                    # Schema access

                git.json                 # Git MCP server
                    # Repository access
                    # Operation limits
                    # Branch permissions

                custom/
                    internal-api.json    # Custom internal API server
                        # Endpoint configuration
                        # Authentication tokens
                        # Rate limits

            tools/
                tool-registry.json       # Available MCP tools
                    # Tool definitions
                    # Parameter schemas
                    # Usage examples

                tool-permissions.json    # Tool access control
                    # User permissions
                    # Context restrictions
                    # Audit requirements

            schemas/
                request-schema.json      # MCP request schema
                    # Tool invocation format
                    # Parameter validation
                    # Response handling

                response-schema.json     # MCP response schema
                    # Success formats
                    # Error handling
                    # Streaming support
```

## MCP Features

### Available Servers
- Filesystem operations
- Database queries
- Git operations
- Custom API integrations

### Security
- Sandboxed execution
- Permission controls
- Audit logging
- Rate limiting

## Configuration Steps

1. **Enable MCP Servers**
   - Select required servers
   - Configure connections
   - Set permissions

2. **Configure Tools**
   - Register available tools
   - Define parameter schemas
   - Set access controls

3. **Test Integration**
   - Verify tool access
   - Test in Cascade
   - Monitor performance

## Success Criteria

- MCP tools available in Cascade
- Sub-second response times
- External capabilities accessible seamlessly
