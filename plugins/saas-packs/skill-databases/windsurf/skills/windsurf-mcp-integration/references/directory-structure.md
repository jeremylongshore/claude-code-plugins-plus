# Directory Structure

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
