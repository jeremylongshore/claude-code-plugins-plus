---
name: windsurf-api-development
description: |
  Generate API clients and documentation with Cascade. Activate when users mention
  "generate api client", "api documentation", "openapi generation", "sdk generation",
  or "api integration". Handles API development workflows.
allowed-tools: Read,Write,Edit,Bash,Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf API Development

Generate API clients and documentation with Cascade AI assistance.

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

## API Features

### Client Generation
- TypeScript/JavaScript clients
- Python clients
- Type-safe implementations
- Error handling patterns

### Documentation
- OpenAPI/Swagger docs
- Interactive examples
- SDK documentation
- Changelog generation

## Configuration Steps

1. **Define API Specification**
   - Create/import OpenAPI spec
   - Define schemas
   - Document endpoints

2. **Generate Clients**
   - Select target languages
   - Configure generation
   - Generate code

3. **Create Documentation**
   - Generate reference docs
   - Add examples
   - Publish documentation

## Success Criteria

- Clients pass contract tests
- 100% endpoint coverage
- 75% reduction in integration time
