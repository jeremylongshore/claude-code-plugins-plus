---
name: windsurf-custom-prompts
description: |
  Create and manage custom prompt libraries for Cascade. Activate when users mention
  "custom prompts", "prompt library", "prompt templates", "cascade prompts",
  or "prompt management". Handles prompt library creation and organization.
allowed-tools: Read,Write,Edit,Grep,Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Custom Prompts

Create and manage custom prompt libraries for team knowledge sharing.

## Directory Structure

```
project-root/
    .windsurf/
        prompts/
            library/
                index.json               # Prompt library index
                    # Prompt categories
                    # Search metadata
                    # Usage statistics

                code-generation/
                    react-component.prompt.md    # React component prompt
                        # Component structure
                        # Props definition
                        # Style integration

                    api-endpoint.prompt.md       # API endpoint prompt
                        # Route definition
                        # Handler structure
                        # Error handling

                    database-query.prompt.md     # Query generation prompt
                        # Schema context
                        # Optimization hints
                        # Safety checks

                code-review/
                    security-review.prompt.md    # Security review prompt
                        # Vulnerability checklist
                        # Best practice validation
                        # Fix suggestions

                    performance-review.prompt.md # Performance review prompt
                        # Bottleneck identification
                        # Optimization opportunities
                        # Benchmark comparison

                documentation/
                    api-docs.prompt.md           # API documentation prompt
                        # OpenAPI generation
                        # Example creation
                        # Error documentation

                    readme.prompt.md             # README generation prompt
                        # Project description
                        # Installation steps
                        # Usage examples

            variables/
                project-context.json         # Project-specific variables
                    # Framework name
                    # Coding standards
                    # Team preferences

                tech-stack.json              # Technology stack variables
                    # Languages
                    # Frameworks
                    # Tools

            favorites.json                   # Frequently used prompts
                # Quick access list
                # Usage counts
                # Last used timestamps
```

## Prompt Features

### Organization
- Category-based structure
- Tag-based search
- Usage tracking
- Version history

### Sharing
- Team libraries
- Personal collections
- Import/export
- Sync across devices

## Configuration Steps

1. **Create Prompt Library**
   - Define categories
   - Create initial prompts
   - Add metadata

2. **Configure Variables**
   - Define project context
   - Set up substitutions
   - Create templates

3. **Enable Team Sharing**
   - Share library with team
   - Set up sync
   - Track usage

## Success Criteria

- 95%+ precision on context retrieval
- Reusable prompts across team
- Knowledge captured and shared
