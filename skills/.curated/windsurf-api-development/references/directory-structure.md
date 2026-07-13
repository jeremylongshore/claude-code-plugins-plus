# Directory Structure

## Directory Structure

```
project-root/
    api/
        specs/
            openapi.yaml                 # OpenAPI specification
                # Endpoint definitions
                # Schema definitions
                # Authentication specs

            graphql.schema.graphql       # GraphQL schema
                # Type definitions
                # Query definitions
                # Mutation definitions

        clients/
            typescript/
                index.ts                 # Generated TypeScript client
                    # API class definition
                    # Method implementations
                    # Type exports

                types.ts                 # Type definitions
                    # Request types
                    # Response types
                    # Error types

            python/
                client.py                # Generated Python client
                    # Client class
                    # Method implementations
                    # Type hints

        docs/
            api-reference.md             # API reference documentation
                # Endpoint descriptions
                # Parameter details
                # Response examples

            getting-started.md           # Quick start guide
                # Installation
                # Authentication
                # First request

    .windsurf/
        api/
            templates/
                client-template.ts       # Client generation template
                    # Class structure
                    # Method patterns
                    # Error handling

                docs-template.md         # Documentation template
                    # Section structure
                    # Example format
                    # Link patterns

            config/
                generation-config.json   # Generation settings
                    # Output paths
                    # Language targets
                    # Style preferences
```
