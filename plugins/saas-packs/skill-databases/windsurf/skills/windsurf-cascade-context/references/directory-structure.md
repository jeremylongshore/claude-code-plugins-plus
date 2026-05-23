# Directory Structure

## Directory Structure

```
project-root/
    .windsurf/
        context/
            project-overview.md      # High-level project context
                # Architecture summary
                # Key components and relationships
                # Technology stack overview

            module-index.md          # Module reference map
                # Directory to module mapping
                # Key files per module
                # Inter-module dependencies

            api-surface.md           # Public API documentation
                # Exported functions and classes
                # API contracts and types
                # Usage examples

            conventions.md           # Coding conventions
                # Naming patterns
                # File organization rules
                # Common patterns and anti-patterns

        memory/
            session-context.json     # Current session state
                # Recently accessed files
                # Active conversation threads
                # Pending operations

            pinned-context.json      # Persistent context items
                # Critical files always in context
                # Key architectural decisions
                # Team agreements

    .windsurfrules                   # Context behavior rules
        # Context prioritization
        # File relevance scoring
        # Memory management preferences
```
