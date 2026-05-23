# Directory Structure

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
