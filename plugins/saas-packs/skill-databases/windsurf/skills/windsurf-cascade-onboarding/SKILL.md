---
name: windsurf-cascade-onboarding
description: |
  Configure Cascade AI agent for new team projects. Activate when users mention
  "setup cascade", "configure windsurf ai", "initialize cascade agent", "new windsurf project",
  or "onboard team to windsurf". Handles agent configuration, context settings, and team defaults.
allowed-tools: Read,Write,Edit,Bash,Grep,Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Cascade Onboarding

Configure Cascade AI agent for optimal team productivity from day one.

## Directory Structure

```
project-root/
    .windsurfrules           # Project-specific AI rules and context
        # YAML configuration defining Cascade behavior patterns
        # Includes code style preferences, framework conventions
        # Custom instructions for project-specific patterns

    .windsurf/
        cascade-config.json  # Cascade agent settings
            # Model preferences and temperature settings
            # Context window configuration
            # Response format preferences

        context/
            project-context.md   # High-level project description
                # Architecture overview for AI understanding
                # Key dependencies and their purposes
                # Team conventions and coding standards

            patterns.md          # Common patterns in codebase
                # Design patterns used in project
                # API conventions and naming schemes
                # Error handling approaches

        snippets/
            README.md            # Snippet library documentation
                # How to add new snippets
                # Snippet naming conventions

            component.snippet    # Reusable code templates
                # Framework-specific component templates
                # Common boilerplate patterns

    docs/
        windsurf-guide.md    # Team Windsurf usage guide
            # Best practices for Cascade interactions
            # Common prompts and their use cases
            # Troubleshooting common issues
```

## Configuration Steps

1. **Initialize Windsurf Rules**
   - Create `.windsurfrules` with project conventions
   - Define code style and framework preferences
   - Set up language-specific instructions

2. **Configure Cascade Context**
   - Add project architecture documentation
   - Define key patterns and conventions
   - Include dependency documentation

3. **Set Up Team Defaults**
   - Configure shared snippets
   - Establish prompt templates
   - Document best practices

## Success Criteria

- Cascade responds within 2 seconds to prompts
- Context maintained across 50+ file edits
- Team productivity increases 40% in first week
