---
name: windsurf-cascade-context
description: |
  Manage Cascade context window and memory for complex projects. Activate when users mention
  "cascade context", "ai memory", "context management", "large codebase navigation",
  or "multi-session development". Handles context optimization and persistence.
allowed-tools: Read,Write,Edit,Grep,Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Cascade Context Management

Optimize Cascade context window for large codebases and complex projects.

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

## Context Optimization

### Priority Levels
1. **Critical** - Always in context (pinned)
2. **High** - Recent edits and related files
3. **Medium** - Same module files
4. **Low** - Project-wide utilities

### Context Strategies
- Pin architectural decision records
- Include test files with source
- Reference documentation inline
- Maintain dependency graph awareness

## Configuration Steps

1. **Map Project Structure**
   - Create module index
   - Document dependencies
   - Identify critical paths

2. **Configure Context Priorities**
   - Pin essential files
   - Set relevance weights
   - Configure memory limits

3. **Optimize for Workflow**
   - Adjust context window size
   - Configure persistence settings
   - Set up context preloading

## Success Criteria

- Context maintained across 100+ file references
- Accurate cross-file understanding
- 50% faster complex refactoring
